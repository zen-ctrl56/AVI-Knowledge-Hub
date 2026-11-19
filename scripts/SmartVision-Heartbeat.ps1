# ZENTREK SmartVision heartbeat collector (read-only, approved deployment only)
# Run locally on each AVI PC under an approved schedule. No admin bypass or process modification.
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$MachineId,
    [Parameter(Mandatory=$true)][string]$SharedDatabasePath,
    [Parameter(Mandatory=$true)][string]$SmartVisionProcessName
)
$ErrorActionPreference = 'Stop'
$processName = [IO.Path]::GetFileNameWithoutExtension($SmartVisionProcessName)
if (-not $processName) { throw 'SmartVisionProcessName is required.' }
$folder = Join-Path $SharedDatabasePath 'Heartbeats'
New-Item -Path $folder -ItemType Directory -Force | Out-Null
$destination = Join-Path $folder ($MachineId + '.json')
$temporary = Join-Path $folder ($MachineId + '.' + [guid]::NewGuid().ToString('N') + '.tmp')
$running = $null -ne (Get-Process -Name $processName -ErrorAction SilentlyContinue | Select-Object -First 1)
$payload = @{
    machine_id = $MachineId
    timestamp_utc = [DateTime]::UtcNow.ToString('o')
    smartvision_running = [bool]$running
    process_name = $processName
} | ConvertTo-Json -Compress
try {
    [IO.File]::WriteAllText($temporary, $payload, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporary -Destination $destination -Force
} finally {
    Remove-Item -LiteralPath $temporary -ErrorAction SilentlyContinue
}
