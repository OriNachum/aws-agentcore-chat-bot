# Setup script for Nova Pro with AgentCore mode
# Run this to configure your environment for Nova Pro

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Nova Pro Configuration Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to set environment variable
function Set-EnvVar {
    param(
        [string]$Name,
        [string]$Value,
        [switch]$Required
    )
    
    $current = [System.Environment]::GetEnvironmentVariable($Name, "Process")
    
    if ($current) {
        Write-Host "  $Name is already set: " -NoNewline
        Write-Host "$current" -ForegroundColor Yellow
        
        $response = Read-Host "  Do you want to override it? (y/N)"
        if ($response -ne "y") {
            return
        }
    }
    
    [System.Environment]::SetEnvironmentVariable($Name, $Value, "Process")
    Write-Host "  ✅ Set $Name = " -NoNewline -ForegroundColor Green
    Write-Host "$Value" -ForegroundColor Cyan
}

# 1. Backend Configuration
Write-Host "1. Setting Backend Configuration" -ForegroundColor Yellow
Write-Host "   " -NoNewline
Set-EnvVar -Name "BACKEND_MODE" -Value "agentcore" -Required
Write-Host "   " -NoNewline
Set-EnvVar -Name "LLM_PROVIDER" -Value "bedrock" -Required

# 2. AWS Region
Write-Host ""
Write-Host "2. AWS Region Configuration" -ForegroundColor Yellow

$currentRegion = $env:AWS_REGION
if ($currentRegion) {
    Write-Host "   Current AWS_REGION: $currentRegion" -ForegroundColor Yellow
    $useRegion = Read-Host "   Use this region? (Y/n)"
    if ($useRegion -eq "n") {
        $currentRegion = $null
    }
}

if (-not $currentRegion) {
    Write-Host "   Available regions for Nova Pro:" -ForegroundColor Gray
    Write-Host "     1. us-east-1 (US East - N. Virginia)" -ForegroundColor Gray
    Write-Host "     2. us-west-2 (US West - Oregon)" -ForegroundColor Gray
    
    $regionChoice = Read-Host "   Select region (1-2, default: 1)"
    
    $region = switch ($regionChoice) {
        "2" { "us-west-2" }
        default { "us-east-1" }
    }
    
    [System.Environment]::SetEnvironmentVariable("AWS_REGION", $region, "Process")
    Write-Host "   ✅ Set AWS_REGION = $region" -ForegroundColor Green
}

# 3. Nova Model Configuration
Write-Host ""
Write-Host "3. Nova Model Configuration" -ForegroundColor Yellow

$currentModel = $env:BEDROCK_MODEL_ID
if ($currentModel) {
    Write-Host "   Current BEDROCK_MODEL_ID: $currentModel" -ForegroundColor Yellow
    $useModel = Read-Host "   Use this model? (Y/n)"
    if ($useModel -eq "n") {
        $currentModel = $null
    }
}

if (-not $currentModel) {
    Write-Host "   Available Nova models:" -ForegroundColor Gray
    Write-Host "     1. Nova Pro   - us.amazon.nova-pro-v1:0 (recommended)" -ForegroundColor Gray
    Write-Host "     2. Nova Lite  - us.amazon.nova-lite-v1:0" -ForegroundColor Gray
    Write-Host "     3. Nova Micro - us.amazon.nova-micro-v1:0" -ForegroundColor Gray
    
    $modelChoice = Read-Host "   Select model (1-3, default: 1)"
    
    $modelId = switch ($modelChoice) {
        "2" { "us.amazon.nova-lite-v1:0" }
        "3" { "us.amazon.nova-micro-v1:0" }
        default { "us.amazon.nova-pro-v1:0" }
    }
    
    [System.Environment]::SetEnvironmentVariable("BEDROCK_MODEL_ID", $modelId, "Process")
    Write-Host "   ✅ Set BEDROCK_MODEL_ID = $modelId" -ForegroundColor Green
}

# 4. Model Parameters
Write-Host ""
Write-Host "4. Model Parameters (using defaults)" -ForegroundColor Yellow

if (-not $env:BEDROCK_TEMPERATURE) {
    [System.Environment]::SetEnvironmentVariable("BEDROCK_TEMPERATURE", "0.7", "Process")
    Write-Host "   ✅ Set BEDROCK_TEMPERATURE = 0.7" -ForegroundColor Green
}

