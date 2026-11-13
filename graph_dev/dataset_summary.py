from pathlib import Path

import pandas as pd

# AtmoGraph/datasets/raw/... found from this script's location
DATA_FILE = (
    Path(__file__).parent.parent
    / "datasets"
    / "raw"
    / "supply_chain_disruption_recovery.csv"
)

# Number columns we will summarise
DAMAGE_COLUMNS = [
    "disruption_severity",
    "production_impact_pct",
    "full_recovery_days",
]


def main():
    df = pd.read_csv(DATA_FILE)
    print("Rows, columns:", df.shape)

    # How many rows for each value in the category columns
    for col in ["supplier_tier", "supplier_region", "industry", "supplier_size"]:
        print(f"\nRows per {col}:")
        print(df[col].value_counts().sort_index())

    # Average damage grouped by a column
    for col in ["supplier_tier", "supplier_region", "industry", "has_backup_supplier"]:
        print(f"\nAverages by {col}:")
        print(df.groupby(col)[DAMAGE_COLUMNS].mean().round(2))


if __name__ == "__main__":
    main()