import json
import unittest

import networkx as nx

from export_json import build_network_json, build_ripple_json
from graph_loader import load_graph, validate_graph
from ripple_simulation import (
    HIGH_LEVEL,
    MEDIUM_LEVEL,
    pick_default_source,
    risk_level,
    simulate_ripple,
)


class GraphModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.G = load_graph()
        cls.source = pick_default_source(cls.G)

    # ---- the graph itself ----
    def test_graph_has_no_problems(self):
        self.assertEqual(validate_graph(self.G), [])

    def test_graph_has_no_loops(self):
        self.assertTrue(nx.is_directed_acyclic_graph(self.G))

    def test_every_supplier_has_disruption_data(self):
        for node, data in self.G.nodes(data=True):
            if data["node_type"] == "supplier":
                self.assertIn("avg_full_recovery_days", data, node)

    # ---- the ripple simulation ----
    def test_retailer_has_nothing_downstream(self):
        retailer = next(
            n for n, d in self.G.nodes(data=True) if d["node_type"] == "retailer"
        )
        self.assertEqual(simulate_ripple(self.G, retailer, 50), [])

    def test_affected_nodes_are_exactly_the_downstream_nodes(self):
        results = simulate_ripple(self.G, self.source, 50)
        self.assertEqual(
            {r["node_id"] for r in results}, nx.descendants(self.G, self.source)
        )

    def test_impact_stays_between_zero_and_start(self):
        for r in simulate_ripple(self.G, self.source, 50):
            self.assertGreaterEqual(r["impact"], 0)
            self.assertLessEqual(r["impact"], 50)

    def test_bigger_start_gives_bigger_impact(self):
        low = {r["node_id"]: r["impact"] for r in simulate_ripple(self.G, self.source, 40)}
        high = {r["node_id"]: r["impact"] for r in simulate_ripple(self.G, self.source, 80)}
        for node in low:
            self.assertGreaterEqual(high[node], low[node])

    def test_risk_levels(self):
        self.assertEqual(risk_level(HIGH_LEVEL), "HIGH")
        self.assertEqual(risk_level(MEDIUM_LEVEL), "MEDIUM")
        self.assertEqual(risk_level(MEDIUM_LEVEL - 1), "LOW")

    # ---- the JSON for the backend ----
    def test_ripple_json_is_consistent(self):
        data = build_ripple_json(self.G, self.source, 50)
        json.dumps(data)  # must not raise an error
        self.assertEqual(data["total_affected"], len(data["affected"]))
        self.assertEqual(sum(data["by_risk_level"].values()), data["total_affected"])

    def test_network_json_counts(self):
        data = build_network_json(self.G)
        self.assertEqual(data["total_nodes"], self.G.number_of_nodes())
        self.assertEqual(data["total_edges"], self.G.number_of_edges())
        self.assertEqual(len(data["nodes"]), data["total_nodes"])
        self.assertEqual(len(data["edges"]), data["total_edges"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
