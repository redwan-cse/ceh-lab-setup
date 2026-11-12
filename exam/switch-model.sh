#!/usr/bin/env bash
# Select the provider used by the single sgpt command. Keys stay off command lines.
set -euo pipefail
if [[ $# -ne 1 ]]; then
    printf 'Usage: %s deepseek|stepfun\n' "$0" >&2
    exit 2
fi
case "$1" in
    deepseek) provider=openrouter-deepseek ;;
    stepfun) provider=stepfun ;;
    *) printf 'Choose deepseek or stepfun.\n' >&2; exit 2 ;;
esac
installed_root="$HOME/.local/share/shellgpt-exam"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$installed_root/setup_exam.py" ]]; then
    setup="$installed_root/setup_exam.py"
else
    setup="$script_dir/setup_exam.py"
fi
if [[ ! -f "$setup" ]]; then
    printf 'ShellGPT setup helper is missing. Keep this script with setup_exam.py or install the exam kit first.\n' >&2
    exit 1
fi
if [[ -x "$installed_root/venv/bin/python" ]]; then
    python="$installed_root/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    python="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    python="$(command -v python)"
else
    printf 'Python 3.10+ is required to switch providers. Run setup-exam.sh first.\n' >&2
    exit 1
fi
exec "$python" "$setup" --switch-provider --provider "$provider"
