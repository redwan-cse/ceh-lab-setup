<#
Copy this file and its Python/policy companions to any Windows lab PC.
Run locally: .\Setup-ShellGPT-StepFun.ps1 -PromptForApiKey
Remote noninteractive setup: specify -ComputerName and optionally -UserName.
Requires Internet; installs signed Python 3.14.10 when Python 3.10+ is missing.
Reinstalls ShellGPT configuration, preserving a recognized StepFun provider key by default.
Use -ResetConfig to discard that key. Shared Python dependencies are preserved.
#>
[CmdletBinding()]
param(
    [string]$ComputerName,
    [string]$UserName = $env:USERNAME,
    [switch]$IsolatedTest,
    [switch]$PromptForApiKey,
    [switch]$ResetConfig
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
if ($ComputerName) {
    if ($PromptForApiKey -and -not $IsolatedTest) {
        throw '-PromptForApiKey requires local interactive setup. SSH setup uses -NonInteractive; run this switch in a local terminal on the target afterward.'
    }
    if ($ComputerName -notmatch '^[a-zA-Z0-9.:-]+$' -or $UserName -notmatch '^[a-zA-Z0-9_.-]+$') { throw 'Invalid SSH target.' }
    $target = "$UserName@$ComputerName"
    # Upload only non-secret setup files into the SSH user's home directory.
    $files = @($PSCommandPath)
    foreach ($name in @('shellgpt_stepfun_setup.py','shellgpt_command_guard.py','shellgpt_command_policy.ps1','test_command_guard.py')) {
        $path = Join-Path $PSScriptRoot $name
        if (-not (Test-Path -LiteralPath $path)) { throw "Missing setup file: $name" }
        $files += $path
    }
    $safetyTests = Join-Path $PSScriptRoot 'test_setup_safety.py'
    if (Test-Path -LiteralPath $safetyTests) { $files += $safetyTests }
    $liveVerifier = Join-Path $PSScriptRoot 'verify_shellgpt_live.py'
    if (Test-Path -LiteralPath $liveVerifier) { $files += $liveVerifier }
    & scp @files "${target}:"
    if ($LASTEXITCODE -ne 0) { throw 'Script upload failed.' }
    $remoteCommand = 'powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File Setup-ShellGPT-StepFun.ps1'
    if ($IsolatedTest) { $remoteCommand += ' -IsolatedTest' }
    if ($ResetConfig) { $remoteCommand += ' -ResetConfig' }
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
$setupArguments = @()
if ($ResetConfig) { $setupArguments += '--reset-config' }
& $python (Join-Path $PSScriptRoot 'shellgpt_stepfun_setup.py') @setupArguments
if ($LASTEXITCODE -ne 0) { throw 'ShellGPT setup failed.' }
$scripts = (& $python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))").Trim()
$userPath = [string][Environment]::GetEnvironmentVariable('Path', 'User')
if ($scripts -notin ($userPath -split ';')) {
    [Environment]::SetEnvironmentVariable('Path', ($userPath.TrimEnd(';') + ';' + $scripts).TrimStart(';'), 'User')
}
$env:Path = "$scripts;$env:Path"
$previousProcessKey = $env:OPENAI_API_KEY
$env:OPENAI_API_KEY = 'offline-verification-only'
try {
    & (Join-Path $scripts 'sgpt.exe') --version
    if ($LASTEXITCODE -ne 0) { throw 'CLI verification failed.' }
} finally {
    if ($null -eq $previousProcessKey) { Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue }
    else { $env:OPENAI_API_KEY = $previousProcessKey }
}
if ($PromptForApiKey) {
    $secureKey = Read-Host 'StepFun API key (hidden; Enter keeps the saved key)' -AsSecureString
    $pointer = [IntPtr]::Zero
    $plainKey = $null
    try {
        if ($secureKey.Length -gt 0) {
            $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
            $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
            if ($plainKey -match '[\r\n]') { throw 'API key must be one line.' }
            $configFile = Join-Path $env:USERPROFILE '.config\shell_gpt\.sgptrc'
            $lines = [IO.File]::ReadAllLines($configFile)
            $updated = @($lines | ForEach-Object {
                if ($_.StartsWith('OPENAI_API_KEY=')) { 'OPENAI_API_KEY=' + $plainKey } else { $_ }
            })
            [IO.File]::WriteAllLines($configFile, [string[]]$updated, (New-Object Text.UTF8Encoding($false)))
            Write-Host 'API key saved in the current user protected ShellGPT configuration.'
        }
    } finally {
        if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
        $plainKey = $null
        if ($secureKey) { $secureKey.Dispose() }
    }
}
Write-Host "API key location: $env:USERPROFILE\.config\shell_gpt\.sgptrc"
Write-Host 'Open a new terminal and run: sgpt "Reply with OK"'
Write-Host 'Setup verification used a dummy key and local HTTP mocks; live authentication was not tested.'
Write-Host 'Command execution: recognized inspection runs automatically; other commands require typing yes.'
Write-Host 'Use sgpt "your task" for tool execution, or sgpt --shell "your task" for one generated command.'
