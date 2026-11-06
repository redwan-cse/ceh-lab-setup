<#
Run remotely:
  .\Setup-ShellGPT-StepFun.ps1 -ComputerName 10.10.10.11 -UserName Win11-Client
Or run without parameters on the target PC. Uses Python 3.10+ with pip, or
installs signed Python 3.14.10 if missing. Requires Internet and SSH/scp for remote use.
Keep all companion setup, guard,
policy and test files beside this script. Re-running deletes settings and caches,
including the previous API key. Shared Python dependencies are preserved.
#>
[CmdletBinding()]
param([string]$ComputerName, [string]$UserName = 'Win11-Client', [switch]$IsolatedTest)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
if ($ComputerName) {
    if ($ComputerName -notmatch '^[a-zA-Z0-9.:-]+$' -or $UserName -notmatch '^[a-zA-Z0-9_.-]+$') { throw 'Invalid SSH target.' }
    $target = "$UserName@$ComputerName"
    # Upload only non-secret setup files into the SSH user's home directory.
    $files = @($PSCommandPath)
    foreach ($name in @('shellgpt_stepfun_setup.py','shellgpt_command_guard.py','shellgpt_command_policy.ps1','test_command_guard.py')) {
        $path = Join-Path $PSScriptRoot $name
        if (-not (Test-Path -LiteralPath $path)) { throw "Missing setup file: $name" }
        $files += $path
    }
    $liveVerifier = Join-Path $PSScriptRoot 'verify_shellgpt_live.py'
    if (Test-Path -LiteralPath $liveVerifier) { $files += $liveVerifier }
    & scp @files "${target}:"
    if ($LASTEXITCODE -ne 0) { throw 'Script upload failed.' }
    $remoteCommand = 'powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File Setup-ShellGPT-StepFun.ps1'
    if ($IsolatedTest) { $remoteCommand += ' -IsolatedTest' }
    & ssh -o ConnectTimeout=15 $target $remoteCommand
    if ($LASTEXITCODE -ne 0) { throw 'Remote setup failed.' }
    return
}
$python = $null
$candidates = @()
$pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
if ($pythonCommand -and $pythonCommand.Source -notlike '*\WindowsApps\*') { $candidates += $pythonCommand.Source }
$candidates += @(Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe", "$env:ProgramFiles\Python*\python.exe", 'C:\Python*\python.exe' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
foreach ($candidate in ($candidates | Select-Object -Unique)) {
    & $candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>$null
    if ($LASTEXITCODE -eq 0) { $python = $candidate; break }
}
if (-not $python) {
    if ($IsolatedTest) { throw 'Isolated testing requires Python 3.10+ already installed; run normal setup first.' }
    $version = '3.14.10'
    $architecture = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } elseif ([Environment]::Is64BitOperatingSystem) { 'amd64' } else { '' }
    $suffix = if ($architecture) { "-$architecture" } else { '' }
    $url = "https://www.python.org/ftp/python/$version/python-$version$suffix.exe"
    $installer = Join-Path ([IO.Path]::GetTempPath()) ('sgpt-python-' + [guid]::NewGuid().ToString('N') + '.exe')
    Write-Host "Python is missing. Downloading signed Python $version installer..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
    $signature = Get-AuthenticodeSignature -LiteralPath $installer
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notlike '*Python Software Foundation*') {
        throw 'Python installer signature validation failed; refusing to execute it.'
    }
    $installDirectory = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314'
    $arguments = @('/quiet','InstallAllUsers=0',('TargetDir="' + $installDirectory + '"'),
        'PrependPath=1','Include_pip=1','Include_test=0','Include_launcher=0','AssociateFiles=0','Shortcuts=0')
    $process = Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
    if ($process.ExitCode -notin @(0,3010)) { throw "Python installation failed: $($process.ExitCode)" }
    $python = Join-Path $installDirectory 'python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'Python installer finished but python.exe was not found.' }
    # Remove only the exact temporary installer this invocation downloaded.
    Remove-Item -LiteralPath $installer -Force
}
$pythonDirectory = Split-Path -Parent $python
$env:Path = "$pythonDirectory;$(Join-Path $pythonDirectory 'Scripts');$env:Path"
& $python --version
& $python -m pip --version
if ($LASTEXITCODE -ne 0) {
    & $python -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) { throw 'Python pip bootstrap failed.' }
}
if ($IsolatedTest) {
    & $python (Join-Path $PSScriptRoot 'shellgpt_stepfun_setup.py') --isolated-test
    if ($LASTEXITCODE -ne 0) { throw 'Isolated setup verification failed.' }
    return
}
& $python (Join-Path $PSScriptRoot 'shellgpt_stepfun_setup.py')
if ($LASTEXITCODE -ne 0) { throw 'ShellGPT setup failed.' }
$scripts = (& $python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))").Trim()
$userPath = [string][Environment]::GetEnvironmentVariable('Path', 'User')
if ($scripts -notin ($userPath -split ';')) {
    [Environment]::SetEnvironmentVariable('Path', ($userPath.TrimEnd(';') + ';' + $scripts).TrimStart(';'), 'User')
}
$env:Path = "$scripts;$env:Path"
$env:OPENAI_API_KEY = 'offline-verification-only'
try {
    & (Join-Path $scripts 'sgpt.exe') --version
    if ($LASTEXITCODE -ne 0) { throw 'CLI verification failed.' }
} finally {
    Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
}
Write-Host "Save the StepFun API key in $env:USERPROFILE\.config\shell_gpt\.sgptrc"
Write-Host 'Set OPENAI_API_KEY=your-key without quotes. Open a new terminal and run: sgpt "Reply with OK"'
Write-Host 'Live authentication has not been tested; no API key was supplied.'
Write-Host 'Command execution: recognized inspection runs automatically; other commands require typing yes.'
Write-Host 'Use sgpt "your task" for tool execution, or sgpt --shell "your task" for one generated command.'
