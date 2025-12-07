"""
FileFerry AI Agent - AWS Bedrock Implementation
Uses Claude Sonnet 4.5 for natural language understanding and decision making
"""

import boto3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from aws_xray_sdk.core import xray_recorder

from ..storage.dynamodb_manager import DynamoDBManager
from ..handlers.sso_handler import SSOHandler
from ..ai_agent.agent_tools import AgentTools
from ..utils.logger import get_logger
from ..utils.tracing import traced_operation

logger = get_logger(__name__)


class BedrockFileFerryAgent:
    """
    Intelligent AI Agent for AWS S3 to FTP/SFTP transfers
    Uses AWS Bedrock (Claude Sonnet 4.5) for natural language processing
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AI Agent
        
        Args:
            config: Configuration dictionary containing:
                - aws.region: AWS region
                - aws.bedrock.model_id: Bedrock model ID
                - aws.dynamodb: DynamoDB configuration
                - aws.sso: SSO configuration
        """
        self.config = config
        
        # AWS Bedrock Runtime Client
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=config.get('aws', {}).get('region', 'us-east-1')
        )
        
        # DynamoDB for state management
        self.db_manager = DynamoDBManager(config)
        
        # SSO Handler
        self.sso_handler = SSOHandler(config.get('aws', {}).get('sso', {}))
        
        # Agent Tools
        self.tools = AgentTools(config, self.db_manager, self.sso_handler)
        
        # Model configuration
        self.model_id = config.get('aws', {}).get('bedrock', {}).get(
            'model_id', 
            'anthropic.claude-3-5-sonnet-20241022-v2:0'
        )
        
        # Conversation management
        self.active_conversations: Dict[str, List[Dict]] = {}
        
        logger.info(f"✅ FileFerry AI Agent initialized with model: {self.model_id}")
    
    @traced_operation(name="process_user_request")
    async def process_natural_language_request(
        self, 
        user_id: str, 
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user's natural language request using Claude Sonnet 4.5
        
        Args:
            user_id: User making the request
            message: Natural language input
            conversation_id: Optional conversation ID for context
            
        Returns:
            Agent response with execution plan and results
        """
        try:
            # Add custom tracing annotations
            xray_recorder.put_annotation('user_id', user_id)
            xray_recorder.put_annotation('message_length', len(message))
            
            # Load user context from DynamoDB
            user_context = await self.db_manager.load_user_context(user_id)
            
            # Get or create conversation history
            conv_id = conversation_id or f"conv_{user_id}_{int(datetime.utcnow().timestamp())}"
            conversation = self._get_conversation(conv_id, user_context)
            
            # Add user message to conversation
            conversation.append({
                "role": "user",
                "content": self._enrich_message_with_context(message, user_context)
            })
            
            # Call Claude Sonnet 4.5 via Bedrock
            start_time = datetime.utcnow()
            response = await self._call_bedrock(conversation)
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            # Log diagnostics if latency is high
            if latency > 5:
                logger.warning(
                    f"High Bedrock latency: {latency:.2f}s for user {user_id}",
                    extra={
                        "latency_seconds": latency,
                        "user_id": user_id,
                        "model_id": self.model_id
                    }
                )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Handle tool calls if present
            if response_body.get('stop_reason') == 'tool_use':
                tool_results = await self._execute_tools(
                    response_body['content'],
                    user_id
                )
                
                # Continue conversation with tool results
                conversation.append({
                    "role": "assistant",
                    "content": response_body['content']
                })
                conversation.append({
                    "role": "user",
                    "content": tool_results
                })
                
                # Get final response after tool execution
                final_response = await self._call_bedrock(conversation)
                response_body = json.loads(final_response['body'].read())
            
            # Extract agent message
            agent_message = self._extract_text_from_response(response_body)
            
            # Store conversation
            conversation.append({
                "role": "assistant",
                "content": agent_message
            })
            self.active_conversations[conv_id] = conversation
            
            # Store interaction in DynamoDB
            await self.db_manager.store_interaction(
                user_id=user_id,
                request=message,
                response=agent_message,
                conversation_id=conv_id
            )
            
            return {
                "status": "success",
                "agent_response": agent_message,
                "conversation_id": conv_id,
                "latency_seconds": latency,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            xray_recorder.put_annotation('error', str(e))
            
            return {
                "status": "error",
                "error": str(e),
                "user_friendly_message": "I encountered an error processing your request. Please try again or contact support.",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _call_bedrock(self, conversation: List[Dict]) -> Dict:
        """
        Call AWS Bedrock with conversation history
        
        Args:
            conversation: List of conversation messages
            
        Returns:
            Bedrock API response
        """
        with xray_recorder.capture('bedrock_inference'):
            try:
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "messages": conversation,
                        "system": self._get_system_prompt(),
                        "tools": self._get_agent_tools()
                    })
                )
                return response
            except Exception as e:
                logger.error(f"Bedrock API error: {str(e)}", exc_info=True)
                raise
    
    def _get_system_prompt(self) -> str:
        """System prompt for Claude Sonnet 4.5"""
        return """You are FileFerry, an intelligent AWS S3 file transfer agent.

## Your Mission
Autonomously manage secure, efficient file transfers from AWS S3 to FTP/SFTP servers while maintaining compliance and audit trails.

## Your Capabilities
1. **Natural Language Understanding**: Parse requests like "Get me the Q4 report from prod-bucket"
2. **AWS S3 Intelligence**: List buckets, browse contents, get metadata, validate access
3. **Transfer Optimization**: Analyze file size, network conditions, historical data to recommend optimal strategies
4. **Security & Compliance**: Enforce 10-second SSO logout, read-only S3 access, dual audit trails
5. **Learning & Prediction**: Learn from past transfers stored in DynamoDB to predict success rates
6. **Monitoring**: Real-time progress tracking with Teams notifications

## Decision Framework
When a user requests a file transfer:
1. **Parse intent** - Extract file name, bucket, region from natural language
2. **Validate access** - Check user has read permission via AWS SSO
3. **Assess file** - Get size, type, storage class from S3 metadata
4. **Query history** - Find similar past transfers in DynamoDB (by file size category + transfer type)
5. **Predict outcome** - Calculate success probability based on historical data (min 20 samples for confidence)
6. **Recommend strategy** - Determine chunk size, parallelization, compression based on file size:
   - Small (<100MB): Direct transfer, no chunking
   - Medium (100MB-1GB): 10MB chunks, 4 parallel uploads, compression
   - Large (>1GB): 20MB chunks, 8 parallel uploads, compression
7. **Create tickets** - Generate dual ServiceNow tickets (user + audit team)
8. **Execute transfer** - Start optimized transfer with real-time monitoring
9. **Learn** - Store outcome, metrics, and insights in DynamoDB for future predictions

## Security Requirements (Non-Negotiable)
- ❌ NEVER modify S3 objects (read-only access only)
- ❌ NEVER share credentials or session tokens
- ❌ NEVER bypass 10-second auto-logout policy
- ✅ ALWAYS validate user permissions before transfers
- ✅ ALWAYS create dual ServiceNow tickets (user + audit)
- ✅ ALWAYS enforce encryption in transit
- ✅ ALWAYS logout within 10 seconds of transfer initiation

## Response Style
- **Conversational**: Friendly, professional tone
- **Proactive**: Suggest optimizations ("This file is large, I'll use parallel transfer with 8 streams")
- **Transparent**: Explain decisions ("Based on 50 similar transfers, I predict 95% success rate")
- **Concise**: Respect user's time, avoid unnecessary details
- **Educational**: Help users understand best practices

## Example Interactions

**User**: "I need the Q4 sales report"

**You**: "I found 2 files matching 'Q4 sales report':
1. sales_Q4_2024.csv (150MB) in prod-data-bucket
2. sales_Q4_summary.xlsx (12MB) in analytics-bucket

Which one do you need? Reply with 1 or 2."

---

**User**: "1"

**You**: "Great! I'll transfer sales_Q4_2024.csv (150MB) from prod-data-bucket.

📊 Analysis:
• Success Rate: 98% (based on 73 similar transfers)
• Estimated Time: 2 minutes
• Strategy: 10MB chunks, 4 parallel uploads, gzip compression
• Risk Level: Low

📋 ServiceNow Tickets:
• User Ticket: INC0012345
• Audit Ticket: INC0012346

Ready to proceed? I'll start the transfer and logout in 10 seconds for security."

---

**User**: "yes"

**You**: "Transfer started! 🚀
⏳ Progress: 25%... 50%... 75%...
✅ Transfer complete! (1m 54s)

Results:
• Speed: 12.8 Mbps
• Size: 150 MB
• Destination: secure-ftp-01.company.com
• Session: Logged out automatically

This transfer was 8% faster than average for similar files. I've recorded these insights for future optimizations."

## Error Handling
When transfers fail:
1. **Diagnose**: Identify root cause (network, authentication, file access, destination)
2. **Assess retry eligibility**: Transient errors (network timeout) → retry, Permanent errors (no permission) → escalate
3. **Adjust strategy**: If retry, use smaller chunks or lower parallelization
4. **Retry intelligently**: Exponential backoff, max 3 attempts
5. **Escalate if needed**: Notify support team with detailed diagnostics

Always maintain a positive, helpful tone even during failures."""
    
    def _get_agent_tools(self) -> List[Dict]:
        """Define tools/functions for Claude"""
        return [
            {
                "name": "list_s3_buckets",
                "description": "List all S3 buckets accessible to the user. Use this when user asks about available buckets or wants to browse S3.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "Optional AWS region filter (e.g., us-east-1, us-west-2)"
                        }
                    }
                }
            },
            {
                "name": "list_bucket_contents",
                "description": "List contents of a specific S3 bucket with optional prefix filtering. Use this to show files in a bucket.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bucket_name": {
                            "type": "string",
                            "description": "Name of the S3 bucket"
                        },
                        "prefix": {
                            "type": "string",
                            "description": "Optional prefix/folder path to filter files (e.g., 'reports/2024/')"
                        },
                        "region": {
                            "type": "string",
                            "description": "AWS region of the bucket"
                        }
                    },
                    "required": ["bucket_name"]
                }
            },
            {
                "name": "get_file_metadata",
                "description": "Get detailed metadata for a specific S3 object including size, last modified date, storage class, and encryption info.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bucket_name": {
                            "type": "string",
                            "description": "Name of the S3 bucket"
                        },
                        "file_key": {
                            "type": "string",
                            "description": "Full key/path of the file in S3"
                        },
                        "region": {
                            "type": "string",
                            "description": "AWS region of the bucket"
                        }
                    },
                    "required": ["bucket_name", "file_key"]
                }
            },
            {
                "name": "validate_user_access",
                "description": "Validate that the user has read access to a specific S3 object. Always call this before attempting a transfer.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bucket_name": {
                            "type": "string",
                            "description": "Name of the S3 bucket"
                        },
                        "file_key": {
                            "type": "string",
                            "description": "Full key/path of the file"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User ID requesting access"
                        }
                    },
                    "required": ["bucket_name", "file_key", "user_id"]
                }
            },
            {
                "name": "analyze_transfer_request",
                "description": "Analyze a transfer request and recommend optimal transfer strategy based on file size and historical data.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_metadata": {
                            "type": "object",
                            "description": "File metadata from get_file_metadata"
                        },
                        "destination_type": {
                            "type": "string",
                            "enum": ["sftp", "ftp"],
                            "description": "Type of destination server"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User ID for context"
                        }
                    },
                    "required": ["file_metadata", "destination_type", "user_id"]
                }
            },
            {
                "name": "predict_transfer_outcome",
                "description": "Predict transfer success rate and duration using historical data from DynamoDB. Requires at least 20 similar transfers for high confidence.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_size_bytes": {
                            "type": "integer",
                            "description": "File size in bytes"
                        },
                        "transfer_type": {
                            "type": "string",
                            "enum": ["sftp", "ftp"],
                            "description": "Transfer protocol type"
                        },
                        "source_region": {
                            "type": "string",
                            "description": "AWS region of source S3 bucket"
                        }
                    },
                    "required": ["file_size_bytes", "transfer_type"]
                }
            },
            {
                "name": "create_servicenow_tickets",
                "description": "Create dual ServiceNow tickets (user + audit) for compliance. Always call this before executing a transfer.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User requesting the transfer"
                        },
                        "transfer_details": {
                            "type": "object",
                            "description": "Transfer details including file, bucket, destination"
                        },
                        "assignment_group": {
                            "type": "string",
                            "description": "ServiceNow assignment group (default: DataOps)",
                            "default": "DataOps"
                        }
                    },
                    "required": ["user_id", "transfer_details"]
                }
            },
            {
                "name": "execute_transfer",
                "description": "Execute the file transfer from S3 to FTP/SFTP with the recommended strategy. This will also schedule auto-logout after 10 seconds.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "transfer_plan": {
                            "type": "object",
                            "description": "Transfer plan from analyze_transfer_request"
                        },
                        "servicenow_tickets": {
                            "type": "array",
                            "description": "ServiceNow ticket IDs",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["user_id", "transfer_plan", "servicenow_tickets"]
                }
            },
            {
                "name": "get_transfer_history",
                "description": "Get user's past transfer history from DynamoDB. Useful when user asks 'what did I transfer before' or 'show my history'.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return",
                            "default": 10
                        }
                    },
                    "required": ["user_id"]
                }
            }
        ]
    
    async def _execute_tools(self, content: List[Dict], user_id: str) -> List[Dict]:
        """
        Execute tools requested by Claude
        
        Args:
            content: Tool use content from Claude
            user_id: User ID
            
        Returns:
            List of tool results
        """
        results = []
        
        for item in content:
            if item.get('type') == 'tool_use':
                tool_name = item['name']
                tool_input = item['input']
                tool_use_id = item['id']
                
                # Add user_id to tool input if not present
                if 'user_id' not in tool_input and tool_name != 'list_s3_buckets':
                    tool_input['user_id'] = user_id
                
                try:
                    # Execute tool with X-Ray tracing
                    with xray_recorder.capture(f'tool_{tool_name}'):
                        result = await self.tools.execute(tool_name, tool_input)
                    
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result)
                    })
                    
                except Exception as e:
                    logger.error(f"Tool execution error in {tool_name}: {str(e)}", exc_info=True)
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps({
                            "error": str(e),
                            "tool": tool_name
                        }),
                        "is_error": True
                    })
        
        return results
    
    def _get_conversation(self, conv_id: str, user_context: Dict) -> List[Dict]:
        """Get or create conversation with context"""
        if conv_id in self.active_conversations:
            return self.active_conversations[conv_id]
        
        # New conversation - no initial messages needed
        # System prompt provides all context
        return []
    
    def _enrich_message_with_context(self, message: str, context: Dict) -> str:
        """Enrich message with user context"""
        frequent_buckets = context.get('frequent_buckets', [])[:3]
        past_transfers = len(context.get('history', []))
        
        if frequent_buckets or past_transfers > 0:
            context_info = f"\n\n[User Context: "
            if frequent_buckets:
                context_info += f"Frequently uses buckets: {', '.join(frequent_buckets)}. "
            if past_transfers > 0:
                context_info += f"Has {past_transfers} past transfers."
            context_info += "]"
            return message + context_info
        
        return message
    
    def _extract_text_from_response(self, response_body: Dict) -> str:
        """Extract text message from Claude response"""
        content = response_body.get('content', [])
        for item in content:
            if item.get('type') == 'text':
                return item.get('text', 'I processed your request.')
        return 'I processed your request.'