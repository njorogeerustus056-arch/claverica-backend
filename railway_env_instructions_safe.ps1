Write-Host "=== ENVIRONMENT VARIABLES FOR RAILWAY ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Copy these to Railway dashboard (REPLACE <YOUR_SECRET_KEY>):" -ForegroundColor Yellow
Write-Host ""
Write-Host "SECRET_KEY=<YOUR_SECURE_SECRET_KEY>" -ForegroundColor White
Write-Host "DEBUG=False" -ForegroundColor White
Write-Host "ALLOWED_HOSTS=.railway.app,localhost,127.0.0.1,0.0.0.0,claverica-backend-production.up.railway.app" -ForegroundColor White
Write-Host "DJANGO_SETTINGS_MODULE=backend.settings" -ForegroundColor White
Write-Host ""
Write-Host "CORS_ALLOWED_ORIGINS=https://claverica-fixed.vercel.app,https://claverica-frontend-vercel.vercel.app,http://localhost:3000,http://localhost:5173" -ForegroundColor White
Write-Host "CSRF_TRUSTED_ORIGINS=https://claverica-backend-production.up.railway.app,https://claverica-fixed.vercel.app,https://claverica-frontend-vercel.vercel.app" -ForegroundColor White
Write-Host ""
Write-Host "EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend" -ForegroundColor White
Write-Host "EMAIL_HOST=smtp.sendgrid.net" -ForegroundColor White
Write-Host "EMAIL_PORT=587" -ForegroundColor White
Write-Host "EMAIL_USE_TLS=True" -ForegroundColor White
Write-Host "EMAIL_HOST_USER=apikey" -ForegroundColor White
Write-Host "EMAIL_HOST_PASSWORD=<YOUR_SENDGRID_API_KEY>" -ForegroundColor White
Write-Host "DEFAULT_FROM_EMAIL=noreply@claverica.com" -ForegroundColor White
Write-Host ""
Write-Host "SECURE_HSTS_INCLUDE_SUBDOMAINS=True" -ForegroundColor White
Write-Host "SECURE_SSL_REDIRECT=True" -ForegroundColor White
Write-Host "WEB_CONCURRENCY=2" -ForegroundColor White
Write-Host ""
Write-Host "=== IMPORTANT NOTES ===" -ForegroundColor Yellow
Write-Host "1. Replace <YOUR_SECURE_SECRET_KEY> with a secure Django secret key" -ForegroundColor White
Write-Host "2. Replace <YOUR_SENDGRID_API_KEY> with your actual SendGrid API key" -ForegroundColor White
Write-Host "3. DATABASE_URL will be auto-added by Railway" -ForegroundColor White
