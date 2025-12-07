"""
BedrockFileFerryAgent - Main AI Orchestrator
Handles natural language requests, tool orchestration, and conversation management.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from .agent_tools import AgentTools

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BedrockFileFerryAgent:
    """
    Main AI agent orchestrator using AWS Bedrock Claude 3.5 Sonnet v2.
    
    Features:
    - Natural language understanding
    - Multi-turn conversations (max 10 exchanges)
    - Tool selection & orchestration
    - Error handling with retries (3 attempts, exponential backoff)
    - Performance tracking via CloudWatch
    """
    
    MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    MAX_TOKENS = 4096
    TEMPERATURE = 0.7
    MAX_CONVERSATION_HISTORY = 10
    MAX_RETRIES = 3
    
    SYSTEM_PROMPT = """You are FileFerry AI Agent, an intelligent file transfer orchestration assistant.

Your responsibilities:
1. Help users transfer files from AWS S3 buckets to FTP/SFTP servers
2. Create dual ServiceNow tickets (user request + audit trail)
3. Manage AWS SSO sessions (10-second timeout for security)
4. Analyze transfer requirements and predict outcomes
5. Monitor transfer progress and provide status updates

Key Security Rules:
- Users have READ-ONLY access to S3 buckets
- AWS SSO sessions auto-expire after 10 seconds
- Users cannot re-login without new ServiceNow request
- All transfers require dual ServiceNow tickets for audit compliance

Available Tools:
1. list_s3_buckets() - List accessible S3 buckets in a region
2. list_bucket_contents() - List files in a specific bucket
3. get_file_metadata() - Get detailed file information
4. validate_user_access() - Verify user permissions
5. analyze_transfer_request() - Analyze transfer requirements
6. predict_transfer_outcome() - Predict success rate and duration
7. create_servicenow_tickets() - Create dual tickets (user + audit)
8. execute_transfer() - Start file transfer workflow
9. get_transfer_history() - Retrieve user's transfer history

