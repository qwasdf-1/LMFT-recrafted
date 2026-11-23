import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from curseforge_versions import resolve, minecraft_version_id


SAMPLE = [
    *({"id": i + 100, "name": mc} for i, mc in enumerate(
        ["26.1", "26.1.1", "26.1.2", "26.2", "26.3"])),
    {"id": 51, "name": "Fabric", "slug": "fabric"},
    {"id": 52, "name": "NeoForge", "slug": "neoforge"},
    {"id": 61, "name": "Java 25"},
    {"id": 9638, "name": "Client"},
    {"id": 9639, "name": "Server"}
]

# Simulate the real failure: 3 distinct categories expose the same name 26.1.
# Category labels are synthetic test data, NOT a claim about the live ID mapping.
DUPLICATES = [
    {"id": 15933, "name": "26.1", "gameVersionTypeID": 101},
    {"id": 16083, "name": "26.1", "gameVersionTypeID": 102},
    {"id": 16128, "name": "26.1", "gameVersionTypeID": 103},
]
TYPES = [
    {"id": 101, "name": "Bukkit 26.1", "slug": "bukkit-26-1"},
    {"id": 102, "name": "Minecraft 26.1", "slug": "minecraft-26-1"},
    {"id": 103, "name": "Modpack 26.1", "slug": "modpack-26-1"},
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

    def test_duplicate_names_disambiguated_by_version_type(self):
        self.assertEqual(minecraft_version_id(DUPLICATES, "26.1", TYPES), 16083)

    def test_duplicate_names_without_types_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "version-types"):
            minecraft_version_id(DUPLICATES, "26.1")

    def test_type_must_represent_minecraft_not_bukkit(self):
        wrong = [v for v in DUPLICATES if v["id"] != 16083]
        with self.assertRaisesRegex(ValueError, "gameVersionTypeID"):
            minecraft_version_id(wrong, "26.1", TYPES)

    def test_hotfix_uses_parent_minecraft_type(self):
        versions = [
            {"id": 207, "name": "26.1.2", "gameVersionTypeID": 102},
            {"id": 208, "name": "26.1.2", "gameVersionTypeID": 101},
        ]
        self.assertEqual(minecraft_version_id(versions, "26.1.2", TYPES), 207)

    def test_more_specific_category_preferred(self):
        types = TYPES + [{"id": 104, "name": "Minecraft 26", "slug": "minecraft-26"}]
        versions = DUPLICATES + [{"id": 209, "name": "26.1", "gameVersionTypeID": 104}]
        self.assertEqual(minecraft_version_id(versions, "26.1", types), 16083)

    def test_two_valid_minecraft_types_fail_closed(self):
        types = TYPES + [{"id": 104, "name": "Minecraft 26.1", "slug": "minecraft-26-1-copy"}]
        versions = DUPLICATES + [{"id": 209, "name": "26.1", "gameVersionTypeID": 104}]
        with self.assertRaisesRegex(ValueError, "Could not uniquely identify"):
            minecraft_version_id(versions, "26.1", types)


if __name__ == "__main__":
    unittest.main()
