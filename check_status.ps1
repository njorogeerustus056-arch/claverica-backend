Write-Host "=== CHECK DEPLOYMENT STATUS ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ All fixes done:" -ForegroundColor Green
Write-Host "1. ✅ runtime.txt cleaned (python-3.11.0)" -ForegroundColor Gray
Write-Host "2. ✅ requirements.txt cleaned" -ForegroundColor Gray
Write-Host "3. ✅ Code pushed to GitHub" -ForegroundColor Gray
Write-Host "4. ✅ Environment variables set" -ForegroundColor Gray
Write-Host ""

Write-Host "🚀 Railway should be deploying NOW!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Check:" -ForegroundColor White
Write-Host "1. Railway → Deployments tab" -ForegroundColor Gray
Write-Host "2. Look for new deployment" -ForegroundColor Gray
Write-Host "3. Monitor build logs" -ForegroundColor Gray
Write-Host ""

Write-Host "📊 Expected deployment stages:" -ForegroundColor Cyan
Write-Host "1. ✅ Initializing" -ForegroundColor Gray
Write-Host "2. ⏳ Building (should work now)" -ForegroundColor Yellow
Write-Host "3. ⏳ Deploying" -ForegroundColor Yellow
Write-Host "4. ✅ Healthy" -ForegroundColor Green
Write-Host ""

Write-Host "🔗 Test URL after deployment:" -ForegroundColor White
Write-Host "https://claverica-backend-production.up.railway.app/" -ForegroundColor Cyan
Write-Host "https://claverica-backend-production.up.railway.app/api/" -ForegroundColor Cyan
Write-Host ""

Write-Host "⏰ Wait 2 minutes, then test..." -ForegroundColor Yellow
Start-Sleep -Seconds 120

Write-Host ""
Write-Host "Testing backend..." -ForegroundColor Cyan
$url = "https://claverica-backend-production.up.railway.app"
try {
    $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 10
    Write-Host "✅ SUCCESS! Backend is LIVE!" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Gray
    Write-Host "Response: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Not ready yet: $_" -ForegroundColor Red
    Write-Host "Check Railway dashboard for deployment logs" -ForegroundColor Yellow
}
