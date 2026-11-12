from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd

# Folder where this script lives, so the CSV files are always found
BASE_DIR = Path(__file__).parent


def load_graph(nodes_file, edges_file):
    """Reads two CSV files and returns a directed graph."""
    nodes_df = pd.read_csv(nodes_file)
    edges_df = pd.read_csv(edges_file)

    # Check that every edge points to a node that exists
    known_ids = set(nodes_df["node_id"])
    used_ids = set(edges_df["source"]) | set(edges_df["target"])
    missing = used_ids - known_ids
    if missing:
        raise ValueError(f"Edges use unknown node ids: {sorted(missing)}")

    G = nx.DiGraph()

    # Each row becomes a node; the other columns become attributes
    for row in nodes_df.to_dict("records"):
        node_id = row.pop("node_id")
        G.add_node(node_id, **row)

    # Each row becomes a directed edge: source -> target
    for row in edges_df.to_dict("records"):
        G.add_edge(row["source"], row["target"])

    return G


def main():
    G = load_graph(BASE_DIR / "sample_nodes.csv", BASE_DIR / "sample_edges.csv")

    print("Total nodes:", G.number_of_nodes())
    print("Total edges:", G.number_of_edges())

    types = Counter(data["node_type"] for _, data in G.nodes(data=True))
    print("Nodes by type:", dict(types))

    affected_ids = nx.descendants(G, "F1")
    affected_names = sorted(G.nodes[n]["name"] for n in affected_ids)
    print("Downstream of Factory A:", affected_names)


if __name__ == "__main__":
    main()