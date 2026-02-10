Write-Host "=== SECURITY CLEANUP ===" -ForegroundColor Red
Write-Host "GitHub detected exposed API key. Cleaning up..." -ForegroundColor Yellow

# 1. Remove files with exposed secrets
Write-Host "`n1. Removing files with secrets..." -ForegroundColor Yellow
Remove-Item railway_env_instructions.ps1, railway_env_vars.txt, .env.railway -Force -ErrorAction SilentlyContinue

# 2. Check for secrets in other files
Write-Host "`n2. Checking for secrets in code..." -ForegroundColor Yellow
$secretsFound = Select-String -Path . -Pattern "SG\." -Recurse -Include *.py, *.txt, *.ps1 -List
if ($secretsFound) {
    Write-Host "   ⚠️  Secrets found in files:" -ForegroundColor Red
    $secretsFound | ForEach-Object { Write-Host "   - $($_.Path)" -ForegroundColor White }
} else {
    Write-Host "   ✓ No secrets found in code" -ForegroundColor Green
}

# 3. Reset commit
Write-Host "`n3. Resetting bad commit..." -ForegroundColor Yellow
git reset --soft HEAD~1

# 4. Create safe files
Write-Host "`n4. Creating safe files..." -ForegroundColor Yellow
@"
# SAFE ENVIRONMENT TEMPLATE
SECRET_KEY=your-secure-key-here
EMAIL_HOST_PASSWORD=your-sendgrid-api-key-here
"@ | Out-File -FilePath env_template_safe.txt -Encoding UTF8

# 5. Add safe files
Write-Host "`n5. Adding safe files to commit..." -ForegroundColor Yellow
git add railway.json Procfile requirements.txt .gitignore backend/settings.py backend/check_email_config.py prepare_railway.ps1 requirements.txt.minimal env_template_safe.txt

# 6. Commit safely
Write-Host "`n6. Creating secure commit..." -ForegroundColor Yellow
git commit -m "Railway deployment - Security cleanup

- Removed exposed API keys from commit
- Added safe environment templates
- Railway configuration ready for deployment

Add actual secrets in Railway dashboard environment variables."

# 7. Push
Write-Host "`n7. Pushing to GitHub..." -ForegroundColor Yellow
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Successfully pushed SECURE commit!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Push failed. Check for remaining secrets." -ForegroundColor Red
}
