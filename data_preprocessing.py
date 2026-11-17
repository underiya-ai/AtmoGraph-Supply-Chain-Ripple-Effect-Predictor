"""Streaming validation and cleaning for AtmoGraph disruption datasets."""

import argparse
import csv
import json
import math
import os
import re
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path


FIELDS = (
    "disruption_id",
    "disruption_type",
    "industry",
    "supplier_tier",
    "supplier_region",
    "supplier_size",
    "has_backup_supplier",
    "disruption_severity",
    "production_impact_pct",
    "revenue_loss_usd",
    "response_type",
    "response_time_days",
    "partial_recovery_days",
    "full_recovery_days",
    "permanent_supplier_change",
)

INTEGER_RANGES = {
    "supplier_tier": (1, 4),
    "disruption_severity": (1, 5),
    "response_time_days": (0, None),
    "partial_recovery_days": (0, None),
    "full_recovery_days": (0, None),
}

DECIMAL_RANGES = {
    "production_impact_pct": (0.0, 100.0),
    "revenue_loss_usd": (0.0, None),
}

BOOLEAN_FIELDS = (
    "has_backup_supplier",
    "permanent_supplier_change",
)

CATEGORY_VALUES = {
    "disruption_type": (
        "Cyber Attack",
        "Factory Incident",
        "Geopolitical",
        "Labor Strike",
        "Natural Disaster",
        "Port Congestion",
    ),
    "industry": (
        "Aerospace",
        "Automotive",
        "Consumer Goods",
        "Electronics",
        "Pharmaceuticals",
    ),
    "supplier_region": (
        "Asia-Pacific",
        "Europe",
        "North America",
        "South America",
    ),
    "supplier_size": ("Large", "Medium", "Small"),
    "response_type": (
        "Alternative Supplier",
        "Combined Strategy",
        "Customer Delay",
        "Inventory Buffer",
        "Production Reroute",
    ),
}

BOOLEAN_VALUES = {
    "true": "True",
    "t": "True",
    "yes": "True",
    "y": "True",
    "1": "True",
    "false": "False",
    "f": "False",
    "no": "False",
    "n": "False",
    "0": "False",
}


def _normalize_header(value):
    normalized = unicodedata.normalize("NFKC", value or "")
    normalized = normalized.lstrip("\ufeff").strip().casefold()
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def _normalize_text(value):
    normalized = unicodedata.normalize("NFKC", value or "")
    return " ".join(normalized.split())


def _normalize_category(field, value):
    text = _normalize_text(value)
    if not text:
        raise ValueError("value is required")
    known = {
        candidate.casefold(): candidate
        for candidate in CATEGORY_VALUES.get(field, ())
    }
    return known.get(text.casefold(), text.title())


def _parse_integer(field, value):
    text = _normalize_text(value)
    if not re.fullmatch(r"[+-]?\d+", text):
        raise ValueError("must be a whole number")
    number = int(text)
    minimum, maximum = INTEGER_RANGES[field]
    if number < minimum:
        raise ValueError("must be at least {}".format(minimum))
    if maximum is not None and number > maximum:
        raise ValueError("must be at most {}".format(maximum))
    return str(number), number


def _parse_decimal(field, value):
    text = _normalize_text(value)
    try:
        number = float(text)
    except ValueError:
        raise ValueError("must be a number")
    if not math.isfinite(number):
        raise ValueError("must be finite")
    minimum, maximum = DECIMAL_RANGES[field]
    if number < minimum:
        raise ValueError("must be at least {}".format(minimum))
    if maximum is not None and number > maximum:
        raise ValueError("must be at most {}".format(maximum))
    return format(number, ".15g"), number


