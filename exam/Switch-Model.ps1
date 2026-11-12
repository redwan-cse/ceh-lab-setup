# Select the provider used by the single sgpt command. Keys stay off command lines.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet('deepseek','stepfun')]
    [string]$Provider
)
$ErrorActionPreference = 'Stop'
$installedRoot = Join-Path $env:LOCALAPPDATA 'CEHLab\shellgpt-exam'
$installedSetup = Join-Path $installedRoot 'setup_exam.py'
$setup = if (Test-Path -LiteralPath $installedSetup -PathType Leaf) { $installedSetup } else { Join-Path $PSScriptRoot 'setup_exam.py' }
if (-not (Test-Path -LiteralPath $setup -PathType Leaf)) { throw 'ShellGPT setup helper is missing. Keep this script with setup_exam.py or install the exam kit first.' }
$dedicatedPython = Join-Path $installedRoot 'venv\Scripts\python.exe'
$pythonArguments = @()
if (Test-Path -LiteralPath $dedicatedPython -PathType Leaf) {
    $python = $dedicatedPython
} else {
    $candidate = Get-Command python,python3,py -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $candidate) { throw 'Python 3.10+ is required to switch providers. Run Setup-Exam.ps1 first.' }
    $python = $candidate.Source
    if ($candidate.Name -eq 'py.exe') { $pythonArguments = @('-3') }
}
$selected = if ($Provider -eq 'deepseek') { 'openrouter-deepseek' } else { 'stepfun' }
& $python @pythonArguments $setup --switch-provider --provider $selected
exit $LASTEXITCODE
