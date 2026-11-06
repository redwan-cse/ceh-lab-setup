# CEH Practical Local Lab Setup Guide (Hyper-V)

This guide documents the complete step-by-step configuration for building an isolated, internet-enabled **CEH Practical Mock Lab** in Microsoft Hyper-V on `10.10.10.0/24`.

---

## 1. Lab Network Architecture & IP Addressing Scheme

All virtual machines connect to a single Hyper-V Internal Virtual Switch (`CEH-Lab-Switch`) routed through the Windows Host (`10.10.10.1`) via WinNAT for internet access.

| Machine / VM Name | Role | Hyper-V Gen | Static IP Address | Subnet Mask | Default Gateway | DNS Servers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Windows Host** (`vEthernet`) | NAT Gateway | Host | `10.10.10.1` | `255.255.255.0` | None | Host Default |
| **Parrot Security OS** | Attacker Machine | Gen 1 / 2 | `10.10.10.13` | `255.255.255.0` | `10.10.10.1` | `8.8.8.8`, `1.1.1.1` |
| **Android-8.1-Target** | Mobile Target (ADB) | **Gen 1** | `10.10.10.9` | `255.255.255.0` | `10.10.10.1` | `8.8.8.8`, `1.1.1.1` |
| **WinServer-2019** | Domain Controller / AD | Gen 2 | `10.10.10.19` | `255.255.255.0` | `10.10.10.1` | `8.8.8.8`, `1.1.1.1` |
| **WinServer-2022** | Web / FTP / SQL / SMB | Gen 2 | `10.10.10.22` | `255.255.255.0` | `10.10.10.1` | `8.8.8.8`, `10.10.10.19` |
| **Win11-Client** | Workstation Target | Gen 2 | `10.10.10.11` | `255.255.255.0` | `10.10.10.1` | `8.8.8.8`, `10.10.10.19` |

> **Important DNS Note:** Never assign `127.0.0.2` (Host local VPN/DNS proxy loopback) inside any VM. Always use `8.8.8.8`, `1.1.1.1`, or the local Domain Controller (`10.10.10.19`).

---

## 2. Host Hyper-V Switch & NAT Setup (Internet Access)

Run the following commands in **Windows PowerShell as Administrator** on your Windows Host to create the isolated switch and enable internet access for the `10.10.10.0/24` subnet:

```powershell
# 1. Create the Internal Virtual Switch
New-VMSwitch -SwitchName "CEH-Lab-Switch" -SwitchType Internal

# 2. Get the InterfaceIndex of the new virtual adapter
$ifIndex = (Get-NetAdapter -Name "vEthernet (CEH-Lab-Switch)").ifIndex

# 3. Assign the Gateway IP (10.10.10.1) to the host virtual switch adapter
New-NetIPAddress -IPAddress 10.10.10.1 -PrefixLength 24 -InterfaceIndex $ifIndex

# 4. Create the NAT rule for internet access
New-NetNat -Name "CEH-Lab-NAT" -InternalIPInterfaceAddressPrefix 10.10.10.0/24
```

### Verification (On Windows Host)
```powershell
Get-NetIPAddress -IPAddress 10.10.10.1
Get-NetNat
```

---

## 3. Parrot Security OS Configuration (`10.10.10.13`)

### 3.1 Attach to Lab Switch & Configure Static IP
1. In **Hyper-V Manager**, open **Parrot Security** -> **Settings** -> **Network Adapter**, and select `CEH-Lab-Switch`.
2. Open the Parrot terminal and configure a persistent static IP using `nmcli`:

```bash
# Check active connection name (typically "Wired connection 1")
nmcli connection show

# Set Static IP, Gateway, and DNS
sudo nmcli connection modify "Wired connection 1" \
  ipv4.addresses 10.10.10.13/24 \
  ipv4.gateway 10.10.10.1 \
  ipv4.dns "8.8.8.8 1.1.1.1" \
  ipv4.method manual

# Restart interface to apply changes
sudo nmcli connection down "Wired connection 1" && sudo nmcli connection up "Wired connection 1"
```

### 3.2 Enable OpenSSH Server on Parrot (For Host Windows Terminal Access)
Run this block inside the Parrot terminal so you can SSH into Parrot directly from Windows PowerShell:

```bash
sudo apt update && sudo apt install -y openssh-server adb
sudo ssh-keygen -A
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl enable --now ssh
sudo ss -tlnp | grep :22
```

* **Connect from Windows Host PowerShell:**
  ```powershell
  ssh redwan@10.10.10.13
  ```
* **Optional Passwordless SSH Key Auth (Run on Windows Host PowerShell):**
  ```powershell
  if (-not (Test-Path "$env:USERPROFILE\.ssh\id_ed25519.pub")) {
      ssh-keygen -t ed25519 -N '""' -f "$env:USERPROFILE\.ssh\id_ed25519"
  }
  Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | ssh redwan@10.10.10.13 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
  ```

