Write-Host "=== DEPLOYMENT READINESS CHECK ===" -ForegroundColor Yellow

# Check requirements.txt
$req = Get-Content requirements.txt
Write-Host "
1. Requirements.txt: $($req.Count) packages" -ForegroundColor Cyan
if ($req.Count -gt 20) {
    Write-Host "   ❌ TOO MANY PACKAGES! Should be ~11 packages" -ForegroundColor Red
    Write-Host "   Current: $($req.Count) packages" -ForegroundColor Red
} else {
    Write-Host "   ✅ Good: $($req.Count) packages" -ForegroundColor Green
}

# Check Dockerfile
if (Test-Path Dockerfile) {
    Write-Host "
2. Dockerfile: ✅ Present" -ForegroundColor Green
} else {
    Write-Host "
2. Dockerfile: ❌ Missing" -ForegroundColor Red
}

# Check wsgi.py settings
$wsgi = Select-String -Path "backend/wsgi.py" -Pattern "SETTINGS_MODULE.*settings" -Quiet
if ($wsgi) {
    Write-Host "
3. wsgi.py: ✅ Points to settings.py" -ForegroundColor Green
} else {
    Write-Host "
3. wsgi.py: ❌ Wrong settings file" -ForegroundColor Red
}

# Check start.sh
if (Test-Path "backend/start.sh") {
    Write-Host "
4. start.sh: ✅ Present" -ForegroundColor Green
} else {
    Write-Host "
4. start.sh: ❌ Missing" -ForegroundColor Red
}

Write-Host "
=== READY TO DEPLOY? ===" -ForegroundColor Yellow
if ($req.Count -le 20 -and (Test-Path Dockerfile) -and $wsgi) {
    Write-Host "✅ YES! Your app is ready to deploy to Railway!" -ForegroundColor Green
    Write-Host "   Make sure to set SECRET_KEY in Railway Dashboard" -ForegroundColor Yellow
} else {
    Write-Host "❌ NO - Fix the issues above" -ForegroundColor Red
}
