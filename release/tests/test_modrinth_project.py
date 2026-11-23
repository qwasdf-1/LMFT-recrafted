import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modrinth_project import lookup, slug_from_url, verify

PROJECT = {
    "id": "AbCd1234",
    "slug": "lmft-recrafted",
    "source_url": "https://github.com/qwasdf-1/LMFT-recrafted",
    "license": {"id": "Apache-2.0", "name": "Apache License 2.0"},
}
SOURCE = "https://github.com/qwasdf-1/LMFT-recrafted"


class ModrinthProjectTests(unittest.TestCase):
    def test_project_slug_is_accepted_in_id_variable(self):
        self.assertEqual(lookup(project_id="lmft-recrafted"), "lmft-recrafted")

    def test_slug_and_url_are_accepted(self):
        self.assertEqual(lookup(slug="lmft-recrafted"), "lmft-recrafted")
        self.assertEqual(lookup(url="https://modrinth.com/mod/lmft-recrafted/"), "lmft-recrafted")
        self.assertEqual(slug_from_url("https://modrinth.com/mod/lmft-recrafted"), "lmft-recrafted")

    def test_canonical_id_extracted(self):
        self.assertEqual(verify(PROJECT, SOURCE, project_id="lmft-recrafted"), "AbCd1234")
        self.assertEqual(verify(PROJECT, SOURCE, slug="lmft-recrafted"), "AbCd1234")
        self.assertEqual(verify(PROJECT, SOURCE, project_id="AbCd1234"), "AbCd1234")

    def test_refuses_wrong_project(self):
        with self.assertRaises(ValueError):
            verify(PROJECT, SOURCE, slug="different-project")
        with self.assertRaises(ValueError):
            verify(PROJECT, "https://github.com/elsewhere/not-lmft")

    def test_rejects_legacy_cc0_marketplace_setting(self):
        project = dict(PROJECT, license={"id": "CC0-1.0"})
        with self.assertRaisesRegex(ValueError, "Apache-2.0"):
            verify(project, SOURCE, slug="lmft-recrafted")

    def test_refuses_invalid_identifier(self):
        with self.assertRaises(ValueError):
            lookup(project_id="../wrong")
        with self.assertRaises(ValueError):
            lookup(url="https://evil.example/mod/lmft-recrafted")
        with self.assertRaises(ValueError):
            lookup()


if __name__ == "__main__":
    unittest.main()