---

## 4. Android-x86 8.1 (`android-x86_64-8.1-r6.iso`) Setup (`10.10.10.9`)

Android-x86 8.1 requires a **Generation 1** VM (Legacy BIOS and IDE controller) and static memory.

### 4.1 Create the Android VM (Run on Windows Host PowerShell)
```powershell
$VMName = "Android-8.1-Target"
$Switch = "CEH-Lab-Switch"
$VHDPath = "C:\Users\Public\Documents\Hyper-V\Virtual Hard Disks\Android-8.1-Target.vhdx"

New-VM -Name $VMName -Generation 1 -MemoryStartupBytes 2048MB -NewVHDPath $VHDPath -NewVHDSizeBytes 16GB -SwitchName $Switch
Set-VMMemory -VMName $VMName -DynamicMemoryEnabled $false
Set-VMProcessor -VMName $VMName -Count 2
```
* Attach `android-x86_64-8.1-r6.iso` under **Settings** -> **IDE Controller 1** -> **DVD Drive**.

### 4.2 OS Installation Steps
1. Boot the VM and select **Installation - Install Android-x86 to harddisk**.
2. Select **Create/Modify partitions** -> **Do you want to use GPT?** -> **No**.
3. In `cfdisk`:
   * Select **New** -> **Primary** -> accept full disk size.
   * Select **Bootable** (ensure `Boot` appears under Flags).
   * Select **Write** -> type `yes` -> press **Enter** -> select **Quit**.
4. Select `sda1` -> format as **ext4** -> **Yes**.
5. Install **GRUB boot loader** -> **Yes**.
6. Install `/system` directory as **read-write** -> **Yes**.
7. Eject the ISO from **Media -> DVD Drive** and reboot.

### 4.3 Bypass `VirtWifi` Loop, Configure `wifi_eth` IP, and Open ADB Port 5555
Android-x86 renames `eth0` to `wifi_eth` and wraps it inside a `VirtWifi` (`wlan0`) interface that hangs at *"Obtaining IP address..."* when no DHCP server is present.

1. Inside the booted Android VM, press **Alt + F1** to open the local root console (`x86_64:/ #`). *(Press **Alt + F7** at any time to return to the Android GUI).*
2. Run the following commands in the Android root shell:

```sh
# 1. Disable the virtual Wi-Fi wrapper
svc wifi disable
ip link set wlan0 down

# 2. Assign 10.10.10.9 and default gateway directly to wifi_eth
ip addr flush dev wifi_eth
ifconfig wifi_eth 10.10.10.9 netmask 255.255.255.0 up
ip route add default via 10.10.10.1 dev wifi_eth
ip rule add from all lookup main pref 1
setprop net.dns1 8.8.8.8
ndc resolver setnetdns wifi_eth "" 8.8.8.8 1.1.1.1

# 3. Enable ADB over TCP port 5555 for CEH exploitation
setprop service.adb.tcp.port 5555
stop adbd
start adbd

# 4. Verify connectivity
ping -c 3 10.10.10.1
ping -c 3 8.8.8.8
```

### 4.4 Verify Exploitation from Parrot OS & Create Checkpoint
From your **Parrot Security** terminal, verify port `5555` is open and accessible:

```bash
nmap -sV -p 5555 10.10.10.9
adb connect 10.10.10.9:5555
adb devices
adb shell
```

> **Crucial:** Once `adb shell` connects, right-click `Android-8.1-Target` in **Hyper-V Manager** and click **Checkpoint**. Because Android resets `ifconfig` and `setprop` on reboot, always restore this checkpoint before starting a practice session.

---

## 5. Windows Server 2019, 2022 & Windows 11 Provisioning

### 5.1 Create All 3 Windows VMs (Run on Windows Host PowerShell)
```powershell
$Switch = "CEH-Lab-Switch"
$VHDDir = "C:\Users\Public\Documents\Hyper-V\Virtual Hard Disks"

# 1. Windows Server 2019 (4GB RAM, 4 vCPU, 50GB Disk)
New-VM -Name "WinServer-2019" -Generation 2 -MemoryStartupBytes 4096MB -NewVHDPath "$VHDDir\WinServer-2019.vhdx" -NewVHDSizeBytes 50GB -SwitchName $Switch
Set-VMProcessor -VMName "WinServer-2019" -Count 4
Set-VMMemory -VMName "WinServer-2019" -DynamicMemoryEnabled $false

# 2. Windows Server 2022 (4GB RAM, 4 vCPU, 50GB Disk)
New-VM -Name "WinServer-2022" -Generation 2 -MemoryStartupBytes 4096MB -NewVHDPath "$VHDDir\WinServer-2022.vhdx" -NewVHDSizeBytes 50GB -SwitchName $Switch
Set-VMProcessor -VMName "WinServer-2022" -Count 4
Set-VMMemory -VMName "WinServer-2022" -DynamicMemoryEnabled $false

# 3. Windows 11 Client (4GB RAM, 4 vCPU, 60GB Disk + TPM 2.0)
New-VM -Name "Win11-Client" -Generation 2 -MemoryStartupBytes 4096MB -NewVHDPath "$VHDDir\Win11-Client.vhdx" -NewVHDSizeBytes 60GB -SwitchName $Switch
Set-VMProcessor -VMName "Win11-Client" -Count 4
Set-VMMemory -VMName "Win11-Client" -DynamicMemoryEnabled $false
Set-VMKeyProtector -VMName "Win11-Client" -NewLocalKeyProtector
Enable-VMTPM -VMName "Win11-Client"
```

