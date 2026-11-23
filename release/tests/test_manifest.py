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
        self.assertRegex(version, r"^[0-9]+\.[0-9]+\.[0-9]+")
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
        self.assertIn("Minecraft 26.1", manifest.notes(manifest.config()[0]))

    def test_license_and_upstream_attribution(self):
        root = manifest.ROOT
        apache = (root / "LICENSE").read_text(encoding="utf-8")
        cc0 = (root / "LICENSES/CC0-1.0.txt").read_text(encoding="utf-8")
        notice = (root / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("Apache License", apache)
        self.assertIn("Version 2.0, January 2004", apache)
        self.assertIn("CC0 1.0 Universal", cc0)
        self.assertIn("Blodhgarm", notice)
        self.assertIn("Dragon-Seeker/LoadMyFingTags", notice)
        self.assertIn("Apache", notice)

    def test_checksums(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "file"
            path.write_bytes(b"lmft")
            self.assertEqual(len(manifest.sha256(path)), 64)


if __name__ == "__main__":
    unittest.main()
