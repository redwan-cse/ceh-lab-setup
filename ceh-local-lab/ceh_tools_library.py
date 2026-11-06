"""Transfer and verify course archives; never execute their contents."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
import zipfile
import zlib

MARKER = '.ceh-library-manifest.json'


def safe_name(name):
    normalized = name.replace('\\', '/')
    if normalized.startswith('/'):
        raise ValueError('Absolute archive path refused')
    parts = tuple(normalized.rstrip('/').split('/'))
    for part in parts:
        if (part in ('', '.', '..') or re.search(r'[<>:"|?*\x00-\x1f]', part)
                or part.endswith((' ', '.'))
                or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', part, re.I)):
            raise ValueError('Unsafe or Windows-incompatible archive path')
    return parts


def long_path(path):
    path = Path(path).absolute()
    if os.name == 'nt' and not str(path).startswith('\\\\?\\'):
        return Path('\\\\?\\' + str(path))
    return path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inventory(source):
    archives = []
    seen = set()
    for path in sorted(Path(source).glob('*.zip')):
        if path.name.casefold() == 'cehv13 iso.zip':
            continue
        print('Checking archive: ' + path.name, file=sys.stderr, flush=True)
        total = 0
        files = []
        with zipfile.ZipFile(path) as archive:
            for entry in archive.infolist():
                parts = safe_name(entry.filename)
                if entry.flag_bits & 1 or stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError('Encrypted entries or symlinks require manual inspection')
                if entry.is_dir():
                    continue
                name = '/'.join(parts)
                if name.casefold() in seen:
                    raise ValueError('Duplicate/case-colliding archive file path')
                seen.add(name.casefold())
                total += entry.file_size
                files.append({'path': name, 'size': entry.file_size, 'crc': entry.CRC})
        archives.append({'name': path.name, 'sha256': digest(path),
                         'size': path.stat().st_size, 'expanded': total, 'files': files})
    if not archives:
        raise ValueError('No included ZIP archives found')
    return {'format': 1, 'archives': archives}


def verify_library(destination, manifest):
    root = long_path(destination)
    marker = root / MARKER
    if not marker.is_file() or root.is_symlink():
        return False
    if json.loads(marker.read_text(encoding='utf-8')) != manifest:
        return False
    for archive in manifest['archives']:
        for entry in archive['files']:
            path = root.joinpath(*safe_name(entry['path']))
            if path.is_symlink() or not path.is_file() or path.stat().st_size != entry['size']:
                return False
            crc = 0
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    crc = zlib.crc32(block, crc)
            if crc != entry['crc']:
                return False
    return True


def extract_library(source, destination, manifest):
    root = long_path(destination)
    if root.exists():
        raise FileExistsError('Destination exists; refusing to overwrite it')
    staging_parent = root.with_name(root.name + '-Staging')
    if staging_parent.is_symlink():
        raise ValueError('Redirected extraction staging directory refused')
    staging_parent.mkdir(exist_ok=True)
    staging = staging_parent / ('extract-' + uuid.uuid4().hex)
    required = sum(a['expanded'] for a in manifest['archives']) + 1024**3
    if shutil.disk_usage(root.parent).free < required:
        raise ValueError('Insufficient disk space for extraction plus 1 GiB headroom')
    staging.mkdir()
    # Failed extraction is preserved for inspection, never published as the share.
    for item in manifest['archives']:
        archive_path = Path(source) / item['name']
        if not archive_path.is_file():
            raise FileNotFoundError('Staged archive missing; check antivirus quarantine: ' + item['name'])
        if archive_path.stat().st_size != item['size'] or digest(archive_path) != item['sha256']:
            raise ValueError('Archive transfer checksum mismatch: ' + item['name'])
        print('Extracting: ' + item['name'], flush=True)
        with zipfile.ZipFile(archive_path) as archive:
            for entry in archive.infolist():
                path = staging.joinpath(*safe_name(entry.filename))
                if entry.flag_bits & 1 or stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError('Unsupported encrypted/symlink entry')
                if entry.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(entry) as reader, path.open('xb') as writer:
                        shutil.copyfileobj(reader, writer, 1024 * 1024)
    (staging / MARKER).write_text(json.dumps(manifest, separators=(',', ':')), encoding='utf-8')
    print('Verifying every extracted file size and CRC...', flush=True)
    if not verify_library(staging, manifest):
        raise ValueError('Extracted file verification failed; staging preserved')
    staging.rename(root)
    print('Verified library published: ' + str(destination), flush=True)


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def remote_ps(target, code):
    encoded = base64.b64encode(code.encode('utf-16-le')).decode()
    return subprocess.check_output(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
                                    target, 'powershell -NoProfile -EncodedCommand ' + encoded],
                                   text=True, encoding='utf-8').strip()


def deploy(args):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', args.server) or not re.fullmatch(r'[A-Za-z0-9_.-]+', args.user):
        raise ValueError('Invalid SSH server/user')
    if not re.fullmatch(r'[A-Za-z]:\\CEH-Tools(?:-[A-Za-z0-9_-]+)?', args.destination):
        raise ValueError('Use a dedicated drive-root CEH-Tools folder, not an OS/user folder')
    print('Reading ZIP inventory and SHA256 checksums; ISO excluded...', flush=True)
    manifest = inventory(Path(args.source))
    target = args.user + '@' + args.server
    info = json.loads(remote_ps(target, r'''
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$folder=Join-Path $env:USERPROFILE 'ceh-tools-deployment'
if ((Test-Path $folder) -and ((Get-Item $folder).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Redirected staging folder'}
New-Item -ItemType Directory -Path $folder -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $folder 'archives') -Force | Out-Null
$python=(Get-Command python.exe -ErrorAction Stop).Source
@{folder=$folder;python=$python}|ConvertTo-Json -Compress
'''))
    if args.allow_defender_exclusions:
        exclusions = [args.destination, args.destination + '-Staging', info['folder'] + '\\archives']
        code = "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; Add-MpPreference -ExclusionPath @("
        code += ','.join(ps_quote(p) for p in exclusions) + "); Write-Output 'Approved lab-only Defender exclusions configured.'"
        print(remote_ps(target, code), flush=True)
    config = {'destination': args.destination, 'manifest': manifest}
    source_file = Path(__file__).resolve()
    with tempfile.TemporaryDirectory(prefix='ceh-tools-') as temp:
        config_file = Path(temp) / 'library.json'
        config_file.write_text(json.dumps(config), encoding='utf-8')
        for local in (source_file, config_file, source_file.with_name('Publish-CehToolsShare.ps1')):
            subprocess.run(['scp', '-o', 'BatchMode=yes', str(local),
                            target + ':ceh-tools-deployment/'], check=True)
    worker = info['folder'] + '\\ceh_tools_library.py'
    configuration = info['folder'] + '\\library.json'
    command = '& ' + ps_quote(info['python']) + ' ' + ps_quote(worker)
    command += ' worker --config ' + ps_quote(configuration)
    status = json.loads(subprocess.check_output(['ssh', '-o', 'BatchMode=yes', target,
                                               command + ' --check'], text=True))
    if status['verified']:
        print('Existing library verified; no archive transfer or extraction needed.', flush=True)
        return
    if status['exists']:
        raise FileExistsError('Existing library did not verify; inspect it before replacing anything')
    staged = json.loads(subprocess.check_output(['ssh', '-o', 'BatchMode=yes', target,
                                               command + ' --staged'], text=True))
    for item in manifest['archives']:
        if staged.get(item['name']) == item['sha256']:
            print('Already staged: ' + item['name'], flush=True)
            continue
        print('Transferring: ' + item['name'], flush=True)
        subprocess.run(['scp', '-o', 'BatchMode=yes', str(Path(args.source) / item['name']),
                        target + ':ceh-tools-deployment/archives/'], check=True)
    subprocess.run(['ssh', '-o', 'BatchMode=yes', target, command], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    host = sub.add_parser('deploy')
    host.add_argument('--source', required=True)
    host.add_argument('--server', default='10.10.10.22')
    host.add_argument('--user', default='Administrator')
    host.add_argument('--destination', default=r'C:\CEH-Tools')
    host.add_argument('--allow-defender-exclusions', action='store_true')
    worker = sub.add_parser('worker')
    worker.add_argument('--config', required=True)
    worker.add_argument('--check', action='store_true')
    worker.add_argument('--staged', action='store_true')
    args = parser.parse_args()
    if args.mode == 'deploy':
        deploy(args)
        return
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    destination = Path(config['destination'])
    source = Path(args.config).parent / 'archives'
    manifest = config['manifest']
    if args.check:
        print(json.dumps({'exists': destination.exists(), 'verified': verify_library(destination, manifest)}))
    elif args.staged:
        print(json.dumps({i['name']: digest(source / i['name']) for i in manifest['archives']
                          if (source / i['name']).is_file()}))
    else:
        extract_library(source, destination, manifest)


if __name__ == '__main__':
    main()
