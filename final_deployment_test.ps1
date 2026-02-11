Write-Host "=== TESTING FINAL DEPLOYMENT ===" -ForegroundColor Cyan

$url = "https://claverica-backend-production.up.railway.app"
$healthUrl = "$url/health/"

Write-Host "`n1. Testing main endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 10
    Write-Host "   ? Main URL: HTTP $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   ??  Main URL: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n2. Testing health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri $healthUrl -Method GET -TimeoutSec 10
    Write-Host "   ? Health endpoint: HTTP $($health.StatusCode)" -ForegroundColor Green
    Write-Host "   Response: $($health.Content)" -ForegroundColor Gray
} catch {
    Write-Host "   ? Health endpoint: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n3. Testing Django admin (if exists)..." -ForegroundColor Yellow
try {
    $adminUrl = "$url/admin/"
    $admin = Invoke-WebRequest -Uri $adminUrl -Method GET -TimeoutSec 10
    if ($admin.Content -match "Django|admin|csrf") {
        Write-Host "   ? Django admin accessible" -ForegroundColor Green
    } else {
        Write-Host "   ??  Admin page returned unexpected content" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ??  Admin endpoint not accessible (normal for some setups)" -ForegroundColor Gray
}

Write-Host "`n=== DEPLOYMENT STATUS ===" -ForegroundColor Cyan
Write-Host "If health endpoint works (HTTP 200), your app is LIVE!" -ForegroundColor White
Write-Host "If health works but main doesn't, check your Django URL routing." -ForegroundColor Gray
Write-Host "If neither works, check Railway deployment logs for errors." -ForegroundColor Gray
