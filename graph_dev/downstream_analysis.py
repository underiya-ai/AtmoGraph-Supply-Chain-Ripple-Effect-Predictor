import sys

import networkx as nx

from graph_loader import load_graph


def downstream_levels(G, source):
    """Returns {node: steps_from_source} for everything downstream of source (BFS)."""
    distances = nx.single_source_shortest_path_length(G, source)
    distances.pop(source)  # the source itself is not "affected downstream"
    return distances


def group_by_level(distances):
    """Turns {node: steps} into {steps: [nodes]}, sorted by steps."""
    levels = {}
    for node, steps in distances.items():
        levels.setdefault(steps, []).append(node)
    return {steps: sorted(nodes) for steps, nodes in sorted(levels.items())}


def count_by_type(G, nodes):
    """Counts how many of the given nodes are suppliers, factories and so on."""
    counts = {}
    for node in nodes:
        node_type = G.nodes[node]["node_type"]
        counts[node_type] = counts.get(node_type, 0) + 1
    return counts


def upstream_suppliers(G, target):
    """Everything that feeds into target, directly or indirectly."""
    return sorted(nx.ancestors(G, target))


def pick_default_source(G):
    """A tier 2 supplier is a good demo: it has something upstream and downstream."""
    for node, data in G.nodes(data=True):
        if data["node_type"] == "supplier" and data["tier"] == 2:
            return node
    return next(iter(G.nodes))


def main():
    G = load_graph()
    source = sys.argv[1] if len(sys.argv) > 1 else pick_default_source(G)
    if source not in G:
        print(f"Unknown node: {source}")
        return

    print("Disrupted node:", source, "-", G.nodes[source]["name"])

    distances = downstream_levels(G, source)
    print("Total affected downstream:", len(distances))
    print("Affected by type:", count_by_type(G, distances))

    print("\nBy distance (number of steps from the disrupted node):")
    for steps, nodes in group_by_level(distances).items():
        names = [G.nodes[n]["name"] for n in nodes]
        shown = ", ".join(names[:3]) + (" ..." if len(names) > 3 else "")
        print(f"  {steps} step(s): {len(nodes)} node(s) - {shown}")

    retailers = [n for n in distances if G.nodes[n]["node_type"] == "retailer"]
    print("\nRetailers affected:", len(retailers))
    for r in sorted(retailers):
        print(f"  {distances[r]} steps - {r} - {G.nodes[r]['name']}")

    print("\nUpstream of the disrupted node:", len(upstream_suppliers(G, source)), "nodes")


if __name__ == "__main__":
    main()
