"""
FileFerry AI Agent - AWS Bedrock-powered intelligent file transfer orchestration
Handles natural language processing, decision making, and transfer coordination

Architecture Notes:
- Currently using AWS DynamoDB for user context storage (with temporary bypass)
- TODO: Migrate to Azure Cosmos DB for production deployment
  - Benefits: Better support for chat history (2MB vs 400KB item limit)
  - User context isolation with partition keys
  - Low-cost scalable Vector Search for semantic file matching
  - Multi-region writes for global availability
"""

import json
import boto3
import asyncio
import os

# Disable X-Ray tracing in local development
if os.getenv('AWS_EXECUTION_ENV') is None:
    from aws_xray_sdk.core import xray_recorder
    xray_recorder.configure(context_missing='LOG_ERROR')

from datetime import datetime
from typing import Dict, List, Any, Optional
from aws_xray_sdk.core import xray_recorder
from botocore.exceptions import ClientError

from src.storage.dynamodb_manager import DynamoDBManager
from src.handlers.sso_handler import SSOHandler
from src.ai_agent.agent_tools import AgentTools
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BedrockFileFerryAgent:
    """
    Main AI Agent orchestrator using AWS Bedrock Claude 3.5 Sonnet v2
    Processes natural language requests and executes file transfer workflows
    
    Architecture:
    - AWS Bedrock for natural language understanding
    - Tool calling for S3, transfer, and ServiceNow operations
    - Conversation history for context-aware responses
    - DynamoDB for user context (plan to migrate to Azure Cosmos DB)
    
    Future Enhancement:
    - Azure Cosmos DB will provide:
      * Better chat history storage (2MB item limit vs DynamoDB 400KB)
      * Built-in vector search for semantic file matching
      * User context isolation with hierarchical partition keys
      * Multi-region writes for global availability
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Bedrock AI Agent with AWS services

        Args:
            config: Configuration dictionary with AWS settings and agent parameters
        """
        self.config = config
        self.region = config.get('aws', {}).get('region', 'us-east-1')
        self.model_id = config.get('bedrock', {}).get('model_id', 
                                                'us.anthropic.claude-3-5-sonnet-20241022-v2:0')
        
        # Initialize AWS Bedrock client
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region
        )
        
        # Initialize supporting services
        self.dynamodb_manager = DynamoDBManager(config)
        self.sso_handler = SSOHandler(config)
        self.agent_tools = AgentTools(config)
        
        # Agent configuration
        self.max_history_length = config.get('agent', {}).get('max_history_length', 10)
        self.high_latency_threshold = config.get('agent', {}).get('high_latency_threshold', 5.0)
        
        # Feature flags
        self.enable_context_storage = config.get('agent', {}).get('enable_context_storage', False)
        
        logger.info(f"✅ Initialized BedrockFileFerryAgent with model: {self.model_id}")
        logger.info(f"📊 Max history length: {self.max_history_length}, Latency threshold: {self.high_latency_threshold}s")
        
        if not self.enable_context_storage:
            logger.warning("⚠️ Context storage is DISABLED - using temporary in-memory context")
        
        # Log future migration plan
        logger.info("📝 Future: Plan to migrate to Azure Cosmos DB for better chat history support")

    @xray_recorder.capture('process_natural_language_request')
    async def process_natural_language_request(
        self,
        user_id: str,
        user_message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process natural language request from user

        Args:
            user_id: User identifier
            user_message: Natural language message from user
            session_id: Optional session identifier for conversation context

        Returns:
            Dict containing agent response and metadata
        """
        try:
            start_time = datetime.utcnow()
            
            # ════════════════════════════════════════════════════════════
            # 🔧 CONTEXT STORAGE - DynamoDB with Azure Cosmos DB Migration Plan
            # ════════════════════════════════════════════════════════════
            # Current State: DynamoDB with temporary bypass due to schema mismatch
            # 
            # Migration Plan to Azure Cosmos DB:
            # 1. Data Model:
            #    - Container: user_contexts
            #    - Partition Key: user_id (ensures user isolation)
            #    - Hierarchical Partition Key (HPK): [user_id, session_id]
            #      * Overcomes 20GB single partition limit
            #      * Enables efficient queries across user sessions
            # 
            # 2. Item Structure (within 2MB limit):
            #    {
            #      "id": "user123_session456",
            #      "user_id": "user123",
            #      "session_id": "session456",
            #      "conversation_history": [...],
            #      "preferences": {...},
            #      "embeddings": [...],  // For vector search
            #      "last_interaction": "2025-12-03T10:00:00Z",
            #      "ttl": 1234567890  // Auto-cleanup old sessions
            #    }
            # 
            # 3. Benefits over DynamoDB:
            #    ✅ 2MB item limit (vs 400KB) - store longer conversations
            #    ✅ Built-in vector search - semantic file/conversation search
            #    ✅ Multi-region writes - global availability
            #    ✅ Better support for chat/AI workloads
            # 
            # 4. SDK Migration:
            #    from azure.cosmos import CosmosClient, PartitionKey
            #    client = CosmosClient(endpoint, credential)
            #    container = database.get_container_client('user_contexts')
            #    
            #    # Upsert with diagnostics
            #    response = container.upsert_item(context)
            #    logger.info(f"Cosmos diagnostics: {response['_diagnostics']}")
            # ════════════════════════════════════════════════════════════
            
            if self.enable_context_storage:
                # Production path: Load from DynamoDB/Cosmos DB
                try:
                    user_context = await self.dynamodb_manager.load_user_context(user_id)
                    logger.info(f"✅ Loaded user context from storage for user {user_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to load user context: {str(e)}")
                    logger.warning(f"⚠️ Falling back to temporary context for user {user_id}")
                    user_context = self._create_temporary_context(user_id)
            else:
                # Development/Testing path: Use temporary in-memory context
                logger.info(f"⚠️ Using temporary in-memory context for user {user_id} (storage disabled)")
                user_context = self._create_temporary_context(user_id)
            
            conversation_history = user_context.get('conversation_history', [])
            
            # Add user message to history
            conversation_history.append({
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"💬 User {user_id} message: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
            
            # Call Bedrock with conversation context
            response = await self._call_bedrock(
                conversation_history=conversation_history,
                user_context=user_context
            )
            
            # Add assistant response to history
            conversation_history.append({
                'role': 'assistant',
                'content': response['content'],
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Trim history if too long (keep last N turns)
            max_messages = self.max_history_length * 2  # 2 messages per turn (user + assistant)
            if len(conversation_history) > max_messages:
                removed_count = len(conversation_history) - max_messages
                conversation_history = conversation_history[-max_messages:]
                logger.info(f"📝 Trimmed conversation history: removed {removed_count} old messages")
            
            # Update user context (only if storage is enabled)
            if self.enable_context_storage:
                try:
                    user_context['conversation_history'] = conversation_history
                    user_context['last_interaction'] = datetime.utcnow().isoformat()
                    user_context['total_interactions'] = user_context.get('total_interactions', 0) + 1
                    
                    await self.dynamodb_manager.store_user_context(user_id, user_context)
                    logger.info(f"✅ Updated user context for {user_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to store user context: {str(e)}")
                    logger.warning("⚠️ Context changes will be lost after this session")
            else:
                logger.debug(f"⏭️ Skipped context storage (disabled in config)")
            
            # Calculate processing time and capture diagnostics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log diagnostic information if latency exceeds threshold
            # (Following Azure Cosmos DB diagnostic logging best practices)
            if processing_time > self.high_latency_threshold:
                logger.warning(
                    f"⚠️ HIGH LATENCY DETECTED: {processing_time:.2f}s for user {user_id}",
                    extra={
                        'processing_time': processing_time,
                        'threshold': self.high_latency_threshold,
                        'user_id': user_id,
                        'message_length': len(user_message),
                        'history_length': len(conversation_history),
                        'tool_calls': len(response.get('tool_calls', []))
                    }
                )
            
            # Log token usage for cost tracking
            usage = response.get('usage', {})
            if usage:
                logger.info(
                    f"📊 Token usage - Input: {usage.get('input_tokens', 0)}, "
                    f"Output: {usage.get('output_tokens', 0)}"
                )
            
            return {
                'success': True,
                'response': response['content'],
                'metadata': {
                    'processing_time': processing_time,
                    'tool_calls': response.get('tool_calls', []),
                    'model': self.model_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'conversation_length': len(conversation_history) // 2,  # Number of turns
                    'token_usage': usage,
                    'context_storage_enabled': self.enable_context_storage
                }
            }
            
        except Exception as e:
            logger.error(
                f"❌ Error processing request for user {user_id}: {str(e)}", 
                exc_info=True,
                extra={
                    'user_id': user_id,
                    'error_type': type(e).__name__,
                    'message': user_message[:100] if user_message else None
                }
            )
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }

    def _create_temporary_context(self, user_id: str) -> Dict[str, Any]:
        """
        Create temporary in-memory user context
        
        Args:
            user_id: User identifier
            
        Returns:
            Temporary user context dictionary
            
        Note:
            In Azure Cosmos DB migration, this would be:
            - Container: user_contexts
            - Partition Key: user_id
            - TTL: 86400 (24 hours for temporary sessions)
        """
        return {
            'user_id': user_id,
            'conversation_history': [],
            'preferences': {},
            'last_interaction': None,
            'total_interactions': 0,
            'created_at': datetime.utcnow().isoformat(),
            'context_type': 'temporary_in_memory'
        }

    @xray_recorder.capture('call_bedrock')
    async def _call_bedrock(
        self,
        conversation_history: List[Dict[str, str]],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call AWS Bedrock API with conversation history and tool definitions

        Args:
            conversation_history: List of conversation messages
            user_context: User context information

        Returns:
            Dict containing assistant response and metadata
        """
        try:
            # Prepare system prompt with user context
            system_prompt = self._get_system_prompt(user_context)
            
            # Prepare tool definitions
            tools = self._get_agent_tools()
            
            # Prepare messages (exclude timestamp for API call)
            messages = [
                {
                    'role': msg['role'],
                    'content': msg['content']
                }
                for msg in conversation_history
            ]
            
            # Prepare request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.config.get('bedrock', {}).get('max_tokens', 4096),
                "system": system_prompt,
                "messages": messages,
                "tools": tools,
                "temperature": self.config.get('bedrock', {}).get('temperature', 0.7)
            }
            
            logger.debug(f"🤖 Calling Bedrock API with {len(messages)} messages and {len(tools)} tools")
            
            # Call Bedrock API with diagnostic timing
            api_start = datetime.utcnow()
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            api_duration = (datetime.utcnow() - api_start).total_seconds()
            
            logger.info(f"✅ Bedrock API call completed in {api_duration:.2f}s")
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Log stop reason for diagnostics
            stop_reason = response_body.get('stop_reason')
            logger.debug(f"🛑 Stop reason: {stop_reason}")
            
            # Handle tool use if present
            if stop_reason == 'tool_use':
                logger.info("🔧 Claude requested tool execution")
                tool_results = await self._execute_tools(response_body, user_context)
                
                # Continue conversation with tool results
                messages.append({
                    'role': 'assistant',
                    'content': response_body['content']
                })
                messages.append({
                    'role': 'user',
                    'content': tool_results
                })
                
                # Recursive call to get final response
                logger.debug("🔄 Continuing conversation with tool results")
                return await self._call_bedrock(messages, user_context)
            
            # Extract text response
            text_content = ''
            tool_calls_made = []
            
            for content_block in response_body.get('content', []):
                if content_block.get('type') == 'text':
                    text_content += content_block.get('text', '')
                elif content_block.get('type') == 'tool_use':
                    tool_calls_made.append(content_block.get('name'))
            
            return {
                'content': text_content,
                'stop_reason': stop_reason,
                'usage': response_body.get('usage', {}),
                'tool_calls': tool_calls_made,
                'api_duration': api_duration
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            logger.error(
                f"❌ Bedrock API error [{error_code}]: {error_message}", 
                exc_info=True,
                extra={
                    'error_code': error_code,
                    'model_id': self.model_id,
                    'region': self.region
                }
            )
            
            # Provide helpful error messages
            if error_code == 'AccessDeniedException':
                logger.error(
                    "💡 Fix: Attach 'AmazonBedrockFullAccess' policy to your IAM user/role. "
                    "Run: aws iam attach-user-policy --user-name YOUR_USER "
                    "--policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
                )
            elif error_code == 'ThrottlingException':
                logger.error(
                    "💡 Bedrock rate limit exceeded. Consider implementing exponential backoff "
                    "or requesting quota increase."
                )
            
            raise
            
        except Exception as e:
            logger.error(
                f"❌ Unexpected error calling Bedrock: {str(e)}", 
                exc_info=True,
                extra={
                    'model_id': self.model_id,
                    'error_type': type(e).__name__
                }
            )
            raise

    async def _execute_tools(
        self,
        response_body: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute tools requested by Claude

        Args:
            response_body: Bedrock response containing tool use requests
            user_context: User context information

        Returns:
            List of tool results
        """
        tool_results = []
        
        for content_block in response_body.get('content', []):
            if content_block.get('type') == 'tool_use':
                tool_use_id = content_block.get('id')
                tool_name = content_block.get('name')
                tool_input = content_block.get('input', {})
                
                logger.info(f"🔧 Executing tool: {tool_name}")
                logger.debug(f"📥 Tool input: {json.dumps(tool_input, indent=2)}")
                
                try:
                    # Execute tool with X-Ray tracing and timing
                    tool_start = datetime.utcnow()
                    
                    # Safe X-Ray handling for local development
                    # (No X-Ray daemon running locally)
                    subsegment = None
                    try:
                        subsegment = xray_recorder.begin_subsegment(f'tool_{tool_name}')
                        if subsegment:
                            subsegment.put_metadata('tool_input', tool_input)
                    except Exception:
                        # X-Ray not available in local mode, continue without tracing
                        pass
                    
                    try:
                        result = await self.agent_tools.execute(
                            tool_name=tool_name,
                            tool_input=tool_input,
                            user_context=user_context
                        )
                        
                        if subsegment:
                            subsegment.put_metadata('tool_result', result)
                    finally:
                        # Close subsegment if it was created
                        if subsegment:
                            try:
                                xray_recorder.end_subsegment()
                            except Exception:
                                pass  # Ignore X-Ray errors in local mode
                    
                    tool_duration = (datetime.utcnow() - tool_start).total_seconds()
                    logger.info(f"✅ Tool {tool_name} completed in {tool_duration:.2f}s")
                    logger.debug(f"📤 Tool result: {json.dumps(result, indent=2)[:500]}...")
                    
                    tool_results.append({
                        'type': 'tool_result',
                        'tool_use_id': tool_use_id,
                        'content': json.dumps(result)
                    })
                    
                except Exception as e:
                    logger.error(
                        f"❌ Tool execution error for {tool_name}: {str(e)}", 
                        exc_info=True,
                        extra={
                            'tool_name': tool_name,
                            'tool_input': tool_input,
                            'error_type': type(e).__name__
                        }
                    )
                    
                    tool_results.append({
                        'type': 'tool_result',
                        'tool_use_id': tool_use_id,
                        'content': json.dumps({
                            'error': str(e),
                            'error_type': type(e).__name__,
                            'tool_name': tool_name
                        }),
                        'is_error': True
                    })
        
        return tool_results

    def _get_system_prompt(self, user_context: Dict[str, Any]) -> str:
        """
        Generate system prompt for Claude with context and instructions

        Args:
            user_context: User context information

        Returns:
            System prompt string
        """
        user_id = user_context.get('user_id', 'unknown')
        user_preferences = user_context.get('preferences', {})
        total_interactions = user_context.get('total_interactions', 0)
        context_type = user_context.get('context_type', 'persistent')
        
        prompt = f"""You are FileFerry AI Agent, an intelligent file transfer orchestration assistant powered by Claude 3.5 Sonnet.

Your role is to help users transfer files from AWS S3 buckets to FTP/SFTP destinations with:
- Natural language understanding of transfer requests
- Automated ServiceNow ticket creation for audit trails
- Secure SSO authentication with 10-second auto-logout
- Intelligent transfer strategy recommendations based on file size and type
- Real-time progress monitoring and notifications
- Historical data analysis for transfer success prediction

SECURITY REQUIREMENTS:
1. Users have READ-ONLY access to S3 buckets
2. SSO sessions MUST auto-logout after 10 seconds for security
3. ALL transfers require dual ServiceNow tickets (user ticket + audit ticket)
4. Always validate user access before any S3 operations
5. Never expose AWS credentials or sensitive configuration

DECISION FRAMEWORK:
1. Analyze transfer requests for file size, type, and destination compatibility
2. Predict transfer success based on historical data:
   - HIGH confidence: 20+ historical samples available
   - MEDIUM confidence: 5-19 samples available
   - LOW confidence: <5 samples (recommend caution)
3. Recommend optimal transfer strategies:
   - Small files (<100MB): Direct transfer, 5MB chunks, single thread
   - Medium files (100MB-1GB): Parallel transfer, 10MB chunks, 3-4 threads
   - Large files (>1GB): Parallel with optional compression, 20MB chunks, 5-8 threads
4. Always create ServiceNow tickets BEFORE initiating transfers
5. Monitor transfer progress and provide proactive status updates

USER CONTEXT:
- User ID: {user_id}
- Total Interactions: {total_interactions}
- Preferences: {json.dumps(user_preferences) if user_preferences else 'None set'}
- Context Storage: {context_type}

RESPONSE STYLE:
- Be conversational, helpful, and professional
- Provide clear explanations for all recommendations
- Ask clarifying questions when transfer details are missing or ambiguous
- Show confidence levels for predictions (High/Medium/Low)
- Proactively suggest optimizations based on file characteristics
- Use emojis sparingly for visual clarity (✅, ⚠️, 📊, 🔄, etc.)
- If context storage is temporary, inform user that conversation history is not persisted

AVAILABLE TOOLS:
Use the provided tools to execute actions. Follow this workflow:
1. Validate user access to S3 resources
2. Get file metadata and analyze transfer requirements
3. Create ServiceNow tickets (dual tickets required)
4. Execute transfer with recommended strategy
5. Provide status updates and completion confirmation

IMPORTANT: Always validate prerequisites before tool execution. Never assume access or skip security checks.
"""
        
        return prompt

    def _get_agent_tools(self) -> List[Dict[str, Any]]:
        """
        Define available tools for Claude to use in Anthropic tool calling format

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "list_s3_buckets",
                "description": "List all S3 buckets accessible to the user in the specified AWS region. Authenticates with SSO and auto-logout after 10 seconds. Returns bucket names, creation dates, and region information.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "AWS region to list buckets from (e.g., us-east-1, us-west-2, eu-west-1)"
                        }
                    },
                    "required": ["region"]
                }
            },
            {
                "name": "list_bucket_contents",
                "description": "List contents of an S3 bucket with optional prefix filtering. Returns paginated results with file names, sizes, last modified dates, and storage classes. Use prefix to navigate folder structures.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bucket_name": {
                            "type": "string",
                            "description": "Name of the S3 bucket to list contents from"
                        },
                        "prefix": {
                            "type": "string",
                            "description": "Optional prefix to filter objects (e.g., 'folder/', 'data/2024/'). Leave empty to list root level."
                        },
                        "max_items": {
                            "type": "integer",
                            "description": "Maximum number of items to return (default: 100, max: 1000)"
                        }
                    },
                    "required": ["bucket_name"]
                }
            },
            {
                "name": "get_file_metadata",
                "description": "Get detailed metadata for a specific S3 object including size, content type, last modified date, storage class, and ETag. Results are cached for 24 hours to improve performance. Essential for transfer strategy planning.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bucket_name": {
                            "type": "string",
                            "description": "Name of the S3 bucket containing the file"
                        },
                        "file_key": {
                            "type": "string",
                            "description": "S3 object key (full file path within bucket, e.g., 'folder/subfolder/file.csv')"
                        }
                    },
                    "required": ["bucket_name", "file_key"]
                }
            },
            {
                "name": "validate_user_access",
                "description": "Validate that the user has read access to the specified S3 bucket and object. Returns access status and any permission issues. Always call this before attempting transfers.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bucket_name": {
                            "type": "string",
                            "description": "Name of the S3 bucket to validate access for"
                        },
                        "file_key": {
                            "type": "string",
                            "description": "S3 object key (file path) to validate access for"
                        }
                    },
                    "required": ["bucket_name", "file_key"]
                }
            },
            {
                "name": "analyze_transfer_request",
                "description": "Analyze a transfer request and recommend optimal transfer strategy based on file size, type, destination characteristics, and historical performance data. Returns recommended chunk size, thread count, compression settings, and estimated duration.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bucket_name": {
                            "type": "string",
                            "description": "Source S3 bucket name"
                        },
                        "file_key": {
                            "type": "string",
                            "description": "Source S3 object key (file path)"
                        },
                        "destination_type": {
                            "type": "string",
                            "description": "Destination protocol type",
                            "enum": ["FTP", "SFTP"]
                        },
                        "destination_host": {
                            "type": "string",
                            "description": "Destination FTP/SFTP hostname or IP address"
                        },
                        "destination_path": {
                            "type": "string",
                            "description": "Optional destination file path. If not provided, uses same name as source."
                        }
                    },
                    "required": ["bucket_name", "file_key", "destination_type", "destination_host"]
                }
            },
            {
                "name": "predict_transfer_outcome",
                "description": "Predict transfer success rate and estimated duration based on historical data. Analyzes past transfers with similar characteristics. Requires at least 20 historical samples for HIGH confidence predictions. Returns success probability, average duration, and confidence level.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transfer_type": {
                            "type": "string",
                            "description": "Transfer type based on destination",
                            "enum": ["S3_TO_FTP", "S3_TO_SFTP"]
                        },
                        "file_size_category": {
                            "type": "string",
                            "description": "File size category for prediction",
                            "enum": ["small", "medium", "large"]
                        }
                    },
                    "required": ["transfer_type", "file_size_category"]
                }
            },
            {
                "name": "create_servicenow_tickets",
                "description": "Create dual ServiceNow tickets (user ticket for user tracking + audit ticket for compliance) for the transfer request. REQUIRED before executing any transfer. Returns both ticket numbers. User ticket is assigned to requestor, audit ticket is for compliance team.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier (email or username)"
                        },
                        "transfer_details": {
                            "type": "object",
                            "description": "Complete transfer details including source bucket, file key, destination host, destination type, file size, and estimated duration",
                            "properties": {
                                "source_bucket": {"type": "string"},
                                "source_key": {"type": "string"},
                                "destination_host": {"type": "string"},
                                "destination_type": {"type": "string"},
                                "file_size_mb": {"type": "number"},
                                "estimated_duration": {"type": "string"}
                            }
                        },
                        "priority": {
                            "type": "string",
                            "description": "Ticket priority based on urgency and business impact",
                            "enum": ["low", "medium", "high"]
                        }
                    },
                    "required": ["user_id", "transfer_details"]
                }
            },
            {
                "name": "execute_transfer",
                "description": "Execute file transfer from S3 to FTP/SFTP destination. PREREQUISITES: ServiceNow tickets must be created first. Initiates AWS Step Functions state machine for the transfer workflow. Returns execution ARN for status tracking. Transfer runs asynchronously with progress updates.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transfer_request": {
                            "type": "object",
                            "description": "Complete transfer request with all required fields",
                            "properties": {
                                "source_bucket": {"type": "string"},
                                "source_key": {"type": "string"},
                                "destination_host": {"type": "string"},
                                "destination_type": {"type": "string"},
                                "destination_path": {"type": "string"},
                                "user_ticket_number": {"type": "string"},
                                "audit_ticket_number": {"type": "string"},
                                "strategy": {
                                    "type": "object",
                                    "properties": {
                                        "chunk_size_mb": {"type": "integer"},
                                        "parallel_threads": {"type": "integer"},
                                        "compression": {"type": "boolean"}
                                    }
                                }
                            },
                            "required": ["source_bucket", "source_key", "destination_host", "destination_type", "user_ticket_number", "audit_ticket_number"]
                        }
                    },
                    "required": ["transfer_request"]
                }
            },
            {
                "name": "get_transfer_history",
                "description": "Retrieve transfer history for the user. Returns recent transfers with status (success/failed/in-progress), duration, file details, and ServiceNow ticket numbers. Use this to show user their past transfers or troubleshoot issues.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier to retrieve history for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of transfers to return (default: 10, max: 50)"
                        },
                        "status_filter": {
                            "type": "string",
                            "description": "Optional filter by transfer status",
                            "enum": ["success", "failed", "in_progress", "all"]
                        }
                    },
                    "required": ["user_id"]
                }
            }
        ]

    async def get_transfer_status(self, execution_arn: str) -> Dict[str, Any]:
        """
        Get status of an ongoing transfer by Step Functions execution ARN

        Args:
            execution_arn: Step Functions execution ARN

        Returns:
            Dict containing transfer status and progress
        """
        try:
            sfn_client = boto3.client('stepfunctions', region_name=self.region)
            
            response = sfn_client.describe_execution(executionArn=execution_arn)
            
            status_info = {
                'status': response['status'],
                'start_date': response['startDate'].isoformat(),
                'execution_arn': execution_arn,
                'input': json.loads(response.get('input', '{}')),
                'output': json.loads(response.get('output', '{}')) if response.get('output') else None
            }
            
            # Add stop date if execution is complete
            if 'stopDate' in response:
                status_info['stop_date'] = response['stopDate'].isoformat()
                status_info['duration_seconds'] = (
                    response['stopDate'] - response['startDate']
                ).total_seconds()
            
            logger.info(f"📊 Transfer status retrieved: {status_info['status']}")
            
            return status_info
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"❌ Error getting transfer status [{error_code}]: {str(e)}", exc_info=True)
            return {
                'error': str(e),
                'error_code': error_code,
                'execution_arn': execution_arn
            }
        except Exception as e:
            logger.error(f"❌ Error getting transfer status: {str(e)}", exc_info=True)
            return {
                'error': str(e),
                'execution_arn': execution_arn
            }

    async def cancel_transfer(self, execution_arn: str, reason: str) -> Dict[str, Any]:
        """
        Cancel an ongoing transfer

        Args:
            execution_arn: Step Functions execution ARN
            reason: Cancellation reason

        Returns:
            Dict containing cancellation result
        """
        try:
            sfn_client = boto3.client('stepfunctions', region_name=self.region)
            
            sfn_client.stop_execution(
                executionArn=execution_arn,
                error='UserCancelled',
                cause=reason
            )
            
            logger.info(f"🛑 Cancelled transfer execution: {execution_arn}")
            logger.info(f"📝 Cancellation reason: {reason}")
            
            return {
                'success': True,
                'execution_arn': execution_arn,
                'reason': reason,
                'cancelled_at': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"❌ Error cancelling transfer [{error_code}]: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_code': error_code
            }
        except Exception as e:
            logger.error(f"❌ Error cancelling transfer: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }