#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Phase 2 Infrastructure Setup - Complete Deployment

.DESCRIPTION
    Creates all DynamoDB tables and IAM roles for FileFerry AI Agent
    Includes: 5 DynamoDB tables, IAM roles, and verification

.PARAMETER Region
    AWS Region (default: us-east-1)

.PARAMETER DryRun
    Preview changes without creating resources

.EXAMPLE
    .\setup-phase2-infrastructure.ps1
    
.EXAMPLE
    .\setup-phase2-infrastructure.ps1 -Region us-west-2 -DryRun
#>

param(
    [string]$Region = "us-east-1",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 69)
Write-Host "FileFerry AI Agent - Phase 2 Infrastructure Setup" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 69)
Write-Host ""
Write-Host "Region: " -NoNewline; Write-Host $Region -ForegroundColor Yellow
Write-Host "Dry Run: " -NoNewline; Write-Host $DryRun -ForegroundColor $(if($DryRun){"Yellow"}else{"Green"})
Write-Host ""

# Check AWS CLI
Write-Host "🔍 Checking AWS CLI..." -ForegroundColor Cyan
try {
    $awsVersion = aws --version 2>&1
    Write-Host "✅ AWS CLI found: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not found. Please install: https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host "🔍 Checking AWS credentials..." -ForegroundColor Cyan
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "✅ Authenticated as: $($identity.Arn)" -ForegroundColor Green
    Write-Host "   Account: $($identity.Account)" -ForegroundColor Gray
} catch {
    Write-Host "❌ AWS credentials not configured. Run 'aws configure'" -ForegroundColor Red
    exit 1
}

if ($DryRun) {
    Write-Host ""
    Write-Host "⚠️  DRY RUN MODE - No resources will be created" -ForegroundColor Yellow
    Write-Host ""
}

# Function to check if table exists
function Test-DynamoDBTable {
    param([string]$TableName)
    
    try {
        aws dynamodb describe-table --table-name $TableName --region $Region --output json 2>$null | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to create table
function New-DynamoDBTable {
    param(
        [string]$TableName,
        [string]$Description,
        [hashtable]$Config
    )
    
    Write-Host ""
    Write-Host "📋 $Description" -ForegroundColor Cyan
    Write-Host "   Table: $TableName" -ForegroundColor Gray
    
    if (Test-DynamoDBTable -TableName $TableName) {
        Write-Host "   ✅ Already exists" -ForegroundColor Green
        return
    }
    
    if ($DryRun) {
        Write-Host "   🔸 Would create table" -ForegroundColor Yellow
        return
    }
    
    Write-Host "   🔧 Creating..." -ForegroundColor Yellow
    
    try {
        # Run Python script to create tables
        python infrastructure\create_all_dynamodb_tables.py
        
        Write-Host "   ✅ Created successfully" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Error: $_" -ForegroundColor Red
        throw
    }
}

# Create DynamoDB tables using Python script
Write-Host ""
Write-Host "🗄️  Creating DynamoDB Tables..." -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN: Would create the following tables:" -ForegroundColor Yellow
    Write-Host "  1. FileFerry-ActiveSessions    (10-sec TTL)" -ForegroundColor Gray
    Write-Host "  2. FileFerry-UserContext       (30-day TTL)" -ForegroundColor Gray
    Write-Host "  3. FileFerry-TransferRequests  (90-day TTL + GSI)" -ForegroundColor Gray
    Write-Host "  4. FileFerry-AgentLearning     (no TTL)" -ForegroundColor Gray
    Write-Host "  5. FileFerry-S3FileCache       (24-hour TTL)" -ForegroundColor Gray
} else {
    Write-Host "Running table creation script..." -ForegroundColor Cyan
    python infrastructure\create_all_dynamodb_tables.py
}

# Create IAM Role
Write-Host ""
Write-Host "🔐 Creating IAM Role..." -ForegroundColor Cyan

$roleName = "FileFerryReadOnlyRole"
try {
    $roleExists = aws iam get-role --role-name $roleName --region $Region 2>$null
    if ($roleExists) {
        Write-Host "✅ Role $roleName already exists" -ForegroundColor Green
    }
} catch {
    if ($DryRun) {
        Write-Host "🔸 Would create IAM role: $roleName" -ForegroundColor Yellow
    } else {
        Write-Host "🔧 Creating IAM role: $roleName..." -ForegroundColor Yellow
        
        # Create role with trust policy
        aws iam create-role `
            --role-name $roleName `
            --assume-role-policy-document file://infrastructure/iam-policies/fileferry-trust-policy.json `
            --description "FileFerry Read-Only Access Role" `
            --region $Region
        
        # Attach policy
        aws iam put-role-policy `
            --role-name $roleName `
            --policy-name FileFerryReadOnlyPolicy `
            --policy-document file://infrastructure/iam-policies/fileferry-readonly-policy.json `
            --region $Region
        
        Write-Host "✅ Created IAM role: $roleName" -ForegroundColor Green
    }
}

# Verify setup
Write-Host ""
Write-Host "🔍 Verifying Infrastructure..." -ForegroundColor Cyan
Write-Host ""

$tables = @(
    "FileFerry-ActiveSessions",
    "FileFerry-UserContext",
    "FileFerry-TransferRequests",
    "FileFerry-AgentLearning",
    "FileFerry-S3FileCache"
)

$allGood = $true

foreach ($table in $tables) {
    $status = if (Test-DynamoDBTable -TableName $table) {
        Write-Host "✅ $table" -ForegroundColor Green
        $true
    } else {
        Write-Host "❌ $table - NOT FOUND" -ForegroundColor Red
        $false
    }
    
    if (-not $status) { $allGood = $false }
}

# Summary
Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 69)

if ($DryRun) {
    Write-Host "DRY RUN COMPLETE" -ForegroundColor Yellow
    Write-Host "Run without -DryRun to create resources" -ForegroundColor Yellow
} elseif ($allGood) {
    Write-Host "✅ Phase 2 Infrastructure Setup COMPLETE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Created Resources:" -ForegroundColor Cyan
    Write-Host "  • 5 DynamoDB Tables (with TTL and GSI)" -ForegroundColor Gray
    Write-Host "  • IAM Role: FileFerryReadOnlyRole" -ForegroundColor Gray
    Write-Host "  • KMS Encryption enabled on all tables" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Update config/config.yaml with table names" -ForegroundColor Gray
    Write-Host "  2. Update SSO configuration (account_id, role_name)" -ForegroundColor Gray
    Write-Host "  3. Test SSO Handler authentication" -ForegroundColor Gray
    Write-Host "  4. Implement ServiceNow Handler (Phase 3)" -ForegroundColor Gray
} else {
    Write-Host "⚠️  Setup completed with errors" -ForegroundColor Yellow
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
}

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 69)
