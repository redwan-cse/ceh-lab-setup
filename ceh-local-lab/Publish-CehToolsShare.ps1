<# Server-side helper. Called by Setup-CehToolsShare.ps1 with JSON on SSH stdin. #>
$ErrorActionPreference = 'Stop'
$r = [Console]::In.ReadToEnd() | ConvertFrom-Json
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Administrator required.' }
$path = [IO.Path]::GetFullPath([string]$r.library)
if ($path -notmatch '^[A-Za-z]:\\[^\\]+') { throw 'Expected a dedicated local library folder.' }
$marker = Join-Path $path '.ceh-library-manifest.json'
if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) { throw 'Verified extraction manifest missing.' }
if ((Get-Item -LiteralPath $path).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Redirected library refused.' }
$manifest = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
if ($manifest.format -ne 1 -or @($manifest.archives).Count -lt 1) { throw 'Invalid extraction manifest.' }
$description = 'CEH local tools read-only library'
$share = Get-SmbShare -Name 'CEH-Tools' -ErrorAction SilentlyContinue
if ($share -and ($share.Path -ine $path -or $share.Description -ne $description)) { throw 'Unrelated existing share; refusing changes.' }
$accountDescription = 'CEH-Tools dedicated read-only share account'
$user = Get-LocalUser -Name 'cehshare' -ErrorAction SilentlyContinue
if ($user -and $user.Description -ne $accountDescription) { throw 'Unrelated cehshare account; refusing changes.' }
$admins = Get-LocalGroup -SID 'S-1-5-32-544'
if ($user -and (Get-LocalGroupMember -Group $admins | Where-Object {$_.SID -eq $user.SID})) { throw 'Share account must not be an administrator.' }
$account = "$env:COMPUTERNAME\cehshare"
$administratorAccount = (New-Object Security.Principal.SecurityIdentifier('S-1-5-32-544')).Translate([Security.Principal.NTAccount]).Value
if ($share) {
    foreach ($access in Get-SmbShareAccess -Name 'CEH-Tools') {
        if ($access.AccountName -notin @($account,$administratorAccount) -or $access.AccessControlType -ne 'Allow') { throw 'Unexpected share access; inspect before reconfiguration.' }
    }
}
$smb = Get-SmbServerConfiguration
if ($smb.EnableSMB1Protocol -or -not $smb.EnableSMB2Protocol) { throw 'Expected SMB1 disabled and SMB2/3 enabled; inspect server policy.' }
$ruleName = 'CEH-Tools-SMB-Lab'
$rule = Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
if ($rule -and $rule.DisplayName -ne 'CEH Tools SMB (lab subnet)') { throw 'Firewall rule name conflict.' }
$password = ConvertTo-SecureString ([string]$r.password) -AsPlainText -Force
try {
    if ($user) { Set-LocalUser -Name 'cehshare' -Password $password }
    else { New-LocalUser -Name 'cehshare' -Password $password -Description $accountDescription -UserMayNotChangePassword -PasswordNeverExpires | Out-Null }
} finally { $password.Dispose(); $r.password = $null }
$user = Get-LocalUser -Name 'cehshare'
$users = Get-LocalGroup -SID 'S-1-5-32-545'
if (-not (Get-LocalGroupMember -Group $users | Where-Object {$_.SID -eq $user.SID})) {
    Add-LocalGroupMember -Group $users -Member $user
}
$acl = New-Object Security.AccessControl.DirectorySecurity
$acl.SetAccessRuleProtection($true, $false)
foreach ($item in @(@('S-1-5-18','FullControl'), @('S-1-5-32-544','FullControl'), @($user.SID.Value,'ReadAndExecute'))) {
    $sid = New-Object Security.Principal.SecurityIdentifier($item[0])
    $rule = New-Object Security.AccessControl.FileSystemAccessRule($sid,$item[1],'ContainerInherit,ObjectInherit','None','Allow')
    $acl.AddAccessRule($rule)
}
Set-Acl -LiteralPath $path -AclObject $acl
if (-not $share) {
    New-SmbShare -Name 'CEH-Tools' -Path $path -Description $description -ReadAccess $account -FullAccess $administratorAccount -EncryptData $true -CachingMode None -FolderEnumerationMode AccessBased | Out-Null
} else {
    Set-SmbShare -Name 'CEH-Tools' -EncryptData $true -CachingMode None -FolderEnumerationMode AccessBased -Confirm:$false | Out-Null
    Grant-SmbShareAccess -Name 'CEH-Tools' -AccountName $account -AccessRight Read -Force | Out-Null
}
if ($rule) { Remove-NetFirewallRule -Name $ruleName }
New-NetFirewallRule -Name $ruleName -DisplayName 'CEH Tools SMB (lab subnet)' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 445 -LocalAddress $r.server -RemoteAddress $r.subnet -Profile Any | Out-Null
if (@(Get-NetFirewallProfile | Where-Object Enabled).Count -ne 3) {
    Write-Warning 'Some firewall profiles remain disabled from the original lab. This scoped rule does not restrict other existing access.'
}
# Remove only verified archive copies from this deployment's staging directory.
$stage = Join-Path $env:USERPROFILE 'ceh-tools-deployment\archives'
$stagePrefix = [IO.Path]::GetFullPath($stage).TrimEnd('\') + '\'
foreach ($archive in $manifest.archives) {
    if ([IO.Path]::GetFileName($archive.name) -cne $archive.name) { throw 'Invalid staging filename.' }
    $zip = [IO.Path]::GetFullPath((Join-Path $stage $archive.name))
    if (-not $zip.StartsWith($stagePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Staging cleanup outside deployment folder.' }
    if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
}
Write-Host "Share ready: \\$($r.server)\CEH-Tools"
Write-Host "Read-only account: $account"
Get-SmbShareAccess -Name 'CEH-Tools' | Format-Table AccountName,AccessControlType,AccessRight
