from graph_loader import load_graph
from ripple_simulation import pick_default_source, simulate_ripple, start_impact_for

VALID_STATES = ("NORMAL", "LOW", "MEDIUM", "HIGH", "DISRUPTED")


def reset_risks(G):
    """Gives every node the state NORMAL."""
    for node in G.nodes:
        G.nodes[node]["risk_state"] = "NORMAL"
        G.nodes[node]["risk_reason"] = ""


def update_node_risk(G, node_id, state, reason=""):
    """Sets the risk state of one node. The NLP part of the project can call this."""
    if node_id not in G:
        raise ValueError(f"Unknown node: {node_id}")
    state = state.upper()
    if state not in VALID_STATES:
        raise ValueError(f"State must be one of {VALID_STATES}, not {state}")
    G.nodes[node_id]["risk_state"] = state
    G.nodes[node_id]["risk_reason"] = reason


def apply_ripple(G, source, results):
    """Copies the result of a ripple simulation onto the nodes as risk states."""
    update_node_risk(G, source, "DISRUPTED", "source of the disruption")
    for r in results:
        update_node_risk(
            G, r["node_id"], r["risk_level"],
            f"ripple from {source}, {r['distance']} step(s) away",
        )


def nodes_at_risk(G):
    """All nodes whose state is not NORMAL."""
    return [
        (n, d["risk_state"]) for n, d in G.nodes(data=True)
        if d.get("risk_state", "NORMAL") != "NORMAL"
    ]


def main():
    G = load_graph()
    reset_risks(G)

    # Pretend a news item says this supplier has a problem (this is what the NLP part would send)
    source = pick_default_source(G)
    print("News says:", G.nodes[source]["name"], "has a problem")
    results = simulate_ripple(G, source, start_impact_for(G, source))
    apply_ripple(G, source, results)

    counts = {}
    for _, d in G.nodes(data=True):
        counts[d["risk_state"]] = counts.get(d["risk_state"], 0) + 1
    print("Nodes by risk state:", counts)
    print("Nodes at risk:", len(nodes_at_risk(G)))

    # A wrong value is rejected with a clear message
    try:
        update_node_risk(G, source, "BROKEN")
    except ValueError as error:
        print("Rejected wrong state:", error)

    # Back to normal
    reset_risks(G)
    print("After reset, nodes at risk:", len(nodes_at_risk(G)))


if __name__ == "__main__":
    main()
