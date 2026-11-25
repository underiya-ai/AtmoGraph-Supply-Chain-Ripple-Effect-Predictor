import unittest

import networkx as nx

from critical_nodes import critical_nodes
from graph_loader import load_graph
from ripple_simulation import pick_default_source, simulate_ripple
from risk_state import apply_ripple, nodes_at_risk, reset_risks, update_node_risk


class RiskStateTests(unittest.TestCase):
    def setUp(self):
        self.G = load_graph()
        reset_risks(self.G)
        self.source = pick_default_source(self.G)

    def test_everything_starts_normal(self):
        self.assertEqual(nodes_at_risk(self.G), [])

    def test_update_sets_state_and_reason(self):
        update_node_risk(self.G, self.source, "high", "port strike")
        self.assertEqual(self.G.nodes[self.source]["risk_state"], "HIGH")
        self.assertEqual(self.G.nodes[self.source]["risk_reason"], "port strike")

    def test_unknown_node_is_rejected(self):
        with self.assertRaises(ValueError):
            update_node_risk(self.G, "NO-SUCH-NODE", "HIGH")

    def test_wrong_state_is_rejected(self):
        with self.assertRaises(ValueError):
            update_node_risk(self.G, self.source, "BROKEN")

    def test_apply_ripple_marks_source_and_affected_nodes(self):
        results = simulate_ripple(self.G, self.source, 50)
        apply_ripple(self.G, self.source, results)
        self.assertEqual(self.G.nodes[self.source]["risk_state"], "DISRUPTED")
        self.assertEqual(len(nodes_at_risk(self.G)), len(results) + 1)

    def test_reset_clears_everything(self):
        apply_ripple(self.G, self.source, simulate_ripple(self.G, self.source, 50))
        reset_risks(self.G)
        self.assertEqual(nodes_at_risk(self.G), [])


class CriticalNodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.G = load_graph()
        cls.rows = critical_nodes(cls.G)

    def test_one_row_per_node(self):
        self.assertEqual(len(self.rows), self.G.number_of_nodes())

    def test_sorted_from_most_to_least_critical(self):
        scores = [r["betweenness"] for r in self.rows]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_retailers_have_nothing_downstream(self):
        for r in self.rows:
            if r["node_type"] == "retailer":
                self.assertEqual(r["downstream_count"], 0)

    def test_reach_matches_descendants(self):
        r = self.rows[0]
        self.assertEqual(r["downstream_count"], len(nx.descendants(self.G, r["node_id"])))


if __name__ == "__main__":
    unittest.main(verbosity=2)
