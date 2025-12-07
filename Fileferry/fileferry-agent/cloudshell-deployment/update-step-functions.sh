#!/bin/bash

# Update Step Functions workflow with ticket creation
echo "🔄 Updating FileFerry-TransferStateMachine..."
echo ""

STATE_MACHINE_ARN="arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine"
REGION="us-east-1"

# Check if JSON file exists
if [ ! -f "step_functions_with_ticket_creation.json" ]; then
    echo "❌ Error: step_functions_with_ticket_creation.json not found!"
    echo "   Make sure to upload this file to CloudShell first."
    exit 1
fi

echo "📋 Updating state machine definition..."
aws stepfunctions update-state-machine \
    --state-machine-arn "$STATE_MACHINE_ARN" \
    --definition file://step_functions_with_ticket_creation.json \
    --region $REGION

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ STEP FUNCTIONS UPDATED SUCCESSFULLY!"
    echo ""
    echo "📋 New Workflow:"
    echo "   1. CreateServiceNowTickets → Creates real tickets"
    echo "   2. MergeTicketsWithInput → Adds ticket numbers"
    echo "   3. ValidateInput → Validates transfer"
    echo "   4. DownloadFromS3 → Downloads file"
    echo "   5. TransferToFTP/ChunkedTransfer → Transfers file"
    echo "   6. UpdateServiceNowSuccess → Updates tickets"
    echo "   7. NotifyUser → Sends notification"
    echo "   8. Cleanup → Cleans up"
    echo ""
    echo "🧪 Test it:"
    echo "   1. Refresh demo.html (Ctrl+F5)"
    echo "   2. Start a file transfer"
    echo "   3. Check ServiceNow portal for real tickets!"
    echo ""
    echo "🔍 View in Console:"
    echo "   https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines/view/$STATE_MACHINE_ARN"
    echo ""
else
    echo ""
    echo "❌ Failed to update Step Functions"
    echo ""
    echo "Possible issues:"
    echo "  1. State machine not found (check name/ARN)"
    echo "  2. JSON syntax error (validate JSON)"
    echo "  3. Lambda functions don't exist yet"
    echo ""
    echo "Debug:"
    echo "  aws stepfunctions describe-state-machine --state-machine-arn $STATE_MACHINE_ARN"
    echo ""
fi
