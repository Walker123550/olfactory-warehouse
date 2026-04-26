import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from olfactory_warehouse import app


def valid_payload(**overrides):
    payload = {
        "smell_date": "2026-04-26",
        "sample_id": "S001",
        "sample_type": "单体",
        "material_name": "柠檬",
        "scientific_name": "Citrus limon",
        "brand_source": "示例来源",
        "primary_category": "柑橘",
        "secondary_category": "柠檬",
        "keywords": "酸、明亮、绿感",
        "intensity": "4",
        "diffusion": "强",
        "note_0m": "刺激酸，明亮",
        "note_10m": "酸感变柔",
        "note_30m": "变淡",
        "note_2h": "几乎无残留",
        "volatility_speed": "快",
        "compared_sample": "橙子",
        "difference_desc": "更酸，甜感更低",
        "relative_intensity": "强",
        "anchor_name": "柠檬",
        "preference_score": "4",
        "usage_scene": "清新",
        "association_desc": "柠檬水",
        "free_note": "",
    }
    payload.update(overrides)
    return payload


class ValidationTests(unittest.TestCase):
    def test_sanitize_payload_casts_numeric_strings(self):
        payload = app.sanitize_payload(valid_payload(intensity="5", preference_score="3"))
        self.assertEqual(payload["intensity"], 5)
        self.assertEqual(payload["preference_score"], 3)

    def test_rejects_invalid_numeric_type(self):
        with self.assertRaisesRegex(ValueError, "intensity"):
            app.sanitize_payload(valid_payload(intensity="4.5"))

    def test_rejects_out_of_range_score(self):
        with self.assertRaisesRegex(ValueError, "preference_score"):
            app.sanitize_payload(valid_payload(preference_score="6"))

    def test_rejects_invalid_enum(self):
        with self.assertRaisesRegex(ValueError, "diffusion"):
            app.sanitize_payload(valid_payload(diffusion="非常强"))


class RepositoryTests(unittest.TestCase):
    def test_create_record_persists_normalized_rows(self):
        original_db_path = app.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            app.DB_PATH = Path(tmpdir) / "test.sqlite3"
            try:
                app.init_db()
                session_key = app.create_record(valid_payload())
                records = app.list_records()
            finally:
                app.DB_PATH = original_db_path

            self.assertEqual(session_key, 1)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["sample_id"], "S001")
            self.assertEqual(records[0]["keywords"], "明亮、绿感、酸")


if __name__ == "__main__":
    unittest.main()
