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