if (-not $env:BEDROCK_MAX_TOKENS) {
    [System.Environment]::SetEnvironmentVariable("BEDROCK_MAX_TOKENS", "4096", "Process")
    Write-Host "   ✅ Set BEDROCK_MAX_TOKENS = 4096" -ForegroundColor Green
}

if (-not $env:BEDROCK_STREAMING) {
    [System.Environment]::SetEnvironmentVariable("BEDROCK_STREAMING", "true", "Process")
    Write-Host "   ✅ Set BEDROCK_STREAMING = true" -ForegroundColor Green
}

# 5. AWS Credentials Check
Write-Host ""
Write-Host "5. Checking AWS Credentials" -ForegroundColor Yellow

$hasEnvCreds = $env:AWS_ACCESS_KEY_ID -and $env:AWS_SECRET_ACCESS_KEY
$credsFile = Join-Path $env:USERPROFILE ".aws\credentials"
$hasCredsFile = Test-Path $credsFile

if ($hasEnvCreds) {
    Write-Host "   ✅ AWS credentials found in environment variables" -ForegroundColor Green
} elseif ($hasCredsFile) {
    Write-Host "   ✅ AWS credentials file found: $credsFile" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  No AWS credentials found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "   You need to set up AWS credentials. Choose one:" -ForegroundColor Yellow
    Write-Host "   1. Set environment variables (current session only):" -ForegroundColor Gray
    Write-Host "      `$env:AWS_ACCESS_KEY_ID = 'your-key'" -ForegroundColor Gray
    Write-Host "      `$env:AWS_SECRET_ACCESS_KEY = 'your-secret'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   2. Create ~/.aws/credentials file (persistent):" -ForegroundColor Gray
    Write-Host "      New-Item -ItemType Directory -Force -Path ~\.aws" -ForegroundColor Gray
    Write-Host "      Set-Content -Path ~\.aws\credentials -Value '[default]'" -ForegroundColor Gray
    Write-Host "      Add-Content -Path ~\.aws\credentials -Value 'aws_access_key_id = YOUR_KEY'" -ForegroundColor Gray
    Write-Host "      Add-Content -Path ~\.aws\credentials -Value 'aws_secret_access_key = YOUR_SECRET'" -ForegroundColor Gray
}

# 6. Logging
Write-Host ""
Write-Host "6. Setting Logging Level" -ForegroundColor Yellow

if (-not $env:LOG_LEVEL) {
    [System.Environment]::SetEnvironmentVariable("LOG_LEVEL", "INFO", "Process")
    Write-Host "   ✅ Set LOG_LEVEL = INFO" -ForegroundColor Green
} else {
    Write-Host "   Current LOG_LEVEL: $env:LOG_LEVEL" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Configuration Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$vars = @{
    "BACKEND_MODE" = $env:BACKEND_MODE
    "LLM_PROVIDER" = $env:LLM_PROVIDER
    "AWS_REGION" = $env:AWS_REGION
    "BEDROCK_MODEL_ID" = $env:BEDROCK_MODEL_ID
    "BEDROCK_TEMPERATURE" = $env:BEDROCK_TEMPERATURE
    "BEDROCK_MAX_TOKENS" = $env:BEDROCK_MAX_TOKENS
    "BEDROCK_STREAMING" = $env:BEDROCK_STREAMING
    "LOG_LEVEL" = $env:LOG_LEVEL
}

foreach ($key in $vars.Keys) {
    $value = $vars[$key]
    if ($value) {
        Write-Host "  $key = " -NoNewline
        Write-Host "$value" -ForegroundColor Cyan
    } else {
        Write-Host "  $key = " -NoNewline
        Write-Host "(not set)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. If you haven't already, ensure Nova Pro is enabled in AWS Bedrock Console" -ForegroundColor Yellow
Write-Host "   https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Test your configuration:" -ForegroundColor Yellow
Write-Host "   uv run python test_nova_pro.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "3. Run interactive mode to test Nova Pro:" -ForegroundColor Yellow
Write-Host "   uv run python src/community_bot/agentcore_app.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "4. Or start the Discord bot:" -ForegroundColor Yellow
Write-Host "   uv run community-bot" -ForegroundColor Cyan
Write-Host ""

Write-Host "Note: These environment variables are set for this PowerShell session only." -ForegroundColor Gray
Write-Host "      To make them permanent, add them to your .env file." -ForegroundColor Gray
Write-Host ""
