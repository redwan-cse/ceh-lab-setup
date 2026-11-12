# Refresh command lookup in THIS PowerShell process and children; no installation.
[CmdletBinding()]
param([string]$CommandDirectory=(Join-Path $env:LOCALAPPDATA 'CEHLab\shellgpt-exam\bin'))
$ErrorActionPreference='Stop'
$CommandDirectory=[IO.Path]::GetFullPath($CommandDirectory)
$wrapper=Join-Path $CommandDirectory 'sgpt.cmd'
if(-not (Test-Path -LiteralPath $wrapper -PathType Leaf)){
    throw "ShellGPT launcher is missing: $wrapper. Run the complete exam Setup-Exam.ps1 under this Windows account."
}
$parts=@($env:Path -split ';' | Where-Object {$_ -and $_.Trim().Trim('"').TrimEnd('\','/') -ine $CommandDirectory.TrimEnd('\','/')})
$env:Path=$CommandDirectory+';'+($parts -join ';')
$command=Get-Command sgpt.cmd -CommandType Application -ErrorAction Stop | Select-Object -First 1
if($command.Source -ine $wrapper){throw 'The expected sgpt launcher is not first on PATH; inspect Get-Command sgpt -All.'}
Write-Host "sgpt command activated in this terminal: $wrapper"
