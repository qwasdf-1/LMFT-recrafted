import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import manifest


class ManifestTests(unittest.TestCase):
    def test_version_and_targets(self):
        version, target = manifest.config()
        self.assertEqual(version, "1.2.0-alpha.1")
        self.assertEqual(target["compilation_target"], "26.3")
        self.assertEqual(len(target["minecraft_versions"]), 5)

    def test_artifact_naming(self):
        self.assertEqual(
            manifest.jar_name("1.2.0-alpha.1", "fabric"),
            "lmft-fabric-26.x-1.2.0-alpha.1+26.x.jar",
        )
        self.assertEqual(
            manifest.jar_name("1.2.0-alpha.1", "neoforge"),
            "lmft-neoforge-26.x-1.2.0-alpha.1+26.x.jar",
        )
        with self.assertRaises(ValueError):
            manifest.jar_name("1.2.0-alpha.1", "forge")

    def test_channels(self):
        self.assertEqual(manifest.channel("1.2.0-alpha.1"), "alpha")
        self.assertEqual(manifest.channel("1.2.0-beta.1"), "beta")
        self.assertEqual(manifest.channel("1.2.0-rc.1"), "beta")
        self.assertEqual(manifest.channel("1.2.0"), "release")

    def test_release_notes(self):
        self.assertIn("Minecraft 26.1", manifest.notes("1.2.0-alpha.1"))

    def test_checksums(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "file"
            path.write_bytes(b"lmft")
            self.assertEqual(len(manifest.sha256(path)), 64)


if __name__ == "__main__":
    unittest.main()
