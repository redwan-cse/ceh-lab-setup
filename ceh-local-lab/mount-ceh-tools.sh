#!/usr/bin/env bash
# Parrot/Debian: read-only SMB3 mount. --persist stores a root-only SMB credential.
set -euo pipefail
server=10.10.10.22
domain=WIN-L4HLUP8AT8K
mountpoint=/mnt/ceh-tools
persist=false
case "${1:-}" in
  '') [[ $# == 0 ]] || exit 1 ;;
  --persist) [[ $# == 1 ]] || exit 1; persist=true ;;
  *) echo 'Usage: bash mount-ceh-tools.sh [--persist]' >&2; exit 1 ;;
esac
sudo -v
if ! command -v mount.cifs >/dev/null && [[ ! -x /usr/sbin/mount.cifs && ! -x /sbin/mount.cifs ]]; then
  sudo apt-get update
  sudo apt-get install -y cifs-utils
fi
[[ ! -L "$mountpoint" ]] || { echo 'Redirected mountpoint refused.' >&2; exit 1; }
sudo mkdir -p "$mountpoint"
mounted=false
if findmnt -rn -M "$mountpoint" >/dev/null; then
  mounted=true
  [[ "$(findmnt -rn -M "$mountpoint" -o SOURCE)" == "//$server/CEH-Tools" ]] || { echo 'Mountpoint is in use.' >&2; exit 1; }
  [[ "$(findmnt -rn -M "$mountpoint" -o FSTYPE)" == cifs ]] || { echo 'Expected CIFS mount.' >&2; exit 1; }
  existing_options=",$(findmnt -rn -M "$mountpoint" -o OPTIONS),"
  for required in ro seal nosuid nodev noexec vers=3.1.1; do
    [[ "$existing_options" == *,"$required",* ]] || { echo "Existing mount lacks $required; inspect/unmount it first." >&2; exit 1; }
  done
fi
  if "$persist"; then
    sudo test ! -L /etc/samba/ceh-tools || { echo 'Redirected credential directory refused.' >&2; exit 1; }
    sudo test ! -L /etc/samba/ceh-tools/credentials || { echo 'Redirected credentials refused.' >&2; exit 1; }
    sudo install -d -m 700 /etc/samba/ceh-tools
    read -r -s -p 'CEH share password (hidden): ' smb_password
    printf '\n'
    [[ -n "$smb_password" && "$smb_password" != *$'\r'* ]] || { echo 'Invalid password.' >&2; exit 1; }
    sudo install -m 600 /dev/null /etc/samba/ceh-tools/credentials
    printf 'username=cehshare\npassword=%s\ndomain=%s\n' "$smb_password" "$domain" | sudo tee /etc/samba/ceh-tools/credentials >/dev/null
    unset smb_password
    sudo python3 - <<'PY'
from pathlib import Path
path=Path('/etc/fstab')
text=path.read_text()
line='//10.10.10.22/CEH-Tools /mnt/ceh-tools cifs ro,vers=3.1.1,seal,nosuid,nodev,noexec,credentials=/etc/samba/ceh-tools/credentials,file_mode=0444,dir_mode=0555,_netdev,nofail,x-systemd.automount 0 0 # ceh-lab-setup tools\n'
for existing in text.splitlines():
    fields=existing.split()
    if len(fields)>1 and not existing.lstrip().startswith('#') and fields[1]=='/mnt/ceh-tools':
        if existing+'\n'!=line:
            raise SystemExit('Existing fstab mount conflicts; inspect manually.')
        break
else:
    backup=Path('/etc/fstab.ceh-tools.bak')
    if not backup.exists():
        backup.write_text(text)
    path.write_text(text.rstrip()+'\n'+line)
PY
    sudo systemctl daemon-reload
fi
if ! "$mounted"; then
  if "$persist"; then
    sudo mount "$mountpoint"
  else
    sudo mount -t cifs "//$server/CEH-Tools" "$mountpoint" -o "ro,vers=3.1.1,seal,nosuid,nodev,noexec,username=cehshare,domain=$domain,file_mode=0444,dir_mode=0555"
  fi
fi
findmnt "$mountpoint"
[[ "$(find "$mountpoint" -mindepth 1 -maxdepth 1 -type d | wc -l)" == 20 ]] || { echo 'Expected 20 folders.' >&2; exit 1; }
[[ ",$(findmnt -rn -M "$mountpoint" -o OPTIONS)," == *,ro,* ]] || { echo 'Mount is not read-only.' >&2; exit 1; }
echo 'PASS: 20 folders accessible through encrypted, read-only SMB3.'
