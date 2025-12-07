#!/bin/bash

# Deploy Create ServiceNow Tickets Lambda Function
# Run this in AWS CloudShell

echo "🚀 Deploying FileFerry-CreateServiceNowTickets Lambda..."

# Configuration
FUNCTION_NAME="FileFerry-CreateServiceNowTickets"
REGION="us-east-1"
ROLE_NAME="FileFerryLambdaExecutionRole"

# Get the role ARN
echo "📋 Getting IAM role ARN..."
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text --region $REGION)

if [ -z "$ROLE_ARN" ]; then
    echo "❌ Role $ROLE_NAME not found!"
    exit 1
fi

echo "✅ Role ARN: $ROLE_ARN"

# Create deployment package
echo "📦 Creating deployment package..."
cd lambda_functions

# Create temporary directory
mkdir -p /tmp/lambda_deploy
cp create_servicenow_tickets.py /tmp/lambda_deploy/lambda_function.py

# Create ZIP
cd /tmp/lambda_deploy
zip -r function.zip .

echo "✅ Package created"

# Check if function exists
echo "🔍 Checking if function exists..."
aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &>/dev/null

if [ $? -eq 0 ]; then
    echo "🔄 Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION
    
    echo "⚙️ Updating configuration..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --handler lambda_function.lambda_handler \
        --timeout 30 \
        --memory-size 256 \
        --region $REGION
else
    echo "🆕 Creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://function.zip \
        --timeout 30 \
        --memory-size 256 \
        --region $REGION \
        --description "Create ServiceNow tickets for file transfers"
fi

# Add Lambda Layer for requests library
echo "📚 Adding Lambda Layer (requests library)..."
LAYER_ARN="arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:18"

aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --layers $LAYER_ARN \
    --region $REGION

# Get ServiceNow environment variables from UpdateServiceNow function
echo "🔑 Getting ServiceNow credentials from existing Lambda..."
SERVICENOW_CONFIG=$(aws lambda get-function-configuration \
    --function-name FileFerry-UpdateServiceNow \
    --query 'Environment.Variables' \
    --output json \
    --region $REGION)

if [ ! -z "$SERVICENOW_CONFIG" ] && [ "$SERVICENOW_CONFIG" != "null" ]; then
    echo "✅ Found ServiceNow configuration"
    
    # Update environment variables
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment "Variables=$SERVICENOW_CONFIG" \
        --region $REGION
    
    echo "✅ Environment variables configured"
else
    echo "⚠️ No ServiceNow config found - you'll need to add manually"
fi

# Cleanup
rm -rf /tmp/lambda_deploy

echo ""
echo "========================================="
echo "   ✅ LAMBDA DEPLOYED SUCCESSFULLY!"
echo "========================================="
echo ""
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Runtime: Python 3.11"
echo ""
echo "Next Steps:"
echo "1. Update Step Functions to call this Lambda first"
echo "2. Test the function in AWS Console"
echo "3. Deploy updated Step Functions workflow"
echo ""
