"""
Microsoft Teams Bot Handler - Provides natural language interface via Teams
Handles user messages, formats responses with Adaptive Cards, manages conversations
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import Activity, ActivityTypes, CardAction, ActionTypes
from aws_xray_sdk.core import xray_recorder

from src.ai_agent.bedrock_agent import BedrockFileFerryAgent
from src.teams_bot.adaptive_cards import AdaptiveCards
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FileFerryTeamsBot(ActivityHandler):
    """
    Microsoft Teams Bot for FileFerry AI Agent
    Provides rich conversational interface with Adaptive Cards
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Teams Bot with configuration

        Args:
            config: Configuration dictionary
        """
        super().__init__()
        self.config = config
        self.bedrock_agent = BedrockFileFerryAgent(config)
        self.adaptive_cards = AdaptiveCards()
        
        logger.info("Initialized FileFerryTeamsBot")

    @xray_recorder.capture('on_message_activity')
    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle incoming messages from Teams users

        Args:
            turn_context: Bot Framework turn context
        """
        try:
            # Get user info
            user_id = turn_context.activity.from_property.id
            user_name = turn_context.activity.from_property.name
            user_message = turn_context.activity.text
            conversation_id = turn_context.activity.conversation.id
            
            logger.info(f"Received message from {user_name} ({user_id}): {user_message}")
            
            # Send typing indicator
            await self._send_typing_indicator(turn_context)
            
            # Process message with AI Agent
            response = await self.bedrock_agent.process_natural_language_request(
                user_id=user_id,
                user_message=user_message,
                session_id=conversation_id
            )
            
            # Format response as Adaptive Card
            if response.get('success'):
                # Check if response contains transfer analysis
                if 'transfer_analysis' in response.get('metadata', {}):
                    card = self.adaptive_cards.create_transfer_analysis_card(
                        analysis=response['metadata']['transfer_analysis'],
                        user_name=user_name
                    )
                else:
                    card = self.adaptive_cards.create_agent_response_card(
                        response_text=response['response'],
                        metadata=response.get('metadata', {}),
                        user_name=user_name
                    )
            else:
                card = self.adaptive_cards.create_error_card(
                    error_message=response.get('error', 'An unexpected error occurred'),
                    user_name=user_name
                )
            
            # Send card response
            card_activity = MessageFactory.attachment(card)
            await turn_context.send_activity(card_activity)
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            
            # Send error card
            error_card = self.adaptive_cards.create_error_card(
                error_message=str(e),
                user_name=turn_context.activity.from_property.name
            )
            await turn_context.send_activity(MessageFactory.attachment(error_card))

    async def on_teams_members_added_activity(
        self,
        members_added: list,
        turn_context: TurnContext
    ):
        """
        Handle new members added to Teams conversation

        Args:
            members_added: List of added members
            turn_context: Bot Framework turn context
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                # Send welcome card
                welcome_card = self.adaptive_cards.create_welcome_card(
                    user_name=member.name
                )
                await turn_context.send_activity(
                    MessageFactory.attachment(welcome_card)
                )

    @xray_recorder.capture('handle_action_submission')
    async def on_invoke_activity(self, turn_context: TurnContext):
        """
        Handle Adaptive Card action submissions

        Args:
            turn_context: Bot Framework turn context
        """
        try:
            if turn_context.activity.name == 'adaptiveCard/action':
                action_data = turn_context.activity.value
                action_type = action_data.get('action')
                
                logger.info(f"Received action: {action_type} with data: {action_data}")
                
                # Route to appropriate handler
                if action_type == 'start_transfer':
                    await self._handle_start_transfer(turn_context, action_data)
                elif action_type == 'view_details':
                    await self._handle_view_details(turn_context, action_data)
                elif action_type == 'cancel_transfer':
                    await self._handle_cancel_transfer(turn_context, action_data)
                elif action_type == 'retry_transfer':
                    await self._handle_retry_transfer(turn_context, action_data)
                else:
                    logger.warning(f"Unknown action type: {action_type}")
            
        except Exception as e:
            logger.error(f"Error handling action submission: {str(e)}", exc_info=True)

    async def _handle_start_transfer(
        self,
        turn_context: TurnContext,
        action_data: Dict[str, Any]
    ):
        """Handle start transfer action"""
        user_id = turn_context.activity.from_property.id
        transfer_request = action_data.get('transfer_request')
        
        # Execute transfer via agent tools
        from src.ai_agent.agent_tools import AgentTools
        agent_tools = AgentTools(self.config)
        
        result = await agent_tools.execute_transfer(
            tool_input={'transfer_request': transfer_request},
            user_context={'user_id': user_id}
        )
        
        if result.get('success'):
            # Send progress card
            card = self.adaptive_cards.create_transfer_progress_card(
                execution_arn=result['execution_arn'],
                transfer_details=transfer_request
            )
            await turn_context.send_activity(MessageFactory.attachment(card))
        else:
            # Send error card
            card = self.adaptive_cards.create_error_card(
                error_message=result.get('error', 'Failed to start transfer'),
                user_name=turn_context.activity.from_property.name
            )
            await turn_context.send_activity(MessageFactory.attachment(card))

    async def _handle_view_details(
        self,
        turn_context: TurnContext,
        action_data: Dict[str, Any]
    ):
        """Handle view details action"""
        execution_arn = action_data.get('execution_arn')
        
        # Get transfer status
        status = await self.bedrock_agent.get_transfer_status(execution_arn)
        
        # Create detailed status card
        response_text = f"""**Transfer Status**\n
