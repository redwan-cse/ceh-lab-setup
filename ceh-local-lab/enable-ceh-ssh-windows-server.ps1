# =====================================================================
# All-in-One CEH Practical Lab OpenSSH Setup (Win Server 2019 / 2022)
# Paste directly into Administrator PowerShell
# =====================================================================

$AllowedSubnet = '10.10.10.0/24'
$ErrorActionPreference = 'Stop'

# 0) Verify Administrator privileges
$principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Open Windows PowerShell using "Run as administrator", then paste this script again.'
}

$os = Get-CimInstance Win32_OperatingSystem
Write-Host "[*] Configuring OpenSSH on $($os.Caption)..." -ForegroundColor Cyan

# 1) Ensure Static IP (10.10.10.19) and Internet DNS are active if not already set
$adapter = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -First 1
$currentIP = (Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue).IPAddress
if ($currentIP -notlike '10.10.10.*') {
    Write-Host "[*] Assigning 10.10.10.19/24 (GW: 10.10.10.1) to $($adapter.Name)..." -ForegroundColor Yellow
    New-NetIPAddress -IPAddress 10.10.10.19 -PrefixLength 24 -DefaultGateway 10.10.10.1 -InterfaceIndex $adapter.ifIndex -ErrorAction SilentlyContinue | Out-Null
    Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -ServerAddresses ('8.8.8.8', '1.1.1.1')
}

# 2) Install OpenSSH Server (Windows Capability first, GitHub MSI fallback for Server 2019)
$sshdService = Get-Service -Name sshd -ErrorAction SilentlyContinue
if ($null -eq $sshdService) {
    Write-Host "[*] Installing Windows OpenSSH Server..." -ForegroundColor Yellow
    
    # Bypass WSUS (0x800f0954 fix on Server 2019)
    $wuPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU'
    $wuRestore = $null
    if (Test-Path $wuPath) {
        $wuRestore = (Get-ItemProperty -Path $wuPath -Name UseWUServer -ErrorAction SilentlyContinue).UseWUServer
        Set-ItemProperty -Path $wuPath -Name UseWUServer -Value 0 -ErrorAction SilentlyContinue
        Restart-Service wuauserv -Force -ErrorAction SilentlyContinue
    }

    try {
        Add-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0' | Out-Null
    } catch {
        Write-Host "[!] Windows Capability slow/unavailable. Using direct Win32-OpenSSH MSI installer..." -ForegroundColor Yellow
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $msiUrl = 'https://github.com/PowerShell/Win32-OpenSSH/releases/latest/download/OpenSSH-Win64-v9.5.0.0.msi'
        $msiPath = Join-Path $env:TEMP 'OpenSSH-Win64.msi'
        Invoke-WebRequest -Uri $msiUrl -OutFile $msiPath -UseBasicParsing
        Start-Process msiexec.exe -ArgumentList "/i `"$msiPath`" /qn /norestart" -Wait -NoNewWindow
    } finally {
        if ($null -ne $wuRestore) {
            Set-ItemProperty -Path $wuPath -Name UseWUServer -Value $wuRestore -ErrorAction SilentlyContinue
            Restart-Service wuauserv -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "[+] OpenSSH Server is already installed." -ForegroundColor Green
}

# 3) Start service once so default sshd_config and host keys are generated
Set-Service -Name sshd -StartupType Automatic
if ((Get-Service -Name sshd).Status -ne 'Running') {
    Start-Service -Name sshd
    Start-Sleep -Seconds 2
}

# 4) Configure Inbound Firewall Rule on Port 22 for the CEH Subnet
$ruleName = 'OpenSSH-Server-In-TCP'
$rule = Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
if ($null -ne $rule) {
    Set-NetFirewallRule -Name $ruleName -Enabled True -Direction Inbound -Action Allow -Profile Any
    Get-NetFirewallRule -Name $ruleName | Get-NetFirewallAddressFilter | Set-NetFirewallAddressFilter -RemoteAddress $AllowedSubnet
} else {
    New-NetFirewallRule -Name $ruleName -DisplayName 'OpenSSH Server (CEH Lab)' `
        -Enabled True -Profile Any -Direction Inbound -Protocol TCP -LocalPort 22 `
        -RemoteAddress $AllowedSubnet -Action Allow | Out-Null
}
Write-Host "[+] Firewall rule enabled for TCP/22 from $AllowedSubnet." -ForegroundColor Green

# 5) Update sshd_config for Password Auth + CEH Hydra/Brute-Force compatibility
$configPath = Join-Path $env:ProgramData 'ssh\sshd_config'
if (-not (Test-Path -LiteralPath $configPath)) {
    throw "OpenSSH did not generate $configPath."
}
$backupPath = "$configPath.ceh-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item -LiteralPath $configPath -Destination $backupPath -Force

$lines = @([System.IO.File]::ReadAllLines($configPath))
$firstMatchIndex = $lines.Count
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*Match\s+') {
        $firstMatchIndex = $i
        break
    }
}

$updated = New-Object 'System.Collections.Generic.List[string]'
$updated.Add('PasswordAuthentication yes')
$updated.Add('PubkeyAuthentication yes')
$updated.Add('MaxAuthTries 20')
$updated.Add('MaxStartups 50:30:100')

for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($i -lt $firstMatchIndex -and
        $lines[$i] -match '^\s*#?\s*(PasswordAuthentication|PubkeyAuthentication|MaxAuthTries|MaxStartups)(?:\s|$)') {
        continue
    }
    $updated.Add($lines[$i])
}

$utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($configPath, $updated.ToArray(), $utf8WithoutBom)

# Locate sshd.exe (handles both System32 capability and Program Files MSI paths)
$sshdExe = Join-Path $env:WINDIR 'System32\OpenSSH\sshd.exe'
if (-not (Test-Path -LiteralPath $sshdExe)) {
    $sshdExe = Join-Path $env:ProgramFiles 'OpenSSH\sshd.exe'
}
& $sshdExe -t -f $configPath
if ($LASTEXITCODE -ne 0) {
    Copy-Item -LiteralPath $backupPath -Destination $configPath -Force
    throw "Invalid sshd_config. Restored backup from $backupPath."
}

# 6) Set Windows PowerShell as Default SSH Shell & Restart sshd
$registryPath = 'HKLM:\SOFTWARE\OpenSSH'
New-Item -Path $registryPath -Force | Out-Null
New-ItemProperty -Path $registryPath -Name DefaultShell `
    -Value (Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe') `
    -PropertyType String -Force | Out-Null

Restart-Service -Name sshd -Force

# 7) Final Verification Summary
$svc = Get-Service -Name sshd
$listener = Get-NetTCPConnection -LocalPort 22 -State Listen -ErrorAction SilentlyContinue
$serverIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '10.10.10.*' } | Select-Object -First 1).IPAddress

Write-Host "`n====== CEH SSH SETUP SUMMARY ======" -ForegroundColor Cyan
Write-Host "Host Name       : $env:COMPUTERNAME"
Write-Host "Server IP       : $serverIP"
Write-Host "Login Account   : $env:USERNAME"
Write-Host "SSH Service     : $($svc.Status) (Automatic)"
Write-Host "Port 22 Active  : $([bool]$listener)"
Write-Host "Allowed Subnet  : $AllowedSubnet"
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Test from Parrot OS: ssh $env:USERNAME@$serverIP" -ForegroundColor Green