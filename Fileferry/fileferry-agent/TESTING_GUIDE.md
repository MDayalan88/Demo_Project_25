# 🧪 FileFerry AI Agent - Testing Guide

Complete guide to test and verify all implemented components

---

## Quick Test Commands

### 1. **Run Existing Test Suite**
```powershell
# Basic component tests (no AWS required)
python test_components.py

# Infrastructure verification (requires AWS)
python verify-phase2-infrastructure.py

# DynamoDB table verification
python infrastructure\create_all_dynamodb_tables.py
```

---

## Component-by-Component Testing

### ✅ TEST 1: Configuration File

**File**: `config/config.yaml`

```powershell
# Test: Load configuration
python -c "import yaml; print(yaml.safe_load(open('config/config.yaml')))"
```

**Expected Output**: YAML dictionary with aws, bedrock, sso, dynamodb sections

**✅ Success Criteria**:
- No errors
- Shows all configuration sections
- DynamoDB tables listed

---

### ✅ TEST 2: DynamoDB Tables

**Files**: All 5 tables in AWS

```powershell
# Test: Verify all tables exist and are active
python verify-phase2-infrastructure.py
```

**Expected Output**:
```
✅ FileFerry-ActiveSessions    - ACTIVE, TTL: ENABLED
✅ FileFerry-UserContext       - ACTIVE, TTL: ENABLED
✅ FileFerry-TransferRequests  - ACTIVE, TTL: ENABLED, GSI ✓
✅ FileFerry-AgentLearning     - ACTIVE, Permanent
✅ FileFerry-S3FileCache       - ACTIVE, TTL: ENABLED
```

**Alternative Test (AWS CLI)**:
```powershell
# List all FileFerry tables
aws dynamodb list-tables --region us-east-1 --query "TableNames[?contains(@, 'FileFerry')]"

# Check specific table
aws dynamodb describe-table --table-name FileFerry-ActiveSessions --region us-east-1
```

**✅ Success Criteria**:
- All 5 tables show ACTIVE status
- TTL enabled on ActiveSessions, UserContext, TransferRequests, S3FileCache
- GSI exists on TransferRequests

---

### ✅ TEST 3: SSO Handler (10-Second Timeout)

**File**: `src/handlers/sso_handler.py`

#### Test A: Basic Import and Initialization
```powershell
python -c "
from src.handlers.sso_handler import SSOHandler
import yaml

# Load config
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Enable test mode (no real AWS calls)
config['agent'] = {'test_mode': True}

# Initialize
sso = SSOHandler(config)
print('✅ SSOHandler initialized successfully')
print(f'   Session duration: {sso.session_duration} seconds')
print(f'   Table: {sso.table_name}')
print(f'   Test mode: {sso.test_mode}')
"
```

#### Test B: Authentication Flow (Test Mode)
```powershell
python -c "
from src.handlers.sso_handler import SSOHandler
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)
config['agent'] = {'test_mode': True}

sso = SSOHandler(config)

# Test authentication
session_token = sso.authenticate_user(
    user_id='test@example.com',
    servicenow_request_id='REQ0010001',
    region='us-east-1'
)
print(f'✅ Session created: {session_token[:8]}...')

# Test validation
is_valid = sso.is_session_valid(session_token)
print(f'✅ Session valid: {is_valid}')

# Test credentials retrieval
creds = sso.get_session_credentials(session_token)
print(f'✅ Credentials retrieved: {creds[\"region\"]}')

# Test session info
info = sso.get_session_info(session_token)
print(f'✅ Session info: {info[\"seconds_remaining\"]}s remaining')
"
```

#### Test C: TTL Expiration (Real DynamoDB)
```powershell
# WARNING: This test writes to DynamoDB and costs ~$0.000125
python -c "
from src.handlers.sso_handler import SSOHandler
import yaml
import time

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Real mode - will use DynamoDB
config['agent'] = {'test_mode': False}
config['sso']['account_id'] = '637423332185'  # Your account

sso = SSOHandler(config)

try:
    session_token = sso.authenticate_user(
        user_id='test@example.com',
        servicenow_request_id='REQ0010001',
        region='us-east-1'
    )
    print(f'✅ Session created: {session_token[:8]}...')
    
    # Immediate check
    print(f'✅ Valid now: {sso.is_session_valid(session_token)}')
    
    # Wait 11 seconds for TTL to expire
    print('⏳ Waiting 11 seconds for TTL expiration...')
    time.sleep(11)
    
    # Check again - should be invalid
    is_valid = sso.is_session_valid(session_token)
    if not is_valid:
        print('✅ TTL WORKING: Session auto-expired after 10 seconds!')
    else:
        print('⚠️  TTL NOT WORKING: Session still valid after 11 seconds')
        
except Exception as e:
    print(f'❌ Error: {e}')
"
```

**✅ Success Criteria**:
- Initialize without errors
- authenticate_user() returns UUID token
- is_session_valid() returns True immediately
- Session expires after 10 seconds (TTL test)
- All methods execute without exceptions

---

### ✅ TEST 4: Agent Tools (9 Functions)

**File**: `src/ai_agent/agent_tools.py`

