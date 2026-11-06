# =====================================================================
# Universal OpenSSH Server Setup (Win Server 2019/2022/2025 & Win 10/11)
# Automatically adapts to any existing IP/Subnet or prompts if unconfigured
# =====================================================================

$AllowedClients = 'LocalSubnet' # Automatically allows any machine on the same subnet
$ErrorActionPreference = 'Stop'

# 0) Verify Administrator privileges
$principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run Windows PowerShell as Administrator, then try again.'
}

$os = Get-CimInstance Win32_OperatingSystem
Write-Host "[*] Configuring OpenSSH Server on $($os.Caption)..." -ForegroundColor Cyan

# 1) Smart IP Detection (Never overwrites an existing valid IP)
$adapter = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -First 1
$validIPs = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254.*' })

if ($validIPs.Count -eq 0 -and $null -ne $adapter) {
    Write-Host "[!] No valid IPv4 address detected on $($adapter.Name) (currently APIPA 169.254.x.x)." -ForegroundColor Yellow
    $inputIP = Read-Host "Enter a Static IP to assign (e.g. 10.10.10.22), or press Enter to skip"
    if (-not [string]::IsNullOrWhiteSpace($inputIP)) {
        $octets = $inputIP.Trim().Split('.')
        $defaultGw = "$($octets[0]).$($octets[1]).$($octets[2]).1"
        $inputGw = Read-Host "Enter Gateway IP (Press Enter for default $defaultGw)"
        if ([string]::IsNullOrWhiteSpace($inputGw)) { $inputGw = $defaultGw }
        
        New-NetIPAddress -IPAddress $inputIP.Trim() -PrefixLength 24 -DefaultGateway $inputGw.Trim() -InterfaceIndex $adapter.ifIndex -ErrorAction SilentlyContinue | Out-Null
        Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -ServerAddresses ('8.8.8.8', '1.1.1.1')
        Write-Host "[+] Assigned $($inputIP.Trim())/24 (GW: $inputGw) to $($adapter.Name)." -ForegroundColor Green
    }
}

# 2) Install OpenSSH Server (Windows Capability first, GitHub MSI fallback)
$sshdService = Get-Service -Name 'sshd' -ErrorAction SilentlyContinue
if ($null -eq $sshdService) {
    Write-Host "[*] Installing OpenSSH Server..." -ForegroundColor Yellow
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
        Write-Host "[!] Windows Capability unavailable. Falling back to Win32-OpenSSH MSI..." -ForegroundColor Yellow
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

# 3) Start service once to generate default sshd_config and host keys
Set-Service -Name 'sshd' -StartupType Automatic
if ((Get-Service -Name 'sshd').Status -ne 'Running') {
    Start-Service -Name 'sshd'
    Start-Sleep -Seconds 2
}

# 4) Back up and update sshd_config (Password Auth + Lab Brute-Force support)
$configPath = Join-Path $env:ProgramData 'ssh\sshd_config'
if (-not (Test-Path -LiteralPath $configPath)) {
    throw "OpenSSH config not found at $configPath"
}
$backupPath = "$configPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item -LiteralPath $configPath -Destination $backupPath -Force

$lines = @([System.IO.File]::ReadAllLines($configPath))
$matchIndex = $lines.Count
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*Match\s+') { $matchIndex = $i; break }
}

$newLines = New-Object 'System.Collections.Generic.List[string]'
$newLines.Add('PasswordAuthentication yes')
$newLines.Add('PubkeyAuthentication yes')
$newLines.Add('MaxAuthTries 20')
$newLines.Add('MaxStartups 50:30:100')

for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($i -lt $matchIndex -and
        $lines[$i] -match '^\s*#?\s*(PasswordAuthentication|PubkeyAuthentication|MaxAuthTries|MaxStartups)(?:\s|$)') {
        continue
    }
    $newLines.Add($lines[$i])
}
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($configPath, $newLines.ToArray(), $utf8NoBom)

$sshdExe = Join-Path $env:WINDIR 'System32\OpenSSH\sshd.exe'
if (-not (Test-Path -LiteralPath $sshdExe)) {
    $sshdExe = Join-Path $env:ProgramFiles 'OpenSSH\sshd.exe'
}
& $sshdExe -t -f $configPath
if ($LASTEXITCODE -ne 0) {
    Copy-Item -LiteralPath $backupPath -Destination $configPath -Force
    throw "sshd config validation failed. Restored backup: $backupPath"
}

# 5) Set Windows PowerShell as default SSH shell
$regPath = 'HKLM:\SOFTWARE\OpenSSH'
New-Item -Path $regPath -Force | Out-Null
New-ItemProperty -Path $regPath -Name DefaultShell `
    -Value (Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe') `
    -PropertyType String -Force | Out-Null

# 6) Configure Firewall Rule using 'LocalSubnet' (works on any IP range automatically)
$ruleName = 'OpenSSH-Server-In-TCP'
$rule = Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
if ($null -ne $rule) {
    Set-NetFirewallRule -Name $ruleName -Enabled True -Direction Inbound -Action Allow -Profile Any
    $rule | Get-NetFirewallAddressFilter | Set-NetFirewallAddressFilter -RemoteAddress $AllowedClients
} else {
    New-NetFirewallRule -Name $ruleName `
        -DisplayName 'OpenSSH Server (LocalSubnet)' `
        -Enabled True -Direction Inbound -Profile Any `
        -Protocol TCP -LocalPort 22 -RemoteAddress $AllowedClients `
        -Action Allow | Out-Null
}
Write-Host "[+] Firewall rule enabled for TCP/22 from $AllowedClients." -ForegroundColor Green

# 7) Restart sshd and print detected IP addresses
Restart-Service -Name 'sshd' -Force

$svc = Get-Service -Name 'sshd'
$listener = Get-NetTCPConnection -LocalPort 22 -State Listen -ErrorAction SilentlyContinue
$addresses = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254.*' })

Write-Host "`n========= SSH SERVER SETUP RESULT =========" -ForegroundColor Cyan
Write-Host "Computer:              $env:COMPUTERNAME"
Write-Host "Windows version:       $($os.Caption)"
Write-Host "SSH service:           $($svc.Status)"
Write-Host "TCP port 22 listening: $([bool]$listener)"
Write-Host "Allowed clients:       $AllowedClients"
Write-Host "===========================================" -ForegroundColor Cyan

if ($addresses.Count -gt 0) {
    Write-Host "Connect from Parrot OS using:" -ForegroundColor Green
    foreach ($addr in $addresses) {
        Write-Host "  ssh $env:USERNAME@$($addr.IPAddress)" -ForegroundColor Green
    }
}