#!/usr/bin/env bash
# Run as the user who will use sgpt, not as root. No API keys in this file.
set -euo pipefail
umask 077
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
for file in configure_shellgpt.py linux_command_guard.py test_linux_guard.py verify_shellgpt_parrot.py; do
    test -f "$script_dir/$file" || { echo "Missing setup file: $file" >&2; exit 1; }
done
if [[ "$(id -u)" == 0 ]]; then
    echo 'Run as your normal Linux user. sudo is used only for missing OS prerequisites.' >&2
    exit 1
fi
if ! command -v python3 >/dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv
fi
python3 -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required"'
install_root="$HOME/.local/share/shellgpt-stepfun"
venv="$install_root/venv"
if [[ -L "$install_root" || -L "$venv" ]]; then
    echo 'Refusing a redirected installation directory.' >&2
    exit 1
fi
mkdir -p -- "$install_root" "$HOME/.local/bin"
if [[ ! -x "$venv/bin/python" ]] || ! "$venv/bin/python" -m pip --version >/dev/null 2>&1; then
    if ! python3 -m venv "$venv"; then
        echo 'Installing the missing Debian/Parrot virtual-environment prerequisite...'
        sudo apt-get update
        sudo apt-get install -y python3-venv
        python3 -m venv "$venv"
    fi
fi
"$venv/bin/python" -m pip install --upgrade pip
"$venv/bin/python" -m pip install --no-cache-dir --force-reinstall 'shell-gpt==1.5.1' 'typer==0.16.0' 'click==8.1.8'
"$venv/bin/python" "$script_dir/configure_shellgpt.py"
"$venv/bin/python" -m unittest discover -s "$script_dir" -p 'test_*.py' -v
"$venv/bin/python" "$script_dir/verify_shellgpt_parrot.py" --offline
echo 'Setup complete. Reconnect SSH or start a new shell to refresh PATH.'
echo "API key: $HOME/.config/shell_gpt/.sgptrc (OPENAI_API_KEY=your-key)"
echo 'After saving a key, verify live: ~/.local/share/shellgpt-stepfun/venv/bin/python verify_shellgpt_parrot.py --live'
