[CmdletBinding()]
param([switch]$NoKeyPrompt)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$python=Get-Command python.exe -ErrorAction SilentlyContinue
if($python -and $python.Source -notlike '*\WindowsApps\*'){
    & $python.Source -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>$null
    if($LASTEXITCODE -ne 0){$python=$null}
}
if(-not $python -or $python.Source -like '*\WindowsApps\*'){
    $version='3.14.10'
    $suffix=if($env:PROCESSOR_ARCHITECTURE -eq 'ARM64'){'-arm64'}elseif([Environment]::Is64BitOperatingSystem){'-amd64'}else{''}
    $installer=Join-Path ([IO.Path]::GetTempPath()) ('exam-python-'+[guid]::NewGuid().ToString('N')+'.exe')
    [Net.ServicePointManager]::SecurityProtocol=[Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/$version/python-$version$suffix.exe" -OutFile $installer -UseBasicParsing
    $signature=Get-AuthenticodeSignature -LiteralPath $installer
    if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notlike '*Python Software Foundation*'){throw 'Python installer signature failed.'}
    $target=Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314'
    $process=Start-Process $installer -ArgumentList @('/quiet','InstallAllUsers=0',('TargetDir="'+$target+'"'),'Include_pip=1','PrependPath=1','Include_test=0') -WindowStyle Hidden -Wait -PassThru
    if($process.ExitCode -notin @(0,3010)){throw 'Python install failed.'}
    Remove-Item -LiteralPath $installer -Force
    $python=Join-Path $target 'python.exe'
}else{$python=$python.Source}
$extra=@()
if($NoKeyPrompt){$extra+='--no-key-prompt'}
& $python (Join-Path $PSScriptRoot 'setup_exam.py') --activate @extra
if($LASTEXITCODE -ne 0){throw 'Exam setup failed.'}
