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

Write-Host "`n=== Clean start ==="
docker compose down -v
docker compose up -d --build

Write-Host "`n=== Containers ==="
docker compose ps

Write-Host "`n=== Health ==="
Start-Sleep -Seconds 5
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8010/health"

Write-Host "`n=== Create JWT ==="
$Token = docker compose exec -T booking_service python /app/tools/create_token.py
$Token = $Token.Trim()
$Headers = @{
    Authorization = "Bearer $Token"
}

Write-Host "`n=== Create event ==="
$CreateBody = @{
    movie_id = "demo-movie-id"
    movie_title = "Demo Movie"
    starts_at = "2026-06-01T19:00:00Z"
    place = "Demo cinema"
    seats_limit = 1
    description = "Demo watch event"
} | ConvertTo-Json -Depth 5

$EventParams = @{
    Method = "POST"
    Uri = "http://127.0.0.1:8010/api/v1/events"
    Headers = $Headers
    ContentType = "application/json; charset=utf-8"
    Body = $CreateBody
}
$Event = Invoke-RestMethod @EventParams
$Event | ConvertTo-Json -Depth 10
$EventId = $Event.id

Write-Host "`n=== Book seat ==="
$BookParams = @{
    Method = "POST"
    Uri = "http://127.0.0.1:8010/api/v1/events/$EventId/booking"
    Headers = $Headers
}
Invoke-RestMethod @BookParams | ConvertTo-Json -Depth 10

Write-Host "`n=== Duplicate booking must return 409 ==="
try {
    Invoke-RestMethod @BookParams | Out-Null
} catch {
    Write-Host "STATUS_CODE=$($_.Exception.Response.StatusCode.value__)"
}

Write-Host "`n=== My bookings ==="
$MyBookingsParams = @{
    Method = "GET"
    Uri = "http://127.0.0.1:8010/api/v1/events/bookings/me"
    Headers = $Headers
}
Invoke-RestMethod @MyBookingsParams | ConvertTo-Json -Depth 10

Write-Host "`n=== Cancel booking ==="
$CancelBookingParams = @{
    Method = "DELETE"
    Uri = "http://127.0.0.1:8010/api/v1/events/$EventId/booking"
    Headers = $Headers
}
Invoke-RestMethod @CancelBookingParams | ConvertTo-Json -Depth 10

Write-Host "`n=== Cancel event ==="
$CancelEventParams = @{
    Method = "PATCH"
    Uri = "http://127.0.0.1:8010/api/v1/events/$EventId/cancel"
    Headers = $Headers
}
Invoke-RestMethod @CancelEventParams | ConvertTo-Json -Depth 10

Write-Host "`n=== Tests after demo ==="
docker compose exec -T booking_service pytest -q /app/tests