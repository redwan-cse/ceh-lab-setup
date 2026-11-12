<#
.SYNOPSIS
Read-only Windows CEH command, uninstall-registry and course-library inventory.
.DESCRIPTION
Emits JSON. Does not launch discovered tools, install packages, modify settings,
read credentials, open archives or recursively search system/user drives.
Library files are matched from the existing bounded course manifest and then
checked with Get-Item (existence/length only; not integrity or runtime validation).
Missing means not found within these checks, not proof of absence from the disk.
#>
[CmdletBinding()]
param(
    [string[]]$LibraryRoots = @('C:\CEH-Tools', 'T:\'),
    [ValidateRange(1,100000)][int]$MaxManifestEntries = 50000,
    [ValidateRange(1,20)][int]$MaxEvidencePerTool = 5
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
# Tool|native executable/launcher names|library leaf regex|registry display regex
$specification = @'
Nmap|nmap.exe|^nmap(?:[- ].*)?\.exe$|^Nmap
Dig|dig.exe|^dig\.exe$|^BIND
Nslookup|nslookup.exe|^nslookup\.exe$|a^
WhatWeb|whatweb,whatweb.rb|^whatweb(?:\.rb)?$|^WhatWeb
Telnet|telnet.exe|^telnet\.exe$|a^
Curl|curl.exe|^curl(?:[- ].*)?\.exe$|^curl
Wget|wget.exe|^wget(?:[- ].*)?\.exe$|^wget
LDAPSearch|ldapsearch.exe|^ldapsearch\.exe$|^OpenLDAP
SMBClient|smbclient.exe|^smbclient(?:\.exe|\.py)?$|^Samba
SMBMap|smbmap.exe,smbmap.py|^smbmap(?:\.py|\.exe)?$|^SMBMap
Gobuster|gobuster.exe|^gobuster(?:\.exe)?$|^Gobuster
John|john.exe|^john(?:-.*)?\.exe$|^John the Ripper
Hydra|hydra.exe|^hydra\.exe$|^Hydra
Hashcat|hashcat.exe|^hashcat(?:64|32)?\.exe$|^Hashcat
L0phtCrack|lc7.exe|^(?:lc7|lc7setup.*|l0phtcrack.*)\.exe$|L0phtCrack
WPScan|wpscan,wpscan.rb|^wpscan(?:\.rb)?$|^WPScan
SQLmap|sqlmap.exe,sqlmap.py|^sqlmap\.py$|^sqlmap
Wireshark|wireshark.exe|^wireshark(?:[- ].*)?\.exe$|^Wireshark
TShark|tshark.exe|^tshark\.exe$|^Wireshark
Tcpdump|tcpdump.exe,windump.exe|^(?:tcpdump|windump)\.exe$|^(?:tcpdump|WinDump)
Yersinia|yersinia.exe|^yersinia(?:\.exe)?$|^Yersinia
Steghide|steghide.exe|^steghide\.exe$|^Steghide
Zsteg|zsteg,zsteg.rb|^zsteg(?:\.rb)?$|^Zsteg
OpenStego|openstego.bat,openstego.exe|^(?:(?:setup-)?openstego.*\.(?:exe|jar|bat))$|^OpenStego
SNOW|snow.exe,stegsnow.exe|^(?:snow|stegsnow)\.exe$|^SNOW
Binwalk|binwalk.exe,binwalk|^binwalk(?:\.py|\.exe)?$|^Binwalk
VeraCrypt|veracrypt.exe|^veracrypt(?:[- ].*)?\.exe$|^VeraCrypt
VeraCrypt2John|veracrypt2john.py|^veracrypt2john\.(?:py|pl|exe)$|a^
CrypTool|cryptool.exe,cryptool2.exe|^(?:setupcryptool.*|cryptool.*)\.exe$|^CrypTool
BCTextEncoder|bctextencoder.exe|^bctextencoder\.exe$|^BCTextEncoder
AES-Tool|aes-tool.exe,aestool.exe|^(?:aes[-_ ]?tool|aes)\.(?:exe|jar)$|^AES[- ]?Tool
7-Zip|7z.exe,7za.exe|^7z(?:a|g)?\.exe$|^7-Zip
Ghidra|ghidraRun.bat|^ghidraRun\.bat$|^Ghidra
Radare2|radare2.exe,r2.exe|^(?:radare2|r2)\.exe$|^Radare
BinText|bintext.exe|^bintext\.exe$|^BinText
Strings|strings.exe,strings64.exe|^strings(?:64|64a)?\.exe$|a^
File|file.exe|^file\.exe$|a^
ADB|adb.exe|^adb\.exe$|^Android.*(?:SDK|Platform)
PhoneSploit|phonesploit.py,phonesploitpro.py|^phonesploit(?:pro)?\.py$|^PhoneSploit
APKTool|apktool.bat,apktool.jar|^apktool(?:[-_].*)?\.(?:jar|bat)$|^APKTool
Aircrack-ng|aircrack-ng.exe|^aircrack-ng\.exe$|^Aircrack
PowerShell|powershell.exe,pwsh.exe|^pwsh\.exe$|^PowerShell
OpenSSH|ssh.exe|^ssh\.exe$|^OpenSSH
SHA1SUM|sha1sum.exe|^sha1sum\.exe$|a^
SHA224SUM|sha224sum.exe|^sha224sum\.exe$|a^
SHA256SUM|sha256sum.exe|^sha256sum\.exe$|a^
Base64|base64.exe|^base64\.exe$|a^
Grep|grep.exe|^grep\.exe$|a^
Find|find.exe|^find\.exe$|a^
Awk|awk.exe,gawk.exe|^(?:g?awk)\.exe$|a^
Sed|sed.exe|^sed\.exe$|a^
'@
$specs = @($specification -split '\r?\n' | ForEach-Object {
    # The regex columns themselves contain alternation pipes.
    $parts = [regex]::Match($_, '^([^|]+)\|([^|]+)\|(.+)\|(\^.*|L0phtCrack|a\^)$')
    if (-not $parts.Success) {throw 'Invalid tool specification'}
    [pscustomobject]@{Name=$parts.Groups[1].Value; Commands=@($parts.Groups[2].Value -split ',');
        Leaf=$parts.Groups[3].Value; Registry=$parts.Groups[4].Value}
})
$registry = @()
foreach ($key in @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*')) {
    $registry += @(Get-ItemProperty -Path $key -ErrorAction SilentlyContinue |
        Where-Object {$_.DisplayName} | Select-Object DisplayName,DisplayVersion,InstallLocation)
}
$library = @()
$libraryChecks = @()
$combinedLeafPattern = '(?:' + (($specs | ForEach-Object {$_.Leaf}) -join ')|(?:') + ')'
foreach ($root in $LibraryRoots) {
    try {
        $marker = Join-Path $root '.ceh-library-manifest.json'
        $item = Get-Item -LiteralPath $marker -ErrorAction Stop
        if ($item.Length -gt 16777216) {throw 'Manifest exceeds 16 MiB limit'}
        $manifest = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
        $entries = @($manifest.archives | ForEach-Object {$_.files})
        if ($entries.Count -gt $MaxManifestEntries) {throw 'Manifest exceeds entry limit'}
        $libraryChecks += [pscustomobject]@{Root=$root;State='manifest-indexed';Entries=$entries.Count}
        foreach ($entry in $entries) {
            # Reject traversal/absolute manifest paths; never leave the selected library.
            if ($entry.path -match '(^[/\\]|:|(^|[/\\])\.\.([/\\]|$))') {continue}
            $leaf = ($entry.path -split '[/\\]')[-1]
            if ($leaf -match '\.(?:zip|7z|rar|tar|gz|bz2|xz)$' -or $leaf -match $combinedLeafPattern) {
                $library += [pscustomobject]@{Root=$root;Relative=$entry.path;Leaf=$leaf;ExpectedSize=$entry.size}
            }
        }
    } catch {
        $libraryChecks += [pscustomobject]@{Root=$root;State='unavailable';Reason=$_.Exception.Message}
    }
}
# Only these bounded application directories supplement PATH and registry evidence.
$knownDirectories = @(
    "$env:ProgramFiles\Nmap", "${env:ProgramFiles(x86)}\Nmap", "$env:ProgramFiles\Wireshark",
    "$env:ProgramFiles\7-Zip", "$env:ProgramFiles\VeraCrypt", "$env:ProgramFiles\OpenStego",
    "$env:ProgramFiles\CrypTool", "${env:ProgramFiles(x86)}\CrypTool",
    "$env:ProgramFiles\Git\usr\bin", 'C:\Tools', 'C:\Android\platform-tools', 'C:\platform-tools'
)
$knownFiles = @($knownDirectories | ForEach-Object {
    Get-ChildItem -LiteralPath $_ -File -ErrorAction SilentlyContinue | Select-Object -First 500
})
$results = foreach ($spec in $specs) {
    $commands = @($spec.Commands | ForEach-Object {
        Get-Command -Name $_ -CommandType Application,ExternalScript -All -ErrorAction SilentlyContinue |
            Select-Object Name,Source,CommandType
    })
    $registered = @($registry | Where-Object {$_.DisplayName -match $spec.Registry})
    $portable = @()
    $installers = @()
    $source = @()
    foreach ($candidate in @($library | Where-Object {$_.Leaf -match $spec.Leaf} | Select-Object -First $MaxEvidencePerTool)) {
        $path = Join-Path $candidate.Root ($candidate.Relative -replace '/', '\')
        try {
            $file = Get-Item -LiteralPath $path -ErrorAction Stop
            $evidence = [pscustomobject]@{Path=$file.FullName;Bytes=$file.Length;SizeMatchesManifest=($file.Length -eq $candidate.ExpectedSize)}
            if ($candidate.Leaf -match '(?i)setup|^wireshark-.*\.exe$') {$installers += $evidence}
            elseif ($candidate.Leaf -match '\.(?:exe|bat|cmd)$') {$portable += $evidence}
            else {$source += $evidence}
        } catch { $source += [pscustomobject]@{Path=$path;State='manifest entry; file inaccessible'} }
    }
    $known = @($knownFiles | Where-Object {$_.Name -match $spec.Leaf -and $_.Name -notmatch '(?i)setup'} |
        Select-Object -First $MaxEvidencePerTool FullName,Length)
    $token = '^(?:' + ([regex]::Escape($spec.Name) -replace '\\-', '[-_ ]?') + ')(?:[-_ .]|\d|$)'
    $archives = @($library | Where-Object {$_.Leaf -match '\.(?:zip|7z|rar|tar|gz|bz2|xz)$' -and $_.Leaf -match $token} |
        Select-Object -First $MaxEvidencePerTool | ForEach-Object {
            $path=Join-Path $_.Root ($_.Relative -replace '/', '\')
            if (Test-Path -LiteralPath $path -PathType Leaf -ErrorAction SilentlyContinue) {$path}
        })
    $states = @()
    if ($commands.Count) {$states += 'PATH-installed'}
    if ($registered.Count) {$states += 'registry-installed'}
    if ($portable.Count -or $known.Count) {$states += 'portable/extracted'}
    if ($source.Count) {$states += 'source/launcher-unverified'}
    if (-not $states.Count -and ($archives.Count -or $installers.Count)) {$states += 'archive/installer-only'}
    if (-not $states.Count) {$states += 'missing-in-audited-scope'}
    [pscustomobject]@{Tool=$spec.Name;Status=$states;Commands=$commands;Registry=$registered;
        KnownFiles=$known;Extracted=$portable;Source=$source;Installers=$installers;Archives=$archives}
}
$equivalents = @('Resolve-DnsName','Invoke-WebRequest','Get-FileHash','Select-String','Get-ChildItem','Select-Object','ForEach-Object') |
    ForEach-Object {Get-Command -Name $_ -ErrorAction SilentlyContinue | Select-Object Name,Source,CommandType}
$aliases = @('curl','wget','find') | ForEach-Object {
    Get-Alias -Name $_ -ErrorAction SilentlyContinue | Select-Object Name,Definition
}
$dependencies = @('java.exe','python.exe','ruby.exe','perl.exe') | ForEach-Object {
    Get-Command -Name $_ -CommandType Application -ErrorAction SilentlyContinue | Select-Object Name,Source
}
[ordered]@{Computer=$env:COMPUTERNAME;User=$env:USERNAME;ObservedUtc=[DateTime]::UtcNow.ToString('o');
    PowerShell=$PSVersionTable.PSVersion.ToString();LibraryChecks=$libraryChecks;Tools=@($results);
    OsEquivalents=@($equivalents);Aliases=@($aliases);Dependencies=@($dependencies);
    Limits='Metadata only; no discovered executable launched; no archive extraction; no CRC/hash validation; bounded known directories and manifest only; missing is scope-limited.'} |
    ConvertTo-Json -Depth 9
