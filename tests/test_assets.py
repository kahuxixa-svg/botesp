"""Check distributable assets and animation decoder inputs without an ESP32."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'xiaozhi-esp32/main/boards/lilygo/troko-t-display-s3/assets'


class AssetsTests(unittest.TestCase):
    def test_original_resources_are_present_and_unchanged(self):
        provenance = json.loads((ASSETS / 'provenance.json').read_text(encoding='utf-8'))
        self.assertEqual(len(provenance['files']), 21)
        for entry in provenance['files']:
            with self.subTest(name=entry['name']):
                self.assertEqual(hashlib.sha256((ASSETS / entry['name']).read_bytes()).hexdigest(),
                                 entry['sha256'])

    def test_generated_scenes_decode_with_black_background_and_loop(self):
        scenes = sorted((ASSETS / 'idle').glob('*.gif'))
        self.assertEqual(len(scenes), 5)
        for path in scenes:
            with self.subTest(scene=path.name), Image.open(path) as image:
                self.assertEqual(image.size, (160, 256))
                self.assertEqual(image.n_frames, 96)
                self.assertEqual(image.info['loop'], 0)
                distinct = set()
                for frame in range(image.n_frames):
                    image.seek(frame)
                    self.assertEqual(image.info['duration'], 80)
                    rgb = image.convert('RGB')
                    distinct.add(hashlib.sha256(rgb.tobytes()).digest())
                    for point in ((0, 0), (159, 0), (0, 255), (159, 255)):
                        self.assertEqual(rgb.getpixel(point), (0, 0, 0))
                self.assertGreater(len(distinct), 40)

    def test_packed_assets_fit_partition_and_contain_all_scenes(self):
        path = ROOT / 'xiaozhi-esp32/scripts/build_default_assets.py'
        spec = importlib.util.spec_from_file_location('asset_pack', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        packed = ROOT / '.local/troko-eyes-assets.bin'
        self.assertTrue(packed.is_file(), 'Run scripts/prepare_troko_assets.py first')
        self.assertLess(packed.stat().st_size, 8 * 1024 * 1024)
        entries = module.read_assets_entries(packed)
        collection = json.loads(entries['index.json'][0])['emoji_collection']
        self.assertEqual(len(collection), 26)
        for item in collection:
            name = item['file']
            source = ASSETS / ('idle' if item['name'].startswith('idle_') else '') / name
            self.assertEqual(entries[name][0], source.read_bytes())


if __name__ == '__main__':
    unittest.main()