* **Installation Notes:**
  * Attach each ISO under **Settings -> SCSI Controller -> DVD Drive** and move **DVD Drive** to the top of the **Firmware** boot order.
  * For Server 2019 and 2022, select **Standard Evaluation (Desktop Experience)** so the full GUI is installed.
  * For Windows 11 offline account setup during OOBE: press **Shift + F10**, run `OOBE\BYPASSNRO`, and select **"I don't have internet"** -> **"Continue with limited setup"**.

### 5.2 Static IP & Lab Firewall Configuration (Run Inside Each Windows VM)
Open **PowerShell as Administrator** inside each respective Windows VM:

* **Inside `WinServer-2019` (`10.10.10.19`):**
  ```powershell
  $idx = (Get-NetAdapter).ifIndex
  New-NetIPAddress -IPAddress 10.10.10.19 -PrefixLength 24 -DefaultGateway 10.10.10.1 -InterfaceIndex $idx
  Set-DnsClientServerAddress -InterfaceIndex $idx -ServerAddresses ("8.8.8.8", "1.1.1.1")
  Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
  ```

* **Inside `WinServer-2022` (`10.10.10.22`):**
  ```powershell
  $idx = (Get-NetAdapter).ifIndex
  New-NetIPAddress -IPAddress 10.10.10.22 -PrefixLength 24 -DefaultGateway 10.10.10.1 -InterfaceIndex $idx
  Set-DnsClientServerAddress -InterfaceIndex $idx -ServerAddresses ("8.8.8.8", "10.10.10.19")
  Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
  ```

* **Inside `Win11-Client` (`10.10.10.11`):**
  ```powershell
  $idx = (Get-NetAdapter).ifIndex
  New-NetIPAddress -IPAddress 10.10.10.11 -PrefixLength 24 -DefaultGateway 10.10.10.1 -InterfaceIndex $idx
  Set-DnsClientServerAddress -InterfaceIndex $idx -ServerAddresses ("8.8.8.8", "10.10.10.19")
  Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
  ```

---

## 6. Universal All-in-One OpenSSH Server Script (For Any Windows Server / Client)

Paste this script directly into an **Administrator PowerShell** window on **any** Windows machine (`WinServer-2019`, `WinServer-2022`, `Win11-Client`, or any future server on any subnet).

* Automatically detects existing IP addresses or prompts if the adapter is unconfigured (`169.254.x.x`).
* Includes a built-in fallback to the official GitHub `Win32-OpenSSH` MSI installer if Windows Update/WSUS fails on Server 2019.
* Configures `PasswordAuthentication yes`, `MaxAuthTries 20`, and `MaxStartups 50:30:100` for CEH password-spraying/Hydra exercises.
* Uses `LocalSubnet` for the firewall rule so it adapts to any IP scheme automatically.

```powershell
# =====================================================================
# Universal OpenSSH Server Setup (Win Server 2019/2022/2025 & Win 10/11)
# Paste directly into an elevated (Administrator) PowerShell window
# =====================================================================

$AllowedClients = 'LocalSubnet'
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

# 6) Configure Firewall Rule using 'LocalSubnet'
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
    Write-Host "Connect from Parrot OS or Windows Host using:" -ForegroundColor Green
    foreach ($addr in $addresses) {
        Write-Host "  ssh $env:USERNAME@$($addr.IPAddress)" -ForegroundColor Green
    }
}
```

---

## 7. Quick Verification Checklist (From Parrot Security `10.10.10.13`)

Run these commands inside Parrot Security before starting your mock exam tasks to confirm all targets are reachable:

```bash
# 1. Discover all live hosts on the CEH Lab Subnet
nmap -sn 10.10.10.0/24

# 2. Verify Android ADB Target (10.10.10.9)
nmap -sV -p 5555 10.10.10.9
adb connect 10.10.10.9:5555

# 3. Verify Windows Server SSH & SMB Targets (.19, .22, .11)
nmap -sV -p 22,139,445,3389 10.10.10.19 10.10.10.22 10.10.10.11
```