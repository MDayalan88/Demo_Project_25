# Deploy Lambda Functions and Step Functions State Machine
# PowerShell Script for AWS Deployment

param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$AccountId = "637423332185"
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "FileFerry - Phase 3 Deployment Script" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI
Write-Host "🔍 Checking AWS CLI..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version 2>&1
    Write-Host "✅ AWS CLI found: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not found. Please install AWS CLI first." -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host "🔍 Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --query 'Account' --output text
    Write-Host "✅ AWS Account: $identity" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not configured. Run 'aws configure'" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Step 1: Create IAM Role for Lambda Functions" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$lambdaRoleName = "FileFerryLambdaExecutionRole"

# Check if role exists
$roleExists = aws iam get-role --role-name $lambdaRoleName 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating IAM role: $lambdaRoleName..." -ForegroundColor Yellow
    
    # Create trust policy
    $trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@
    
    $trustPolicy | Out-File -FilePath ".\trust-policy.json" -Encoding utf8
    
    aws iam create-role `
        --role-name $lambdaRoleName `
        --assume-role-policy-document file://trust-policy.json
    
    # Attach policies
    aws iam attach-role-policy `
        --role-name $lambdaRoleName `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    aws iam attach-role-policy `
        --role-name $lambdaRoleName `
        --policy-arn "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
    
    aws iam attach-role-policy `
        --role-name $lambdaRoleName `
        --policy-arn "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
    
    Write-Host "✅ IAM role created" -ForegroundColor Green
    
    # Wait for role to propagate
    Write-Host "⏳ Waiting 10 seconds for IAM role to propagate..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
} else {
    Write-Host "✅ IAM role already exists" -ForegroundColor Green
}

$lambdaRoleArn = "arn:aws:iam::${AccountId}:role/${lambdaRoleName}"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Step 2: Package and Deploy Lambda Functions" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$lambdaFunctions = @(
    @{Name="FileFerry-ValidateInput"; File="validate_input.py"; Handler="validate_input.lambda_handler"},
    @{Name="FileFerry-AuthSSO"; File="auth_sso.py"; Handler="auth_sso.lambda_handler"},
    @{Name="FileFerry-DownloadS3"; File="download_s3.py"; Handler="download_s3.lambda_handler"},
    @{Name="FileFerry-TransferFTP"; File="transfer_ftp.py"; Handler="transfer_ftp.lambda_handler"},
    @{Name="FileFerry-ChunkedTransfer"; File="chunked_transfer.py"; Handler="chunked_transfer.lambda_handler"},
    @{Name="FileFerry-UpdateServiceNow"; File="update_servicenow.py"; Handler="update_servicenow.lambda_handler"},
    @{Name="FileFerry-NotifyUser"; File="notify_user.py"; Handler="notify_user.lambda_handler"},
    @{Name="FileFerry-Cleanup"; File="cleanup.py"; Handler="cleanup.lambda_handler"}
)

$deployedLambdas = @{}

foreach ($lambda in $lambdaFunctions) {
    Write-Host "📦 Deploying: $($lambda.Name)..." -ForegroundColor Yellow
    
    $functionPath = ".\infrastructure\lambda_functions\$($lambda.File)"
    
    if (-not (Test-Path $functionPath)) {
        Write-Host "❌ File not found: $functionPath" -ForegroundColor Red
        continue
    }
    
    # Create deployment package
    $zipFile = "$($lambda.File).zip"
    Compress-Archive -Path $functionPath -DestinationPath $zipFile -Force
    
    # Check if function exists
    $functionExists = aws lambda get-function --function-name $($lambda.Name) 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        # Update existing function
        Write-Host "  Updating existing function..." -ForegroundColor Cyan
        aws lambda update-function-code `
            --function-name $($lambda.Name) `
            --zip-file fileb://$zipFile
    } else {
        # Create new function
        Write-Host "  Creating new function..." -ForegroundColor Cyan
        aws lambda create-function `
            --function-name $($lambda.Name) `
            --runtime python3.11 `
            --role $lambdaRoleArn `
            --handler $($lambda.Handler) `
            --zip-file fileb://$zipFile `
            --timeout 300 `
            --memory-size 512 `
            --environment "Variables={SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com}"
    }
    
    if ($LASTEXITCODE -eq 0) {
        $functionArn = "arn:aws:lambda:${Region}:${AccountId}:function:$($lambda.Name)"
        $deployedLambdas[$lambda.Name] = $functionArn
        Write-Host "✅ Deployed: $($lambda.Name)" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to deploy: $($lambda.Name)" -ForegroundColor Red
    }
    
    # Clean up zip file
    Remove-Item $zipFile -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Step 3: Create Step Functions State Machine" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# Update state machine JSON with actual ARNs
