# Graph Network Development (AtmoGraph)

This folder holds the supply chain graph module. Author: Kishore.

## Important: what is real and what is synthetic
- The network structure (nodes and connections) is SYNTHETIC. The disruption dataset has no supplier, factory or warehouse names and no links between them, so the team agreed to build the network by script.
- The disruption values (severity, recovery days and so on) are REAL. They come from supply_chain_disruption_recovery.csv.

## Files
- build_network.py: creates network_data/nodes.csv and edges.csv. Suppliers: one per industry, region and tier. Factories, warehouses and retailers are added per industry. Links run inside one industry: tier 4 -> 3 -> 2 -> 1 -> factory -> warehouse -> retailer. A fixed random seed makes the result repeatable.
- build_supplier_attributes.py: maps each disruption record to a supplier node (by industry, region and tier) and creates supplier_attributes.csv (averages per supplier) and disruption_mapping.csv.
- validate_mapping.py: checks the mapping and saves network_data/mapping_report.txt.
- graph_loader.py: load_graph() builds one NetworkX directed graph from the three CSV files. validate_graph() returns a list of problems (empty means healthy).

## How to run (from the AtmoGraph folder, in this order)
    python graph_dev\build_network.py
    python graph_dev\build_supplier_attributes.py
    python graph_dev\validate_mapping.py
    python graph_dev\graph_loader.py

## Use in other code
    from graph_loader import load_graph, validate_graph
    G = load_graph()

## Assumptions (to be confirmed with the team)
- A higher tier number is further upstream (tier 4 supplies tier 3, and so on).
- The graph is built with NetworkX.

## Notes
- The dataset file is not stored in this folder. Expected at datasets/raw/supply_chain_disruption_recovery.csv.
- Scripts use Python's csv module instead of pandas, because Windows Application Control blocked pandas on the author's laptop.
