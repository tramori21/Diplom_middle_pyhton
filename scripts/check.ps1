$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ProjectSuffix = ((Split-Path -Leaf $Root) -replace "[^A-Za-z0-9]", "").ToLower()
$env:COMPOSE_PROJECT_NAME = "diplom_booking_$ProjectSuffix"

Set-Location $Root

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