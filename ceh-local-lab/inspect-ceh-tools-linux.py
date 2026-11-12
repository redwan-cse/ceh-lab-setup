#!/usr/bin/env python3
"""Read-only CEH command/package/library inventory; never starts a CEH tool.

Uses only the standard library and trusted /usr/bin/dpkg-query. It reads package
metadata, executable metadata, and filenames under the supplied library root.
It does not read home/config files, inspect credentials, scan hosts, extract
archives, install packages, or test tool functionality. JSON goes to stdout.
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess


# Display name, commands, Debian packages, additional installed paths.
TOOLS = [
    ("Nmap", ["nmap"], ["nmap"], []),
    ("Dig", ["dig"], ["bind9-dnsutils"], []),
    ("Nslookup", ["nslookup"], ["bind9-dnsutils"], []),
    ("WhatWeb", ["whatweb"], ["whatweb"], []),
    ("Telnet", ["telnet"], ["inetutils-telnet", "telnet"], []),
    ("Curl", ["curl"], ["curl"], []),
    ("Wget", ["wget"], ["wget"], []),
    ("LDAPSearch", ["ldapsearch"], ["ldap-utils"], []),
    ("SMBClient", ["smbclient"], ["smbclient"], []),
    ("SMBMap", ["smbmap"], ["smbmap"], []),
    ("Gobuster", ["gobuster"], ["gobuster"], []),
    ("John", ["john"], ["john"], ["/usr/sbin/john"]),
    ("Hydra", ["hydra"], ["hydra"], []),
    ("Hashcat", ["hashcat"], ["hashcat"], []),
    ("WPScan", ["wpscan"], ["wpscan"], []),
    ("SQLmap", ["sqlmap"], ["sqlmap"], []),
    ("Wireshark", ["wireshark"], ["wireshark"], []),
    ("TShark", ["tshark"], ["tshark"], []),
    ("Tcpdump", ["tcpdump"], ["tcpdump"], []),
    ("Yersinia", ["yersinia"], ["yersinia"], ["/usr/sbin/yersinia"]),
    ("Steghide", ["steghide"], ["steghide"], []),
    ("Zsteg", ["zsteg"], ["zsteg"], []),
    ("OpenStego", ["openstego"], ["openstego"], []),
    ("SNOW", ["snow", "stegsnow"], ["snow", "stegsnow"], []),
    ("Binwalk", ["binwalk"], ["binwalk"], []),
    ("VeraCrypt", ["veracrypt"], ["veracrypt"], []),
    ("VeraCrypt2John", ["veracrypt2john", "veracrypt2john.py"], [],
     ["/usr/share/john/veracrypt2john.py", "/usr/share/john/veracrypt2john"]),
    ("Ghidra", ["ghidra"], ["ghidra"], []),
    ("Radare2", ["radare2", "r2"], ["radare2"], []),
    ("BinText", ["bintext"], [], []),
    ("Strings", ["strings"], ["binutils"], []),
    ("File", ["file"], ["file"], []),
    ("ADB", ["adb"], ["adb"], []),
    ("PhoneSploit", ["phonesploit", "phonesploit-pro"], [], []),
    ("APKTool", ["apktool"], ["apktool"], []),
    ("Aircrack-ng", ["aircrack-ng"], ["aircrack-ng"], []),
    ("PowerShell", ["pwsh", "powershell"], ["powershell"], []),
    ("OpenSSH", ["ssh"], ["openssh-client"], []),
    ("SHA1SUM", ["sha1sum"], ["coreutils"], []),
    ("SHA224SUM", ["sha224sum"], ["coreutils"], []),
    ("SHA256SUM", ["sha256sum"], ["coreutils"], []),
    ("Base64", ["base64"], ["coreutils"], []),
    ("Grep", ["grep"], ["grep"], []),
    ("Find", ["find"], ["findutils"], []),
    ("Awk", ["awk"], ["mawk", "gawk"], []),
    ("Sed", ["sed"], ["sed"], []),
]


def executable_metadata(path):
    """Metadata only. A discovered path is never executed."""
    try:
        resolved = Path(path).resolve(strict=True)
        info = resolved.stat()
        return {"path": str(path), "resolved": str(resolved),
                "executable": os.access(path, os.X_OK),
                "root_owned": info.st_uid == 0,
                "group_world_writable": bool(info.st_mode & 0o022),
                "regular_file": stat.S_ISREG(info.st_mode)}
    except OSError:
        return None


def packages():
    query = executable_metadata("/usr/bin/dpkg-query")
    if not query or not query["root_owned"] or query["group_world_writable"]:
        return {}, "Trusted /usr/bin/dpkg-query unavailable"
    try:
        result = subprocess.run(
            ["/usr/bin/dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${db:Status-Status}\n"],
            check=True, capture_output=True, text=True, timeout=30,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
        rows = {}
        for line in result.stdout.splitlines():
            name, version, status_value = line.split("\t", 2)
            if status_value == "installed":
                rows[name.split(":", 1)[0]] = version
        return rows, None
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        return {}, str(error)


def library_index(root, max_depth, max_entries):
    """Bounded filename walk without symlink traversal or file-content reads."""
    rows, errors, truncated = [], [], False
    def onerror(error):
        if len(errors) < 10:
            errors.append(str(error))
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
        dirs[:] = sorted(d for d in dirs if d not in {".git", "node_modules", "__pycache__"})
        relative = Path(directory).relative_to(root)
        if len(relative.parts) >= max_depth:
            dirs[:] = []
        for name in sorted(dirs + files):
            rows.append((name, str(Path(directory) / name), name in dirs))
            if len(rows) >= max_entries:
                truncated = True
                return rows, errors, truncated
    return rows, errors, truncated


def library_matches(name, rows):
    # Match product filenames/folders, not incidental code references in files.
    if name in {"Telnet", "PowerShell"}:
        # Cowrie protocol modules/SET payload folders are not these clients.
        return []
    tokens = {name.lower(), name.lower().replace("-", "")}
    if name == "PhoneSploit":
        tokens.add("phonesploit-pro")
    result = []
    for leaf, path, is_dir in rows:
        lower = leaf.lower()
        if not is_dir and lower.endswith((".yml", ".yaml", ".rules")):
            continue
        if any(re.match(r"^" + re.escape(t) + r"(?:$|[_. -]|\d)", lower) for t in tokens):
            result.append({"path": path, "directory": is_dir})
    return sorted(result, key=lambda item: (not item["directory"], len(item["path"])))[:5]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", default="/mnt/ceh-tools")
    parser.add_argument("--max-depth", type=int, default=7)
    parser.add_argument("--max-entries", type=int, default=100000)
    args = parser.parse_args()
    if args.max_depth < 0 or args.max_entries < 1:
        parser.error("max-depth must be nonnegative and max-entries positive")
    installed, package_error = packages()
    rows, errors, truncated = library_index(Path(args.library), args.max_depth, args.max_entries)
    tools = []
    for name, commands, package_names, extra_paths in TOOLS:
        paths = [executable_metadata(p) for c in commands if (p := shutil.which(c))]
        paths = [p for p in paths if p]
        alternatives = [p for s in extra_paths if (p := executable_metadata(s))]
        versions = {p: installed[p] for p in package_names if p in installed}
        matches = library_matches(name, rows)
        if paths:
            status_value = "path_ready"
        elif any(p["executable"] for p in alternatives):
            status_value = "verified_path"
        elif matches:
            # Windows executables/installers and source trees remain unverified.
            archive_suffixes = (".zip", ".7z", ".rar", ".tar", ".tar.gz", ".tgz")
            status_value = "archive_only" if all(not m["directory"] and m["path"].lower().endswith(archive_suffixes) for m in matches) else "unverified"
        else:
            status_value = "unverified" if versions or alternatives else "missing"
        tools.append({"tool": name, "status": status_value, "paths": paths,
                      "verified_other_paths": alternatives, "package_versions": versions,
                      "library_filename_evidence": matches})
    print(json.dumps({"captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      "account_uid": os.getuid(), "library": args.library,
                      "library_entries_examined": len(rows), "library_walk_truncated": truncated,
                      "library_walk_errors": errors, "package_query_error": package_error,
                      "method": "metadata only; no CEH executables launched; no network scans",
                      "tools": tools}, indent=2))


if __name__ == "__main__":
    main()
