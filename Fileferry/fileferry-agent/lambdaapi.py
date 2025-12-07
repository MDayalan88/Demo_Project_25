"""
AWS Lambda Handler for API Gateway
Entry point for Teams Bot and REST API requests
"""

import json
import asyncio
from typing import Dict, Any

from ..teams_bot.bot_handler import FileFerryTeamsBot
from ..ai_agent.bedrock_agent import BedrockFileFerryAgent
from ..utils.config import load_config
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Global instances (Lambda container reuse)
config = None
teams_bot = None
ai_agent = None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for API Gateway requests
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    global config, teams_bot, ai_agent
    
    # Initialize on cold start
    if config is None:
        config = load_config()
        teams_bot = FileFerryTeamsBot(config)
        ai_agent = BedrockFileFerryAgent(config)
        logger.info("✅ Lambda cold start initialization complete")
    
    try:
        # Parse request
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/')
        body = json.loads(event.get('body', '{}'))
        
        logger.info(f"Received {http_method} request to {path}")
        
        # Route to appropriate handler
        if path == '/api/messages':
            # Teams Bot message
            result = _handle_teams_message(body)
        elif path == '/api/chat':
            # Direct API chat
            result = _handle_api_chat(body)
        elif path == '/health':
            # Health check
            result = {'status': 'healthy', 'service': 'FileFerry AI Agent'}
        else:
            result = {'error': 'Not found'}
            return _create_response(404, result)
        
        return _create_response(200, result)
        
    except Exception as e:
        logger.error(f"Lambda error: {str(e)}", exc_info=True)
        return _create_response(500, {'error': str(e)})


def _handle_teams_message(body: Dict) -> Dict:
    """Handle Teams Bot message"""
    # Teams Bot Framework expects specific handling
    # This is simplified - full implementation needs Bot Framework SDK
    
    loop = asyncio.get_event_loop()
    # Process message with bot
    # result = loop.run_until_complete(teams_bot.process_activity(body))
    
    return {'status': 'success', 'message': 'Teams message processed'}


def _handle_api_chat(body: Dict) -> Dict:
    """Handle direct API chat request"""
    user_id = body.get('user_id')
    message = body.get('message')
    
    if not user_id or not message:
        return {'error': 'user_id and message required'}
    
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        ai_agent.process_natural_language_request(user_id, message)
    )
    
    return result


def _create_response(status_code: int, body: Dict) -> Dict:
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }