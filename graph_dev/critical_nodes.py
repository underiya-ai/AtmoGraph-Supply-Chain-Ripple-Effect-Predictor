import networkx as nx

from graph_loader import load_graph


def critical_nodes(G):
    """Scores every node. A critical node sits on many paths and many nodes depend on it."""
    betweenness = nx.betweenness_centrality(G)
    rows = []
    for node, data in G.nodes(data=True):
        rows.append(
            {
                "node_id": node,
                "name": data["name"],
                "node_type": data["node_type"],
                "downstream_count": len(nx.descendants(G, node)),
                "betweenness": round(betweenness[node], 4),
            }
        )
    rows.sort(key=lambda r: (-r["betweenness"], -r["downstream_count"], r["node_id"]))
    return rows


def main():
    G = load_graph()
    rows = critical_nodes(G)

    print("Top 10 critical nodes (by betweenness, then downstream reach):")
    for r in rows[:10]:
        print(f"  {r['betweenness']:7.4f}  reach {r['downstream_count']:3}  {r['node_id']}  {r['name']}")

    suppliers = [r for r in rows if r["node_type"] == "supplier"]
    suppliers.sort(key=lambda r: (-r["downstream_count"], r["node_id"]))
    print("\nSuppliers with the biggest downstream reach:")
    for r in suppliers[:5]:
        print(f"  reach {r['downstream_count']:3}  {r['node_id']}  {r['name']}")


if __name__ == "__main__":
    main()