Always be helpful, secure, and efficient. Provide clear explanations and proactive guidance."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Bedrock FileFerry Agent.
        
        Args:
            config: Configuration dictionary containing AWS credentials, regions, etc.
        """
        self.config = config
        self.region = config.get('aws', {}).get('region', 'us-east-1')
        
        # Initialize Bedrock client
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=self.region
        )
        
        # Initialize CloudWatch for metrics
        self.cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        
        # Initialize agent tools
        self.agent_tools = AgentTools(config)
        
        # Conversation storage (in production, use DynamoDB)
        self.conversations = {}
        
        logger.info(f"BedrockFileFerryAgent initialized with model: {self.MODEL_ID}")
    
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Define all available tools for the agent.
        
        Returns:
            List of tool definitions in Claude's tool format
        """
        return [
            {
                "name": "list_s3_buckets",
                "description": "List all accessible S3 buckets in a specific AWS region. Requires active SSO session.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "AWS region (e.g., us-east-1, us-west-2)"
                        },
                        "session_token": {
                            "type": "string",
                            "description": "Active SSO session token"
                        }
                    },
                    "required": ["region", "session_token"]
                }
            },
            {
                "name": "list_bucket_contents",
                "description": "List files and folders in a specific S3 bucket. Shows file names, sizes, and last modified dates.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bucket_name": {
                            "type": "string",
                            "description": "Name of the S3 bucket"
                        },
                        "prefix": {
                            "type": "string",
                            "description": "Optional folder prefix to filter results"
                        },
                        "session_token": {
                            "type": "string",
                            "description": "Active SSO session token"
                        }
                    },
                    "required": ["bucket_name", "session_token"]
                }
            },
            {
                "name": "get_file_metadata",
                "description": "Get detailed metadata for a specific S3 file including size, type, last modified, and storage class.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bucket_name": {
                            "type": "string",
                            "description": "Name of the S3 bucket"
                        },
                        "file_key": {
                            "type": "string",
                            "description": "Full path to the file in the bucket"
                        },
                        "session_token": {
                            "type": "string",
                            "description": "Active SSO session token"
                        }
                    },
                    "required": ["bucket_name", "file_key", "session_token"]
                }
            },
            {
                "name": "validate_user_access",
                "description": "Verify if user has read-only access to specified S3 bucket. Returns permissions details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bucket_name": {
                            "type": "string",
                            "description": "Name of the S3 bucket to check"
                        },
                        "session_token": {
                            "type": "string",
                            "description": "Active SSO session token"
                        }
                    },
                    "required": ["bucket_name", "session_token"]
                }
            },
            {
                "name": "analyze_transfer_request",
                "description": "Analyze a transfer request to determine optimal strategy, estimated time, and potential issues.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "source_bucket": {
                            "type": "string",
                            "description": "Source S3 bucket name"
                        },
                        "source_key": {
                            "type": "string",
                            "description": "Source file key/path"
                        },
                        "destination_host": {
                            "type": "string",
                            "description": "FTP/SFTP destination host"
                        },
                        "destination_port": {
                            "type": "integer",
                            "description": "FTP/SFTP port (21 for FTP, 22 for SFTP)"
                        },
                        "transfer_type": {
                            "type": "string",
                            "enum": ["ftp", "sftp"],
                            "description": "Type of transfer protocol"
                        }
                    },
                    "required": ["source_bucket", "source_key", "destination_host", "transfer_type"]
                }
            },
            {
                "name": "predict_transfer_outcome",
                "description": "Predict transfer success rate and duration based on historical data and file characteristics.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_size_bytes": {
                            "type": "integer",
                            "description": "File size in bytes"
                        },
                        "transfer_type": {
                            "type": "string",
                            "enum": ["ftp", "sftp"],
                            "description": "Type of transfer protocol"
                        },
                        "destination_region": {
                            "type": "string",
                            "description": "Geographic region of destination server"
                        }
                    },
                    "required": ["file_size_bytes", "transfer_type"]
                }
            },
            {
                "name": "create_servicenow_tickets",
                "description": "Create TWO ServiceNow tickets: one for user request and one for audit team. Returns both ticket numbers.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "requester_email": {
                            "type": "string",
                            "description": "Email of person requesting transfer"
                        },
                        "source_bucket": {
                            "type": "string",
                            "description": "Source S3 bucket name"
                        },
                        "source_file": {
                            "type": "string",
                            "description": "Source file key/path"
                        },
                        "destination_server": {
                            "type": "string",
                            "description": "Destination FTP/SFTP server details"
                        },
                        "environment": {
                            "type": "string",
                            "enum": ["production", "staging", "development"],
                            "description": "Target environment"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["critical", "high", "medium", "low"],
                            "description": "Transfer priority"
                        }
                    },
                    "required": ["requester_email", "source_bucket", "source_file", "destination_server", "environment"]
                }
            },
            {
                "name": "execute_transfer",
                "description": "Start file transfer from S3 to FTP/SFTP using AWS Step Functions workflow. Returns transfer ID for tracking.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transfer_id": {
                            "type": "string",
                            "description": "Unique transfer identifier"
                        },
                        "source_bucket": {
                            "type": "string",
                            "description": "Source S3 bucket name"
                        },
                        "source_key": {
                            "type": "string",
                            "description": "Source file key/path"
                        },
                        "destination_config": {
                            "type": "object",
                            "description": "FTP/SFTP destination configuration",
                            "properties": {
                                "type": {"type": "string", "enum": ["ftp", "sftp"]},
                                "host": {"type": "string"},
                                "port": {"type": "integer"},
                                "username": {"type": "string"},
                                "password": {"type": "string"},
                                "path": {"type": "string"}
                            },
                            "required": ["type", "host", "username", "password"]
                        },
                        "servicenow_tickets": {
                            "type": "object",
                            "description": "ServiceNow ticket numbers",
                            "properties": {
                                "user_ticket": {"type": "string"},
                                "audit_ticket": {"type": "string"}
                            },
                            "required": ["user_ticket", "audit_ticket"]
                        },
                        "session_token": {
                            "type": "string",
                            "description": "Active SSO session token"
                        }
                    },
                    "required": ["transfer_id", "source_bucket", "source_key", "destination_config", "servicenow_tickets", "session_token"]
                }
            },
            {
                "name": "get_transfer_history",
                "description": "Retrieve user's past transfer requests with status, duration, and outcome.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User identifier"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return (default: 10)"
                        },
                        "status_filter": {
                            "type": "string",
                            "enum": ["all", "completed", "in_progress", "failed"],
                            "description": "Filter by transfer status"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        ]
    
    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool function and return results.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            
        Returns:
            Tool execution results
        """
        try:
            logger.info(f"Executing tool: {tool_name} with input: {json.dumps(tool_input, default=str)}")
            
            # Map tool names to AgentTools methods
            tool_methods = {
                "list_s3_buckets": self.agent_tools.list_s3_buckets,
                "list_bucket_contents": self.agent_tools.list_bucket_contents,
                "get_file_metadata": self.agent_tools.get_file_metadata,
                "validate_user_access": self.agent_tools.validate_user_access,
                "analyze_transfer_request": self.agent_tools.analyze_transfer_request,
                "predict_transfer_outcome": self.agent_tools.predict_transfer_outcome,
                "create_servicenow_tickets": self.agent_tools.create_servicenow_tickets,
                "execute_transfer": self.agent_tools.execute_transfer,
                "get_transfer_history": self.agent_tools.get_transfer_history
            }
            
            if tool_name not in tool_methods:
                return {"error": f"Unknown tool: {tool_name}"}
            
            # Execute the tool
            result = tool_methods[tool_name](**tool_input)
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
            return {"error": str(e), "tool": tool_name}
    
    def _get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a user (max 10 exchanges).
        
        Args:
            user_id: User identifier
            
        Returns:
            List of conversation messages
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        # Return last 10 exchanges (20 messages: 10 user + 10 assistant)
        return self.conversations[user_id][-20:]
    
    def _add_to_conversation_history(self, user_id: str, role: str, content: Any):
        """
        Add message to conversation history.
        
        Args:
            user_id: User identifier
            role: Message role (user/assistant)
            content: Message content
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages (10 exchanges)
        if len(self.conversations[user_id]) > 20:
            self.conversations[user_id] = self.conversations[user_id][-20:]
    
    def _send_metrics_to_cloudwatch(self, metric_name: str, value: float, unit: str = 'Count'):
        """
        Send performance metrics to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
        """
        try:
            self.cloudwatch.put_metric_data(
                Namespace='FileFerry/Agent',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Timestamp': datetime.now()
                    }
                ]
            )
        except Exception as e:
            logger.warning(f"Failed to send CloudWatch metric: {str(e)}")
    
    def process_request(
        self,
        user_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user request using Bedrock Claude with tool orchestration.
        
        Args:
            user_id: User identifier
            user_message: User's natural language request
            context: Optional additional context (SSO session, etc.)
            
        Returns:
            Dict containing agent response and metadata
        """
        start_time = time.time()
        
        try:
            # Get conversation history
            history = self._get_conversation_history(user_id)
            
            # Add user message to history
            self._add_to_conversation_history(user_id, "user", user_message)
            
            # Prepare messages for Bedrock
            messages = []
            for msg in history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"] if isinstance(msg["content"], str) else json.dumps(msg["content"])
                    })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Prepare request for Bedrock with retries
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = self.bedrock_client.converse(
                        modelId=self.MODEL_ID,
                        messages=messages,
                        system=[{"text": self.SYSTEM_PROMPT}],
                        inferenceConfig={
                            "maxTokens": self.MAX_TOKENS,
                            "temperature": self.TEMPERATURE
                        },
                        toolConfig={
                            "tools": [{"toolSpec": tool} for tool in self._get_tool_definitions()]
                        }
                    )
                    break  # Success, exit retry loop
                    
                except ClientError as e:
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Bedrock API error (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                        time.sleep(wait_time)
                    else:
                        raise  # Max retries exceeded
            
            # Process response
            stop_reason = response.get('stopReason')
            output_message = response.get('output', {}).get('message', {})
            
            # Handle tool use
            if stop_reason == 'tool_use':
                tool_results = []
                
                for content_block in output_message.get('content', []):
                    if 'toolUse' in content_block:
                        tool_use = content_block['toolUse']
                        tool_name = tool_use['name']
                        tool_input = tool_use['input']
                        tool_use_id = tool_use['toolUseId']
                        
                        # Execute tool
                        tool_result = self._execute_tool(tool_name, tool_input)
                        
                        tool_results.append({
                            "toolUseId": tool_use_id,
                            "content": [{"json": tool_result}]
                        })
                
                # Continue conversation with tool results
                messages.append({
                    "role": "assistant",
                    "content": output_message.get('content', [])
                })
                
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
                # Get final response from Bedrock
                final_response = self.bedrock_client.converse(
                    modelId=self.MODEL_ID,
                    messages=messages,
                    system=[{"text": self.SYSTEM_PROMPT}],
                    inferenceConfig={
                        "maxTokens": self.MAX_TOKENS,
                        "temperature": self.TEMPERATURE
                    }
                )
                
                final_output = final_response.get('output', {}).get('message', {})
                response_text = ""
                for block in final_output.get('content', []):
                    if 'text' in block:
                        response_text += block['text']
                
            else:
                # No tool use, extract text response
                response_text = ""
                for block in output_message.get('content', []):
                    if 'text' in block:
                        response_text += block['text']
            
            # Add assistant response to history
            self._add_to_conversation_history(user_id, "assistant", response_text)
            
            # Calculate metrics
            duration = time.time() - start_time
            self._send_metrics_to_cloudwatch('RequestDuration', duration * 1000, 'Milliseconds')
            self._send_metrics_to_cloudwatch('RequestCount', 1, 'Count')
            
            logger.info(f"Request processed successfully in {duration:.2f}s")
            
            return {
                "success": True,
                "response": response_text,
                "user_id": user_id,
                "duration_ms": duration * 1000,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            self._send_metrics_to_cloudwatch('RequestErrors', 1, 'Count')
            
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
