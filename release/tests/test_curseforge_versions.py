import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from curseforge_versions import resolve


SAMPLE = [
    *({"id": i + 100, "name": mc} for i, mc in enumerate(
        ["26.1", "26.1.1", "26.1.2", "26.2", "26.3"])),
    {"id": 51, "name": "Fabric", "slug": "fabric"},
    {"id": 52, "name": "NeoForge", "slug": "neoforge"},
    {"id": 61, "name": "Java 25"},
    {"id": 9638, "name": "Client"},
    {"id": 9639, "name": "Server"}
]


class CurseForgeVersionsTests(unittest.TestCase):
    def test_universal_fabric(self):
        ids = resolve(SAMPLE, "fabric")
        self.assertTrue(set(range(100, 105)).issubset(ids))
        self.assertIn(51, ids)
        self.assertNotIn(52, ids)
        self.assertIn(61, ids)
        self.assertIn(9638, ids)
        self.assertIn(9639, ids)

    def test_neoforge_server_only(self):
        ids = resolve(SAMPLE, "neoforge", environment="server")
        self.assertIn(52, ids)
        self.assertNotIn(51, ids)
        self.assertIn(9639, ids)
        self.assertNotIn(9638, ids)

    def test_missing_game_version_fails_closed(self):
        with self.assertRaises(ValueError):
            resolve([v for v in SAMPLE if v.get("name") != "26.1.2"], "fabric")

    def test_explicit_override(self):
        filtered = [v for v in SAMPLE if v.get("name") != "26.1.2"]
        ids = resolve(filtered, "fabric", overrides={"26.1.2": [99999]})
        self.assertIn(99999, ids)


if __name__ == "__main__":
    unittest.main()
