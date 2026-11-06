<# Run in Administrator PowerShell. Creates a native, persistent machine-wide
SMB drive for all local sessions. The server still grants only read access.
Windows manages the saved SMB credential; scripts never store its plaintext.
#>
[CmdletBinding()]
param([string]$Server='10.10.10.22',[string]$AccountDomain='WIN-L4HLUP8AT8K',[ValidatePattern('^[D-Z]$')][string]$DriveLetter='T',[switch]$FromStdin)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
if($Server -notmatch '^[A-Za-z0-9_.-]+$'){throw 'Invalid server.'}
$principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Machine-wide mounting requires Administrator PowerShell.'}
if(-not (Get-Command New-SmbGlobalMapping -ErrorAction SilentlyContinue)){throw 'This Windows version lacks native global SMB mappings.'}
if($FromStdin){
    $r=[Console]::In.ReadToEnd()|ConvertFrom-Json
    $password=ConvertTo-SecureString ([string]$r.password) -AsPlainText -Force
    $credential=New-Object Management.Automation.PSCredential("$AccountDomain\cehshare",$password)
    $r.password=$null
}else{$credential=Get-Credential -UserName "$AccountDomain\cehshare" -Message 'Read-only CEH tools share'}
$root="\\$Server\CEH-Tools"
$localPath="$DriveLetter`:"
$existing=@(Get-SmbMapping -LocalPath $localPath -ErrorAction SilentlyContinue)
$global=@(Get-SmbGlobalMapping -LocalPath $localPath -ErrorAction SilentlyContinue)
foreach($mapping in @($existing)+@($global)){
    if($mapping.RemotePath -ine $root){throw 'Drive letter is mapped elsewhere; refusing to replace it.'}
}
$disk=Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$localPath'" -ErrorAction SilentlyContinue
if($disk -and $disk.DriveType -ne 4){throw 'Drive letter belongs to a local/removable volume.'}
# Some Windows versions include global entries in Get-SmbMapping too. Remove
# the global mapping first; system error 2250 means that connection is absent.
if($global.Count){
    try{Remove-SmbGlobalMapping -LocalPath $localPath -Force}
    catch{if($_.FullyQualifiedErrorId -notmatch 'Windows System Error 2250,'){throw}}
}
$existing=@(Get-SmbMapping -LocalPath $localPath -ErrorAction SilentlyContinue)
if($existing.Count){
    try{Remove-SmbMapping -LocalPath $localPath -Force -UpdateProfile}
    catch{if($_.FullyQualifiedErrorId -notmatch 'Windows System Error 2250,'){throw}}
}
New-SmbGlobalMapping -LocalPath $localPath -RemotePath $root -Credential $credential -Persistent $true -RequirePrivacy $true | Out-Null
$driveRoot="$DriveLetter`:\"
$dirs=[IO.Directory]::GetDirectories($driveRoot)
if($dirs.Count -ne 20){throw "Expected 20 module/prerequisite folders; found $($dirs.Count)."}
$test=Join-Path $driveRoot ('.ceh-write-test-'+[guid]::NewGuid().ToString('N'))
$denied=$false
try{[IO.File]::WriteAllText($test,'read-only test')}catch [UnauthorizedAccessException]{$denied=$true}
if(-not $denied){if(Test-Path -LiteralPath $test){Remove-Item -LiteralPath $test -Force};throw 'Share unexpectedly allowed a write.'}
Write-Host "PASS: $DriveLetter`: mounted machine-wide to $root; 20 folders readable; file creation denied."
Write-Host 'The persistent encrypted SMB drive is available across desktop and SSH sessions; Windows retains its connection credential.'
$credential=$null
if($password){$password.Dispose()}
