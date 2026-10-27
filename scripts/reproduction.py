"""Package and restore a private, hashed S5D snapshot. Run inside Docker.

This utility copies existing resources. It never trains, calibrates or evaluates
the scientific test split. The source list is supplied by git ls-files -z.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import tarfile


PRIVATE_PATHS = (
    'core/models/e8f8c211226b894fcb81acc59f3b34ba3efd5f42',
    'core/artifacts/ci/raw',
    'core/artifacts/ci/fixtures',
    'core/artifacts/artifacts/s4-fechamento-01/frozen-curated-01',
    'core/artifacts/artifacts/s4-fechamento-01/idf-final-01',
    'core/artifacts/artifacts/s5b-01',
    'core/artifacts/plan16-r3-01/H1-restart-01',
    'core/artifacts/plan16-r3-01/campaign',
    'core/artifacts/plan16-r3-01/campaign-restart-01',
    'core/artifacts/plan16-r4-01/H2-scientific-01',
    'core/artifacts/s5c-claims',
    'TCC/evidencias/codex-p00-02',
    'TCC/evidencias/codex-p01-02',
    'TCC/evidencias/codex-p02-03',
    'TCC/evidencias/codex-p03-01',
    'TCC/evidencias/codex-p04-01',
    'TCC/evidencias/codex-p05-02',
    'TCC/evidencias/codex-p06-01',
    'TCC/evidencias/codex-p07-04',
    'TCC/evidencias/codex-p08-02',
    'TCC/evidencias/codex-p09-02',
    'TCC/evidencias/codex-p10-01',
    'TCC/evidencias/codex-p11-01',
    'TCC/evidencias/codex-ci-40451552564-01',
    'TCC/evidencias/codex-s4-fechamento-01/datasheet-operacional.md',
    'TCC/evidencias/codex-s4-fechamento-01/relatorio-final.md',
    'TCC/evidencias/codex-s4-fechamento-01/contratos.md',
    'TCC/evidencias/codex-s4-fechamento-01/politica-curadoria.md',
)
MANIFEST = 'reproduction-manifest.json'


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError(f'unsafe relative path: {name}')
    return path


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pack(root, source_list, output, extra=()):
    if output.exists():
        raise FileExistsError(output)
    names = {p for p in source_list.read_text().split('\0') if p}
    names.update(str(p.relative_to(root)) for p in (root / 'TCC').glob('[0-9][0-9]-*.md'))
    for relative in (*PRIVATE_PATHS, *extra):
        safe_name(relative)
        base = root / relative
        if base.is_file():
            names.add(relative)
            continue
        if not base.is_dir():
            raise FileNotFoundError(base)
        # Evidence seals can include historical cache/bytecode files. Preserve
        # every existing regular file in explicit private trees so those seals
        # remain verifiable after restoration.
        names.update(str(p.relative_to(root)) for p in base.rglob('*') if p.is_file())
    files = {}
    for name in sorted(names):
        safe_name(name)
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'links are not allowed: {name}')
        if path.is_file():
            files[name] = {'sha256': digest(path), 'bytes': path.stat().st_size,
                           'mode': stat.S_IMODE(path.stat().st_mode) & 0o777}
    manifest = {'schema': 'hts-private-reproduction-1',
                'source': 'export of current working tree, including unpublished changes; not a clone of HEAD',
                'scientific_test_policy': 'saved predictions only; never repeat P10 inference',
                'files': files}
    encoded = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    # x mode preserves every prior attempt. No symlinks, credentials or .git.
    with tarfile.open(output, 'x:gz', compresslevel=1) as archive:
        import io
        info = tarfile.TarInfo(MANIFEST)
        info.size = len(encoded)
        archive.addfile(info, io.BytesIO(encoded))
        for name in files:
            archive.add(root / name, arcname=name, recursive=False)
    with output.with_suffix(output.suffix + '.manifest.json').open('xb') as stream:
        stream.write(encoded)
    print(json.dumps({'bundle': str(output), 'files': len(files),
                      'uncompressed_bytes': sum(p['bytes'] for p in files.values()),
                      'bundle_bytes': output.stat().st_size, 'bundle_sha256': digest(output)}))


def restore(bundle, target):
    if target.exists() and any(target.iterdir()):
        raise FileExistsError('restore requires a new or empty directory')
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(bundle, 'r:gz') as archive:
        members = archive.getmembers()
        for member in members:
            safe_name(member.name)
            if not member.isfile():
                raise ValueError('only regular files are accepted')
        index = json.load(archive.extractfile(MANIFEST))
        expected = set(index['files']) | {MANIFEST}
        if {m.name for m in members} != expected or len(members) != len(expected):
            raise ValueError('archive inventory differs or contains duplicate entries')
        for member in members:
            destination = target / member.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as stream:
                source = archive.extractfile(member)
                while chunk := source.read(1024 * 1024):
                    stream.write(chunk)
            destination.chmod(0o644 if member.name == MANIFEST else index['files'][member.name]['mode'])
    verify(target)


def verify(root):
    index = json.loads((root / MANIFEST).read_text())
    if index['schema'] != 'hts-private-reproduction-1':
        raise ValueError('unknown reproduction manifest')
    for name, expected in index['files'].items():
        safe_name(name)
        path = root / name
        if (path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or
                path.stat().st_size != expected['bytes'] or digest(path) != expected['sha256'] or
                stat.S_IMODE(path.stat().st_mode) != expected['mode']):
            raise ValueError(f'restored file differs: {name}')
    print(json.dumps({'status': 'passed', 'verified_files': len(index['files']),
                      'scientific_inference_repeated': False, 'root': str(root)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    packing = sub.add_parser('pack')
    packing.add_argument('--root', type=Path, required=True)
    packing.add_argument('--source-list', type=Path, required=True)
    packing.add_argument('--out', type=Path, required=True)
    packing.add_argument('--include', action='append', default=[], help='additional existing root-relative evidence file/directory')
    restoring = sub.add_parser('restore')
    restoring.add_argument('--bundle', type=Path, required=True)
    restoring.add_argument('--target', type=Path, required=True)
    checking = sub.add_parser('verify')
    checking.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.operation == 'pack':
        pack(args.root, args.source_list, args.out, args.include)
    elif args.operation == 'restore':
        restore(args.bundle, args.target)
    else:
        verify(args.root)
