# Native entry point used by the single sgpt.cmd wrapper.
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$root=$PSScriptRoot
$python=Join-Path $root 'venv\Scripts\python.exe'
$ready=Test-Path -LiteralPath $python -PathType Leaf
if($ready){try{& $python -c 'import sys' 2>$null; $ready=$LASTEXITCODE -eq 0}catch{$ready=$false}}
if(-not $ready){
    Write-Host 'The private ShellGPT Python is missing or damaged. Running the setup prerequisite check.'
    & (Join-Path $root 'Setup-Exam.ps1') -NoKeyPrompt
}
$extra=@()
foreach($arg in $args){if($arg -in @('init the machine','initialize the machine','init machine','initialize machine','--init-lab')){$extra=@('--for-init')}}
& $python (Join-Path $root 'preflight.py') @extra
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& $python (Join-Path $root 'exam_runtime.py') @args
exit $LASTEXITCODE
