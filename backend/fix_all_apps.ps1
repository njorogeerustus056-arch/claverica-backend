Write-Host "=== FIXING ALL APPS ===" -ForegroundColor Yellow

# Counter
$fixed = 0

Get-ChildItem -Recurse -Filter apps.py | ForEach-Object {
    $appPath = $_.FullName
    $appDir = $_.Directory.Name
    
    Write-Host "Processing: $appDir" -ForegroundColor Cyan
    
    # Read content
    $content = Get-Content $appPath -Raw
    
    # Check if it has backend. prefix
    if ($content -match 'name\s*=\s*["'']backend\.') {
        # Remove backend. prefix
        $content = $content -replace 'name\s*=\s*["'']backend\.', 'name = "'
        
        # Also fix verbose_name if present
        $content = $content -replace 'verbose_name\s*=\s*["'']backend\.', 'verbose_name = "'
        
        # Save
        Set-Content $appPath -Value $content -Encoding UTF8
        
        Write-Host "  ✓ Fixed: $appDir" -ForegroundColor Green
        $fixed++
    } else {
        Write-Host "  ✓ Already correct" -ForegroundColor Gray
    }
}

Write-Host "`n=== SUMMARY ===" -ForegroundColor Yellow
Write-Host "Fixed $fixed apps" -ForegroundColor Cyan

# Verify
Write-Host "`nVerifying fixes:" -ForegroundColor Cyan
Get-ChildItem -Recurse -Filter apps.py | ForEach-Object {
    $nameLine = Get-Content $_.FullName | Select-String 'name\s*='
    Write-Host "  $($_.Directory.Name): $($nameLine.ToString().Trim())"
}

Write-Host "`nTesting Django..." -ForegroundColor Cyan
try {
    python manage.py check
    Write-Host "✓ Django check passed!" -ForegroundColor Green
} catch {
    Write-Host "✗ Django check failed: $_" -ForegroundColor Red
}