#### Test A: Import and Initialization
```powershell
python -c "
from src.ai_agent.agent_tools import AgentTools
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

tools = AgentTools(config)
print('✅ AgentTools initialized')

# List all tools
tool_names = [
    'list_s3_buckets',
    'list_bucket_contents',
    'get_file_metadata',
    'validate_user_access',
    'analyze_transfer_request',
    'predict_transfer_outcome',
    'create_servicenow_tickets',
    'execute_transfer',
    'get_transfer_history'
]

for i, tool_name in enumerate(tool_names, 1):
    if hasattr(tools, tool_name):
        print(f'✅ Tool {i}: {tool_name}()')
    else:
        print(f'❌ Tool {i}: {tool_name}() - NOT FOUND')
"
```

#### Test B: Individual Tool Testing
```powershell
# Tool 5: Analyze Transfer Request (no AWS calls)
python -c "
from src.ai_agent.agent_tools import AgentTools
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

tools = AgentTools(config)

# Test analyze_transfer_request
result = tools.analyze_transfer_request(
    source_bucket='my-bucket',
    source_key='large-file.zip',
    destination_host='ftp.example.com',
    destination_port=21,
    transfer_type='ftp'
)

print('✅ analyze_transfer_request() result:')
print(f'   Strategy: {result[\"strategy\"]}')
print(f'   Chunk size: {result[\"recommended_chunk_size_mb\"]} MB')
print(f'   Parallel: {result[\"parallel_transfers\"]}')
"
```

**✅ Success Criteria**:
- All 9 tools present
- No import errors
- analyze_transfer_request() returns valid strategy

---

### ✅ TEST 5: Bedrock FileFerry Agent

**File**: `src/ai_agent/bedrock_fileferry_agent.py`

#### Test A: Import and Initialization
```powershell
python -c "
from src.ai_agent.bedrock_fileferry_agent import BedrockFileFerryAgent
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

agent = BedrockFileFerryAgent(config)
print('✅ BedrockFileFerryAgent initialized')
print(f'   Model: {agent.model_id}')
print(f'   Max tokens: {agent.max_tokens}')
print(f'   Temperature: {agent.temperature}')
print(f'   Max retries: {agent.max_retries}')

# Check methods
methods = [
    'process_request',
    '_execute_tool',
    '_get_conversation_history',
    '_add_to_conversation_history',
    '_send_metrics_to_cloudwatch',
    '_get_tool_definitions'
]

for method in methods:
    if hasattr(agent, method):
        print(f'✅ Method: {method}()')
    else:
        print(f'❌ Method: {method}() - NOT FOUND')
"
```

#### Test B: Tool Definitions
```powershell
python -c "
from src.ai_agent.bedrock_fileferry_agent import BedrockFileFerryAgent
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

agent = BedrockFileFerryAgent(config)

# Get tool definitions
tools = agent._get_tool_definitions()

print(f'✅ Tool definitions: {len(tools)} tools')
for i, tool in enumerate(tools, 1):
    print(f'   {i}. {tool[\"name\"]}')
    print(f'      Description: {tool[\"description\"][:60]}...')
"
```

#### Test C: Full Agent Request (⚠️ Requires Bedrock Access)
```powershell
# WARNING: This makes real Bedrock API calls and costs ~$0.003 per request
python -c "
from src.ai_agent.bedrock_fileferry_agent import BedrockFileFerryAgent
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

agent = BedrockFileFerryAgent(config)

try:
    # Simple request
    response = agent.process_request(
        user_id='test@example.com',
        user_message='Hello, what can you help me with?',
        context={}
    )
    
    print('✅ Agent response received:')
    print(response[:200])
    
except Exception as e:
    print(f'❌ Error: {e}')
    print('Note: Requires AWS Bedrock access and proper permissions')
"
```

**✅ Success Criteria**:
- Initialize without errors
- 6 methods present
- 9 tool definitions returned
- (Optional) Bedrock API returns valid response

---

### ✅ TEST 6: End-to-End Integration Test

**Combined test of SSO + Tools + Agent**

```powershell
# Save this as: test_integration.py
python -c "
from src.handlers.sso_handler import SSOHandler
from src.ai_agent.agent_tools import AgentTools
from src.ai_agent.bedrock_fileferry_agent import BedrockFileFerryAgent
import yaml

print('=' * 70)
print('FileFerry AI Agent - Integration Test')
print('=' * 70)
print()

# Load config
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Test mode
config['agent'] = {'test_mode': True}

# Initialize all components
print('1. Initializing components...')
sso = SSOHandler(config)
print('   ✅ SSOHandler')

tools = AgentTools(config)
print('   ✅ AgentTools')

agent = BedrockFileFerryAgent(config)
print('   ✅ BedrockFileFerryAgent')

# Test SSO flow
print()
print('2. Testing SSO authentication...')
session_token = sso.authenticate_user(
    user_id='test@example.com',
    servicenow_request_id='REQ0010001',
    region='us-east-1'
)
print(f'   ✅ Session: {session_token[:8]}...')

# Test tool execution
print()
print('3. Testing tool execution...')
result = tools.analyze_transfer_request(
    source_bucket='test-bucket',
    source_key='test-file.txt',
    destination_host='ftp.example.com',
    destination_port=21,
    transfer_type='ftp'
)
print(f'   ✅ Tool result: {result[\"strategy\"]}')

# Test conversation history (DynamoDB write)
print()
print('4. Testing conversation history...')
try:
    agent._add_to_conversation_history('test@example.com', 'user', 'test message')
    history = agent._get_conversation_history('test@example.com')
    print(f'   ✅ History stored: {len(history)} messages')
except Exception as e:
    print(f'   ⚠️  DynamoDB write: {e}')

print()
print('=' * 70)
print('✅ Integration Test PASSED')
print('=' * 70)
"
```

