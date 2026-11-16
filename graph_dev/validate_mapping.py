import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_FILE = (
    BASE_DIR.parent / "datasets" / "raw" / "supply_chain_disruption_recovery.csv"
)
NET_DIR = BASE_DIR / "network_data"


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    lines = []

    def report(text):
        print(text)
        lines.append(text)

    def check(name, ok):
        report(("PASS  " if ok else "FAIL  ") + name)
        return ok

    nodes = read_rows(NET_DIR / "nodes.csv")
    edges = read_rows(NET_DIR / "edges.csv")
    attrs = read_rows(NET_DIR / "supplier_attributes.csv")
    mapping = read_rows(NET_DIR / "disruption_mapping.csv")
    dataset_ids = [r["disruption_id"] for r in read_rows(DATA_FILE)]

    node_ids = [n["node_id"] for n in nodes]
    node_set = set(node_ids)
    supplier_set = {n["node_id"] for n in nodes if n["node_type"] == "supplier"}
    mapped_ids = [m["disruption_id"] for m in mapping]

    report("Mapping and network checks")
    report("--------------------------")
    check("Node ids are unique", len(node_ids) == len(node_set))
    check(
        "Every edge points to an existing node",
        all(e["source"] in node_set and e["target"] in node_set for e in edges),
    )
    check(
        f"Mapping has one row per dataset record ({len(mapping)} of {len(dataset_ids)})",
        len(mapping) == len(dataset_ids),
    )
    check("No disruption_id is mapped twice", len(mapped_ids) == len(set(mapped_ids)))
    check("Mapped ids match the dataset ids", set(mapped_ids) == set(dataset_ids))
    check(
        "Every mapped supplier exists in nodes.csv",
        all(m["supplier_id"] in supplier_set for m in mapping),
    )
    check(
        "Every supplier node has attribute data",
        {a["supplier_id"] for a in attrs} == supplier_set,
    )
    check(
        "Disruption counts in attributes add up to the mapping rows",
        sum(int(a["disruption_count"]) for a in attrs) == len(mapping),
    )

    # Readable findings for the write-up
    names = {n["node_id"]: n["name"] for n in nodes}
    by_recovery = sorted(attrs, key=lambda a: float(a["avg_full_recovery_days"]))
    low, high = by_recovery[0], by_recovery[-1]
    by_count = sorted(attrs, key=lambda a: int(a["disruption_count"]))

    report("")
    report("Findings")
    report("--------")
    report(
        f"Slowest recovery: {high['supplier_id']} ({names[high['supplier_id']]}) "
        f"- {high['avg_full_recovery_days']} days"
    )
    report(
        f"Fastest recovery: {low['supplier_id']} ({names[low['supplier_id']]}) "
        f"- {low['avg_full_recovery_days']} days"
    )
    report(
        f"Fewest disruption records: {by_count[0]['supplier_id']} "
        f"({by_count[0]['disruption_count']})"
    )
    report(
        f"Most disruption records: {by_count[-1]['supplier_id']} "
        f"({by_count[-1]['disruption_count']})"
    )

    with open(NET_DIR / "mapping_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\nReport saved to:", NET_DIR / "mapping_report.txt")


if __name__ == "__main__":
    main()
