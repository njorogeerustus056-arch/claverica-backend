# Fix all apps.py files with proper quote handling
Get-ChildItem -Recurse -Filter apps.py | ForEach-Object {
    $path = $_.FullName
    $appName = $_.Directory.Name
    
    Write-Host "Checking: $appName" -ForegroundColor Cyan
    
    # Read file line by line
    $lines = Get-Content $path
    $fixedLines = @()
    
    foreach ($line in $lines) {
        # Fix name line
        if ($line -match 'name\s*=\s*["'']backend\.(\w+)["'']') {
            $app = $matches[1]
            $line = "    name = `"$app`""
            Write-Host "  Fixed name to: $app" -ForegroundColor Green
        }
        # Fix verbose_name line
        elseif ($line -match 'verbose_name\s*=\s*["'']backend\.(\w+)["'']') {
            $app = $matches[1]
            $line = "    verbose_name = `"$app`""
            Write-Host "  Fixed verbose_name to: $app" -ForegroundColor Green
        }
        # Fix already broken lines (mixed quotes)
        elseif ($line -match 'name\s*=\s*["''][^"''\n]*["'']' -and $line[0] -ne $line[-1]) {
            # Extract app name and fix quotes
            if ($line -match 'name\s*=\s*["'']([^"''\n]*)["'']') {
                $app = $matches[1]
                $line = "    name = `"$app`""
                Write-Host "  Fixed mixed quotes for: $app" -ForegroundColor Yellow
            }
        }
        
        $fixedLines += $line
    }
    
    # Write back
    Set-Content $path -Value $fixedLines -Encoding UTF8
}

Write-Host "`n=== VERIFYING FIXES ===" -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter apps.py | ForEach-Object {
    Write-Host "`n$($_.Directory.Name):" -ForegroundColor Cyan
    Get-Content $_.FullName | Where-Object { $_ -match 'name\s*=|verbose_name\s*=' }
}
