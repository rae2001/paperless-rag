# PowerShell script to fix CORS issues on Windows

Write-Host "Fixing CORS issues for Paperless RAG" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# Step 1: Stop the current containers
Write-Host "`n1. Stopping current containers..." -ForegroundColor Yellow
docker compose down

# Step 2: Rebuild with new CORS settings  
Write-Host "`n2. Rebuilding API with updated CORS configuration..." -ForegroundColor Yellow
docker compose build rag-api

# Step 3: Start containers
Write-Host "`n3. Starting containers..." -ForegroundColor Yellow
docker compose up -d

# Step 4: Wait for API to be ready
Write-Host "`n4. Waiting for API to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 5: Test the API
Write-Host "`n5. Testing API connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8088/health" -Method Head
    Write-Host "API Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "API test failed: $_" -ForegroundColor Red
}

Write-Host "`n====================================" -ForegroundColor Green
Write-Host "CORS fix complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Now you can:" -ForegroundColor Cyan
Write-Host "1. Access the UI at: http://192.168.1.77:8080" -ForegroundColor White
Write-Host "2. The API should be available at: http://192.168.1.77:8088" -ForegroundColor White
Write-Host ""
Write-Host "If you still see issues, run: python debug_cors.py" -ForegroundColor Yellow
