#!/usr/bin/env bash
# Reuse a compatible Python or bootstrap one privately; never replace OS Python.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

compatible_python() {
  "$1" -c 'import sys; assert sys.version_info >= (3,10); import ssl,venv,ensurepip' >/dev/null 2>&1
}

select_python() {
  local candidate resolved
  local candidates=("$HOME/.local/share/shellgpt-exam/venv/bin/python")
  if [[ -f "$script_dir/bootstrap-python-linux.sh" ]]; then
    local cached
    cached=$(bash "$script_dir/bootstrap-python-linux.sh" --find 2>/dev/null) || cached=''
    [[ -z "$cached" ]] || candidates+=("$cached")
  fi
  candidates+=(python3.12 python3.13 python3.14 python3.11 python3.10 python3)
  for candidate in "${candidates[@]}"; do
    resolved=$(command -v "$candidate" 2>/dev/null) || continue
    if compatible_python "$resolved"; then printf '%s\n' "$resolved"; return 0; fi
  done
  return 1
}

setup_exam_main() {
  [[ "$(id -u)" != 0 ]] || { echo 'Run as the normal user, not root.' >&2; return 1; }
  local python private_python app_ready answer preview line
  local packages=()
  python=$(select_python) || python=''
  command -v ip >/dev/null || packages+=(iproute2)
  private_python="$HOME/.local/share/shellgpt-exam/venv/bin/python"
  app_ready=false
  if [[ -x "$private_python" ]] && compatible_python "$private_python" && "$private_python" -c 'from importlib.metadata import version; assert all(version(n)==v for n,v in {"shell-gpt":"1.5.1","openai":"2.54.0","typer":"0.16.0","click":"8.1.8"}.items())' >/dev/null 2>&1; then app_ready=true; fi
  if [[ -z "$python" || ${#packages[@]} -gt 0 || "$app_ready" != true ]]; then
    printf 'Required setup: private ShellGPT 1.5.1 environment with pinned dependencies.\n'
    if [[ -z "$python" ]]; then
      printf 'No usable Python 3.10+ with SSL/venv/ensurepip found.\nApp-local Python 3.12 and a pinned, checksum-verified uv bootstrap will be downloaded.\n'
    fi
    if [[ ${#packages[@]} -gt 0 ]]; then printf 'Missing OS prerequisites: %s\n' "${packages[*]}"; fi
    printf 'System Python and repositories will remain unchanged. No OS upgrades/removals or network/security-setting changes.\n'
    if [[ ! -t 0 ]]; then echo 'Interactive approval required. Nothing installed.' >&2; return 3; fi
    read -r -p 'Install these prerequisites now? [y/N] ' answer
    [[ "${answer,,}" == y || "${answer,,}" == yes ]] || { echo 'Cancelled; nothing installed.'; return 3; }
  fi
  if [[ ${#packages[@]} -gt 0 ]]; then
    command -v apt-get >/dev/null || { echo 'Automatic iproute2 installation requires apt-get.' >&2; return 3; }
    preview=$(LC_ALL=C apt-get --simulate install --no-upgrade --no-remove --no-install-recommends "${packages[@]}") || { echo 'Cannot resolve iproute2; no task commands were run.' >&2; return 3; }
    while IFS= read -r line; do
      if [[ "$line" == Remv\ * || "$line" =~ ^Inst\ [^\ ]+\ \[ ]]; then
        echo 'Prerequisites would upgrade or remove existing packages; stopped for manual review.' >&2; return 3
      fi
    done <<< "$preview"
    if ! sudo apt-get install --no-upgrade --no-remove --no-install-recommends -y "${packages[@]}"; then
      echo 'iproute2 installation failed. Stale/EOL repositories may return 404. Repositories were not rewritten or upgraded; review this OS prerequisite manually.' >&2
      return 3
    fi
  fi
  if [[ -z "$python" ]]; then
    python=$(bash "$script_dir/bootstrap-python-linux.sh" --approved) || {
      echo 'Private Python download failed. Check GitHub access, TLS certificates and supported architecture; system Python was not changed.' >&2; return 3;
    }
  fi
  compatible_python "$python" || { echo 'Selected Python failed compatibility verification; setup stopped.' >&2; return 3; }
  exec "$python" "$script_dir/setup_exam.py" --activate "$@"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then setup_exam_main "$@"; fi
