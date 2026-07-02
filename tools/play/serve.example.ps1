# Example GUI launcher for BalatroBot.
# Copy this file to serve.ps1, adjust $BalatroDir for your machine, and keep serve.ps1 untracked.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ServeArgs
)

$ToolRoot = $PSScriptRoot
$RepoRoot = Resolve-Path (Join-Path $ToolRoot '..\..')

$BalatroDir = $env:BALATROBOT_GAME_DIR
if (-not $BalatroDir) {
    $BalatroDir = 'C:\Program Files (x86)\Steam\steamapps\common\Balatro'
}

$env:BALATROBOT_LOVE_PATH = Join-Path $BalatroDir 'Balatro.exe'
$env:BALATROBOT_LOVELY_PATH = Join-Path $BalatroDir 'version.dll'

Set-Location $RepoRoot
& (Join-Path $RepoRoot '.venv\Scripts\balatrobot.exe') serve @ServeArgs
