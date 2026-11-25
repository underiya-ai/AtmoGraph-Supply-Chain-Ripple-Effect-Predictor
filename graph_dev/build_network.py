import csv
import random
from pathlib import Path

import networkx as nx

BASE_DIR = Path(__file__).parent
DATA_FILE = (
    BASE_DIR.parent / "AtmoGraph_DataPreprocessing" / "data" / "processed" / "supply_chain_cleaned.csv"
)
OUT_DIR = BASE_DIR / "network_data"

SEED = 42  # same seed = same network every time
FACTORIES_PER_INDUSTRY = 2
WAREHOUSES_PER_INDUSTRY = 3
RETAILERS_PER_INDUSTRY = 5
LINKS_PER_NODE = 2  # each node connects to up to this many nodes one step downstream

NODE_COLUMNS = ["node_id", "name", "node_type", "industry", "region", "tier"]


def read_unique_values(path):
    """Reads the dataset and returns the sorted industries, regions and tiers."""
    industries, regions, tiers = set(), set(), set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            industries.add(row["industry"])
            regions.add(row["supplier_region"])
            tiers.add(int(row["supplier_tier"]))
    return sorted(industries), sorted(regions), sorted(tiers)


def make_sites(prefix, node_type, count, i, industry, regions):
    """Makes factory / warehouse / retailer rows for one industry."""
    rows = []
    for n in range(1, count + 1):
        region = regions[(n - 1) % len(regions)]
        rows.append(
            {
                "node_id": f"{prefix}-I{i}-{n}",
                "name": f"{industry} {node_type.title()} {n}",
                "node_type": node_type,
                "industry": industry,
                "region": region,
                "tier": "",
            }
        )
    return rows


def build_nodes(industries, regions, tiers):
    """One supplier per (industry, region, tier), plus factories, warehouses, retailers."""
    rows = []
    for i, industry in enumerate(industries, start=1):
        for r, region in enumerate(regions, start=1):
            for tier in tiers:
                rows.append(
                    {
                        "node_id": f"SUP-I{i}-R{r}-T{tier}",
                        "name": f"{industry} Supplier ({region}, Tier {tier})",
                        "node_type": "supplier",
                        "industry": industry,
                        "region": region,
                        "tier": tier,
                    }
                )
        rows += make_sites("FAC", "factory", FACTORIES_PER_INDUSTRY, i, industry, regions)
        rows += make_sites("WH", "warehouse", WAREHOUSES_PER_INDUSTRY, i, industry, regions)
        rows += make_sites("RET", "retailer", RETAILERS_PER_INDUSTRY, i, industry, regions)
    return rows


def link_layers(sources, targets, rng):
    """Connects one layer to the next layer downstream."""
    edges = set()
    k = min(LINKS_PER_NODE, len(targets))
    for s in sources:
        for t in rng.sample(targets, k):
            edges.add((s, t))
    # Make sure every downstream node has at least one supplier
    linked = {t for _, t in edges}
    for t in targets:
        if t not in linked:
            edges.add((rng.choice(sources), t))
    return edges


def build_edges(nodes, industries, tiers, rng):
    """Connects layers inside each industry: tier 4 -> 3 -> 2 -> 1 -> factory -> warehouse -> retailer."""
    edges = set()
    for industry in industries:
        group = [n for n in nodes if n["industry"] == industry]
        layers = []
        for tier in sorted(tiers, reverse=True):
            layers.append(
                [n["node_id"] for n in group
                 if n["node_type"] == "supplier" and n["tier"] == tier]
            )
        for node_type in ["factory", "warehouse", "retailer"]:
            layers.append([n["node_id"] for n in group if n["node_type"] == node_type])

        for upstream, downstream in zip(layers, layers[1:]):
            edges |= link_layers(upstream, downstream, rng)

    return sorted(edges)


def write_csv(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


def main():
    industries, regions, tiers = read_unique_values(DATA_FILE)
    print("Industries:", industries)
    print("Regions:", regions)
    print("Tiers:", tiers)

    rng = random.Random(SEED)
    nodes = build_nodes(industries, regions, tiers)
    edges = build_edges(nodes, industries, tiers, rng)

    OUT_DIR.mkdir(exist_ok=True)
    write_csv(OUT_DIR / "nodes.csv", NODE_COLUMNS, [[n[c] for c in NODE_COLUMNS] for n in nodes])
    write_csv(OUT_DIR / "edges.csv", ["source", "target"], edges)

    # Quick checks
    G = nx.DiGraph()
    G.add_nodes_from(n["node_id"] for n in nodes)
    G.add_edges_from(edges)
    counts = {}
    for n in nodes:
        counts[n["node_type"]] = counts.get(n["node_type"], 0) + 1
    print("\nTotal nodes:", G.number_of_nodes())
    print("Total edges:", G.number_of_edges())
    print("Nodes by type:", counts)
    print("Has no loops (DAG):", nx.is_directed_acyclic_graph(G))
    print("Isolated nodes:", list(nx.isolates(G)))
    print("Saved to:", OUT_DIR)


if __name__ == "__main__":
    main()



