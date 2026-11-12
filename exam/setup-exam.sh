#!/usr/bin/env bash
set -euo pipefail
[[ "$(id -u)" != 0 ]] || { echo 'Run as the normal user, not root.' >&2; exit 1; }
if ! command -v python3 >/dev/null || ! python3 -c 'import ensurepip' 2>/dev/null; then
  sudo apt-get update
  sudo apt-get install -y python3 python3-venv
fi
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "$script_dir/setup_exam.py" --activate "$@"
