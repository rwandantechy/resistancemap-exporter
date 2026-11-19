import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import parser, scraper


class SourceUnitTests(unittest.TestCase):
    def test_uses_unit_from_request(self):
        response = {"post_data": "page=use&units=DDD"}
        self.assertEqual(parser.source_unit(response, {}), "DDD")

    def test_returns_blank_when_unit_is_not_verified(self):
        self.assertIsNone(parser.source_unit({"post_data": "page=use"}, {}))

    def test_build_use_url_preserves_units(self):
        entry = {
            "country": "Australia",
            "source_url": "https://resistancemap.onehealthtrust.org/CountryPage.php?countryId=1&country=Australia",
        }
        use_url = scraper.build_use_url(entry)
        self.assertIn("chartsubtype=use", use_url)
        self.assertIn("units=DDD", use_url)


class CacheAndManifestTests(unittest.TestCase):
    def test_load_manifest_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(scraper, "MANIFEST_PATH", Path(directory) / "countries_manifest.json"):
                with self.assertRaisesRegex(RuntimeError, "manifest is missing"):
                    scraper.load_manifest()

    def test_load_manifest_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "countries_manifest.json"
            manifest_path.write_text("{invalid", encoding="utf-8")
            with patch.object(scraper, "MANIFEST_PATH", manifest_path):
                with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
                    scraper.load_manifest()

    def test_load_cache_rejects_missing_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "country.json"
            cache_path.write_text(json.dumps({"country": "Test"}), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "missing 'responses'"):
                scraper.load_cache(cache_path)


if __name__ == "__main__":
    unittest.main()
