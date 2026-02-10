Write-Host "=== FIXING RUNTIME.TXT ENCODING ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "Problem: runtime.txt has invalid UTF-8" -ForegroundColor Red
Write-Host ""

# Check current runtime.txt
Write-Host "1. Checking current runtime.txt..." -ForegroundColor Yellow
if (Test-Path runtime.txt) {
    try {
        $content = Get-Content runtime.txt -Encoding UTF8 -ErrorAction Stop
        Write-Host "   Content: $content" -ForegroundColor Gray
    } catch {
        Write-Host "   ❌ Invalid UTF-8: $_" -ForegroundColor Red
    }
    
    # Show hex dump
    $bytes = [System.IO.File]::ReadAllBytes("$PWD\runtime.txt")
    Write-Host "   Hex (first 20): $($bytes[0..19] | ForEach-Object { '{0:X2}' -f $_ })" -ForegroundColor Gray
} else {
    Write-Host "   ❌ runtime.txt missing" -ForegroundColor Red
}

Write-Host ""

# Create clean runtime.txt
Write-Host "2. Creating clean runtime.txt..." -ForegroundColor Green
$cleanRuntime = 'python-3.11.0'
[System.IO.File]::WriteAllText("$PWD\runtime.txt", $cleanRuntime, [System.Text.Encoding]::ASCII)
Write-Host "   ✅ Created: $cleanRuntime" -ForegroundColor Green

Write-Host ""

# Also check requirements.txt
Write-Host "3. Checking requirements.txt..." -ForegroundColor Yellow
if (Test-Path requirements.txt) {
    $reqBytes = [System.IO.File]::ReadAllBytes("$PWD\requirements.txt")
    $hasNonAscii = $reqBytes | Where-Object { $_ -gt 127 } | Select-Object -First 1
    if ($hasNonAscii) {
        Write-Host "   ⚠️  requirements.txt has non-ASCII" -ForegroundColor Yellow
        # Clean it
        $reqContent = [System.IO.File]::ReadAllText("$PWD\requirements.txt", [System.Text.Encoding]::UTF8)
        $cleanReq = $reqContent -replace '[^\x00-\x7F]', ''
        [System.IO.File]::WriteAllText("$PWD\requirements.txt", $cleanReq, [System.Text.Encoding]::ASCII)
        Write-Host "   ✅ Cleaned requirements.txt" -ForegroundColor Green
    } else {
        Write-Host "   ✅ requirements.txt is clean" -ForegroundColor Green
    }
}

Write-Host ""

# Push fix
Write-Host "4. Pushing fix to GitHub..." -ForegroundColor Green
git add runtime.txt requirements.txt
git commit -m "FIX: Clean runtime.txt and requirements.txt encoding for Railway"
git push origin main

Write-Host ""
Write-Host "✅ Fix pushed! Railway will redeploy." -ForegroundColor Green
Write-Host "Check Railway dashboard for new deployment." -ForegroundColor Cyan
