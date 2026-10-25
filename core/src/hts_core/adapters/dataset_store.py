import hashlib
import json
from pathlib import Path
import zipfile


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(value):
    return digest(canonical(value))


def inside(folder, relative):
    relative = Path(relative)
    target = (Path(folder) / relative).resolve()
    if relative.is_absolute() or '..' in relative.parts or not target.is_relative_to(Path(folder).resolve()):
        raise ValueError('caminho fora do artefato')
    return target


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def write_json(path, value):
    write_new(path, canonical(value))


def write_jsonl(path, values):
    write_new(path, b''.join(canonical(v) for v in values))


def read_json(path):
    return json.loads(Path(path).read_bytes())


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line]


def seal(folder, metadata):
    folder = Path(folder)
    if (folder / 'manifest.json').exists():
        raise FileExistsError('manifesto já existe')
    files = {p.relative_to(folder).as_posix(): digest(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()}
    body = {'schema': 'hts-dataset-1', 'metadata': metadata, 'files': files}
    manifest = {**body, 'version': identity(body)}
    write_json(folder / 'manifest.json', manifest)
    return manifest


def verify_seal(folder):
    folder = Path(folder)
    manifest = read_json(folder / 'manifest.json')
    body = {k: manifest[k] for k in ('schema', 'metadata', 'files')}
    if manifest['version'] != identity(body):
        raise ValueError('identidade do manifesto divergente')
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    if actual != set(manifest['files']) | {'manifest.json'}:
        raise ValueError('inventário de arquivos divergente')
    for name, expected in manifest['files'].items():
        if digest(inside(folder, name).read_bytes()) != expected:
            raise ValueError(f'hash divergente: {name}')
    return manifest


def export_bundle(folder, destination):
    folder = Path(folder)
    manifest = verify_seal(folder)
    with Path(destination).open('xb') as stream, zipfile.ZipFile(stream, 'w', zipfile.ZIP_STORED) as archive:
        for name in sorted([*manifest['files'], 'manifest.json']):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o600 << 16
            archive.writestr(info, inside(folder, name).read_bytes())
    return manifest['version']


def import_bundle(bundle, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(bundle) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError('nomes duplicados no pacote')
        if sum(i.file_size for i in archive.infolist()) > 512 * 1024 * 1024:
            raise ValueError('pacote excede 512 MiB')
        for info in archive.infolist():
            if info.is_dir() or info.external_attr >> 16 & 0o170000 == 0o120000:
                raise ValueError('diretórios/links não permitidos no pacote')
            write_new(inside(destination, info.filename), archive.read(info))
    return verify_seal(destination)
