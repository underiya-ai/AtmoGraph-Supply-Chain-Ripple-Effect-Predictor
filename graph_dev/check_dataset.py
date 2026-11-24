import csv
import sys
from pathlib import Path

RAW_FILE = (
    Path(__file__).parent.parent / "datasets" / "raw" / "supply_chain_disruption_recovery.csv"
)

# Columns our scripts read by name
REQUIRED = [
    "disruption_id", "industry", "supplier_region", "supplier_tier",
    "disruption_severity", "production_impact_pct", "revenue_loss_usd",
    "response_time_days", "full_recovery_days",
    "has_backup_supplier", "permanent_supplier_change",
]
NUMBER_COLUMNS = [
    "disruption_severity", "production_impact_pct", "revenue_loss_usd",
    "response_time_days", "full_recovery_days",
]
YES_NO_COLUMNS = ["has_backup_supplier", "permanent_supplier_change"]


def scan(path):
    """Reads a dataset file and collects what our scripts care about."""
    info = {
        "headers": [], "rows": 0, "industries": set(), "regions": set(), "tiers": set(),
        "bad_numbers": 0, "bad_yes_no": set(), "duplicate_ids": 0,
    }
    seen = set()
    # utf-8 is what our scripts use, so a hidden BOM shows up here as a bad header
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        info["headers"] = reader.fieldnames or []
        if any(c not in info["headers"] for c in REQUIRED):
            return info
        for row in reader:
            info["rows"] += 1
            try:
                for c in NUMBER_COLUMNS:
                    float(row[c])
                info["tiers"].add(int(row["supplier_tier"]))
            except (ValueError, TypeError):
                info["bad_numbers"] += 1
                continue
            info["industries"].add(row["industry"])
            info["regions"].add(row["supplier_region"])
            for c in YES_NO_COLUMNS:
                if row[c].strip().lower() not in ("true", "false"):
                    info["bad_yes_no"].add(row[c])
            if row["disruption_id"] in seen:
                info["duplicate_ids"] += 1
            seen.add(row["disruption_id"])
    return info


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_dataset.py <path-to-cleaned-csv>")
        return
    clean_path = Path(sys.argv[1])
    clean = scan(clean_path)
    raw = scan(RAW_FILE)
    failed = False

    def check(name, ok):
        nonlocal failed
        print(("PASS  " if ok else "FAIL  ") + name)
        failed = failed or not ok

    print("File:", clean_path)
    print("Rows: raw", raw["rows"], "| cleaned", clean["rows"], "\n")

    missing = [c for c in REQUIRED if c not in clean["headers"]]
    check("All columns our scripts need are present", not missing)
    if missing:
        print("      Missing:", missing)
        print("      First header names found:", clean["headers"][:5])
        print("\nNot safe to switch. Send me the lines above.")
        return

    check(f"Number columns can be read ({clean['bad_numbers']} bad rows)", clean["bad_numbers"] == 0)
    check("True/False columns use True or False", not clean["bad_yes_no"])
    if clean["bad_yes_no"]:
        print("      Other values found:", sorted(clean["bad_yes_no"])[:5])
    check(f"No duplicate disruption ids ({clean['duplicate_ids']})", clean["duplicate_ids"] == 0)
    check("Cleaned file has at least one row", clean["rows"] > 0)

    print()
    same = (clean["industries"] == raw["industries"] and clean["regions"] == raw["regions"]
            and clean["tiers"] == raw["tiers"])
    print("NOTE  Same industries, regions and tiers as the raw file:", same)
    if not same:
        print("      Industries:", sorted(clean["industries"]))
        print("      Regions:", sorted(clean["regions"]))
        print("      Tiers:", sorted(clean["tiers"]))
        print("      The network will have a different number of nodes. That is fine, but tell the team.")

    print("\n" + ("Not safe to switch. Send me the lines above." if failed else "Safe to switch to this file."))


if __name__ == "__main__":
    main()