def _normalize_record(record):
    cleaned = {}
    errors = []
    numeric_values = {}
    for field in FIELDS:
        value = _normalize_text(record.get(field))
        if not value:
            errors.append("{}: value is required".format(field))
            continue

        try:
            if field == "disruption_id":
                cleaned[field] = value.upper()
            elif field in INTEGER_RANGES:
                cleaned[field], numeric_values[field] = _parse_integer(
                    field, value
                )
            elif field in DECIMAL_RANGES:
                cleaned[field], numeric_values[field] = _parse_decimal(
                    field, value
                )
            elif field in BOOLEAN_FIELDS:
                normalized = value.casefold()
                if normalized not in BOOLEAN_VALUES:
                    raise ValueError(
                        "must be true/false, yes/no, y/n, t/f, or 1/0"
                    )
                cleaned[field] = BOOLEAN_VALUES[normalized]
            elif field in CATEGORY_VALUES:
                cleaned[field] = _normalize_category(field, value)
            else:
                cleaned[field] = value
        except ValueError as error:
            errors.append("{}: {}".format(field, error))

    partial = numeric_values.get("partial_recovery_days")
    full = numeric_values.get("full_recovery_days")
    if partial is not None and full is not None and full < partial:
        errors.append(
            "full_recovery_days: must be greater than or equal to "
            "partial_recovery_days"
        )
    return cleaned, errors, numeric_values


def _validate_headers(raw_headers):
    if not raw_headers or any(header is None for header in raw_headers):
        raise ValueError("CSV must have one non-empty header row.")
    normalized = [_normalize_header(header) for header in raw_headers]
    if any(not header for header in normalized):
        raise ValueError("CSV headers cannot be blank.")
    duplicates = sorted(
        header for header, count in Counter(normalized).items() if count > 1
    )
    if duplicates:
        raise ValueError(
            "CSV has duplicate headers after normalization: {}".format(
                ", ".join(duplicates)
            )
        )
    missing = [field for field in FIELDS if field not in normalized]
    if missing:
        raise ValueError(
            "CSV is missing required columns: {}".format(", ".join(missing))
        )
    return normalized


def _prepare_output_paths(input_path, output_path, reject_path, report_path):
    input_resolved = Path(input_path).resolve()
    output_resolved = Path(output_path).resolve()
    reject_resolved = Path(reject_path).resolve()
    report_resolved = Path(report_path).resolve()
    destinations = (output_resolved, reject_resolved, report_resolved)
    if len(set(destinations)) != len(destinations):
        raise ValueError("Output, rejects, and report paths must be different.")
    if input_resolved in destinations:
        raise ValueError("Output files must not overwrite the input dataset.")
    return input_resolved, output_resolved, reject_resolved, report_resolved


def _temporary_file(destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        prefix="." + destination.name + ".",
        suffix=".tmp",
        dir=str(destination.parent),
        delete=False,
    )
    return handle