$stateMachinePath = ".\infrastructure\step_functions_state_machine.json"
$stateMachineJson = Get-Content $stateMachinePath -Raw

# Replace placeholders
$stateMachineJson = $stateMachineJson -replace '\$\{AWS_REGION\}', $Region
$stateMachineJson = $stateMachineJson -replace '\$\{ACCOUNT_ID\}', $AccountId

$stateMachineJson | Out-File -FilePath ".\step_functions_deployed.json" -Encoding utf8

Write-Host "📝 State machine JSON updated with ARNs" -ForegroundColor Yellow

# Create IAM role for Step Functions
$sfnRoleName = "FileFerryStepFunctionsRole"
$sfnRoleExists = aws iam get-role --role-name $sfnRoleName 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating IAM role for Step Functions..." -ForegroundColor Yellow
    
    $sfnTrustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "states.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@
    
    $sfnTrustPolicy | Out-File -FilePath ".\sfn-trust-policy.json" -Encoding utf8
    
    aws iam create-role `
        --role-name $sfnRoleName `
        --assume-role-policy-document file://sfn-trust-policy.json
    
    aws iam attach-role-policy `
        --role-name $sfnRoleName `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
    
    Write-Host "✅ Step Functions IAM role created" -ForegroundColor Green
    Start-Sleep -Seconds 10
}

$sfnRoleArn = "arn:aws:iam::${AccountId}:role/${sfnRoleName}"

# Create or update state machine
$stateMachineName = "FileFerry-TransferStateMachine"
$stateMachineExists = aws stepfunctions describe-state-machine --state-machine-arn "arn:aws:states:${Region}:${AccountId}:stateMachine:${stateMachineName}" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Updating existing state machine..." -ForegroundColor Yellow
    aws stepfunctions update-state-machine `
        --state-machine-arn "arn:aws:states:${Region}:${AccountId}:stateMachine:${stateMachineName}" `
        --definition file://step_functions_deployed.json
} else {
    Write-Host "Creating new state machine..." -ForegroundColor Yellow
    aws stepfunctions create-state-machine `
        --name $stateMachineName `
        --definition file://step_functions_deployed.json `
        --role-arn $sfnRoleArn
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Step Functions state machine deployed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to deploy state machine" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Lambda Functions: $($deployedLambdas.Count) deployed" -ForegroundColor Green
Write-Host "✅ Step Functions: State machine created/updated" -ForegroundColor Green
Write-Host ""
Write-Host "State Machine ARN:" -ForegroundColor Yellow
Write-Host "arn:aws:states:${Region}:${AccountId}:stateMachine:${stateMachineName}" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test Lambda functions individually" -ForegroundColor White
Write-Host "2. Test Step Functions execution" -ForegroundColor White
Write-Host "3. Configure ServiceNow credentials in Lambda environment variables" -ForegroundColor White
Write-Host "4. Update config.yaml with state machine ARN" -ForegroundColor White
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan

# Clean up temporary files
Remove-Item ".\trust-policy.json" -ErrorAction SilentlyContinue
Remove-Item ".\sfn-trust-policy.json" -ErrorAction SilentlyContinue
Remove-Item ".\step_functions_deployed.json" -ErrorAction SilentlyContinue
