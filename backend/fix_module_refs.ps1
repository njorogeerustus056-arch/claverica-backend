Write-Host "=== FIXING MODULE REFERENCES ===" -ForegroundColor Yellow

# 1. Fix manage.py
Write-Host "1. Fixing manage.py..." -ForegroundColor Cyan
$manageContent = Get-Content manage.py -Raw
$manageContent = $manageContent -replace "'DJANGO_SETTINGS_MODULE', 'backend\.settings'", "'DJANGO_SETTINGS_MODULE', 'settings'"
Set-Content manage.py -Value $manageContent -Encoding UTF8
Write-Host "   ✓ Fixed manage.py" -ForegroundColor Green

# 2. Fix asgi.py
Write-Host "2. Fixing asgi.py..." -ForegroundColor Cyan
if (Test-Path asgi.py) {
    $asgiContent = Get-Content asgi.py -Raw
    $asgiContent = $asgiContent -replace "'backend\.settings'", "'settings'"
    Set-Content asgi.py -Value $asgiContent -Encoding UTF8
    Write-Host "   ✓ Fixed asgi.py" -ForegroundColor Green
}

# 3. Fix wsgi.py
Write-Host "3. Fixing wsgi.py..." -ForegroundColor Cyan
if (Test-Path wsgi.py) {
    $wsgiContent = Get-Content wsgi.py -Raw
    $wsgiContent = $wsgiContent -replace "'backend\.settings'", "'settings'"
    Set-Content wsgi.py -Value $wsgiContent -Encoding UTF8
    Write-Host "   ✓ Fixed wsgi.py" -ForegroundColor Green
}

# 4. Check settings.py for self-references
Write-Host "4. Checking settings.py..." -ForegroundColor Cyan
$settingsContent = Get-Content settings.py -Raw

# Fix ROOT_URLCONF if it references backend.urls
if ($settingsContent -match "ROOT_URLCONF.*=.*['\"]backend\.urls['\"]") {
    $settingsContent = $settingsContent -replace "ROOT_URLCONF.*=.*['\"]backend\.urls['\"]", "ROOT_URLCONF = 'urls'"
    Write-Host "   Fixed ROOT_URLCONF" -ForegroundColor Yellow
}

# Fix WSGI_APPLICATION if it references backend.wsgi
if ($settingsContent -match "WSGI_APPLICATION.*=.*['\"]backend\.wsgi\.application['\"]") {
    $settingsContent = $settingsContent -replace "WSGI_APPLICATION.*=.*['\"]backend\.wsgi\.application['\"]", "WSGI_APPLICATION = 'wsgi.application'"
    Write-Host "   Fixed WSGI_APPLICATION" -ForegroundColor Yellow
}

Set-Content settings.py -Value $settingsContent -Encoding UTF8
Write-Host "   ✓ Fixed settings.py" -ForegroundColor Green

# 5. Test
Write-Host "5. Testing Django..." -ForegroundColor Cyan
try {
    python manage.py check
    Write-Host "   ✓ Django check passed!" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Still having issues: $_" -ForegroundColor Red
    
    # Show debug info
    Write-Host "   Debug info:" -ForegroundColor Yellow
    python -c "
import sys
print('Python path:')
for p in sys.path:
    if 'claverica' in p:
        print(f'  {p}')
print()
try:
    import settings
    print('✓ Can import settings directly')
except Exception as e:
    print(f'✗ Cannot import settings: {e}')
"
}

Write-Host "=== FIX COMPLETE ===" -ForegroundColor Green
