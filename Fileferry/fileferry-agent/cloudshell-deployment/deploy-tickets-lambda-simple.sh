#!/bin/bash

# Simple deployment script for FileFerry-CreateServiceNowTickets Lambda
# Run in AWS CloudShell after uploading create_servicenow_tickets.py

echo "🚀 Deploying FileFerry-CreateServiceNowTickets Lambda..."
echo ""

# Configuration
FUNCTION_NAME="FileFerry-CreateServiceNowTickets"
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::637423332185:role/FileFerryLambdaExecutionRole"
LAYER_ARN="arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:18"

# Create deployment package
echo "📦 Creating deployment package..."
mkdir -p /tmp/lambda_deploy
cp create_servicenow_tickets.py /tmp/lambda_deploy/lambda_function.py
cd /tmp/lambda_deploy
zip -q function.zip lambda_function.py
echo "✅ Package created"
echo ""

# Check if function exists
echo "🔍 Checking if function exists..."
aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &>/dev/null

if [ $? -eq 0 ]; then
    # Update existing function
    echo "🔄 Function exists - updating code..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION > /dev/null
    
    echo "⚙️ Updating configuration..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --timeout 30 \
        --memory-size 256 \
        --region $REGION > /dev/null
    
    echo "📚 Adding Lambda Layer..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --layers $LAYER_ARN \
        --region $REGION > /dev/null
else
    # Create new function
    echo "➕ Creating new Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://function.zip \
        --timeout 30 \
        --memory-size 256 \
        --region $REGION > /dev/null
    
    echo "📚 Adding Lambda Layer..."
    sleep 2
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --layers $LAYER_ARN \
        --region $REGION > /dev/null
fi

# Copy ServiceNow environment variables from existing Lambda
echo "🔐 Copying ServiceNow credentials..."
sleep 2

SERVICENOW_CONFIG=$(aws lambda get-function-configuration \
    --function-name FileFerry-UpdateServiceNow \
    --region $REGION \
    --query 'Environment.Variables' \
    --output json)

if [ ! -z "$SERVICENOW_CONFIG" ] && [ "$SERVICENOW_CONFIG" != "null" ]; then
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment "Variables=$SERVICENOW_CONFIG" \
        --region $REGION > /dev/null
    echo "✅ ServiceNow credentials configured"
else
    echo "⚠️  Warning: Could not copy ServiceNow credentials"
    echo "   You may need to set them manually"
fi

echo ""
echo "✅ LAMBDA DEPLOYED SUCCESSFULLY!"
echo ""
echo "📋 Function Details:"
echo "   Name: $FUNCTION_NAME"
echo "   Runtime: Python 3.11"
echo "   Timeout: 30 seconds"
echo "   Memory: 256 MB"
echo "   Layer: AWSSDKPandas (requests library)"
echo ""
echo "🧪 Test the function:"
echo "   aws lambda invoke --function-name $FUNCTION_NAME \\"
echo "     --payload '{\"user_id\":\"test@example.com\",\"transfer_plan\":{\"source\":{\"bucket\":\"test\",\"file\":\"test.txt\",\"size\":\"1MB\"},\"destination\":{\"type\":\"FTP\",\"host\":\"ftp.example.com\",\"path\":\"/uploads\"}}}' \\"
echo "     response.json"
echo ""
echo "✅ Next: Update Step Functions workflow"
echo ""

# Cleanup
rm -rf /tmp/lambda_deploy
