"""Quick test of FileFerry AI Agent with Bedrock"""
import asyncio
from src.ai_agent.bedrock_agent import BedrockFileFerryAgent
from src.utils.config import load_config

async def test_agent():
    print("\n🧪 Testing FileFerry AI Agent...")
    
    # Load config
    config = load_config('config/config.yaml')
    
    # Initialize agent
    agent = BedrockFileFerryAgent(config)
    
    # Test natural language request
    response = await agent.process_natural_language_request(
        user_id="test_user",
        user_message="List my S3 buckets in us-east-1"
    )
    
    print("\n✅ Agent Response:")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())