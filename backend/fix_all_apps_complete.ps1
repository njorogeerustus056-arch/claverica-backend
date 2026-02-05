Write-Host "=== FIXING ALL APPS.PY FILES ===" -ForegroundColor Yellow

# List of all apps
$apps = @(
    "accounts", "cards", "compliance", "crypto", "escrow", "kyc",
    "notifications", "payments", "receipts", "savings", "tac",
    "tasks", "transactions", "transfers", "users", "withdrawal"
)

foreach ($app in $apps) {
    $appPath = ".\$app\apps.py"
    
    if (Test-Path $appPath) {
        Write-Host "Fixing: $app" -ForegroundColor Cyan
        
        # Capitalize first letter for class name
        $className = (Get-Culture).TextInfo.ToTitleCase($app)
        
        # Create simple correct apps.py
        $content = @"
from django.apps import AppConfig

class ${className}Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "$app"
"@
        
        Set-Content $appPath -Value $content -Encoding UTF8
        Write-Host "  ✓ Fixed" -ForegroundColor Green
    } else {
        Write-Host "  Skipping: $app (no apps.py)" -ForegroundColor Gray
    }
}

Write-Host "`n=== VERIFYING ===" -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter apps.py | ForEach-Object {
    $nameLine = Get-Content $_.FullName | Select-String 'name\s*='
    Write-Host "  $($_.Directory.Name): $($nameLine.ToString().Trim())"
}

Write-Host "`n=== TESTING DJANGO ===" -ForegroundColor Yellow
try {
    python manage.py check
    Write-Host "✓ Django check passed!" -ForegroundColor Green
} catch {
    Write-Host "✗ Django check failed: $_" -ForegroundColor Red
}
