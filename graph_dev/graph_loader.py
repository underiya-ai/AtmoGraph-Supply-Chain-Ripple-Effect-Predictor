import csv
from pathlib import Path

import networkx as nx

NET_DIR = Path(__file__).parent / "network_data"

# Which node types may be connected, in the direction goods flow
ALLOWED_LINKS = {
    ("supplier", "supplier"),
    ("supplier", "factory"),
    ("factory", "warehouse"),
    ("warehouse", "retailer"),
}


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_graph(net_dir=NET_DIR):
    """Builds ONE directed graph from nodes.csv, edges.csv and supplier_attributes.csv."""
    net_dir = Path(net_dir)
    G = nx.DiGraph()

    # 1. Nodes (the other columns become node attributes)
    for row in read_rows(net_dir / "nodes.csv"):
        node_id = row.pop("node_id")
        row["tier"] = int(row["tier"]) if row["tier"] else None
        G.add_node(node_id, **row)

    # 2. Edges: source -> target, only between known nodes
    for row in read_rows(net_dir / "edges.csv"):
        if row["source"] not in G or row["target"] not in G:
            raise ValueError(f"Edge uses an unknown node: {row}")
        G.add_edge(row["source"], row["target"])

    # 3. Disruption averages, stored on the supplier nodes
    for row in read_rows(net_dir / "supplier_attributes.csv"):
        supplier_id = row.pop("supplier_id")
        if supplier_id not in G:
            raise ValueError(f"Attributes for unknown node: {supplier_id}")
        for key, value in row.items():
            G.nodes[supplier_id][key] = int(value) if key == "disruption_count" else float(value)

    return G


def validate_graph(G):
    """Returns a list of problems found. An empty list means the graph looks healthy."""
    problems = []

    if not nx.is_directed_acyclic_graph(G):
        problems.append("The graph has a loop")

    for node in nx.isolates(G):
        problems.append(f"{node} has no connections")

    for node, data in G.nodes(data=True):
        if data["node_type"] == "supplier" and "avg_full_recovery_days" not in data:
            problems.append(f"{node} has no disruption attributes")

    for u, v in G.edges():
        a, b = G.nodes[u], G.nodes[v]
        pair = (a["node_type"], b["node_type"])
        if pair not in ALLOWED_LINKS:
            problems.append(f"Unexpected link {u} -> {v} ({pair[0]} to {pair[1]})")
        if a["industry"] != b["industry"]:
            problems.append(f"{u} -> {v} connects different industries")
        if pair == ("supplier", "supplier") and b["tier"] != a["tier"] - 1:
            problems.append(f"{u} -> {v} does not step down one tier")
        if pair == ("supplier", "factory") and a["tier"] != 1:
            problems.append(f"{u} -> {v}: only tier 1 suppliers should feed factories")

    return problems


def main():
    G = load_graph()
    print("Total nodes:", G.number_of_nodes())
    print("Total edges:", G.number_of_edges())

    counts = {}
    for _, data in G.nodes(data=True):
        counts[data["node_type"]] = counts.get(data["node_type"], 0) + 1
    print("Nodes by type:", counts)

    problems = validate_graph(G)
    print("\nProblems found:", len(problems))
    for p in problems[:10]:
        print(" -", p)

    # Look at one furthest-upstream supplier
    top_tier = max(d["tier"] for _, d in G.nodes(data=True) if d["tier"] is not None)
    example = next(
        n for n, d in G.nodes(data=True) if d["node_type"] == "supplier" and d["tier"] == top_tier
    )
    data = G.nodes[example]
    print("\nExample node:", example, "-", data["name"])
    print("Average full recovery days:", data["avg_full_recovery_days"])
    print("Direct downstream:", [G.nodes[n]["name"] for n in G.successors(example)])
    print("All downstream nodes:", len(nx.descendants(G, example)))


if __name__ == "__main__":
    main()
