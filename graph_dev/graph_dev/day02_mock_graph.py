import networkx as nx
from collections import Counter


def build_mock_graph():
    """Builds a small SAMPLE supply chain graph (not real team data)."""
    G = nx.DiGraph()

    # (name, type) for every entity
    nodes = [
        ("Supplier A", "supplier"),
        ("Supplier B", "supplier"),
        ("Factory A", "factory"),
        ("Factory B", "factory"),
        ("Warehouse A", "warehouse"),
        ("Warehouse B", "warehouse"),
        ("Retailer A", "retailer"),
        ("Retailer B", "retailer"),
        ("Retailer C", "retailer"),
    ]
    for name, node_type in nodes:
        G.add_node(name, node_type=node_type)

    # (from, to): goods flow in this direction
    edges = [
        ("Supplier A", "Factory A"),
        ("Supplier B", "Factory A"),
        ("Supplier B", "Factory B"),
        ("Factory A", "Warehouse A"),
        ("Factory A", "Warehouse B"),
        ("Factory B", "Warehouse B"),
        ("Warehouse A", "Retailer A"),
        ("Warehouse A", "Retailer B"),
        ("Warehouse B", "Retailer C"),
    ]
    G.add_edges_from(edges)
    return G


def main():
    G = build_mock_graph()

    print("Total nodes:", G.number_of_nodes())
    print("Total edges:", G.number_of_edges())

    # Count how many nodes of each type
    types = Counter(data["node_type"] for _, data in G.nodes(data=True))
    print("Nodes by type:", dict(types))

    # Everything reachable from Factory A (all downstream entities)
    affected = nx.descendants(G, "Factory A")
    print("Downstream of Factory A:", sorted(affected))


if __name__ == "__main__":
    main()