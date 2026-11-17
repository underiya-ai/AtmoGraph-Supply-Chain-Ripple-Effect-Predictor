AtmoGraph: Supply Chain Ripple Effect Predictor

Project Overview

AtmoGraph is a project designed to predict and analyze the ripple effects of disruptions in supply chain networks using graph-based analysis and predictive modeling.

Problem Statement

Traditional supply chain predictive models rely on linear, isolated time-series data. They fail to understand complex global networks and cannot predict how a localized crisis in one industry will affect entirely unrelated industries across the globe.

Objectives

- Represent supply chains as interconnected graphs.
- Identify important suppliers and network dependencies.
- Analyze the impact of supply chain disruptions.
- Predict potential ripple effects across the network.
- Support better supply chain risk management.

Technologies Used

- Python
- Graph Analysis
- Machine Learning
- Data Visualization

Project Structure

- "main.py" – Main project execution file.
- "README.md" – Project documentation.

Expected Outcome

The project aims to identify supply chain vulnerabilities and provide insights into how disruptions propagate through interconnected networks.

Project Status

Currently under development.

Ripple-effect prediction

Choose option 45 from the menu, enter a disrupted company, and provide a severity
from 1 to 100. AtmoGraph estimates downstream risk using network distance and
the affected company's configured failure probability. This is a transparent
heuristic for exploration, not a trained machine-learning forecast.

Dashboard data export

Choose option 46 to export the current dashboard summary, company details,
network connections, and simulation history to `atmograph_dashboard.json`.
The export includes company counts, network health, and the same ripple-risk
estimates used by the dashboard interface.

Disruption dataset preprocessing

Choose option 47 in the Python menu to validate and clean the raw disruption
dataset. Press Enter at either prompt to use the default source and output
paths. The workflow streams the CSV, normalizes headers, whitespace,
categories, booleans, and numeric values, and checks required fields, numeric
ranges, recovery-day ordering, and duplicate disruption IDs. It writes accepted
rows to `datasets/processed/supply_chain_disruption_recovery_clean.csv`,
invalid rows and reasons to a sibling `_rejected.csv`, and aggregate quality
statistics to a sibling `_report.json`. The raw file is never overwritten.

The same workflow can be run without opening the interactive menu:

```text
python data_preprocessing.py
python data_preprocessing.py --input path/to/source.csv --output path/to/clean.csv
```

The `--rejects` and `--report` options can override the default companion file
paths. Invalid rows are reported rather than silently discarded.

Browser dashboard

Open `index.html` in a browser to explore the interactive dashboard. Search or
filter companies by status, select a company as the disruption source, and
adjust severity to view downstream risk estimates. Use **Mark source failed**
to record a simulated failure, then recover individual companies or reset all
statuses. The dashboard keeps up to 50 scenarios and failed-company statuses in
browser local storage. Use **Export JSON** or **Export CSV** to download the
current dashboard data. These browser scenarios are local to the browser and
are separate from the Python CLI's simulation history.