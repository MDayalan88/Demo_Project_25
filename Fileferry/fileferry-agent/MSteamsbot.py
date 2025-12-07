"""
Microsoft Teams Bot Handler for FileFerry Agent
Provides conversational interface in Teams with Adaptive Cards
"""

from botbuilder.core import ActivityHandler, TurnContext, MessageFactory, CardFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes, Attachment
from botbuilder.core.teams import TeamsInfo
from typing import Dict, Any, List
import json
from datetime import datetime

from ..ai_agent.bedrock_agent import BedrockFileFerryAgent
from .adaptive_cards import AdaptiveCards
from ..utils.logger import get_logger
from aws_xray_sdk.core import xray_recorder

logger = get_logger(__name__)


class FileFerryTeamsBot(ActivityHandler):
    """
    Teams Bot that wraps the Bedrock AI Agent
    Provides natural language interface in Microsoft Teams
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Teams Bot
        
        Args:
            config: Configuration dictionary
        """
        super().__init__()
        self.config = config
        self.ai_agent = BedrockFileFerryAgent(config)
        self.cards = AdaptiveCards()
        
        # Store active conversations per user
        self.active_conversations: Dict[str, str] = {}
        
        logger.info("✅ FileFerry Teams Bot initialized")
    
    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle incoming messages from Teams
        
        Args:
            turn_context: Bot Framework turn context
        """
        with xray_recorder.capture('teams_bot_message'):
            try:
                # Extract user info from Teams
                user_id = turn_context.activity.from_property.aad_object_id
                user_name = turn_context.activity.from_property.name
                user_email = turn_context.activity.from_property.email or user_id
                message_text = turn_context.activity.text
                
                logger.info(f"Received message from {user_name}: {message_text[:50]}...")
                
                # Handle action submissions (button clicks)
                if turn_context.activity.value:
                    await self._handle_action_submission(turn_context, user_id, user_name)
                    return
                
                # Send typing indicator
                await self._send_typing_indicator(turn_context)
                
                # Get conversation ID for context continuity
                conversation_id = self.active_conversations.get(user_id)
                
                # Process with AI Agent
                response = await self.ai_agent.process_natural_language_request(
                    user_id=user_email,
                    message=message_text,
                    conversation_id=conversation_id
                )
                
                # Store conversation ID for context
                if response.get('status') == 'success':
                    self.active_conversations[user_id] = response['conversation_id']
                
                # Create and send Adaptive Card response
                if response.get('status') == 'success':
                    card = self.cards.create_agent_response_card(
                        agent_message=response['agent_response'],
                        user_name=user_name,
                        metadata={
                            'latency': response.get('latency_seconds'),
                            'conversation_id': response.get('conversation_id')
                        }
                    )
                else:
                    card = self.cards.create_error_card(
                        error_message=response.get('user_friendly_message', 'An error occurred'),
                        technical_details=response.get('error')
                    )
                
                # Send card to Teams
                await turn_context.send_activity(
                    MessageFactory.attachment(CardFactory.adaptive_card(card))
                )
                
            except Exception as e:
                logger.error(f"Error in on_message_activity: {str(e)}", exc_info=True)
                
                # Send user-friendly error message
                error_card = self.cards.create_error_card(
                    error_message="I encountered an unexpected error. Please try again or contact support.",
                    technical_details=str(e)
                )
                await turn_context.send_activity(
                    MessageFactory.attachment(CardFactory.adaptive_card(error_card))
                )
    
    async def _handle_action_submission(self, turn_context: TurnContext, user_id: str, user_name: str):
        """
        Handle Adaptive Card action button clicks
        
        Args:
            turn_context: Turn context
            user_id: User ID
            user_name: User name
        """
        action_data = turn_context.activity.value
        action_type = action_data.get('action')
        
        logger.info(f"Action submitted: {action_type} by {user_name}")
        
        if action_type == 'start_transfer':
            # User clicked "Start Transfer" button
            await self._handle_start_transfer(turn_context, action_data, user_id, user_name)
        
        elif action_type == 'view_details':
            # User clicked "View Details" button
            await self._handle_view_details(turn_context, action_data, user_id)
        
        elif action_type == 'cancel':
            # User clicked "Cancel" button
            await self._handle_cancel(turn_context, user_name)
        
        elif action_type == 'retry':
            # User clicked "Retry" button
            await self._handle_retry(turn_context, action_data, user_id)
        
        else:
            logger.warning(f"Unknown action type: {action_type}")
    
    async def _handle_start_transfer(self, turn_context: TurnContext, action_data: Dict, user_id: str, user_name: str):
        """Handle transfer initiation"""
        await self._send_typing_indicator(turn_context)
        
        # Extract transfer details from action data
        response_data = action_data.get('response', {})
        
        # Send confirmation card
        card = self.cards.create_transfer_progress_card(
            status="initiated",
            message=f"Starting transfer for {user_name}...",
            progress=0
        )
        
        await turn_context.send_activity(
            MessageFactory.attachment(CardFactory.adaptive_card(card))
        )
        
        # Note: Actual transfer execution happens in Step Functions
        # This is just the UI acknowledgment
    
    async def _handle_view_details(self, turn_context: TurnContext, action_data: Dict, user_id: str):
        """Show detailed transfer information"""
        details_card = self.cards.create_details_card(action_data)
        await turn_context.send_activity(
            MessageFactory.attachment(CardFactory.adaptive_card(details_card))
        )
    
    async def _handle_cancel(self, turn_context: TurnContext, user_name: str):
        """Handle transfer cancellation"""
        card = self.cards.create_simple_message_card(
            title="❌ Transfer Cancelled",
            message=f"No problem, {user_name}! Let me know if you need anything else.",
            color="attention"
        )
        await turn_context.send_activity(
            MessageFactory.attachment(CardFactory.adaptive_card(card))
        )
    
    async def _handle_retry(self, turn_context: TurnContext, action_data: Dict, user_id: str):
        """Handle retry request"""
        await turn_context.send_activity("Retrying your request...")
        # Re-process the original message
        original_message = action_data.get('original_message', '')
        if original_message:
            # Simulate new message
            turn_context.activity.text = original_message
            await self.on_message_activity(turn_context)
    
    async def on_teams_members_added(self, members_added: List[ChannelAccount], turn_context: TurnContext):
        """
        Welcome message when bot is added to chat
        
        Args:
            members_added: List of members added
            turn_context: Turn context
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                logger.info(f"New member added: {member.name}")
                
                welcome_card = self.cards.create_welcome_card(member.name)
                await turn_context.send_activity(
                    MessageFactory.attachment(CardFactory.adaptive_card(welcome_card))
                )
    
    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """Handle conversation updates (bot added/removed)"""
        if turn_context.activity.members_added:
            await self.on_teams_members_added(
                turn_context.activity.members_added,
                turn_context
            )
        
        return await super().on_conversation_update_activity(turn_context)
    
    async def _send_typing_indicator(self, turn_context: TurnContext):
        """Send typing indicator while processing"""
        typing_activity = Activity(
            type=ActivityTypes.typing,
            relates_to=turn_context.activity.relates_to
        )
        await turn_context.send_activity(typing_activity)
    
    async def send_proactive_notification(
        self, 
        user_id: str, 
        message: str, 
        card: Dict = None
    ):
        """
        Send proactive notification to user (e.g., transfer complete)
        
        Args:
            user_id: Teams user ID
            message: Notification message
            card: Optional Adaptive Card
        """
        # This requires bot to be configured for proactive messaging
        # Implementation depends on your Teams app setup
        logger.info(f"Proactive notification to {user_id}: {message}")
        # TODO: Implement proactive messaging logic