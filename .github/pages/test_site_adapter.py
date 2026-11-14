"""Check real DUKE bytes and prevent unreviewed data or executable content."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from site_adapter import prepare


ROOT = Path(__file__).resolve().parents[2]


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.stage = self.parent / "stage"
        self.stage.mkdir()

    def fixture(self):
        source = self.parent / "source"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        return source

    def test_every_existing_public_byte_is_retained(self):
        prepare(ROOT, self.stage)
        expected = {p.relative_to(ROOT).as_posix(): p.read_bytes()
                    for p in ROOT.rglob("*") if p.is_file()
                    and p.relative_to(ROOT).parts[0] not in {".git", ".github"}}
        actual = {p.relative_to(self.stage).as_posix(): p.read_bytes()
                  for p in self.stage.rglob("*") if p.is_file()}
        self.assertEqual(expected, actual)
        self.assertEqual(len([p for p in actual if p.startswith("records/")]),
                         len(json.loads(actual["data/dashboard.json"])["items"]))
        self.assertNotIn("_release.json", actual)

    def test_generated_validators_match_source_manifest(self):
        manifest = json.loads((ROOT / ".github/pages/source-manifest.json").read_text())
        for path, expected in manifest["outputs"].items():
            raw = (ROOT / ".github/pages" / path).read_bytes()
            self.assertEqual(len(raw), expected["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected["sha256"])

    def test_unknown_file_is_rejected(self):
        source = self.fixture()
        (source / "unreviewed.txt").write_text("unreviewed")
        with self.assertRaisesRegex(ValueError, "UNMANAGED_FILE"):
            prepare(source, self.stage)
        self.assertEqual(list(self.stage.iterdir()), [])

    def test_unknown_management_file_is_rejected(self):
        source = self.fixture()
        (source / ".github/pages/unknown.py").write_text("unreviewed")
        with self.assertRaisesRegex(ValueError, "UNMANAGED_FILE"):
            prepare(source, self.stage)

    def test_symlink_is_rejected(self):
        source = self.fixture()
        path = source / "assets/app.js"
        path.unlink()
        path.symlink_to(ROOT / "assets/app.js")
        with self.assertRaisesRegex(ValueError, "SYMLINK_FORBIDDEN"):
            prepare(source, self.stage)

    def test_hardlink_is_rejected(self):
        source = self.fixture()
        path = source / "assets/app.js"
        other = self.parent / "same-device.js"
        other.write_bytes(path.read_bytes())
        path.unlink()
        os.link(other, path)
        with self.assertRaisesRegex(ValueError, "REGULAR_SINGLE_LINK_REQUIRED"):
            prepare(source, self.stage)

    def test_browser_network_capability_is_rejected(self):
        source = self.fixture()
        path = source / "assets/app.js"
        path.write_text(path.read_text() + "\nfetch('/private');\n")
        with self.assertRaisesRegex(ValueError, "JAVASCRIPT_UNREVIEWED_CAPABILITY"):
            prepare(source, self.stage)

    def test_private_snapshot_field_is_rejected(self):
        source = self.fixture()
        path = source / "data/dashboard.json"
        value = json.loads(path.read_text())
        value["private_notes"] = "not approved for publication"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "PUBLIC_SNAPSHOT_FIELDS"):
            prepare(source, self.stage)

    def test_missing_record_is_rejected(self):
        source = self.fixture()
        next((source / "records").glob("*.html")).unlink()
        with self.assertRaisesRegex(ValueError, "PUBLIC_FILE_ALLOWLIST_MISMATCH"):
            prepare(source, self.stage)

    def test_nonempty_stage_is_rejected(self):
        (self.stage / "unexpected").write_text("unreviewed")
        with self.assertRaisesRegex(ValueError, "EMPTY_STAGE_REQUIRED"):
            prepare(ROOT, self.stage)


if __name__ == "__main__":
    unittest.main()
