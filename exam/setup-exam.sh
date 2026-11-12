#!/usr/bin/env bash
set -euo pipefail
[[ "$(id -u)" != 0 ]] || { echo 'Run as the normal user, not root.' >&2; exit 1; }
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
packages=()
command -v python3 >/dev/null || packages+=(python3)
if ! command -v python3 >/dev/null || ! python3 -c 'import ensurepip' >/dev/null 2>&1; then packages+=(python3-venv); fi
command -v ip >/dev/null || packages+=(iproute2)
private_python="$HOME/.local/share/shellgpt-exam/venv/bin/python"
app_ready=false
if [[ -x "$private_python" ]] && "$private_python" -c 'from importlib.metadata import version; assert all(version(n)==v for n,v in {"shell-gpt":"1.5.1","openai":"2.54.0","typer":"0.16.0","click":"8.1.8"}.items())' >/dev/null 2>&1; then app_ready=true; fi
if [[ ${#packages[@]} -gt 0 || "$app_ready" != true ]]; then
  printf 'Required setup: private ShellGPT 1.5.1 environment with pinned dependencies.\n'
  if [[ ${#packages[@]} -gt 0 ]]; then printf 'Missing OS prerequisites: %s\n' "${packages[*]}"; fi
  printf 'No OS upgrade, firewall, SSH, Defender, or network-setting changes.\n'
  if [[ ! -t 0 ]]; then echo 'Interactive approval required. Nothing installed.' >&2; exit 3; fi
  read -r -p 'Install these prerequisites now? [y/N] ' answer
  [[ "${answer,,}" == y || "${answer,,}" == yes ]] || { echo 'Cancelled; nothing installed.'; exit 3; }
fi
if [[ ${#packages[@]} -gt 0 ]]; then
  command -v apt-get >/dev/null || { echo 'Automatic prerequisite installation needs a Debian/Parrot apt-based system.' >&2; exit 3; }
  preview=$(LC_ALL=C apt-get --simulate install --no-upgrade --no-remove --no-install-recommends "${packages[@]}") || { echo 'Cannot resolve prerequisites; nothing installed.' >&2; exit 3; }
  while IFS= read -r line; do
    if [[ "$line" == Remv\ * || "$line" =~ ^Inst\ [^\ ]+\ \[ ]]; then
      echo 'Prerequisites would upgrade or remove existing packages; stopped for manual review.' >&2; exit 3
    fi
  done <<< "$preview"
  # No apt upgrade/update, no removal, and no recommended desktop packages.
  sudo apt-get install --no-upgrade --no-remove --no-install-recommends -y "${packages[@]}"
fi
exec python3 "$script_dir/setup_exam.py" --activate "$@"
