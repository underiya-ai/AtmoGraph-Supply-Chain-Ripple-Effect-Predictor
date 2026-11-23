import json
import sys
from pathlib import Path

from graph_loader import load_graph
from ripple_simulation import pick_default_source, simulate_ripple, start_impact_for

OUT_DIR = Path(__file__).parent / "output"


def build_ripple_json(G, source, start_impact=None):
    """Result of disrupting `source`, as a plain dictionary ready for the API."""
    if start_impact is None:
        start_impact = start_impact_for(G, source)
    results = simulate_ripple(G, source, start_impact)

    levels = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in results:
        levels[r["risk_level"]] += 1

    return {
        "disrupted_node": source,
        "disrupted_name": G.nodes[source]["name"],
        "start_impact": round(float(start_impact), 2),
        "total_affected": len(results),
        "by_risk_level": levels,
        "affected": results,
    }


def build_network_json(G):
    """The whole network (nodes with their attributes, and edges) as a dictionary."""
    nodes = [{"node_id": n, **data} for n, data in G.nodes(data=True)]
    edges = [{"source": u, "target": v} for u, v in G.edges()]
    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


def save_json(data, path):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main():
    G = load_graph()
    source = sys.argv[1] if len(sys.argv) > 1 else pick_default_source(G)
    if source not in G:
        print(f"Unknown node: {source}")
        return
    start = float(sys.argv[2]) if len(sys.argv) > 2 else None

    OUT_DIR.mkdir(exist_ok=True)

    ripple = build_ripple_json(G, source, start)
    ripple_path = OUT_DIR / f"ripple_{source}.json"
    save_json(ripple, ripple_path)

    network_path = OUT_DIR / "network.json"
    save_json(build_network_json(G), network_path)

    # Read the files back to prove they are valid JSON
    json.loads(ripple_path.read_text(encoding="utf-8"))
    json.loads(network_path.read_text(encoding="utf-8"))

    print("Saved:", ripple_path)
    print("Saved:", network_path)
    print("\nDisrupted:", ripple["disrupted_node"], "-", ripple["disrupted_name"])
    print("Total affected:", ripple["total_affected"], ripple["by_risk_level"])
    if ripple["affected"]:
        print("First affected node:")
        print(json.dumps(ripple["affected"][0], indent=2))
    else:
        print("Nothing is downstream of this node, so nobody is affected.")


if __name__ == "__main__":
    main()
