import csv
import json
import tempfile
import unittest
from pathlib import Path

from data_preprocessing import FIELDS, preprocess_csv


VALID_ROW = {
    "disruption_id": "DIS-000001",
    "disruption_type": " Cyber Attack ",
    "industry": "Electronics",
    "supplier_tier": "2",
    "supplier_region": "Asia-Pacific",
    "supplier_size": "Medium",
    "has_backup_supplier": "true",
    "disruption_severity": "4",
    "production_impact_pct": "52.4",
    "revenue_loss_usd": "1199054.59",
    "response_type": "Alternative Supplier",
    "response_time_days": "1",
    "partial_recovery_days": "29",
    "full_recovery_days": "97",
    "permanent_supplier_change": "yes",
}


class PreprocessCsvTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.source = self.root / "source.csv"
        self.cleaned = self.root / "clean.csv"

    def tearDown(self):
        self.directory.cleanup()

    def write_rows(self, rows, headers=FIELDS):
        with self.source.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(
                output, fieldnames=headers, extrasaction="ignore"
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    header: row.get(field, "")
                    for field, header in zip(FIELDS, headers)
                })

    def run_pipeline(self):
        return preprocess_csv(self.source, self.cleaned)

    def test_normalizes_and_reports_valid_row(self):
        self.write_rows([VALID_ROW])

        report = self.run_pipeline()

        with self.cleaned.open(encoding="utf-8", newline="") as cleaned_file:
            rows = list(csv.DictReader(cleaned_file))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["disruption_type"], "Cyber Attack")
        self.assertEqual(rows[0]["has_backup_supplier"], "True")
        self.assertEqual(rows[0]["permanent_supplier_change"], "True")
        self.assertEqual(report["accepted_rows"], 1)
        self.assertEqual(report["rejected_rows"], 0)
        self.assertEqual(report["numeric_summary"]["supplier_tier"]["mean"], 2)

    def test_normalizes_header_case_spaces_and_byte_order_mark(self):
        headers = ["\ufeff" + field.replace("_", " ").upper() for field in FIELDS]
        self.write_rows([VALID_ROW], headers=headers)

        report = self.run_pipeline()

        self.assertEqual(report["accepted_rows"], 1)

    def test_rejects_bad_rows_and_keeps_good_rows(self):
        invalid = dict(VALID_ROW, disruption_id="DIS-000002")
        invalid["supplier_tier"] = "5"
        invalid["has_backup_supplier"] = "sometimes"
        self.write_rows([VALID_ROW, invalid])

        report = self.run_pipeline()

        self.assertEqual(report["accepted_rows"], 1)
        self.assertEqual(report["rejected_rows"], 1)
        self.assertEqual(report["error_counts"]["supplier_tier"], 1)
        self.assertEqual(report["error_counts"]["has_backup_supplier"], 1)
        rejected = self.root / "clean_rejected.csv"
        with rejected.open(encoding="utf-8", newline="") as rejected_file:
            rejected_rows = list(csv.DictReader(rejected_file))
        self.assertIn("supplier_tier", rejected_rows[0]["errors"])
        self.assertEqual(rejected_rows[0]["source_row"], "3")

    def test_detects_duplicate_ids_case_insensitively(self):
        duplicate = dict(VALID_ROW, disruption_id="dis-000001")
        self.write_rows([VALID_ROW, duplicate])

        report = self.run_pipeline()

        self.assertEqual(report["accepted_rows"], 1)
        self.assertEqual(report["duplicate_ids"], 1)
        self.assertIn("duplicate identifier", (self.root / "clean_rejected.csv").read_text(
            encoding="utf-8"
        ))

    def test_rejects_recovery_order_and_out_of_range_percent(self):
        invalid = dict(VALID_ROW)
        invalid["production_impact_pct"] = "100.1"
        invalid["full_recovery_days"] = "28"
        self.write_rows([invalid])

        report = self.run_pipeline()

        self.assertEqual(report["rejected_rows"], 1)
        self.assertEqual(report["error_counts"]["production_impact_pct"], 1)
        self.assertEqual(report["error_counts"]["full_recovery_days"], 1)

    def test_fails_fast_for_missing_required_headers(self):
        self.write_rows([VALID_ROW], headers=FIELDS[:-1])

        with self.assertRaisesRegex(ValueError, "missing required columns"):
            self.run_pipeline()
        self.assertFalse(self.cleaned.exists())

    def test_fails_fast_for_duplicate_normalized_headers(self):
        headers = list(FIELDS) + [" Supplier Tier "]
        self.write_rows([VALID_ROW], headers=headers)

        with self.assertRaisesRegex(ValueError, "duplicate headers"):
            self.run_pipeline()

    def test_does_not_allow_output_to_overwrite_source(self):
        self.write_rows([VALID_ROW])

        with self.assertRaisesRegex(ValueError, "must not overwrite"):
            preprocess_csv(self.source, self.source)

    def test_emits_machine_readable_report_and_empty_reject_file(self):
        self.write_rows([VALID_ROW])

        report = self.run_pipeline()

        report_file = self.root / "clean_report.json"
        with report_file.open(encoding="utf-8") as source:
            saved_report = json.load(source)
        self.assertEqual(saved_report["accepted_rows"], 1)
        self.assertEqual(saved_report["category_counts"]["industry"]["Electronics"], 1)
        with (self.root / "clean_rejected.csv").open(
            encoding="utf-8", newline=""
        ) as rejected_file:
            self.assertEqual(list(csv.DictReader(rejected_file)), [])
        self.assertEqual(report["report_file"], str(report_file.resolve()))


if __name__ == "__main__":
    unittest.main()
