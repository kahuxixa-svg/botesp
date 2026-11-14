"""Pack verified original Troko GIFs, without speech models or credentials."""
import importlib.util
import hashlib
import json
from pathlib import Path

from generate_idle_animations import generate, SCENES

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'xiaozhi-esp32/main/boards/lilygo/troko-t-display-s3/assets'
OUTPUT = ROOT / '.local/troko-eyes-assets.bin'


def prepare():
    generate()
    spec = importlib.util.spec_from_file_location(
        'xiaozhi_assets', ROOT / 'xiaozhi-esp32/scripts/build_default_assets.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    provenance = json.loads((SOURCE / 'provenance.json').read_text(encoding='utf-8'))
    entries = {}
    collection = []
    for item in provenance['files']:
        name = item['name']
        if Path(name).name != name or not name.endswith('.gif'):
            raise ValueError('Invalid asset filename')
        data = (SOURCE / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError(f'Original GIF checksum mismatch: {name}')
        if data[:6] not in (b'GIF89a', b'GIF87a'):
            raise ValueError(f'Invalid GIF: {name}')
        entries[name] = (data, 0, 0)
        collection.append({'name': Path(name).stem, 'file': name})
    for name in SCENES:
        filename = name + '.gif'
        entries[filename] = ((SOURCE / 'idle' / filename).read_bytes(), 0, 0)
        collection.append({'name': name, 'file': filename})
    entries['index.json'] = (json.dumps({'version': 1, 'emoji_collection': collection}).encode(), 0, 0)
    OUTPUT.parent.mkdir(exist_ok=True)
    packed = module.pack_assets_entries(entries)
    OUTPUT.write_bytes(packed)
    assert module.read_assets_entries(OUTPUT) == entries
    print(f'Packed 21 original Troko expressions + {len(SCENES)} idle scenes: '
          f'{len(packed)} bytes; no audio models')


if __name__ == '__main__':
    prepare()
