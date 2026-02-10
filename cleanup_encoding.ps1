# Clean all Python files in the project
Write-Host "Cleaning all Python files for UTF-8 compliance..." -ForegroundColor Yellow

Get-ChildItem -Path . -Recurse -Filter "*.py" | ForEach-Object {
    $file = $_.FullName
    try {
        # Try to read as UTF-8 first
        $null = Get-Content $file -Encoding UTF8 -ErrorAction Stop
    } catch {
        Write-Host "  Cleaning: $($_.Name)" -ForegroundColor Gray
        try {
            # Read bytes and clean
            $bytes = [System.IO.File]::ReadAllBytes($file)
            $content = [System.Text.Encoding]::Latin1.GetString($bytes) -replace '[^\x00-\x7F]', ''
            [System.IO.File]::WriteAllText($file, $content, [System.Text.Encoding]::UTF8)
        } catch {
            Write-Host "  ? Failed to clean: $($_.Name)" -ForegroundColor DarkGray
        }
    }
}

Write-Host "? Encoding cleanup complete!" -ForegroundColor Green
