# Test API Gateway Transfer Endpoint
$apiUrl = "https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/start"

Write-Host "`nTesting API Gateway...`n" -ForegroundColor Cyan

$payload = @{
    user_id = "test@example.com"
    transfer_plan = @{
        source_bucket = "test-bucket"
        source_key = "test-file.txt"
        destination_host = "ftp.example.com"
        destination_port = 21
        destination_user = "ftpuser"
        destination_password = "ftppass"
        destination_path = "/uploads/"
        transfer_type = "ftp"
    }
    servicenow_tickets = @("INC0010001", "INC0010002")
} | ConvertTo-Json -Depth 10

Write-Host "Payload:" -ForegroundColor Yellow
Write-Host $payload -ForegroundColor Gray

try {
    Write-Host "`nSending request..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri $apiUrl -Method POST -ContentType "application/json" -Body $payload -ErrorAction Stop
    Write-Host "`nSuccess!" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json -Depth 10)
} catch {
    Write-Host "`nError:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($_.ErrorDetails.Message) {
        Write-Host "`nDetails:" -ForegroundColor Yellow
        Write-Host $_.ErrorDetails.Message
    }
}
Write-Host ""
