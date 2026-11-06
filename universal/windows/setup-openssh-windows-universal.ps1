<#
.SYNOPSIS
Fast OpenSSH server setup for disposable Windows CEH lab VMs (run elevated).
.DESCRIPTION
Leaves all adapter, IP, subnet, gateway and DNS settings untouched. Any allows
inbound SSH on every firewall profile from any reachable client: use only on
the intended disposable lab. Use -AllowedClients LocalSubnet or explicit IPs /
CIDRs to narrow that scope. Existing sshd installations are reused. Auto uses
the latest official Win32-OpenSSH MSI, avoiding Windows Update capability delays.
Password and public key login are enabled globally; existing Match policy is
preserved. Lab auth limits change only with -EnableLabAuthTuning.
.EXAMPLE
.\setup-openssh-windows-universal.ps1 -AllowedClients '10.50.8.10','10.60.0.0/16'
.EXAMPLE
.\setup-openssh-windows-universal.ps1 -InstallMethod MSI -InstallerPath C:\Lab\OpenSSH-Win64.msi
#>
[CmdletBinding()]
param(
    [ValidateRange(1,65535)][int]$Port = 22,
    [string[]]$AllowedClients = @('Any'),
    [ValidateSet('Auto','MSI','Capability')][string]$InstallMethod = 'Auto',
    [string]$InstallerPath,
    [ValidatePattern('^[a-fA-F0-9]{64}$')][string]$InstallerSha256,
    [switch]$EnableLabAuthTuning,
    [switch]$FunctionsOnly
)

function Get-LabSshConfigText {
    param([AllowEmptyString()][string]$Text, [int]$Port = 22, [switch]$EnableLabAuthTuning)
    $lines = @([regex]::Split($Text, '\r?\n'))
    $settings = @("Port $Port", 'PasswordAuthentication yes', 'PubkeyAuthentication yes')
    $names = 'Port|PasswordAuthentication|PubkeyAuthentication'
    if ($EnableLabAuthTuning) {
        $settings += @('MaxAuthTries 20', 'MaxStartups 50:30:100')
        $names += '|MaxAuthTries|MaxStartups'
    }
    $output = New-Object 'System.Collections.Generic.List[string]'
    foreach ($setting in $settings) { $output.Add($setting) }
    $inMatch = $false
    foreach ($line in $lines) {
        if ($line -match '^\s*Match\s+') { $inMatch = $true }
        if (-not $inMatch -and $line -match "^\s*#?\s*($names)(?:\s|$)") { continue }
        $output.Add($line)
    }
    return (($output.ToArray() -join "`r`n").TrimEnd("`r", "`n") + "`r`n")
}

function Select-LabSshReleaseAsset {
    param($Release, [string]$Architecture)
    $platform = switch ($Architecture.ToUpperInvariant()) {
        'AMD64' { 'Win64' }
        'X64' { 'Win64' }
        'X86' { 'Win32' }
        'ARM64' { 'ARM64' }
        default { throw "Unsupported Windows architecture: $Architecture" }
    }
    $assets = @($Release.assets | Where-Object { $_.name -match "^OpenSSH-$platform-v[^/]+\.msi$" })
    if ($assets.Count -ne 1) { throw "Expected exactly one official $platform MSI; found $($assets.Count)." }
    $asset = $assets[0]
    if ($asset.browser_download_url -notmatch '^https://github\.com/PowerShell/Win32-OpenSSH/releases/download/') {
        throw 'Release asset URL is outside the official Win32-OpenSSH repository.'
    }
    if ($asset.digest -notmatch '^sha256:[a-fA-F0-9]{64}$') { throw 'Official asset has no SHA256 digest; refusing an unverified download.' }
    return $asset
}

function Get-LabSshServiceExecutable {
    param([string]$PathName)
    if ($PathName -match '^\s*"([^"]+\.exe)"') { return $Matches[1] }
    if ($PathName -match '^\s*(.+?\.exe)(?:\s|$)') { return $Matches[1] }
    throw "Cannot resolve sshd executable from service path: $PathName"
}

