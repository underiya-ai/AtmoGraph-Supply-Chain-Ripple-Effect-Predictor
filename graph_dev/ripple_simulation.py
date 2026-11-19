import sys

import networkx as nx

from graph_loader import load_graph

# Simple, explainable rules (a heuristic, not a trained model)
STEP_FACTOR = 0.9  # the effect weakens by 10% at every step downstream
HIGH_LEVEL = 25    # impact score at or above this = HIGH
MEDIUM_LEVEL = 10  # at or above this = MEDIUM, below = LOW
DEFAULT_START_IMPACT = 50.0  # used when the disrupted node has no dataset average


def pick_default_source(G):
    """A tier 2 supplier is a good demo: it has something upstream and downstream."""
    for node, data in G.nodes(data=True):
        if data["node_type"] == "supplier" and data["tier"] == 2:
            return node
    return next(iter(G.nodes))


def risk_level(impact):
    if impact >= HIGH_LEVEL:
        return "HIGH"
    if impact >= MEDIUM_LEVEL:
        return "MEDIUM"
    return "LOW"


def start_impact_for(G, source):
    """Real average production impact (%) of a supplier, or a default for other nodes."""
    return G.nodes[source].get("avg_production_impact_pct", DEFAULT_START_IMPACT)


def simulate_ripple(G, source, start_impact):
    """Disrupts `source` and returns the affected downstream nodes with an impact score.

    Rule: a node is hurt in proportion to how many of its suppliers are hit.
        impact = STEP_FACTOR * (sum of impact of its affected suppliers) / (number of its suppliers)
    A node with many alternative suppliers is therefore hurt less.
    """
    impact = {source: float(start_impact)}
    distance = nx.single_source_shortest_path_length(G, source)
    reachable = nx.descendants(G, source)

    # Topological order: every supplier is processed before the nodes it feeds
    for node in nx.topological_sort(G):
        if node not in reachable:
            continue
        hit = sum(impact[p] for p in G.predecessors(node) if p in impact)
        impact[node] = min(100.0, STEP_FACTOR * hit / G.in_degree(node))

    results = []
    for node in reachable:
        results.append(
            {
                "node_id": node,
                "name": G.nodes[node]["name"],
                "node_type": G.nodes[node]["node_type"],
                "distance": distance[node],
                "impact": round(impact[node], 2),
                "risk_level": risk_level(impact[node]),
            }
        )
    results.sort(key=lambda r: (r["distance"], -r["impact"], r["node_id"]))
    return results


def main():
    G = load_graph()
    source = sys.argv[1] if len(sys.argv) > 1 else pick_default_source(G)
    if source not in G:
        print(f"Unknown node: {source}")
        return
    start = float(sys.argv[2]) if len(sys.argv) > 2 else start_impact_for(G, source)

    print("Disrupted node:", source, "-", G.nodes[source]["name"])
    print("Starting impact:", start)

    results = simulate_ripple(G, source, start)
    print("Affected downstream:", len(results))

    levels = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in results:
        levels[r["risk_level"]] += 1
    print("By risk level:", levels)

    print("\nMost impacted nodes:")
    for r in sorted(results, key=lambda r: -r["impact"])[:8]:
        print(f"  {r['impact']:6.2f}  {r['risk_level']:6}  {r['distance']} step(s)  {r['node_id']}  {r['name']}")

    retailers = [r for r in results if r["node_type"] == "retailer"]
    print("\nRetailers affected:", len(retailers))
    for r in sorted(retailers, key=lambda r: -r["impact"]):
        print(f"  {r['impact']:6.2f}  {r['risk_level']:6}  {r['node_id']}  {r['name']}")


if __name__ == "__main__":
    main()