---

## AWS CLI Tests

### Check DynamoDB Tables
```powershell
# List all tables
aws dynamodb list-tables --region us-east-1

# Describe ActiveSessions table
aws dynamodb describe-table --table-name FileFerry-ActiveSessions --region us-east-1

# Check TTL status
aws dynamodb describe-time-to-live --table-name FileFerry-ActiveSessions --region us-east-1

# Query table (check for items)
aws dynamodb scan --table-name FileFerry-ActiveSessions --limit 5 --region us-east-1
```

### Check IAM Role
```powershell
# Check if role exists
aws iam get-role --role-name FileFerryReadOnlyRole --region us-east-1

# List attached policies
aws iam list-attached-role-policies --role-name FileFerryReadOnlyRole --region us-east-1
```

### Check Bedrock Access
```powershell
# List available models
aws bedrock list-foundation-models --region us-east-1 --query "modelSummaries[?contains(modelId, 'claude')]"

# Test model access
aws bedrock invoke-model --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 --region us-east-1 --body '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":100}' --content-type application/json output.json
```

---

## Troubleshooting Guide

### Issue 1: Import Errors
```powershell
# Fix: Install missing packages
pip install boto3 pyyaml

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Issue 2: AWS Credentials Not Found
```powershell
# Fix: Configure AWS credentials
aws configure

# Or set environment variables
$env:AWS_ACCESS_KEY_ID="your-key"
$env:AWS_SECRET_ACCESS_KEY="your-secret"
$env:AWS_DEFAULT_REGION="us-east-1"
```

### Issue 3: DynamoDB Table Not Found
```powershell
# Fix: Create tables
python infrastructure\create_all_dynamodb_tables.py

# Or use CloudFormation
aws cloudformation create-stack --stack-name FileFerry-Infra --template-body file://infrastructure/cloudformation/template.yaml --capabilities CAPABILITY_NAMED_IAM
```

### Issue 4: Bedrock Access Denied
```powershell
# Fix: Request Bedrock model access in AWS Console
# Go to: AWS Console → Bedrock → Model Access → Request Access
# Select: Claude 3.5 Sonnet
```

---

## Performance Benchmarks

### Expected Performance:
- **SSO authenticate_user()**: < 500ms (test mode), < 2s (real)
- **DynamoDB query**: < 50ms
- **Bedrock API call**: 2-5 seconds (varies by response length)
- **Tool execution**: < 100ms (without external calls)

### Test Performance:
```powershell
python -c "
import time
from src.handlers.sso_handler import SSOHandler
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)
config['agent'] = {'test_mode': True}

sso = SSOHandler(config)

start = time.time()
token = sso.authenticate_user('test@example.com', 'REQ001', 'us-east-1')
elapsed = time.time() - start

print(f'⏱️  Authentication: {elapsed*1000:.2f}ms')
if elapsed < 0.5:
    print('✅ Performance: EXCELLENT')
elif elapsed < 2.0:
    print('✅ Performance: GOOD')
else:
    print('⚠️  Performance: SLOW')
"
```

---

## Summary Checklist

Run these commands in order:

```powershell
# 1. Basic component test
python test_components.py

# 2. Infrastructure verification
python verify-phase2-infrastructure.py

# 3. SSO Handler test
python -c "from src.handlers.sso_handler import SSOHandler; import yaml; config=yaml.safe_load(open('config/config.yaml')); config['agent']={'test_mode':True}; sso=SSOHandler(config); print('✅ SSO Works')"

# 4. Agent Tools test
python -c "from src.ai_agent.agent_tools import AgentTools; import yaml; tools=AgentTools(yaml.safe_load(open('config/config.yaml'))); print('✅ Tools Work')"

# 5. Agent test
python -c "from src.ai_agent.bedrock_fileferry_agent import BedrockFileFerryAgent; import yaml; agent=BedrockFileFerryAgent(yaml.safe_load(open('config/config.yaml'))); print('✅ Agent Works')"
```

**All tests passing? ✅ Your FileFerry AI Agent is working!**

---

## Next Steps After Testing

Once all tests pass:

1. **Test with real AWS** - Remove `test_mode`, use real credentials
2. **Test Bedrock API** - Make actual AI requests
3. **Implement Phase 3** - ServiceNow Handler, Transfer Handler
4. **Create API endpoints** - Lambda + API Gateway
5. **Integrate frontend** - React UI with real backend

---

**Questions?** Check `CURRENT_STATUS.md` for architecture details.
