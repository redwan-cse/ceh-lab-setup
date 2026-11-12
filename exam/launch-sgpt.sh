#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python="$root/venv/bin/python"
if [[ ! -x "$python" ]] || ! "$python" -c 'import sys' >/dev/null 2>&1; then
  echo 'The private ShellGPT Python is missing or damaged. Running the setup prerequisite check.' >&2
  bash "$root/setup-exam.sh" --no-key-prompt
fi
extra=()
for arg in "$@"; do
  case "${arg,,}" in 'init the machine'|'initialize the machine'|'init machine'|'initialize machine'|--init-lab) extra=(--for-init);; esac
done
"$python" "$root/preflight.py" "${extra[@]}"
exec "$python" "$root/exam_runtime.py" "$@"
