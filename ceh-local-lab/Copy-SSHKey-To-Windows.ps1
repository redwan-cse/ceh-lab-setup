<#
Windows equivalent of ssh-copy-id for the default OpenSSH Administrator setup.
Adds an existing PUBLIC key; never copies a private key or saves a password.
Preserves sshd_config and password authentication. Does not restart sshd.

Example:
  .\Copy-SSHKey-To-Windows.ps1 -ComputerName 10.10.10.19
Requires password or existing SSH access as an Administrator, with the default
Match Group administrators / administrators_authorized_keys configuration.
#>
[CmdletBinding()]
param(
    [string]$ComputerName = '10.10.10.19',
    [string]$UserName = 'Administrator',
    [string]$PublicKeyPath = (Join-Path $env:USERPROFILE '.ssh\id_ed25519.pub')
)
$ErrorActionPreference = 'Stop'
if ($ComputerName -notmatch '^[a-zA-Z0-9.:-]+$' -or $UserName -notmatch '^[a-zA-Z0-9_.-]+$') {
    throw 'Invalid SSH target.'
}
$key = (Get-Content -Raw -LiteralPath $PublicKeyPath).Trim()
if ($key -notmatch '^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/]+={0,3}(?: [^\r\n]*)?$') {
    throw 'Expected one SSH public key, never a private key.'
}
& ssh-keygen -lf $PublicKeyPath
if ($LASTEXITCODE -ne 0) { throw 'Invalid public key.' }
$keyBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($key))
$remoteScript = @'
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'An Administrator account is required.'
}
$config = Join-Path $env:ProgramData 'ssh\sshd_config'
$configBefore = (Get-FileHash -LiteralPath $config -Algorithm SHA256).Hash
$text = Get-Content -Raw -LiteralPath $config
if ($text -notmatch '(?im)^\s*Match\s+Group\s+administrators\s*\r?\n\s*AuthorizedKeysFile\s+__PROGRAMDATA__/ssh/administrators_authorized_keys\s*$') {
    throw 'Custom sshd_config: inspect the effective Administrator key path before using this script.'
}
$publicKey = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('PUBLIC_KEY_BASE64'))
$keyFile = Join-Path $env:ProgramData 'ssh\administrators_authorized_keys'
if ((Test-Path -LiteralPath $keyFile) -and
    ((Get-Item -Force -LiteralPath $keyFile).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Refusing a redirected authorized-keys file.'
}
$existing = if (Test-Path -LiteralPath $keyFile) { [IO.File]::ReadAllText($keyFile) } else { '' }
$keyIdentity = ($publicKey -split '\s+')[0..1] -join ' '
$present = $false
foreach ($line in ($existing -split '\r?\n')) {
    if (($line.Trim() -split '\s+').Count -ge 2 -and
        (($line.Trim() -split '\s+')[0..1] -join ' ') -eq $keyIdentity) { $present = $true }
}
if (-not $present) {
    if ($existing.Length -and -not $existing.EndsWith("`n")) { $existing += "`r`n" }
    [IO.File]::WriteAllText($keyFile, $existing + $publicKey + "`r`n", (New-Object Text.UTF8Encoding($false)))
    Write-Output 'Added public key.'
} else {
    Write-Output 'Public key already present.'
}
# Restrict access to the Windows Administrators group and SYSTEM, using SIDs
# so permissions work regardless of the server display language.
$admins = New-Object Security.Principal.SecurityIdentifier('S-1-5-32-544')
$system = New-Object Security.Principal.SecurityIdentifier('S-1-5-18')
$acl = New-Object Security.AccessControl.FileSecurity
$acl.SetOwner($admins)
$acl.SetAccessRuleProtection($true, $false)
$acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($admins, 'FullControl', 'Allow')))
$acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($system, 'FullControl', 'Allow')))
Set-Acl -LiteralPath $keyFile -AclObject $acl
if ((Get-FileHash -LiteralPath $config -Algorithm SHA256).Hash -ne $configBefore) {
    throw 'sshd_config changed during the operation; inspect before continuing.'
}
Write-Output "Authorized-key file: $keyFile"
Write-Output 'PASS: sshd_config unchanged; password authentication settings preserved.'
icacls $keyFile
'@
$remoteScript = $remoteScript.Replace('PUBLIC_KEY_BASE64', $keyBase64)
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($remoteScript))
& ssh -o ConnectTimeout=15 -o NumberOfPasswordPrompts=1 "$UserName@$ComputerName" "powershell -NoProfile -OutputFormat Text -EncodedCommand $encoded"
if ($LASTEXITCODE -ne 0) { throw 'Public-key installation failed.' }
$privateKey = $PublicKeyPath -replace '\.pub$', ''
& ssh -o BatchMode=yes -o IdentitiesOnly=yes -i $privateKey "$UserName@$ComputerName" 'whoami'
if ($LASTEXITCODE -ne 0) { throw 'Key-only login verification failed.' }
Write-Host "PASS: key-only login works. Future command: ssh $UserName@$ComputerName"
