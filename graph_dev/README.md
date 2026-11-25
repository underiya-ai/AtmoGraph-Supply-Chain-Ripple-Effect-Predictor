# Graph Network Development (AtmoGraph)

This folder holds the supply chain graph module. Author: Kishore (branch kishore).

## Important: what is real and what is synthetic
- The network structure (nodes and connections) is SYNTHETIC. The disruption dataset has no supplier, factory or warehouse names and no links between them, so the team agreed to build the network by script.
- The disruption values (severity, recovery days and so on) are REAL. They come from the team's disruption dataset.

## Files: building the data
- build_network.py: creates network_data/nodes.csv and edges.csv. One supplier per industry, region and tier, plus factories, warehouses and retailers per industry. Links run inside one industry: tier 4 -> 3 -> 2 -> 1 -> factory -> warehouse -> retailer. A fixed random seed makes the result repeatable.
- build_supplier_attributes.py: maps each disruption record to a supplier node (by industry, region and tier) and creates supplier_attributes.csv (averages per supplier) and disruption_mapping.csv.
- validate_mapping.py: checks the mapping and saves network_data/mapping_report.txt.
- check_dataset.py: checks whether another dataset file (for example a cleaned one) works with these scripts.

## Files: using the graph
- graph_loader.py: load_graph() builds one NetworkX directed graph from the CSV files. validate_graph() returns a list of problems (empty means healthy).
- downstream_analysis.py: BFS from a disrupted node, listing affected nodes and their distance in steps.
- ripple_simulation.py: simulate_ripple() gives every downstream node an impact score and a HIGH, MEDIUM or LOW level.
- risk_state.py: update_node_risk() sets the risk state of a node (for the NLP part of the project), apply_ripple() copies a simulation onto the nodes.
- critical_nodes.py: ranks the nodes whose failure matters most (betweenness and downstream reach).
- visualize_ripple.py: draws one industry as an SVG picture in output/ and opens it in the browser.
- export_json.py: writes output/ripple_<node>.json and output/network.json for the backend.

## Tests
- test_graph_module.py and test_risk_and_critical.py (20 tests, run each with python).

## The ripple rule (a transparent heuristic, not a trained model)
A disrupted supplier starts with its real average production impact (%) from the dataset. Each downstream node is hurt in proportion to how many of its suppliers are hit, and the effect weakens by 10% at each step. HIGH is 25 or more, MEDIUM is 10 or more, otherwise LOW.

## How to run (from the AtmoGraph folder, in this order)
    python graph_dev\build_network.py
    python graph_dev\build_supplier_attributes.py
    python graph_dev\validate_mapping.py
    python graph_dev\graph_loader.py
    python graph_dev\ripple_simulation.py
    python graph_dev\visualize_ripple.py
    python graph_dev\export_json.py

## Use in other code
    from graph_loader import load_graph
    from export_json import build_ripple_json
    G = load_graph()
    result = build_ripple_json(G, "SUP-I1-R1-T2")

## Dataset
The cleaned file AtmoGraph_DataPreprocessing/data/processed/supply_chain_cleaned.csv from Sri Varshini's pipeline (branch dev_s), checked with check_dataset.py (100,000 rows, same columns and values our scripts need). Re-running the scripts on it gave the same network and supplier averages as the raw file.

## Assumptions (to be confirmed by the team lead)
- A higher tier number is further upstream (tier 4 supplies tier 3, and so on).
- The graph is built with NetworkX.
- The JSON format in export_json.py is a proposal for the API.

## Notes
- The dataset is not stored in this folder.
- Scripts use Python's csv module instead of pandas, because Windows Application Control blocked pandas on the author's laptop.

