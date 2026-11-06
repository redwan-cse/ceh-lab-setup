<# Run as the Windows account that will use T:. Credentials are prompted, never embedded. #>
[CmdletBinding()]
param([string]$Server='10.10.10.22',[string]$AccountDomain='WIN-L4HLUP8AT8K',[ValidatePattern('^[D-Z]$')][string]$DriveLetter='T',[switch]$FromStdin)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
if($Server -notmatch '^[A-Za-z0-9_.-]+$'){throw 'Invalid server.'}
if($FromStdin){
    $r=[Console]::In.ReadToEnd()|ConvertFrom-Json
    $password=ConvertTo-SecureString ([string]$r.password) -AsPlainText -Force
    $credential=New-Object Management.Automation.PSCredential("$AccountDomain\cehshare",$password)
    $r.password=$null
}else{$credential=Get-Credential -UserName "$AccountDomain\cehshare" -Message 'Read-only CEH tools share'}
$root="\\$Server\CEH-Tools"
$existing=Get-PSDrive -Name $DriveLetter -ErrorAction SilentlyContinue
if($existing -and $existing.DisplayRoot -ine $root -and $existing.Root -ine $root){throw 'Drive letter already used; choose another letter.'}
if(-not $existing){New-PSDrive -Name $DriveLetter -PSProvider FileSystem -Root $root -Credential $credential -Persist -Scope Global | Out-Null}
$dirs=@(Get-ChildItem -LiteralPath "$DriveLetter`:\" -Directory)
if($dirs.Count -ne 20){throw "Expected 20 module/prerequisite folders; found $($dirs.Count)."}
$test=Join-Path $root ('.ceh-write-test-'+[guid]::NewGuid().ToString('N'))
$denied=$false
try{[IO.File]::WriteAllText($test,'read-only test')}catch [UnauthorizedAccessException]{$denied=$true}
if(-not $denied){if(Test-Path -LiteralPath $test){Remove-Item -LiteralPath $test -Force};throw 'Share unexpectedly allowed a write.'}
Write-Host "PASS: $DriveLetter`: mapped to $root; 20 folders readable; file creation denied."
Write-Host 'Mapping is persistent. Windows may ask for the share password after sign-in; save it in Windows Credential Manager if desired.'
$credential=$null
if($password){$password.Dispose()}
