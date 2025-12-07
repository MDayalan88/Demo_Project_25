"""
Lambda API Handler - Entry point for API Gateway requests
Handles Teams Bot messages and direct API chat requests
"""

import json
import os
import asyncio
from typing import Dict, Any
from aws_xray_sdk.core import xray_recorder, patch_all

# Patch AWS SDK for X-Ray tracing
patch_all()

from src.ai_agent.bedrock_agent import BedrockFileFerryAgent
from src.teams_bot.bot_handler import FileFerryTeamsBot
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global config and agent (for Lambda warm starts)
config = None
bedrock_agent = None
teams_bot = None


def initialize():
    """Initialize global config and agent instances (cold start)"""
    global config, bedrock_agent, teams_bot
    
    if config is None:
        logger.info("Lambda cold start - initializing...")
        
        # Load configuration
        config_path = os.environ.get('CONFIG_PATH', 'config/config.yaml')
        config = load_config(config_path)
        
        # Initialize Bedrock agent
        bedrock_agent = BedrockFileFerryAgent(config)
        
        # Initialize Teams Bot
        teams_bot = FileFerryTeamsBot(config)
        
        logger.info("Lambda initialization complete")


@xray_recorder.capture('lambda_handler')
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for API Gateway requests
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        # Initialize on cold start
        initialize()
        
        # Parse request
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}'))
        
        logger.info(f"Received {http_method} request to {path}")
        
        # Route request
        if '/api/messages' in path:
            # Teams Bot message
            response = asyncio.run(_handle_teams_message(body))
        elif '/api/chat' in path:
            # Direct API chat
            response = asyncio.run(_handle_api_chat(body))
        elif '/health' in path:
            # Health check
            response = {
                'status': 'healthy',
                'agent': 'FileFerry AI Agent',
                'version': '1.0.0'
            }
        else:
            response = {
                'error': 'Unknown endpoint',
                'path': path
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}", exc_info=True)
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e),
                'error_type': type(e).__name__
            })
        }


async def _handle_teams_message(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle Teams Bot message
    
    Args:
        body: Teams Bot activity
        
    Returns:
        Response dict
    """
    try:
        # Extract user info and message
        activity_type = body.get('type')
        
        if activity_type == 'message':
            user_id = body.get('from', {}).get('id')
            user_message = body.get('text', '')
            conversation_id = body.get('conversation', {}).get('id')
            
            # Process with Bedrock agent
            response = await bedrock_agent.process_natural_language_request(
                user_id=user_id,
                user_message=user_message,
                session_id=conversation_id
            )
            
            return {
                'type': 'message',
                'text': response.get('response', 'Sorry, I could not process your request.'),
                'metadata': response.get('metadata', {})
            }
        
        return {
            'type': 'acknowledgement',
            'message': 'Activity received'
        }
        
    except Exception as e:
        logger.error(f"Error handling Teams message: {str(e)}", exc_info=True)
        return {
            'type': 'message',
            'text': f'Error: {str(e)}'
        }


async def _handle_api_chat(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle direct API chat request
    
    Args:
        body: Chat request body
        
    Returns:
        Response dict
    """
    try:
        user_id = body.get('user_id')
        user_message = body.get('message')
        session_id = body.get('session_id')
        
        if not user_id or not user_message:
            return {
                'error': 'Missing required fields: user_id and message'
            }
        
        # Process with Bedrock agent
        response = await bedrock_agent.process_natural_language_request(
            user_id=user_id,
            user_message=user_message,
            session_id=session_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling API chat: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