function Install-LabSshMsi {
    param([string]$LocalPath, [string]$ExpectedHash)
    $downloadDirectory = $null
    try {
        if ([string]::IsNullOrWhiteSpace($LocalPath)) {
            [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
            $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/PowerShell/Win32-OpenSSH/releases/latest' -Headers @{ 'User-Agent' = 'CEH-Lab-OpenSSH-Setup' } -TimeoutSec 60
            $architecture = $env:PROCESSOR_ARCHITEW6432
            if (-not $architecture) { $architecture = $env:PROCESSOR_ARCHITECTURE }
            $asset = Select-LabSshReleaseAsset -Release $release -Architecture $architecture
            $downloadDirectory = Join-Path ([IO.Path]::GetTempPath()) ('ceh-openssh-' + [guid]::NewGuid().ToString('N'))
            New-Item -ItemType Directory -Path $downloadDirectory | Out-Null
            $LocalPath = Join-Path $downloadDirectory $asset.name
            Write-Host "Downloading official OpenSSH $($release.tag_name): $($asset.name)"
            Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $LocalPath -UseBasicParsing -TimeoutSec 180
            $ExpectedHash = $asset.digest.Substring(7)
        }
        $LocalPath = (Resolve-Path -LiteralPath $LocalPath).ProviderPath
        if ([IO.Path]::GetExtension($LocalPath) -ne '.msi') { throw 'InstallerPath must be an MSI file.' }
        if ($ExpectedHash -and (Get-FileHash -LiteralPath $LocalPath -Algorithm SHA256).Hash -ne $ExpectedHash) {
            throw 'OpenSSH MSI SHA256 digest mismatch.'
        }
        $signature = Get-AuthenticodeSignature -LiteralPath $LocalPath
        if ($signature.Status -ne 'Valid' -or $null -eq $signature.SignerCertificate -or
            $signature.SignerCertificate.Subject -notmatch '(?:^|,\s*)O=Microsoft Corporation(?:,|$)') {
            throw 'OpenSSH MSI must have a valid Microsoft Authenticode signature.'
        }
        $process = Start-Process -FilePath 'msiexec.exe' -ArgumentList "/i `"$LocalPath`" /qn /norestart ADDLOCAL=Server" -WindowStyle Hidden -Wait -PassThru
        if ($process.ExitCode -notin @(0,3010)) { throw "OpenSSH MSI failed with exit code $($process.ExitCode)." }
        if ($process.ExitCode -eq 3010) { Write-Warning 'The MSI reports that Windows needs a reboot.' }
    } finally {
        # Only the unique directory created by this function is removed.
        if ($downloadDirectory -and (Test-Path -LiteralPath $downloadDirectory)) {
            if ($LocalPath -and (Test-Path -LiteralPath $LocalPath)) { Remove-Item -LiteralPath $LocalPath -Force }
            Remove-Item -LiteralPath $downloadDirectory -Force
        }
    }
}

if ($FunctionsOnly) { return }
$ErrorActionPreference = 'Stop'
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run Windows PowerShell as Administrator inside the intended lab VM.'
}
if ($AllowedClients.Count -eq 0 -or @($AllowedClients | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count -gt 0) {
    throw 'AllowedClients must contain Any, LocalSubnet, or explicit IP addresses/CIDRs.'
}
if ($InstallerPath -and $InstallMethod -eq 'Capability') { throw 'InstallerPath cannot be used with Capability.' }
$service = Get-Service -Name sshd -ErrorAction SilentlyContinue
if ($null -eq $service) {
    if ($InstallMethod -eq 'Capability') {
        $capability = Add-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0'
        if ($capability.RestartNeeded) { Write-Warning 'Windows reports that a reboot is needed.' }
    } else {
        Install-LabSshMsi -LocalPath $InstallerPath -ExpectedHash $InstallerSha256
    }
    $service = Get-Service -Name sshd -ErrorAction Stop
} else { Write-Host 'Existing sshd service found; installation skipped.' }
$serviceInfo = Get-CimInstance Win32_Service -Filter "Name='sshd'"
$sshdExe = Get-LabSshServiceExecutable -PathName $serviceInfo.PathName
if (-not (Test-Path -LiteralPath $sshdExe)) { throw "sshd executable not found: $sshdExe" }
$configPath = Join-Path $env:ProgramData 'ssh\sshd_config'
if ($serviceInfo.PathName -match '(?:^|\s)-f\s+(?:"([^"]+)"|(\S+))') {
    if ($Matches[1]) { $configPath = $Matches[1] } else { $configPath = $Matches[2] }
}
$configDirectory = Split-Path -Parent $configPath
if (-not (Test-Path -LiteralPath $configDirectory)) { New-Item -Path $configDirectory -ItemType Directory | Out-Null }
$hadConfig = Test-Path -LiteralPath $configPath
if ($hadConfig) { $original = [IO.File]::ReadAllText($configPath) }
else {
    $defaultPath = Join-Path (Split-Path -Parent $sshdExe) 'sshd_config_default'
    if (-not (Test-Path -LiteralPath $defaultPath)) { throw "Default sshd config not found: $defaultPath" }
    $original = [IO.File]::ReadAllText($defaultPath)
}
$newText = Get-LabSshConfigText -Text $original -Port $Port -EnableLabAuthTuning:$EnableLabAuthTuning
$changed = (-not $hadConfig) -or ($newText -cne $original)
$backupPath = $null
$candidatePath = Join-Path $configDirectory ('sshd_config.candidate-' + [guid]::NewGuid().ToString('N'))
$wasRunning = $service.Status -eq 'Running'
$serviceApplied = $false
try {
    # Generate missing host keys without starting/restarting the live listener.
    $keygen = Join-Path (Split-Path -Parent $sshdExe) 'ssh-keygen.exe'
    & $keygen -A
    if ($LASTEXITCODE -ne 0) { throw 'Host key generation failed.' }
    [IO.File]::WriteAllText($candidatePath, $newText, (New-Object Text.UTF8Encoding($false)))
    & $sshdExe -t -f $candidatePath
    if ($LASTEXITCODE -ne 0) { throw 'sshd config validation failed; existing config and listener were preserved.' }
    if ($changed) {
        if ($hadConfig) {
            $backupPath = "$configPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')-$([guid]::NewGuid().ToString('N'))"
            Copy-Item -LiteralPath $configPath -Destination $backupPath
        }
        [IO.File]::WriteAllText($configPath, $newText, (New-Object Text.UTF8Encoding($false)))
    }
    # A dedicated rule avoids changing existing SSH rules or closing an old port.
    $ruleName = "CEH-Lab-OpenSSH-TCP-$Port"
    $rule = Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
    if ($rule) {
        Set-NetFirewallRule -Name $ruleName -Enabled True -Direction Inbound -Profile Any -Protocol TCP -LocalPort $Port -RemoteAddress $AllowedClients -Action Allow | Out-Null
    } else {
        New-NetFirewallRule -Name $ruleName -DisplayName "CEH lab OpenSSH TCP/$Port" -Enabled True -Direction Inbound -Profile Any -Protocol TCP -LocalPort $Port -RemoteAddress $AllowedClients -Action Allow | Out-Null
    }
    Set-Service -Name sshd -StartupType Automatic
    if ($wasRunning -and $changed) { $serviceApplied = $true; Restart-Service -Name sshd -ErrorAction Stop }
    elseif (-not $wasRunning) { $serviceApplied = $true; Start-Service -Name sshd -ErrorAction Stop }
    (Get-Service -Name sshd).WaitForStatus([ServiceProcess.ServiceControllerStatus]::Running, [TimeSpan]::FromSeconds(20))
    $listener = @()
    for ($attempt = 0; $attempt -lt 10; $attempt++) {
        $listener = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
        if ($listener.Count -gt 0) { break }
        Start-Sleep -Milliseconds 200
    }
    if ($listener.Count -eq 0) { throw "sshd is running but no TCP/$Port listener was found. Inspect sshd logs and existing Include/Match policies." }
} catch {
    $failure = $_
    if ($changed -and $backupPath) {
        Copy-Item -LiteralPath $backupPath -Destination $configPath -Force
        if ($wasRunning -and $serviceApplied) {
            try {
                if ((Get-Service -Name sshd).Status -eq 'Running') { Restart-Service -Name sshd }
                else { Start-Service -Name sshd }
            } catch { Write-Warning "Could not restore running sshd: $_" }
        }
        Write-Warning "Restored previous config from $backupPath"
    } elseif ($changed -and -not $hadConfig -and (Test-Path -LiteralPath $configPath)) {
        Remove-Item -LiteralPath $configPath -Force
    }
    throw $failure
} finally {
    if (Test-Path -LiteralPath $candidatePath) { Remove-Item -LiteralPath $candidatePath -Force }
}
Write-Host "OpenSSH running on TCP/$Port; firewall clients: $($AllowedClients -join ', ')."
Write-Host 'Existing network addressing and existing SSH firewall rules were preserved.'
Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254.*' } |
    ForEach-Object { Write-Host "  ssh -p $Port $env:USERNAME@$($_.IPAddress)" }