def preprocess_csv(input_path, output_path, reject_path=None, report_path=None):
    """Clean a CSV in one pass, separating invalid rows and writing a report."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    reject_path = Path(reject_path or output_path.with_name(
        output_path.stem + "_rejected.csv"
    ))
    report_path = Path(report_path or output_path.with_name(
        output_path.stem + "_report.json"
    ))
    input_path, output_path, reject_path, report_path = _prepare_output_paths(
        input_path, output_path, reject_path, report_path
    )

    temporary_paths = []
    handles = []
    try:
        with input_path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            _validate_headers(reader.fieldnames)
            clean_handle = _temporary_file(output_path)
            handles.append(clean_handle)
            temporary_paths.append(Path(clean_handle.name))
            reject_handle = _temporary_file(reject_path)
            handles.append(reject_handle)
            temporary_paths.append(Path(reject_handle.name))
            report_handle = _temporary_file(report_path)
            handles.append(report_handle)
            temporary_paths.append(Path(report_handle.name))

            clean_writer = csv.DictWriter(
                clean_handle, fieldnames=FIELDS, extrasaction="ignore"
            )
            reject_writer = csv.DictWriter(
                reject_handle,
                fieldnames=("source_row", "errors") + FIELDS,
                extrasaction="ignore",
            )
            clean_writer.writeheader()
            reject_writer.writeheader()

            report = {
                "input_file": str(input_path),
                "output_file": str(output_path),
                "reject_file": str(reject_path),
                "report_file": str(report_path),
                "input_rows": 0,
                "accepted_rows": 0,
                "rejected_rows": 0,
                "blank_rows": 0,
                "duplicate_ids": 0,
                "error_counts": Counter(),
                "category_counts": {
                    field: Counter() for field in CATEGORY_VALUES
                },
                "numeric_summary": {
                    field: {"count": 0, "min": None, "max": None, "sum": 0.0}
                    for field in tuple(INTEGER_RANGES) + tuple(DECIMAL_RANGES)
                },
            }
            seen_ids = set()

            for record in reader:
                report["input_rows"] += 1
                source_row = reader.line_num
                if record.get(None):
                    errors = ["row: contains more cells than the header"]
                    cleaned = {}
                    numeric_values = {}
                else:
                    normalized_record = {}
                    for raw_key, value in record.items():
                        if raw_key is not None:
                            normalized_record[_normalize_header(raw_key)] = value
                    if all(
                        not _normalize_text(normalized_record.get(field))
                        for field in FIELDS
                    ):
                        report["blank_rows"] += 1
                        continue

                    cleaned, errors, numeric_values = _normalize_record(
                        normalized_record
                    )
                    identifier = cleaned.get("disruption_id")
                    if identifier:
                        if identifier in seen_ids:
                            errors.append(
                                "disruption_id: duplicate identifier {}".format(
                                    identifier
                                )
                            )
                            report["duplicate_ids"] += 1
                        else:
                            seen_ids.add(identifier)

                if errors:
                    report["rejected_rows"] += 1
                    for error in errors:
                        report["error_counts"][error.split(":", 1)[0]] += 1
                    reject_writer.writerow({
                        "source_row": source_row,
                        "errors": " | ".join(errors),
                        **{
                            field: _normalize_text(
                                record.get(
                                    next(
                                        (
                                            key for key in record
                                            if _normalize_header(key) == field
                                        ),
                                        "",
                                    )
                                )
                            )
                            for field in FIELDS
                        },
                    })
                    continue

                clean_writer.writerow(cleaned)
                report["accepted_rows"] += 1
                for field in CATEGORY_VALUES:
                    report["category_counts"][field][cleaned[field]] += 1
                for field, number in numeric_values.items():
                    summary = report["numeric_summary"][field]
                    summary["count"] += 1
                    summary["sum"] += number
                    summary["min"] = (
                        number if summary["min"] is None
                        else min(summary["min"], number)
                    )
                    summary["max"] = (
                        number if summary["max"] is None
                        else max(summary["max"], number)
                    )

            for field, summary in report["numeric_summary"].items():
                if summary["count"]:
                    summary["mean"] = summary["sum"] / summary["count"]
                else:
                    summary["mean"] = None
                del summary["sum"]
            report["error_counts"] = dict(sorted(report["error_counts"].items()))
            report["category_counts"] = {
                field: dict(sorted(counts.items()))
                for field, counts in report["category_counts"].items()
            }
            json.dump(report, report_handle, indent=2, ensure_ascii=False)
            report_handle.write("\n")

        for handle in handles:
            handle.close()
        handles.clear()
        for temporary, destination in zip(
            temporary_paths, (output_path, reject_path, report_path)
        ):
            os.replace(str(temporary), str(destination))
        temporary_paths.clear()
        return report
    except (OSError, csv.Error, UnicodeError, ValueError):
        for handle in handles:
            if not handle.closed:
                handle.close()
        for temporary in temporary_paths:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate, normalize, and split an AtmoGraph disruption CSV."
    )
    parser.add_argument(
        "--input",
        default="datasets/raw/supply_chain_disruption_recovery.csv",
        help="Source CSV path",
    )
    parser.add_argument(
        "--output",
        default="datasets/processed/supply_chain_disruption_recovery_clean.csv",
        help="Cleaned CSV path",
    )
    parser.add_argument("--rejects", help="Invalid-row CSV path")
    parser.add_argument("--report", help="Quality-report JSON path")
    args = parser.parse_args(argv)
    report = preprocess_csv(args.input, args.output, args.rejects, args.report)
    print(
        "Preprocessing complete: {accepted_rows} accepted, "
        "{rejected_rows} rejected, {blank_rows} blank.".format(**report)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
