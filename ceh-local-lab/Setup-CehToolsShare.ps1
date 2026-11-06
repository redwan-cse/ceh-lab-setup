<# Run on the host with SSH key access to the lab server. Never stores a password. #>
[CmdletBinding()]
param(
    [string]$SourcePath = 'D:\CEHv13\CEHv13_Tools_26-Nov-2025',
    [string]$Server = '10.10.10.22',
    [string]$UserName = 'Administrator',
    [ValidatePattern('^[A-Za-z]:\\CEH-Tools(?:-[A-Za-z0-9_-]+)?$')][string]$LibraryPath = 'C:\CEH-Tools',
    [string]$LabSubnet = '10.10.10.0/24',
    [switch]$PrepareOnly,
    [switch]$AllowLabDefenderExclusions
)
$ErrorActionPreference = 'Stop'
if ($Server -notmatch '^[A-Za-z0-9_.-]+$' -or $UserName -notmatch '^[A-Za-z0-9_.-]+$') { throw 'Invalid SSH target.' }
if (-not (Test-Path -LiteralPath $SourcePath -PathType Container)) { throw 'Source folder not found.' }
$python = (Get-Command python.exe -ErrorAction Stop).Source
& $python -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ is required"'
if ($LASTEXITCODE -ne 0) { throw 'Python prerequisite failed.' }
$extra=@()
if($AllowLabDefenderExclusions){$extra+='--allow-defender-exclusions'}
& $python (Join-Path $PSScriptRoot 'ceh_tools_library.py') deploy --source $SourcePath --server $Server --user $UserName --destination $LibraryPath @extra
if ($LASTEXITCODE -ne 0) { throw 'Transfer/extraction verification failed; share was not published.' }
if ($PrepareOnly) { Write-Host 'Verified library ready. Rerun without -PrepareOnly to configure its share.'; return }
$secret = Read-Host 'Password for the dedicated cehshare account (hidden)' -AsSecureString
if ($secret.Length -eq 0) { throw 'A nonempty share password is required.' }
$pointer = [IntPtr]::Zero
try {
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    $request = @{
        password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
        library = $LibraryPath; server = $Server; subnet = $LabSubnet
    }
    $json = $request | ConvertTo-Json -Compress
    # Send the credential over encrypted SSH stdin, never as a command argument/file.
    $json | & ssh -o BatchMode=yes "$UserName@$Server" 'powershell -NoProfile -ExecutionPolicy Bypass -File ceh-tools-deployment/Publish-CehToolsShare.ps1'
    if ($LASTEXITCODE -ne 0) { throw 'SMB publication failed; the verified library remains available for inspection.' }
} finally {
    if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    $json = $null; $request = $null
    $secret.Dispose()
}
