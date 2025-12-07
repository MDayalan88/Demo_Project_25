"""
Adaptive Card Templates for FileFerry Teams Bot
Creates rich, interactive cards for Microsoft Teams
Following Adaptive Cards schema v1.4
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class AdaptiveCards:
    """
    Adaptive Card factory for FileFerry Teams Bot
    Creates rich, interactive cards for Teams conversations
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
                                    "value": "Track transfer history and status"
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
                            "text": "💬 **Try asking me:**",
                            "wrap": True,
                            "weight": "Bolder"
                        },
                        {
                            "type": "TextBlock",
                            "text": "• \"List my S3 buckets\"\n• \"Transfer file.txt from my-bucket to ftp.example.com\"\n• \"Show me recent transfers\"\n• \"What's the status of transfer REQ123?\"",
                            "wrap": True,
                            "spacing": "Small"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "List S3 Buckets",
                    "data": {
                        "action": "list_buckets"
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "View Recent Transfers",
                    "data": {
                        "action": "recent_transfers"
                    }
                }
            ]
        }
    
    def create_transfer_request_card(self, 
                                     bucket_name: str,
                                     file_key: str,
                                     destination_host: str,
                                     transfer_id: str,
                                     estimated_time: str = "5 minutes") -> Dict:
        """
        Card showing transfer request details
        
        Args:
            bucket_name: S3 bucket name
            file_key: S3 object key
            destination_host: FTP/SFTP destination
            transfer_id: Unique transfer ID
            estimated_time: Estimated completion time
            
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
                            "text": "📤 Transfer Request Created",
                            "weight": "Bolder",
                            "size": "Large",
                            "color": "Good"
                        }
                    ]
                },
                {
                    "type": "FactSet",
                    "separator": True,
                    "spacing": "Medium",
                    "facts": [
                        {
                            "title": "Transfer ID:",
                            "value": transfer_id
                        },
                        {
                            "title": "Source Bucket:",
                            "value": bucket_name
                        },
                        {
                            "title": "File:",
                            "value": file_key
                        },
                        {
                            "title": "Destination:",
                            "value": destination_host
                        },
                        {
                            "title": "Status:",
                            "value": "⏳ In Progress"
                        },
                        {
                            "title": "Estimated Time:",
                            "value": estimated_time
                        }
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": "I've created ServiceNow tickets and started the transfer. You'll receive notifications when it completes.",
                    "wrap": True,
                    "spacing": "Medium",
                    "isSubtle": True
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Check Status",
                    "data": {
                        "action": "check_status",
                        "transfer_id": transfer_id
                    }
                },
                {
                    "type": "Action.OpenUrl",
                    "title": "View in ServiceNow",
                    "url": f"https://your-instance.service-now.com/nav_to.do?uri=u_fileferry_request.do?sysparm_query=transfer_id={transfer_id}"
                }
            ]
        }
    
    def create_transfer_complete_card(self,
                                      transfer_id: str,
                                      bucket_name: str,
                                      file_key: str,
                                      destination_host: str,
                                      file_size: str,
                                      duration: str,
                                      success: bool = True) -> Dict:
        """
        Card showing transfer completion
        
        Args:
            transfer_id: Unique transfer ID
            bucket_name: S3 bucket name
            file_key: S3 object key
            destination_host: FTP/SFTP destination
            file_size: File size (e.g., "10.5 MB")
            duration: Transfer duration (e.g., "3m 45s")
            success: Whether transfer succeeded
            
        Returns:
            Adaptive Card JSON
        """
        status_icon = "✅" if success else "❌"
        status_text = "Transfer Successful!" if success else "Transfer Failed"
        status_color = "Good" if success else "Attention"
        
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
                            "text": f"{status_icon} {status_text}",
                            "weight": "Bolder",
                            "size": "Large",
                            "color": status_color
                        }
                    ]
                },
                {
                    "type": "FactSet",
                    "separator": True,
                    "spacing": "Medium",
                    "facts": [
                        {
                            "title": "Transfer ID:",
                            "value": transfer_id
                        },
                        {
                            "title": "Source:",
                            "value": f"{bucket_name}/{file_key}"
                        },
                        {
                            "title": "Destination:",
                            "value": destination_host
                        },
                        {
                            "title": "File Size:",
                            "value": file_size
                        },
                        {
                            "title": "Duration:",
                            "value": duration
                        },
                        {
                            "title": "Completed:",
                            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "View Details",
                    "data": {
                        "action": "view_details",
                        "transfer_id": transfer_id
                    }
                }
            ]
        }
    
    def create_s3_bucket_list_card(self, buckets: List[Dict[str, Any]]) -> Dict:
        """
        Card showing list of S3 buckets
        
        Args:
            buckets: List of bucket dictionaries with 'name' and 'creation_date'
            
        Returns:
            Adaptive Card JSON
        """
        bucket_items = []
        
        for bucket in buckets[:10]:  # Limit to first 10
            bucket_items.append({
                "type": "TextBlock",
                "text": f"📦 **{bucket.get('name', 'Unknown')}**",
                "wrap": True
            })
            bucket_items.append({
                "type": "TextBlock",
                "text": f"Created: {bucket.get('creation_date', 'Unknown')}",
                "isSubtle": True,
                "spacing": "None",
                "size": "Small"
            })
        
        if len(buckets) > 10:
            bucket_items.append({
                "type": "TextBlock",
                "text": f"... and {len(buckets) - 10} more buckets",
                "isSubtle": True,
                "spacing": "Medium"
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
                            "text": f"📂 Your S3 Buckets ({len(buckets)} total)",
                            "weight": "Bolder",
                            "size": "Large"
                        }
                    ]
                },
                {
                    "type": "Container",
                    "separator": True,
                    "spacing": "Medium",
                    "items": bucket_items
                }
            ]
        }
    
    def create_error_card(self, error_message: str, error_details: Optional[str] = None) -> Dict:
        """
        Card showing error information
        
        Args:
            error_message: Main error message
            error_details: Optional detailed error information
            
        Returns:
            Adaptive Card JSON
        """
        body_items = [
            {
                "type": "Container",
                "style": "attention",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "⚠️ Error",
                        "weight": "Bolder",
                        "size": "Large",
                        "color": "Attention"
                    }
                ]
            },
            {
                "type": "TextBlock",
                "text": error_message,
                "wrap": True,
                "separator": True,
                "spacing": "Medium"
            }
        ]
        
        if error_details:
            body_items.append({
                "type": "TextBlock",
                "text": f"**Details:** {error_details}",
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True
            })
        
        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": body_items,
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Try Again",
                    "data": {
                        "action": "retry"
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "Get Help",
                    "data": {
                        "action": "help"
                    }
                }
            ]
        }
    
    def create_transfer_history_card(self, transfers: List[Dict[str, Any]]) -> Dict:
        """
        Card showing recent transfer history
        
        Args:
            transfers: List of transfer dictionaries with details
            
        Returns:
            Adaptive Card JSON
        """
        if not transfers:
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
                                "text": "📊 Transfer History",
                                "weight": "Bolder",
                                "size": "Large"
                            }
                        ]
                    },
                    {
                        "type": "TextBlock",
                        "text": "No transfers found.",
                        "wrap": True,
                        "separator": True,
                        "spacing": "Medium"
                    }
                ]
            }
        
        transfer_items = []
        
        for transfer in transfers[:5]:  # Show last 5 transfers
            status_icon = "✅" if transfer.get('status') == 'completed' else "⏳"
            transfer_items.append({
                "type": "Container",
                "separator": True,
                "spacing": "Medium",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"{status_icon} **{transfer.get('file_key', 'Unknown file')}**",
                        "wrap": True,
                        "weight": "Bolder"
                    },
                    {
                        "type": "FactSet",
                        "spacing": "Small",
                        "facts": [
                            {
                                "title": "Transfer ID:",
                                "value": transfer.get('transfer_id', 'N/A')
                            },
                            {
                                "title": "Status:",
                                "value": transfer.get('status', 'unknown').capitalize()
                            },
                            {
                                "title": "Date:",
                                "value": transfer.get('created_at', 'Unknown')
                            }
                        ]
                    }
                ]
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
                            "text": f"📊 Recent Transfers ({len(transfers)} total)",
                            "weight": "Bolder",
                            "size": "Large"
                        }
                    ]
                }
            ] + transfer_items
        }
    
    def create_help_card(self) -> Dict:
        """
        Card showing help and available commands
        
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
                            "text": "❓ FileFerry Help",
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
                            "text": "**Available Commands:**",
                            "weight": "Bolder",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": "• **List buckets** - Show all available S3 buckets\n• **List files in [bucket]** - Browse files in a bucket\n• **Transfer [file] from [bucket] to [destination]** - Start a file transfer\n• **Status of [transfer-id]** - Check transfer status\n• **Recent transfers** - Show transfer history\n• **Help** - Show this help message",
                            "wrap": True,
                            "spacing": "Small"
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
                            "text": "**Examples:**",
                            "weight": "Bolder",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": "• \"List my S3 buckets\"\n• \"Show files in my-data-bucket\"\n• \"Transfer report.csv from my-bucket to ftp.example.com\"\n• \"What's the status of REQ0010001?\"",
                            "wrap": True,
                            "spacing": "Small"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "List Buckets",
                    "data": {
                        "action": "list_buckets"
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "Recent Transfers",
                    "data": {
                        "action": "recent_transfers"
                    }
                }
            ]
        }
