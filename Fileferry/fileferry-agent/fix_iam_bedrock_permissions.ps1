Write-Host "Checking and Fixing IAM Bedrock Permissions..." -ForegroundColor Cyan
Write-Host ""

# Get current IAM user
Write-Host "1. Getting current IAM identity..." -ForegroundColor Yellow
$identity = aws sts get-caller-identity | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to get IAM identity. Ensure AWS CLI is configured." -ForegroundColor Red
    exit 1
}

$userName = $identity.Arn -replace 'arn:aws:iam::\d+:user/', ''
$accountId = $identity.Account

Write-Host "   SUCCESS: Current user: $userName" -ForegroundColor Green
Write-Host "   Account ID: $accountId" -ForegroundColor Gray
Write-Host ""

# Check if user already has Bedrock access
Write-Host "2. Checking existing Bedrock permissions..." -ForegroundColor Yellow
$policies = aws iam list-attached-user-policies --user-name $userName | ConvertFrom-Json

$hasBedrockAccess = $false
foreach ($policy in $policies.AttachedPolicies) {
    if ($policy.PolicyName -like "*Bedrock*") {
        Write-Host "   SUCCESS: Found policy: $($policy.PolicyName)" -ForegroundColor Green
        $hasBedrockAccess = $true
    }
}

if (!$hasBedrockAccess) {
    Write-Host "   WARNING: No Bedrock policies found" -ForegroundColor Yellow
    Write-Host ""
    
    # Option 1: Attach AmazonBedrockFullAccess (recommended for development)
    Write-Host "3. Attaching Bedrock permissions..." -ForegroundColor Yellow
    Write-Host "   Using: AmazonBedrockFullAccess (AWS managed policy)" -ForegroundColor Gray
    
    $attachResult = aws iam attach-user-policy `
        --user-name $userName `
        --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   SUCCESS: Attached AmazonBedrockFullAccess policy" -ForegroundColor Green
    } else {
        Write-Host "   ERROR: Failed to attach policy: $attachResult" -ForegroundColor Red
        Write-Host ""
        Write-Host "   ALTERNATIVE: Creating inline policy with minimum permissions" -ForegroundColor Yellow
        
        # Create minimum Bedrock policy
        $minPolicy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = @(
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    )
                    Resource = "arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
                }
            )
        } | ConvertTo-Json -Depth 10 -Compress
        
        $policyFile = "bedrock-min-policy.json"
        $minPolicy | Out-File -FilePath $policyFile -Encoding utf8
        
        aws iam put-user-policy `
            --user-name $userName `
            --policy-name FileFerry-Bedrock-Access `
            --policy-document "file://$policyFile"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   SUCCESS: Created inline policy: FileFerry-Bedrock-Access" -ForegroundColor Green
            Remove-Item $policyFile -Force
        } else {
            Write-Host "   ERROR: Failed to create inline policy" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   SUCCESS: Bedrock access already configured" -ForegroundColor Green
}

Write-Host ""

# Check Bedrock model access
Write-Host "4. Verifying Bedrock model access..." -ForegroundColor Yellow
$modelId = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

# Try to list foundation models (simpler test than invoking)
$models = aws bedrock list-foundation-models --region us-east-1 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "   SUCCESS: Bedrock API access confirmed" -ForegroundColor Green
    
    # Check if our specific model is available
    $modelsJson = $models | ConvertFrom-Json
    $ourModel = $modelsJson.modelSummaries | Where-Object { $_.modelId -eq $modelId }
    
    if ($ourModel) {
        Write-Host "   SUCCESS: Model available: $modelId" -ForegroundColor Green
        Write-Host "   Model status: $($ourModel.modelLifecycle.status)" -ForegroundColor Gray
    } else {
        Write-Host "   WARNING: Model not found in available models" -ForegroundColor Yellow
        Write-Host "   ACTION REQUIRED: Request model access in AWS Console" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ERROR: Bedrock API access denied: $models" -ForegroundColor Red
    Write-Host ""
    Write-Host "   TROUBLESHOOTING STEPS:" -ForegroundColor Yellow
    Write-Host "   1. Check AWS region (must be us-east-1)" -ForegroundColor Gray
    Write-Host "   2. Verify IAM policies are attached" -ForegroundColor Gray
    Write-Host "   3. Request model access: https://console.aws.amazon.com/bedrock/" -ForegroundColor Gray
}

Write-Host ""

# Summary
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "IAM Permission Check Complete" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Clear Python cache:" -ForegroundColor Gray
Write-Host "   Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force" -ForegroundColor White
Write-Host ""
Write-Host "2. Test agent:" -ForegroundColor Gray
Write-Host "   python local_agent.py" -ForegroundColor White
Write-Host ""
Write-Host "3. If still failing, check model access:" -ForegroundColor Gray
Write-Host "   https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess" -ForegroundColor White
Write-Host ""