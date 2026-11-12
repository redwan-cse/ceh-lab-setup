#!/usr/bin/env bash
# Private fallback for old Linux distributions. Never modifies system Python or PATH.
# stdout is exclusively the validated Python path; diagnostics go to stderr.
set -euo pipefail

die() { printf 'Private Python: %s\n' "$*" >&2; exit 1; }
if [[ $# != 1 || ( $1 != --approved && $1 != --find ) ]]; then
    die 'Explicit approval required: run this helper with --approved after consent, or --find for read-only lookup.'
fi
mode=$1
[[ $(uname -s) == Linux ]] || die 'Unsupported OS; this helper supports Linux only.'
case "$(uname -m)" in
    x86_64|amd64)
        arch=x86_64
        archive_sha=287491da03f2a785c70fa75b13e1f849918c2f2b5415fe84876b8214eeb792f9 ;;
    aarch64|arm64)
        arch=aarch64
        archive_sha=2d3ec076a0c4c0e8250bb6418c44080828b544f1a3be0b6e46adf9fb6923de45 ;;
    *) die 'Unsupported Linux architecture; supported: x86_64 and aarch64.' ;;
esac
[[ -n ${HOME:-} && -d $HOME && $HOME == /* && $HOME != *$'\n'* ]] || die 'HOME must be an existing absolute directory.'
home_dir=$(cd -- "$HOME" && pwd -P)
root="$home_dir/.local/share/shellgpt-python"

# Refuse redirected storage before any writes. HOME itself may have a normal alias;
# every component below its canonical location must be a real directory.
check_dir() {
    [[ ! -L $1 ]] || die "Refusing symlink directory: $1"
    [[ ! -e $1 || ( -d $1 && -O $1 ) ]] || die "Directory is not owned by this user: $1"
}
for directory in "$home_dir/.local" "$home_dir/.local/share" "$root" "$root/python"; do
    check_dir "$directory"
done

validate_python() {
    local candidate=$1 resolved
    [[ -x $candidate ]] || return 1
    resolved=$(readlink -f -- "$candidate") || return 1
    [[ $resolved == "$root/python/"* ]] || return 1
    # -I ignores PYTHONPATH, PYTHONHOME, user site packages, and the current directory.
    "$candidate" -I -c 'import sys, ssl, venv, ensurepip; assert sys.version_info >= (3, 10); assert sys.version_info[:2] == (3, 12)' >/dev/null 2>&1
}

# Read-only lookup also works when the system interpreter is still Python 3.8.
for candidate in "$root/python"/cpython-3.12*/bin/python3.12; do
    if validate_python "$candidate"; then
        printf '%s\n' "$candidate"
        exit 0
    fi
done
[[ $mode != --find ]] || die "No validated private Python 3.12 found in $root/python."

for command_name in mkdir chmod mktemp rm mv tar sha256sum readlink; do
    command -v "$command_name" >/dev/null || die "Required command unavailable: $command_name"
done
if command -v curl >/dev/null; then downloader=curl
elif command -v wget >/dev/null; then downloader=wget
else die 'Install curl or wget using your normal system maintenance process, then retry.'
fi

umask 077
mkdir -p -- "$home_dir/.local/share"
mkdir -p -- "$root"
chmod 700 -- "$root"
for directory in "$root/tools" "$root/tools/uv" "$root/tools/uv/0.13.7" "$root/python" "$root/bin" "$root/cache" "$root/logs"; do
    check_dir "$directory"
    mkdir -p -- "$directory"
    chmod 700 -- "$directory"
done
stage=$(mktemp -d "$root/.bootstrap.XXXXXXXX")
[[ -d $stage && ! -L $stage && -O $stage && $stage == "$root/.bootstrap."* ]] || die 'Could not create private staging directory.'
log=''
cleanup() {
    local status=$?
    if [[ -n ${stage:-} && $stage == "$root/.bootstrap."* && -d $stage && ! -L $stage && -O $stage ]]; then
        rm -rf -- "$stage"
    fi
    if [[ $status != 0 && -n $log ]]; then printf 'Private Python: diagnostic log: %s\n' "$log" >&2; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
log=$(mktemp "$root/logs/bootstrap.XXXXXXXX.log")

version=0.13.7
target="uv-$arch-unknown-linux-musl"
tool_dir="$root/tools/uv/$version"
archive="$tool_dir/$target.tar.gz"
uv="$tool_dir/uv"
for file in "$archive" "$uv"; do
    [[ ! -L $file && ( ! -e $file || ( -f $file && -O $file ) ) ]] || die "Refusing unsafe tool cache: $file"
done
check_archive() {
    local actual
    [[ -f $1 ]] || return 1
    actual=$(sha256sum -- "$1") || return 1
    [[ ${actual%% *} == "$archive_sha" ]]
}
if ! check_archive "$archive"; then
    printf 'Private Python: downloading pinned uv %s for %s.\n' "$version" "$arch" >&2
    url="https://github.com/astral-sh/uv/releases/download/$version/$target.tar.gz"
    if [[ $downloader == curl ]]; then
        # --disable must be first, to ignore ~/.curlrc (including insecure options).
        curl --disable --fail --location --proto '=https' --proto-redir '=https' \
            --connect-timeout 20 --max-time 180 --retry 2 --retry-delay 1 \
            --silent --show-error --output "$stage/uv.tar.gz" "$url" >>"$log" 2>&1 \
            || die 'uv download failed; check network and TLS certificate trust, then retry.'
    else
        wget --no-config --https-only --secure-protocol=TLSv1_2 --timeout=60 --tries=3 \
            --output-document="$stage/uv.tar.gz" "$url" >>"$log" 2>&1 \
            || die 'uv download failed; check network and TLS certificate trust, then retry.'
    fi
    check_archive "$stage/uv.tar.gz" || die 'uv archive checksum validation failed; no downloaded program was executed.'
    mv -- "$stage/uv.tar.gz" "$archive"
fi
# These SHA256 pins came from the official release's .tar.gz.sha256 assets.
# Extract only the exact executable member, so archive paths/links are never materialized.
# Re-extract on every use: an edited cached executable is never trusted or executed.
unset TAR_OPTIONS
tar -xOf "$archive" "$target/uv" >"$stage/uv" 2>>"$log" || die 'Unable to extract verified uv archive.'
[[ -s $stage/uv ]] || die 'Verified uv archive contains an empty executable.'
chmod 700 -- "$stage/uv"
mv -- "$stage/uv" "$uv"

# Ignore exported uv settings, particularly mirrors, custom download metadata,
# insecure-host overrides, config paths, and settings that redirect private storage.
for setting in ${!UV_@}; do unset "$setting"; done
unset PYTHONHOME PYTHONPATH PYTHONSTARTUP VIRTUAL_ENV CONDA_PREFIX
export UV_PYTHON_INSTALL_DIR="$root/python" UV_PYTHON_BIN_DIR="$root/bin"
export UV_CACHE_DIR="$root/cache" UV_NO_CONFIG=1 UV_NO_PROGRESS=1
export UV_HTTP_RETRIES=2 UV_HTTP_TIMEOUT=60
export TMPDIR="$stage"
[[ $("$uv" --version 2>>"$log") == 'uv 0.13.7'* ]] || die 'Verified uv failed its version check.'
printf 'Private Python: installing Python 3.12 into %s.\n' "$root/python" >&2
"$uv" --no-config python install 3.12 --install-dir "$root/python" --no-bin >>"$log" 2>&1 \
    || die 'Python download/install failed; see the private diagnostic log. System Python was not changed.'
candidate=$("$uv" --no-config python find --managed-python --no-python-downloads 3.12 2>>"$log") \
    || die 'Installed Python could not be located.'
validate_python "$candidate" || die 'Installed Python failed validation (Python 3.12, ssl, venv, ensurepip required).'
printf '%s\n' "$candidate"
