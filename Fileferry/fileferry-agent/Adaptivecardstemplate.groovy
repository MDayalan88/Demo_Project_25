"""
Adaptive Card templates for Teams Bot
Following Microsoft Adaptive Cards schema v1.4
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class AdaptiveCards:
    """
    Adaptive Card factory for FileFerry Teams Bot
    Creates rich, interactive cards for Teams
    """
    
    def create_welcome_card(self, user_name: str = "there") -> Dict:
        """
        Welcome card for new users
        
        Args:
            user_name: User's name
            
        Returns:
            Adaptive Card JSON
        """
        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "ColumnSet",
                            "columns": [
                                {
                                    "type": "Column",
                                    "width": "auto",
                                    "items": [
                                        {
                                            "type": "Image",
                                            "url": "https://raw.githubusercontent.com/microsoft/BotBuilder-Samples/main/generator-botbuilder/generators/app/templates/core/bots/resources/icon.png",
                                            "size": "Small",
                                            "style": "Person"
                                        }
                                    ]
                                },
                                {
                                    "type": "Column",
                                    "width": "stretch",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": "FileFerry AI Agent 🚀",
                                            "weight": "Bolder",
                                            "size": "Large"
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": f"Hi {user_name}! 👋",
                                            "isSubtle": True,
                                            "spacing": "None"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "I'm your intelligent file transfer assistant. I can help you:",
                            "wrap": True
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {
                                    "title": "✅",
                                    "value": "Transfer files from AWS S3 to FTP/SFTP"
                                },
                                {
                                    "title": "✅",
                                    "value": "Search and browse S3 buckets"
                                },
                                {
                                    "title": "✅",
                                    "value": "Predict transfer success rates"
                                },
                                {
                                    "title": "✅",
                                    "value": "Create ServiceNow tickets automatically"
                                },
                                {
                                    "title": "✅",
                                    "value": "Track your transfer history"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "**Try saying:**",
                            "weight": "Bolder"
                        },
                        {
                            "type": "TextBlock",
                            "text": "• \"I need the Q4 report from prod-bucket\"\n• \"Show me my transfer history\"\n• \"What files are in staging-bucket?\"",
                            "wrap": True,
                            "spacing": "Small"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "🚀 Start New Transfer",
                    "data": {
                        "action": "new_transfer"
                    }
                },
                {
                    "type": "Action.OpenUrl",
                    "title": "📖 Documentation",
                    "url": "https://docs.company.com/fileferry"
                }
            ]
        }
    
    def create_agent_response_card(
        self, 
        agent_message: str, 
        user_name: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Agent response card with message and actions
        
        Args:
            agent_message: Message from AI agent
            user_name: User's name
            metadata: Optional metadata (latency, conversation_id, etc.)
            
        Returns:
            Adaptive Card JSON
        """
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "🤖 FileFerry Agent",
                            "weight": "Bolder",
                            "size": "Medium"
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": agent_message,
                            "wrap": True
                        }
                    ]
                }
            ]
        }
        
        # Add metadata if provided
        if metadata and metadata.get('latency'):
            card["body"].append({
                "type": "Container",
                "separator": True,
                "spacing": "Small",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"_Response time: {metadata['latency']:.2f}s_",
                        "isSubtle": True,
                        "size": "Small"
                    }
                ]
            })
        
        return card
    
    def create_transfer_analysis_card(
        self,
        file_info: Dict,
        prediction: Dict,
        strategy: Dict,
        tickets: List[str]
    ) -> Dict:
        """
        Transfer analysis card with recommendations
        
        Args:
            file_info: File metadata
            prediction: Transfer outcome prediction
            strategy: Recommended transfer strategy
            tickets: ServiceNow ticket IDs
            
        Returns:
            Adaptive Card JSON
        """
        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "📊 Transfer Analysis",
                            "weight": "Bolder",
                            "size": "Large"
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "**File Information**",
                            "weight": "Bolder"
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {
                                    "title": "Name:",
                                    "value": file_info.get('name', 'Unknown')
                                },
                                {
                                    "title": "Size:",
                                    "value": f"{file_info.get('size_mb', 0):.2f} MB"
                                },
                                {
                                    "title": "Bucket:",
                                    "value": file_info.get('bucket', 'Unknown')
                                },
                                {
                                    "title": "Region:",
                                    "value": file_info.get('region', 'Unknown')
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "**Prediction**",
                            "weight": "Bolder"
                        },
                        {
                            "type": "ColumnSet",
                            "columns": [
                                {
                                    "type": "Column",
                                    "width": "auto",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": "Success Rate:",
                                            "weight": "Bolder"
                                        }
                                    ]
                                },
                                {
                                    "type": "Column",
                                    "width": "stretch",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": f"{prediction.get('success_rate', 0)*100:.1f}%",
                                            "color": "Good" if prediction.get('success_rate', 0) > 0.9 else "Warning"
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {
                                    "title": "Estimated Time:",
                                    "value": f"{prediction.get('estimated_seconds', 0)//60}m {prediction.get('estimated_seconds', 0)%60}s"
                                },
                                {
                                    "title": "Sample Size:",
                                    "value": str(prediction.get('sample_size', 0))
                                },
                                {
                                    "title": "Confidence:",
                                    "value": prediction.get('confidence', 'unknown').capitalize()
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "**Strategy**",
                            "weight": "Bolder"
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {
                                    "title": "Chunk Size:",
                                    "value": f"{strategy.get('chunk_size_mb', 0)} MB"
                                },
                                {
                                    "title": "Parallel Uploads:",
                                    "value": str(strategy.get('parallel_uploads', 1))
                                },
                                {
                                    "title": "Compression:",
                                    "value": "Yes" if strategy.get('compression', False) else "No"
                                },
                                {
                                    "title": "Risk Level:",
                                    "value": strategy.get('risk_level', 'unknown').capitalize()
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "**ServiceNow Tickets**",
                            "weight": "Bolder"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"• User: {tickets[0] if len(tickets) > 0 else 'N/A'}\n• Audit: {tickets[1] if len(tickets) > 1 else 'N/A'}",
                            "wrap": True
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "✅ Start Transfer",
                    "style": "positive",
                    "data": {
                        "action": "start_transfer",
                        "file_info": file_info,
                        "strategy": strategy,
                        "tickets": tickets
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "📋 View Details",
                    "data": {
                        "action": "view_details",
                        "full_data": {
                            "file_info": file_info,
                            "prediction": prediction,
                            "strategy": strategy
                        }
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "❌ Cancel",
                    "data": {
                        "action": "cancel"
                    }
                }
            ]
        }
    
    def create_transfer_progress_card(
        self,
        status: str,
        message: str,
        progress: int = 0,
        details: Optional[Dict] = None
    ) -> Dict:
        """
        Transfer progress card with real-time updates
        
        Args:
            status: Transfer status (initiated, in_progress, complete, failed)
            message: Status message
            progress: Progress percentage (0-100)
            details: Optional transfer details
            
        Returns:
            Adaptive Card JSON
        """
        status_colors = {
            "initiated": "accent",
            "in_progress": "attention",
            "complete": "good",
            "failed": "attention"
        }
        
        status_icons = {
            "initiated": "⏳",
            "in_progress": "⚙️",
            "complete": "✅",
            "failed": "❌"
        }
        
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"{status_icons.get(status, '•')} Transfer {status.replace('_', ' ').title()}",
                            "weight": "Bolder",
                            "size": "Large",
                            "color": status_colors.get(status, "default")
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": message,
                            "wrap": True
                        }
                    ]
                }
            ]
        }
        
        # Add progress bar for in-progress transfers
        if status == "in_progress" and progress > 0:
            card["body"].append({
                "type": "Container",
                "spacing": "Medium",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"Progress: {progress}%",
                        "weight": "Bolder"
                    },
                    {
                        "type": "ProgressBar",
                        "value": progress
                    }
                ]
            })
        
        # Add details if provided
        if details:
            facts = []
            for key, value in details.items():
                facts.append({
                    "title": f"{key}:",
                    "value": str(value)
                })
            
            card["body"].append({
                "type": "Container",
                "separator": True,
                "spacing": "Medium",
                "items": [
                    {
                        "type": "FactSet",
                        "facts": facts
                    }
                ]
            })
        
        return card
    
    def create_error_card(
        self,
        error_message: str,
        technical_details: Optional[str] = None
    ) -> Dict:
        """
        Error card for failures
        
        Args:
            error_message: User-friendly error message
            technical_details: Optional technical details
            
        Returns:
            Adaptive Card JSON
        """
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "Container",
                    "style": "attention",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "❌ Error",
                            "weight": "Bolder",
                            "size": "Large",
                            "color": "Attention"
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": error_message,
                            "wrap": True
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "🔄 Try Again",
                    "data": {
                        "action": "retry"
                    }
                },
                {
                    "type": "Action.OpenUrl",
                    "title": "📞 Contact Support",
                    "url": "https://support.company.com/fileferry"
                }
            ]
        }
        
        # Add technical details if provided (collapsible)
        if technical_details:
            card["body"].append({
                "type": "Container",
                "separator": True,
                "spacing": "Small",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "**Technical Details:**",
                        "weight": "Bolder",
                        "size": "Small"
                    },
                    {
                        "type": "TextBlock",
                        "text": technical_details,
                        "wrap": True,
                        "size": "Small",
                        "isSubtle": True
                    }
                ]
            })
        
        return card
    
    def create_simple_message_card(
        self,
        title: str,
        message: str,
        color: str = "default"
    ) -> Dict:
        """
        Simple message card
        
        Args:
            title: Card title
            message: Card message
            color: Color theme (default, accent, good, warning, attention)
            
        Returns:
            Adaptive Card JSON
        """
        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis" if color == "default" else color,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": title,
                            "weight": "Bolder",
                            "size": "Large"
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": message,
                            "wrap": True
                        }
                    ]
                }
            ]
        }
    
    def create_details_card(self, data: Dict) -> Dict:
        """
        Detailed information card
        
        Args:
            data: Data dictionary to display
            
        Returns:
            Adaptive Card JSON
        """
        facts = []
        for key, value in data.items():
            if isinstance(value, dict):
                # Nested data
                for sub_key, sub_value in value.items():
                    facts.append({
                        "title": f"{key}.{sub_key}:",
                        "value": str(sub_value)
                    })
            else:
                facts.append({
                    "title": f"{key}:",
                    "value": str(value)
                })
        
        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "📋 Details",
                            "weight": "Bolder",
                            "size": "Large"
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": [
                        {
                            "type": "FactSet",
                            "facts": facts
                        }
                    ]
                }
            ]
        }