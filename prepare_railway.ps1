Write-Host "=== RAILWAY DEPLOYMENT PREPARATION ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check current directory
Write-Host "1. Current Directory:" -ForegroundColor Yellow
Get-Location
Write-Host ""

# 2. Check which requirements.txt Railway will use
Write-Host "2. Checking requirements.txt files:" -ForegroundColor Yellow
Write-Host "Project root:" -ForegroundColor White
type requirements.txt | Select-String -Pattern "Django|gunicorn|psycopg2|whitenoise" -Context 0,0
Write-Host ""
Write-Host "Backend folder:" -ForegroundColor White
type backend\requirements.txt | Select-String -Pattern "Django|gunicorn|psycopg2|whitenoise" -Context 0,0
Write-Host ""

# 3. Check railway.json
Write-Host "3. Checking railway.json:" -ForegroundColor Yellow
type railway.json
Write-Host ""

# 4. Check Procfile
Write-Host "4. Checking Procfile:" -ForegroundColor Yellow
type Procfile
Write-Host ""

# 5. Check environment variables needed for Railway
Write-Host "5. Environment Variables Needed for Railway:" -ForegroundColor Yellow
Write-Host "You'll need to set these in Railway dashboard:" -ForegroundColor White
Write-Host "  • SECRET_KEY (generate a new secure one)" -ForegroundColor White
Write-Host "  • DEBUG=False" -ForegroundColor White
Write-Host "  • ALLOWED_HOSTS=.railway.app,localhost,127.0.0.1,0.0.0.0" -ForegroundColor White
Write-Host "  • CORS_ALLOWED_ORIGINS=<your-frontend-urls>" -ForegroundColor White
Write-Host "  • EMAIL_* settings (if using email)" -ForegroundColor White
Write-Host "  • DATABASE_URL (automatically provided by Railway)" -ForegroundColor White
Write-Host ""

# 6. Generate a secure SECRET_KEY
Write-Host "6. Generate a secure SECRET_KEY:" -ForegroundColor Yellow
python -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
secret_key = ''.join(secrets.choice(alphabet) for i in range(50))
print(f'SECRET_KEY={secret_key}')
"
Write-Host ""

# 7. Test with production settings
Write-Host "7. Testing with production settings:" -ForegroundColor Yellow
cd backend
$env:DEBUG='False'
$env:ALLOWED_HOSTS='.railway.app,localhost,127.0.0.1,0.0.0.0'
$env:DATABASE_URL='postgresql://test:test@localhost/test'  # Dummy for testing
python manage.py check --deploy
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All checks passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Some checks failed" -ForegroundColor Red
}
Write-Host ""

# 8. Final steps
Write-Host "=== DEPLOYMENT READY ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Commit all changes to git:" -ForegroundColor White
Write-Host "   git add ." -ForegroundColor Gray
Write-Host "   git commit -m 'Prepare for Railway deployment'" -ForegroundColor Gray
Write-Host "   git push origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Go to Railway.app and:" -ForegroundColor White
Write-Host "   a. New Project → Deploy from GitHub repo" -ForegroundColor Gray
Write-Host "   b. Connect your repository" -ForegroundColor Gray
Write-Host "   c. Add environment variables (see list above)" -ForegroundColor Gray
Write-Host "   d. Deploy!" -ForegroundColor Gray
Write-Host ""
Write-Host "3. After deployment:" -ForegroundColor White
Write-Host "   a. Check logs in Railway dashboard" -ForegroundColor Gray
Write-Host "   b. Test your API endpoints" -ForegroundColor Gray
Write-Host "   c. Connect your frontend to the new backend URL" -ForegroundColor Gray
Write-Host ""
