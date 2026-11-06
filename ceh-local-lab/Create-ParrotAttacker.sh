#!/usr/bin/env bash
# Local Parrot account setup. Password is entered interactively, never stored.
# Usage: bash Create-ParrotAttacker.sh /path/to/host-public-key.pub
# Rerunning prompts to reset attacker's password; this is not a daily-use script.
set -euo pipefail
umask 077
[[ $# == 1 && -f "$1" ]] || { echo 'Provide one SSH PUBLIC key file.' >&2; exit 1; }
public_key="$(tr -d '\r' < "$1")"
pattern='^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521))[[:space:]]+[A-Za-z0-9+/]+={0,3}([[:space:]].*)?$'
[[ "$public_key" =~ $pattern && "$public_key" != *$'\n'* ]] || { echo 'Expected one public key, never a private key.' >&2; exit 1; }
ssh-keygen -l -f "$1"
getent group sudo >/dev/null || { echo 'This helper expects the Debian/Parrot sudo group.' >&2; exit 1; }
if [[ "$(id -u)" == 0 ]]; then admin=(); else sudo -v; admin=(sudo); fi
if getent passwd attacker >/dev/null; then
    [[ "$(id -u attacker)" != 0 ]] || { echo 'Refusing to modify a UID 0 account.' >&2; exit 1; }
    [[ "$(getent passwd attacker | cut -d: -f6)" == /home/attacker ]] || { echo 'Unexpected attacker home; inspect manually.' >&2; exit 1; }
else
    "${admin[@]}" useradd --create-home --user-group --shell /bin/bash attacker
fi
"${admin[@]}" usermod -aG sudo --shell /bin/bash attacker
"${admin[@]}" passwd attacker
for path in /home/attacker /home/attacker/.ssh /home/attacker/.ssh/authorized_keys; do
    if "${admin[@]}" test -L "$path"; then echo "Refusing redirected path: $path" >&2; exit 1; fi
done
group="$(id -gn attacker)"
"${admin[@]}" install -d -m 700 -o attacker -g "$group" /home/attacker/.ssh
if ! "${admin[@]}" grep -qxF -- "$public_key" /home/attacker/.ssh/authorized_keys 2>/dev/null; then
    printf '%s\n' "$public_key" | "${admin[@]}" tee -a /home/attacker/.ssh/authorized_keys >/dev/null
fi
"${admin[@]}" chown attacker:"$group" /home/attacker/.ssh/authorized_keys
"${admin[@]}" chmod 600 /home/attacker/.ssh/authorized_keys
"${admin[@]}" /usr/sbin/sshd -t
id attacker
echo 'Attacker sudo user and public-key access configured. Existing SSH authentication policy was not changed.'
