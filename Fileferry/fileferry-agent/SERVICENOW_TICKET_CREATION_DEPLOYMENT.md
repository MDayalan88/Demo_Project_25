# ServiceNow Ticket Creation - Deployment Guide

## Overview
This adds automatic ServiceNow ticket creation to your FileFerry workflow. Real tickets will be created before transfers start.

## What's New

### 1. New Lambda Function: `FileFerry-CreateServiceNowTickets`
- **Purpose**: Creates 2 tickets in ServiceNow before transfer starts
- **Tickets Created**:
  - User Incident (INC######) - Tracks the transfer request
  - Audit Trail (INC######) - Compliance tracking
- **Location**: `cloudshell-deployment/lambda_functions/create_servicenow_tickets.py`

### 2. Updated Step Functions Workflow
- **Change**: Adds ticket creation as first step
- **Flow**: 
  1. Create ServiceNow Tickets → 
  2. Validate Input → 
  3. Download S3 → 
  4. Transfer FTP → 
  5. Update Tickets with result
- **Location**: `cloudshell-deployment/step_functions_with_ticket_creation.json`

## Deployment Steps

### Step 1: Deploy Lambda Function (5 minutes)

1. **Upload to CloudShell**:
   ```bash
   # Upload these files to CloudShell:
   # - lambda_functions/create_servicenow_tickets.py
   # - deploy-create-tickets-lambda.sh
   ```

2. **Run Deployment Script**:
   ```bash
   cd cloudshell-deployment
   chmod +x deploy-create-tickets-lambda.sh
   ./deploy-create-tickets-lambda.sh
   ```

3. **Verify**:
   - Check AWS Lambda Console
   - Function: `FileFerry-CreateServiceNowTickets`
   - Should have Lambda Layer for `requests` library
   - Should have ServiceNow environment variables

### Step 2: Update Step Functions (3 minutes)

1. **Open Step Functions Console**:
   - Go to: https://console.aws.amazon.com/states/home?region=us-east-1
   - Find: `FileFerry-TransferStateMachine`
   - Click: Edit

2. **Replace Definition**:
   - Click "Definition" tab
   - Replace entire JSON with content from:
     `step_functions_with_ticket_creation.json`
   - Click "Save"

3. **Deploy**:
   - Click "Update state machine"
   - Confirm changes

### Step 3: Test (2 minutes)

1. **Test Lambda Function**:
   ```bash
   # Test event:
   {
     "user_id": "test@example.com",
     "transfer_plan": {
       "source": {
         "bucket": "my-test-bucket",
         "file": "test-file.txt",
         "size": "1 TB"
       },
       "destination": {
         "type": "FTP",
         "host": "ftp.example.com",
         "path": "/uploads"
       }
     }
   }
   ```

2. **Check ServiceNow**:
   - Login to ServiceNow portal
   - Go to Incidents
   - Look for newly created tickets
   - Should see: "File Transfer Request - test-file.txt"

3. **Test Full Workflow**:
   - Use demo.html to start a transfer
   - Check Step Functions execution
   - Verify tickets created at start
   - Verify tickets updated at completion

## How It Works

### Before (Old Flow):
```
Frontend generates mock ticket → Transfer starts → Lambda tries to update non-existent ticket → Fails silently
```

### After (New Flow):
```
1. Frontend sends transfer request
2. Step Functions calls CreateServiceNowTickets Lambda
3. Lambda creates 2 real tickets in ServiceNow
4. Ticket numbers returned (INC0012345, INC0012346)
5. Transfer proceeds with real ticket numbers
6. UpdateServiceNow Lambda updates those real tickets
7. You see updates in ServiceNow portal ✅
```

## Ticket Details

### User Incident Ticket
- **Number**: INC#######
- **Short Description**: "File Transfer Request - {filename}"
- **Description**: Full transfer details (source, destination, user, size)
- **Category**: Data Transfer
- **Priority**: Moderate
- **State**: In Progress → Resolved (when complete)

### Audit Trail Ticket
- **Number**: INC#######
- **Short Description**: "Transfer Audit Trail - {filename}"
- **Description**: Compliance tracking information
- **Category**: Audit
- **Priority**: Low
- **Caller**: system@fileferry.com

## Fallback Behavior

If ServiceNow API fails (network issue, credentials, etc.):
- Lambda returns mock tickets (INC0010001, INC0010002)
- Transfer still proceeds
- No ticket updates (graceful degradation)
- Error logged in CloudWatch

## Environment Variables Required

The Lambda function needs these environment variables (automatically copied from `FileFerry-UpdateServiceNow`):

```bash
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password
```

## Troubleshooting

### Lambda fails to create tickets:
1. Check CloudWatch Logs: `/aws/lambda/FileFerry-CreateServiceNowTickets`
2. Verify ServiceNow credentials
3. Test ServiceNow API manually:
   ```bash
   curl -X POST \
     https://your-instance.service-now.com/api/now/table/incident \
     -u username:password \
     -H "Content-Type: application/json" \
     -d '{"short_description":"Test","description":"Test incident"}'
   ```

### Step Functions fails at ticket creation:
- Workflow continues with fallback tickets
- Check execution history in Step Functions Console
- Review "CreateServiceNowTickets" step error details

### Tickets created but not updated:
- Check `FileFerry-UpdateServiceNow` Lambda logs
- Verify ticket numbers passed correctly through workflow
- Check ServiceNow API permissions (PATCH /incident/{sys_id})

## Testing Checklist

- [ ] Lambda function deployed successfully
- [ ] Lambda has requests library (Layer)
- [ ] Lambda has ServiceNow environment variables
- [ ] Step Functions definition updated
- [ ] Test Lambda with sample event
- [ ] Verify tickets created in ServiceNow
- [ ] Test full transfer workflow
- [ ] Verify tickets updated after completion
- [ ] Check CloudWatch logs for errors

## Rollback Plan

If issues occur:

1. **Restore old Step Functions**:
   - Use `step_functions_complete.json` (backup)
   - Edit State Machine → Replace definition

2. **Delete new Lambda** (optional):
   ```bash
   aws lambda delete-function \
     --function-name FileFerry-CreateServiceNowTickets \
     --region us-east-1
   ```

3. **System returns to demo mode**:
   - Mock tickets shown in UI
   - No real ServiceNow integration

## Next Steps

After deployment:
1. Monitor CloudWatch Logs for both Lambdas
2. Review tickets created in ServiceNow
3. Adjust ticket templates if needed (edit `create_servicenow_tickets.py`)
4. Consider adding:
   - Ticket assignment rules
   - Custom categories
   - SLA tracking
   - Email notifications

## Support

If you encounter issues:
1. Check CloudWatch Logs
2. Review Step Functions execution history
3. Test ServiceNow API credentials
4. Verify IAM permissions for Lambda

---

**Deployment Time**: ~10 minutes
**Complexity**: Medium
**Impact**: High (enables real ServiceNow integration)
**Rollback**: Easy (restore old Step Functions definition)
