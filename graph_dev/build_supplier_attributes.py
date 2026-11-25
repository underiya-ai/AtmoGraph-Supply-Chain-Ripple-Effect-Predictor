import csv
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_FILE = (
    BASE_DIR.parent / "AtmoGraph_DataPreprocessing" / "data" / "processed" / "supply_chain_cleaned.csv"
)
NET_DIR = BASE_DIR / "network_data"

# Number columns we average per supplier (all exist in the dataset)
NUMBER_COLUMNS = [
    "disruption_severity",
    "production_impact_pct",
    "revenue_loss_usd",
    "response_time_days",
    "full_recovery_days",
]
# True/False columns: we calculate the share of True
YES_NO_COLUMNS = ["has_backup_supplier", "permanent_supplier_change"]


def load_supplier_lookup(nodes_file):
    """Returns {(industry, region, tier): node_id} for every supplier node."""
    lookup = {}
    with open(nodes_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["node_type"] == "supplier":
                key = (row["industry"], row["region"], int(row["tier"]))
                lookup[key] = row["node_id"]
    return lookup


def write_csv(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


def main():
    lookup = load_supplier_lookup(NET_DIR / "nodes.csv")
    print("Supplier nodes in network:", len(lookup))

    counts = defaultdict(int)
    totals = defaultdict(lambda: defaultdict(float))
    mapping = []
    unmatched = 0

    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["industry"], row["supplier_region"], int(row["supplier_tier"]))
            node_id = lookup.get(key)
            if node_id is None:
                unmatched += 1
                continue

            mapping.append((row["disruption_id"], node_id))
            counts[node_id] += 1
            for col in NUMBER_COLUMNS:
                totals[node_id][col] += float(row[col])
            for col in YES_NO_COLUMNS:
                totals[node_id][col] += 1 if row[col].strip().lower() == "true" else 0

    # One row per supplier with its averages
    columns = (
        ["supplier_id", "disruption_count"]
        + [f"avg_{c}" for c in NUMBER_COLUMNS]
        + [f"share_{c}" for c in YES_NO_COLUMNS]
    )
    rows = []
    for node_id in sorted(counts):
        n = counts[node_id]
        row = [node_id, n]
        row += [round(totals[node_id][c] / n, 2) for c in NUMBER_COLUMNS]
        row += [round(totals[node_id][c] / n, 2) for c in YES_NO_COLUMNS]
        rows.append(row)

    write_csv(NET_DIR / "supplier_attributes.csv", columns, rows)
    write_csv(NET_DIR / "disruption_mapping.csv", ["disruption_id", "supplier_id"], mapping)

    print("Disruption records matched to a supplier:", len(mapping))
    print("Records with no matching supplier:", unmatched)
    print("Suppliers with data:", len(rows), "of", len(lookup))
    print("Saved to:", NET_DIR)
    print("\nFirst 3 suppliers:")
    print(columns)
    for r in rows[:3]:
        print(r)


if __name__ == "__main__":
    main()



