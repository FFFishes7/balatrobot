# Convenience wrapper for BalatroBot Play Helper (JSON only).
# Examples:
#   .\bot.ps1 state
#   .\bot.ps1 query deck
#   .\bot.ps1 know preflight
#   .\bot.ps1 exec '{"command":"play","params":{"cards":[0,1,2,3,4]}}'
#   .\bot.ps1 help
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BotArgs
)

$ToolRoot = $PSScriptRoot
$Root = Resolve-Path (Join-Path $ToolRoot '..\..')
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    Write-Error "Missing virtualenv python: $Python"
    exit 2
}

if ($BotArgs.Count -eq 0) {
    Write-Host 'Usage:'
    Write-Host '  .\bot.ps1 state'
    Write-Host '  .\bot.ps1 query deck'
    Write-Host '  .\bot.ps1 know preflight'
    Write-Host '  .\bot.ps1 exec ''{"command":"play","params":{"cards":[0,1,2,3,4]}}'''
    Write-Host '  .\bot.ps1 help'
    exit 2
}

$cmd = $BotArgs[0]
$rest = @()
if ($BotArgs.Count -gt 1) {
    $rest = $BotArgs[1..($BotArgs.Count - 1)]
}

switch ($cmd) {
    'state' { & $Python (Join-Path $ToolRoot 'state.py') @rest; exit $LASTEXITCODE }
    'query' { & $Python (Join-Path $ToolRoot 'query.py') @rest; exit $LASTEXITCODE }
    'know'  { & $Python (Join-Path $ToolRoot 'know.py') @rest; exit $LASTEXITCODE }
    'exec'  { & $Python (Join-Path $ToolRoot 'exec.py') @rest; exit $LASTEXITCODE }
    'help'  { & $Python (Join-Path $ToolRoot 'help.py') @rest; exit $LASTEXITCODE }
    default {
        Write-Error "Unknown command: $cmd (use state|query|know|exec|help)"
        exit 2
    }
}