Execution ARN: {execution_arn}\n
Status: {status.get('status', 'Unknown')}\n
Start Time: {status.get('start_date', 'N/A')}\n
"""
        
        if status.get('output'):
            response_text += f"\n**Results:**\n```json\n{json.dumps(status['output'], indent=2)}\n```"
        
        card = self.adaptive_cards.create_agent_response_card(
            response_text=response_text,
            metadata={'execution_arn': execution_arn},
            user_name=turn_context.activity.from_property.name
        )
        
        await turn_context.send_activity(MessageFactory.attachment(card))

    async def _handle_cancel_transfer(
        self,
        turn_context: TurnContext,
        action_data: Dict[str, Any]
    ):
        """Handle cancel transfer action"""
        execution_arn = action_data.get('execution_arn')
        reason = action_data.get('reason', 'User requested cancellation')
        
        # Cancel transfer
        result = await self.bedrock_agent.cancel_transfer(execution_arn, reason)
        
        if result.get('success'):
            response_text = f"✅ Transfer cancelled successfully.\n\nExecution ARN: {execution_arn}\nReason: {reason}"
        else:
            response_text = f"❌ Failed to cancel transfer: {result.get('error')}"
        
        card = self.adaptive_cards.create_agent_response_card(
            response_text=response_text,
            metadata={'execution_arn': execution_arn},
            user_name=turn_context.activity.from_property.name
        )
        
        await turn_context.send_activity(MessageFactory.attachment(card))

    async def _handle_retry_transfer(
        self,
        turn_context: TurnContext,
        action_data: Dict[str, Any]
    ):
        """Handle retry transfer action"""
        user_id = turn_context.activity.from_property.id
        transfer_request = action_data.get('transfer_request')
        
        # Re-initiate transfer
        await self._handle_start_transfer(turn_context, action_data)

    async def _send_typing_indicator(self, turn_context: TurnContext):
        """Send typing indicator to show bot is processing"""
        typing_activity = Activity(
            type=ActivityTypes.typing,
            relates_to=turn_context.activity.relates_to
        )
        await turn_context.send_activity(typing_activity)

    async def send_proactive_notification(
        self,
        conversation_reference: Dict[str, Any],
        notification_data: Dict[str, Any]
    ):
        """
        Send proactive notification to user (e.g., transfer completion)

        Args:
            conversation_reference: Teams conversation reference
            notification_data: Notification data
        """
        try:
            # Create notification card based on type
            notification_type = notification_data.get('type')
            
            if notification_type == 'transfer_complete':
                card = self.adaptive_cards.create_transfer_complete_card(
                    transfer_details=notification_data.get('transfer_details'),
                    execution_results=notification_data.get('results')
                )
            elif notification_type == 'transfer_failed':
                card = self.adaptive_cards.create_error_card(
                    error_message=notification_data.get('error_message'),
                    user_name=notification_data.get('user_name')
                )
            else:
                card = self.adaptive_cards.create_agent_response_card(
                    response_text=notification_data.get('message'),
                    metadata=notification_data.get('metadata', {}),
                    user_name=notification_data.get('user_name')
                )
            
            # Send notification
            # Note: Requires bot adapter with conversation reference
            logger.info(f"Sent proactive notification: {notification_type}")
            
        except Exception as e:
            logger.error(f"Error sending proactive notification: {str(e)}", exc_info=True)
