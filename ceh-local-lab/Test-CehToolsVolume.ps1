<# Read-only mounted-drive checks. Run in a fresh session after configuration. #>
[CmdletBinding()]
param([ValidatePattern('^[D-Z]$')][string]$DriveLetter='T',[string]$Server='10.10.10.22',[switch]$DesktopCheck,[string]$OutputPath)
$ErrorActionPreference='Stop'
try {
$root="\\$Server\CEH-Tools"
$mapping=Get-SmbGlobalMapping -LocalPath "$DriveLetter`:" -ErrorAction SilentlyContinue
if(-not $mapping -or $mapping.RemotePath -ine $root){throw 'Expected machine-wide SMB volume is missing.'}
if(-not $mapping.RequirePrivacy){throw 'SMB encryption is not required by this mapping.'}
$driveRoot="$DriveLetter`:\"
$folders=[IO.Directory]::GetDirectories($driveRoot)
if($folders.Count -ne 20){throw "Expected 20 folders on $driveRoot; found $($folders.Count)."}
$manifest=Join-Path $driveRoot '.ceh-library-manifest.json'
if(-not [IO.File]::Exists($manifest)){throw 'Library manifest not readable through mounted drive.'}
if([IO.File]::ReadAllText($manifest).Length -eq 0){throw 'Library manifest is empty.'}
$desktopEntry=$null
if($DesktopCheck){
    if([Diagnostics.Process]::GetCurrentProcess().SessionId -eq 0){throw 'Desktop check must run in an interactive user session.'}
    $shell=New-Object -ComObject Shell.Application
    $desktopEntry=@($shell.Namespace(17).Items() | Where-Object {$_.Path -ieq $driveRoot})
    if($desktopEntry.Count -ne 1){throw 'Mounted drive is missing from the desktop This PC namespace.'}
}
$result=[ordered]@{Success=$true;Computer=$env:COMPUTERNAME;User=[Security.Principal.WindowsIdentity]::GetCurrent().Name;
    SessionId=[Diagnostics.Process]::GetCurrentProcess().SessionId;Drive=$driveRoot;
    RemotePath=$mapping.RemotePath;Status=[string]$mapping.Status;
    RequirePrivacy=$mapping.RequirePrivacy;Folders=$folders.Count;DesktopThisPC=if($DesktopCheck){$desktopEntry[0].Name}else{$null}}|ConvertTo-Json -Compress
if($OutputPath){[IO.File]::WriteAllText($OutputPath,$result,(New-Object Text.UTF8Encoding($false)))}
$result
} catch {
    if($OutputPath){
        $failure=[ordered]@{Success=$false;Computer=$env:COMPUTERNAME;SessionId=[Diagnostics.Process]::GetCurrentProcess().SessionId;Error=$_.Exception.Message}|ConvertTo-Json -Compress
        [IO.File]::WriteAllText($OutputPath,$failure,(New-Object Text.UTF8Encoding($false)))
    }
    throw
}
