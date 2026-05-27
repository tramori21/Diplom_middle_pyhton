$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ProjectSuffix = ((Split-Path -Leaf $Root) -replace "[^A-Za-z0-9]", "").ToLower()
$env:COMPOSE_PROJECT_NAME = "diplom_booking_$ProjectSuffix"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Ensure-LocalEnv {
    $EnvPath = Join-Path $Root ".env"
    $ExamplePath = Join-Path $Root ".env.example"

    if (!(Test-Path $ExamplePath)) {
        throw ".env.example not found"
    }

    if (!(Test-Path $EnvPath)) {
        Copy-Item $ExamplePath $EnvPath
    }

    $Text = [System.IO.File]::ReadAllText($EnvPath)
    $Secret = ([guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N"))
    $DbPassword = ([guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N"))

    $Text = $Text.Replace("replace_with_secure_random_secret", $Secret)
    $Text = $Text.Replace("replace_with_local_password", $DbPassword)

    [System.IO.File]::WriteAllText($EnvPath, $Text, $Utf8NoBom)
}

Set-Location $Root
Ensure-LocalEnv

Write-Host "`n=== Docker Compose project ==="
Write-Host $env:COMPOSE_PROJECT_NAME

Write-Host "`n=== Docker Compose config ==="
docker compose config --quiet

Write-Host "`n=== Rebuild and start ==="
docker compose down -v
docker compose up -d --build

Write-Host "`n=== Containers ==="
docker compose ps

Write-Host "`n=== Health ==="
Start-Sleep -Seconds 5
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8010/health"

Write-Host "`n=== Tests ==="
docker compose exec -T booking_service pytest -q /app/tests

Write-Host "`n=== Logs ==="
docker compose logs --tail=80 booking_service