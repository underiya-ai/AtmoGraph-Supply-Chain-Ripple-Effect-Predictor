
# ============================================================
# ATMOGRAPH - SUPPLY CHAIN RIPPLE EFFECT PREDICTOR
# Advanced Version 2.0
# ============================================================

import csv
import json
import math
from collections import deque
from datetime import datetime
from pathlib import Path


class AtmoGraph:

    def __init__(self):

        # 1. Initialize supply chain network
        self.graph = {
            "Supplier_A": ["Manufacturer"],
            "Supplier_B": ["Manufacturer"],
            "Supplier_C": ["Manufacturer_2"],
            "Manufacturer": ["Distributor"],
            "Manufacturer_2": ["Distributor"],
            "Distributor": ["Retailer"],
            "Retailer": ["Customer"],
            "Customer": []
        }

        # 2. Company information
        self.details = {}

        # 3. Initialize company properties
        for company in self.graph:
            self.details[company] = self._new_company_details()

        # 4. Simulation history
        self.history = []

        # 5. Failed companies
        self.failed = set()

    @staticmethod
    def _new_company_details():
        return {
            "status": "Active",
            "inventory": 100,
            "capacity": 100,
            "demand": 50,
            "failure_probability": 10
        }

    def resolve_company(self, name):
        """Return the canonical company name for a case-insensitive exact match."""
        if not isinstance(name, str):
            return None
        normalized = name.strip().casefold()
        return next(
            (company for company in self.graph if company.casefold() == normalized),
            None
        )

    @staticmethod
    def risk_level(score):
        if score >= 60:
            return "HIGH"
        if score >= 30:
            return "MEDIUM"
        return "LOW"

    def calculate_ripple_effect(self, origin, severity):
        """Return dashboard-compatible ripple estimates, ordered by distance."""
        origin = self.resolve_company(origin)
        if origin is None:
            raise ValueError("Company not found.")
        if (
            isinstance(severity, bool)
            or not isinstance(severity, (int, float))
            or not 1 <= severity <= 100
            or not math.isfinite(severity)
        ):
            raise ValueError("Severity must be a number between 1 and 100.")

        estimates = []
        for company, distance in self.find_affected([origin]).items():
            vulnerability = self.details[company]["failure_probability"]
            score = severity * (0.65 ** (distance - 1))
            score *= (1 + vulnerability / 100) / 2
            estimates.append({
                "company": company,
                "distance": distance,
                "score": round(score, 1),
                "risk": self.risk_level(score)
            })

        return sorted(
            estimates,
            key=lambda item: (item["distance"], -item["score"], item["company"].casefold())
        )

    def dashboard_data(self):
        """Return the same core values shown by the HTML dashboard."""
        total = len(self.graph)
        default_origin = next(iter(self.graph), None)
        failed_names = sorted(
            self.failed.intersection(self.graph),
            key=str.casefold
        )
        failed = len(failed_names)
        active = total - failed
        return {
            "total_companies": total,
            "active_companies": active,
            "failed_companies": failed,
            "failed_company_names": failed_names,
            "network_health": round(active / total * 100, 2) if total else 0,
            "network": {
                company: list(connections)
                for company, connections in self.graph.items()
            },
            "company_details": {
                company: dict(details)
                for company, details in self.details.items()
            },
            "simulation_count": len(self.history),
            "default_ripple": {
                "source": default_origin,
                "severity": 60,
                "estimates": (
                    self.calculate_ripple_effect(default_origin, 60)
                    if default_origin else []
                )
            }
        }

    def _record_history(self, company, affected, severity=None):
        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "company": company,
            "affected": affected
        }
        if severity is not None:
            record["severity"] = severity
        self.history.append(record)

    # --------------------------------------------------------
    # 6. Display network
    # --------------------------------------------------------

    def display_network(self):

        print("\n========== SUPPLY CHAIN NETWORK ==========")

        for company, connections in self.graph.items():
            status = self.details[company]["status"].upper()
            destinations = ", ".join(connections) if connections else "None"
            print(f"{company} [{status}] -> {destinations}")

        print("==========================================")

    # --------------------------------------------------------
    # 7. Display network statistics
    # --------------------------------------------------------

    def network_statistics(self):

        data = self.dashboard_data()
        total = data["total_companies"]
        connections = sum(len(value) for value in self.graph.values())

        suppliers = sum(
            1 for name in self.graph
            if name.startswith("Supplier")
        )

        print("\n========== NETWORK STATISTICS ==========")
        print("Total Companies:", total)
        print("Total Connections:", connections)
        print("Total Suppliers:", suppliers)
        print("Failed Companies:", data["failed_companies"])
        print("Active Companies:", data["active_companies"])
        print("Network Health:", str(data["network_health"]) + "%")
        print("========================================")

    # --------------------------------------------------------
    # 8. Add new company
    # --------------------------------------------------------

    def add_company(self):

        name = input("Enter company name: ").strip()

        if not name:
            print("Company name cannot be empty.")
            return

        if self.resolve_company(name):
            print("Company already exists.")
            return

        self.graph[name] = []
        self.details[name] = self._new_company_details()

        print(name, "added successfully.")

    # --------------------------------------------------------
    # 9. Remove company
    # --------------------------------------------------------

    def remove_company(self):

        name = input("Enter company to remove: ").strip()
        name = self.resolve_company(name)

        if name not in self.graph:
            print("Company not found.")
            return

        del self.graph[name]
        del self.details[name]

        self.failed.discard(name)

        for company, connections in self.graph.items():
            self.graph[company] = [
                destination for destination in connections
                if destination != name
            ]

        print("Company removed successfully.")

    # --------------------------------------------------------
    # 10. Add connection
    # --------------------------------------------------------

    def add_connection(self):

        source = self.resolve_company(input("Enter source company: "))
        destination = self.resolve_company(input("Enter destination company: "))

        if source not in self.graph or destination not in self.graph:
            print("Invalid company name.")
            return

        if source == destination:
            print("A company cannot connect to itself.")
            return

        if destination in self.graph[source]:
            print("Connection already exists.")
            return

        self.graph[source].append(destination)
        print("Connection added:", source, "->", destination)

    # --------------------------------------------------------
    # 11. Remove connection
    # --------------------------------------------------------

    def remove_connection(self):

        source = self.resolve_company(input("Enter source company: "))
        destination = self.resolve_company(input("Enter destination company: "))

        if source not in self.graph:
            print("Source company not found.")
            return

        if destination in self.graph[source]:
            self.graph[source].remove(destination)
            print("Connection removed.")
        else:
            print("Connection does not exist.")

    # --------------------------------------------------------
    # 12. BFS traversal
    # --------------------------------------------------------

    def bfs(self, start):

        start = self.resolve_company(start)
        if start not in self.graph:
            print("Company not found.")
            return

        visited = set()
        queue = deque([start])

        print("\nBFS Traversal:")

        while queue:

            current = queue.popleft()

            if current not in visited:

                visited.add(current)
                print(current, end=" -> ")

                for neighbor in self.graph[current]:

                    if neighbor not in visited:
                        queue.append(neighbor)

        print("END")

    # --------------------------------------------------------
    # 13. DFS traversal
    # --------------------------------------------------------

    def dfs(self, start):

        start = self.resolve_company(start)
        if start not in self.graph:
            print("Company not found.")
            return

        visited = set()

        def explore(company):

            if company in visited:
                return

            visited.add(company)

            print(company, end=" -> ")

            for neighbor in self.graph[company]:
                explore(neighbor)

        print("\nDFS Traversal:")
        explore(start)
        print("END")

    # --------------------------------------------------------
    # 14. Find affected companies
    # --------------------------------------------------------

    def find_affected(self, failed_companies):

        starts = [
            company for company in dict.fromkeys(failed_companies)
            if company in self.graph
        ]
        visited = set(starts)
        queue = deque(starts)
        levels = {}

        while queue:

            current = queue.popleft()

            for company in self.graph.get(current, []):

                if company not in visited:

                    visited.add(company)
                    queue.append(company)

                    parent_level = levels.get(current, 0)
                    levels[company] = parent_level + 1

        return levels

    # --------------------------------------------------------
    # 15. Supplier failure simulation
    # --------------------------------------------------------

    def simulate_failure(self):

        if not self.graph:
            print("Network is empty.")
            return

        print("\nAvailable Companies:")

        for company in self.graph:
            print("-", company)

        failed = self.resolve_company(input("\nEnter failed company: "))

        if failed not in self.graph:
            print("Invalid company.")
            return

        if failed in self.failed:
            print("Company is already marked as failed.")
            return

        self.failed.add(failed)
        self.details[failed]["status"] = "Failed"

        affected = self.find_affected([failed])
        active_affected = {
            company: level
            for company, level in affected.items()
            if company not in self.failed
        }

        print("\n========== FAILURE REPORT ==========")
        print("Failed Company:", failed)

        if not active_affected:
            print("No downstream companies affected.")

        for company, level in active_affected.items():
            risk = "HIGH" if level == 1 else "MEDIUM" if level == 2 else "LOW"

            print(
                company,
                "| Level:", level,
                "| Risk:", risk
            )

        print("Total Downstream Companies:", len(active_affected))

        self._record_history(failed, len(active_affected))

        print("====================================")

    # --------------------------------------------------------
    # 16. Multiple company failure
    # --------------------------------------------------------

    def multiple_failure(self):

        names = input(
            "Enter failed companies separated by commas: "
        ).split(",")

        failed = []
        invalid = []

        for name in names:
            entered_name = name.strip()
            name = self.resolve_company(entered_name)

            if name is None:
                if entered_name:
                    invalid.append(entered_name)
            elif name not in self.failed:
                self.failed.add(name)
                self.details[name]["status"] = "Failed"
                failed.append(name)

        if invalid:
            print("Invalid companies:", ", ".join(invalid))

        if not failed:
            print("No new valid failures selected.")
            return

        affected = self.find_affected(failed)
        active_affected = {
            company: level
            for company, level in affected.items()
            if company not in self.failed
        }

        print("\nMultiple Failure Analysis")

        for company, level in active_affected.items():
            print(company, "- Level", level)

        self._record_history(", ".join(failed), len(active_affected))

    # --------------------------------------------------------
    # 17. Risk analysis
    # --------------------------------------------------------

    def risk_analysis(self):

        print("\n========== RISK ANALYSIS ==========")

        for company in self.graph:

            if company in self.failed:
                continue

            probability = self.details[company]["failure_probability"]

            risk = self.risk_level(probability)

            print(
                company,
                "| Probability:", str(probability) + "%",
                "| Risk:", risk
            )

    # --------------------------------------------------------
    # 18. Risk percentage
    # --------------------------------------------------------

    def risk_percentage(self):

        total = len(self.graph)

        if total == 0:
            print("No companies available.")
            return

        failed = len(self.failed.intersection(self.graph))
        percentage = (failed / total) * 100

        print("\nNetwork Failure Percentage:",
              round(percentage, 2), "%")

    # --------------------------------------------------------
    # 19. Company impact score
    # --------------------------------------------------------

    def impact_score(self):

        print("\n========== COMPANY IMPACT SCORES ==========")

        for company in self.graph:

            downstream = self.find_affected([company])

            score = len(downstream)

            print(company, ":", score, "/",
                  max(0, len(self.graph) - 1))

    # --------------------------------------------------------
    # 20. Predict disruption ripple risk
    # --------------------------------------------------------

    def predict_ripple_effect(self):

        if not self.graph:
            print("Network is empty.")
            return

        origin_input = input("Enter disrupted company: ").strip()
        origin = self.resolve_company(origin_input)

        if origin is None:
            print("Company not found.")
            return

        try:
            severity = float(input("Enter disruption severity (1-100): "))
        except ValueError:
            print("Enter a valid severity number.")
            return

        if not 1 <= severity <= 100:
            print("Severity must be between 1 and 100.")
            return

        estimates = self.calculate_ripple_effect(origin, severity)

        print("\n========== RIPPLE EFFECT PREDICTION ==========")
        print("Disruption source:", origin)
        print("Disruption severity:", f"{severity:g}%")
        print("Estimate uses graph distance and each company's failure probability.")

        if not estimates:
            print("No downstream companies are connected to this company.")
            self._record_history(origin, 0, severity)
            return

        for estimate in estimates:
            print(
                estimate["company"],
                "| Distance:", estimate["distance"],
                "| Estimated Ripple Risk:", estimate["score"], "%",
                "| Risk:", estimate["risk"]
            )

        self._record_history(origin, len(estimates), severity)
        print("==============================================")

    # --------------------------------------------------------
    # 21. Critical company detection
    # --------------------------------------------------------

    def critical_companies(self):

        scores = {}

        for company in self.graph:

            scores[company] = len(
                self.find_affected([company])
            )

        print("\n========== CRITICAL COMPANIES ==========")

        for company, score in sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True
        ):

            if score > 0:
                print(company, ":", score, "downstream companies")

    # --------------------------------------------------------
    # 21. Find alternative suppliers
    # --------------------------------------------------------

    def alternative_suppliers(self):

        company = self.resolve_company(input("Enter company name: "))

        if company not in self.graph:
            print("Company not found.")
            return

        suppliers = []

        for name, connections in self.graph.items():

            if company in connections and name not in self.failed:
                suppliers.append(name)

        print("\nAvailable Alternative Suppliers:")

        if suppliers:
            for supplier in suppliers:
                print("->", supplier)
        else:
            print("No active direct suppliers found.")

    # --------------------------------------------------------
    # 22. Find bottlenecks
    # --------------------------------------------------------

    def bottleneck_detection(self):

        print("\n========== BOTTLENECK ANALYSIS ==========")

        for company in self.graph:

            incoming = sum(
                1 for connections in self.graph.values()
                if company in connections
            )

            outgoing = len(self.graph[company])

            if incoming <= 1 and outgoing > 1:
                print(company, "- Potential supply bottleneck")

    # --------------------------------------------------------
    # 23. Dependency analysis
    # --------------------------------------------------------

    def dependency_analysis(self):

        print("\n========== DEPENDENCY ANALYSIS ==========")

        for company in self.graph:

            dependencies = []

            for source, destinations in self.graph.items():

                if company in destinations:
                    dependencies.append(source)

            print(company, "depends on:", dependencies)

    # --------------------------------------------------------
    # 24. Supplier ranking
    # --------------------------------------------------------

    def supplier_ranking(self):

        ranking = []

        for company in self.graph:

            if company.startswith("Supplier"):
                score = len(self.graph[company])
                ranking.append((company, score))

        ranking.sort(key=lambda item: (-item[1], item[0].casefold()))

        print("\n========== SUPPLIER RANKING ==========")

        for index, (name, score) in enumerate(ranking, 1):
            print(index, name, "| Connections:", score)

    # --------------------------------------------------------
    # 25. Recovery simulation
    # --------------------------------------------------------

    def recover_company(self):

        name = self.resolve_company(input("Enter company to recover: "))

        if name not in self.graph:
            print("Company not found.")
            return

        if name not in self.failed:
            print("Company is already active.")
            return

        self.failed.remove(name)
        self.details[name]["status"] = "Active"

        print(name, "has been recovered.")

    # --------------------------------------------------------
    # 26. Company search
    # --------------------------------------------------------

    def search_company(self):

        name = input("Enter company name: ").strip()

        if not name:
            print("Enter at least one character to search.")
            return

        matches = [
            company for company in self.graph
            if name.lower() in company.lower()
        ]

        if matches:
            print("\nMatching Companies:")
            for company in matches:
                print(company)
        else:
            print("No matching company found.")

    # --------------------------------------------------------
    # 27. Company details
    # --------------------------------------------------------

    def company_details(self):

        name = self.resolve_company(input("Enter company name: "))

        if name not in self.graph:
            print("Company not found.")
            return

        print("\nCompany:", name)

        for key, value in self.details[name].items():
            print(key.capitalize(), ":", value)

        print("Supplies to:", self.graph[name])

    # --------------------------------------------------------
    # 28. Failure history
    # --------------------------------------------------------

    def show_history(self):

        print("\n========== FAILURE HISTORY ==========")

        if not self.history:
            print("No simulation history.")
            return

        for record in self.history:

            print("\nTime:", record["time"])
            print("Failed:", record["company"])
            print("Affected:", record["affected"])

    # --------------------------------------------------------
    # 29. Risk dashboard
    # --------------------------------------------------------

    def dashboard(self):

        data = self.dashboard_data()

        print("\n========== ATMOGRAPH DASHBOARD ==========")
        print("Total Companies:", data["total_companies"])
        print("Active Companies:", data["active_companies"])
        print("Failed Companies:", data["failed_companies"])
        print("Network Health:", str(data["network_health"]) + "%")
        print("Total Simulations:", len(self.history))
        print("=========================================")

        print("\n========== SUPPLY CHAIN NETWORK ==========")
        for company, connections in data["network"].items():
            status = self.details[company]["status"].upper()
            destinations = ", ".join(connections) if connections else "None"
            print(f"{company} [{status}] -> {destinations}")

        if self.graph:
            print("\n========== SAMPLE RIPPLE ESTIMATE (60%) ==========")
            origin = next(iter(self.graph))
            print("Disruption source:", origin)
            estimates = self.calculate_ripple_effect(origin, 60)
            if estimates:
                for estimate in estimates:
                    print(
                        estimate["company"],
                        "| Distance:", estimate["distance"],
                        "| Estimated Ripple Risk:", estimate["score"], "%",
                        "| Risk:", estimate["risk"]
                    )
            else:
                print("No downstream companies are connected.")
            print("==================================================")

    # --------------------------------------------------------
    # 30. Text-based network visualization
    # --------------------------------------------------------

    def visualize_network(self):

        print("\n========== NETWORK VISUALIZATION ==========")

        for company, connections in self.graph.items():

            status = "[FAILED]" if company in self.failed else "[ACTIVE]"

            print("\n", company, status)

            for connection in connections:
                print("    |")
                print("    +---->", connection)

    # --------------------------------------------------------
    # 31. Shortest path
    # --------------------------------------------------------

    def shortest_path(self):

        start = self.resolve_company(input("Enter starting company: "))
        end = self.resolve_company(input("Enter destination company: "))

        if start not in self.graph or end not in self.graph:
            print("Invalid company.")
            return

        queue = deque([(start, [start])])
        visited = {start}

        while queue:

            current, path = queue.popleft()

            if current == end:
                print("Shortest Path:", " -> ".join(path))
                print("Distance:", len(path) - 1)
                return

            for neighbor in self.graph[current]:

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        print("No path found.")

    # --------------------------------------------------------
    # 32. Path analysis
    # --------------------------------------------------------

    def path_analysis(self):

        start = self.resolve_company(input("Enter starting company: "))

        if start not in self.graph:
            print("Company not found.")
            return

        paths = self.find_affected([start])

        print("\nReachable Companies:")

        for company, level in paths.items():
            print(company, "| Distance:", level)

    # --------------------------------------------------------
    # 33. Disconnected company detection
    # --------------------------------------------------------

    def disconnected_companies(self):

        print("\n========== DISCONNECTED COMPANIES ==========")

        disconnected = []

        for company in self.graph:

            incoming = any(
                company in destinations
                for destinations in self.graph.values()
            )

            outgoing = len(self.graph[company]) > 0

            if not incoming and not outgoing:
                disconnected.append(company)

        if disconnected:
            for company in disconnected:
                print(company)
        else:
            print("No completely isolated companies.")

    # --------------------------------------------------------
    # 34. Circular dependency detection
    # --------------------------------------------------------

    def detect_cycles(self):

        visited = set()
        active = set()

        def dfs(company):

            visited.add(company)
            active.add(company)

            for neighbor in self.graph[company]:

                if neighbor not in visited:

                    if dfs(neighbor):
                        return True

                elif neighbor in active:
                    return True

            active.remove(company)

            return False

        for company in self.graph:

            if company not in visited:

                if dfs(company):
                    print("Circular dependency detected.")
                    return

        print("No circular dependency detected.")

    # --------------------------------------------------------
    # 35. Network validation
    # --------------------------------------------------------

    def validate_network(self):

        valid = True

        for company, connections in self.graph.items():
            if company not in self.details:
                print("Missing company details:", company)
                valid = False

            if len(connections) != len(set(connections)):
                print("Duplicate connections found for:", company)
                valid = False

            for destination in connections:

                if destination not in self.graph:
                    print("Invalid connection:", company, destination)
                    valid = False
                elif destination == company:
                    print("Self-connection found:", company)
                    valid = False

        for company in self.details:
            if company not in self.graph:
                print("Company details without network entry:", company)
                valid = False

        for company in self.failed:
            if company not in self.graph:
                print("Failed-company record without network entry:", company)
                valid = False
            elif self.details[company].get("status") != "Failed":
                print("Status mismatch for failed company:", company)
                valid = False

        for company in self.graph:
            if company not in self.failed and self.details.get(company, {}).get("status") != "Active":
                print("Status mismatch for active company:", company)
                valid = False

        if valid:
            print("Network validation successful.")

    # --------------------------------------------------------
    # 36. Failure probability update
    # --------------------------------------------------------

    def update_probability(self):

        name = self.resolve_company(input("Enter company name: "))

        if name not in self.graph:
            print("Company not found.")
            return

        try:
            probability_text = input(
                "Enter failure probability (0-100): "
            ).strip()
            probability = int(probability_text)

            if not 0 <= probability <= 100:
                print("Enter a value between 0 and 100.")
                return

            self.details[name]["failure_probability"] = probability

            print("Failure probability updated.")

        except ValueError:
            print("Enter a valid number.")

    # --------------------------------------------------------
    # 37. Inventory tracking
    # --------------------------------------------------------

    def inventory_tracking(self):

        print("\n========== INVENTORY TRACKING ==========")

        for company, data in self.details.items():

            print(company, ":", data["inventory"], "units")

    # --------------------------------------------------------
    # 38. Inventory shortage alerts
    # --------------------------------------------------------

    def inventory_alerts(self):

        print("\n========== INVENTORY ALERTS ==========")

        for company, data in self.details.items():

            if data["inventory"] < 30:
                print("WARNING:", company, "has low inventory.")

    # --------------------------------------------------------
    # 39. Update inventory
    # --------------------------------------------------------

    def update_inventory(self):

        name = self.resolve_company(input("Enter company name: "))

        if name not in self.graph:
            print("Company not found.")
            return

        try:
            amount = int(input("Enter new inventory: "))

            if amount < 0:
                print("Inventory cannot be negative.")
                return

            self.details[name]["inventory"] = amount

            print("Inventory updated.")

        except ValueError:
            print("Invalid inventory value.")

    # --------------------------------------------------------
    # 40. Production capacity
    # --------------------------------------------------------

    def production_capacity(self):

        print("\n========== PRODUCTION CAPACITY ==========")

        for company, data in self.details.items():
            print(company, ":", data["capacity"], "units")

    # --------------------------------------------------------
    # 41. Update production capacity
    # --------------------------------------------------------

    def update_capacity(self):

        name = self.resolve_company(input("Enter company name: "))

        if name not in self.graph:
            print("Company not found.")
            return

        try:
            capacity = int(input("Enter production capacity: "))

            if capacity < 0:
                print("Capacity cannot be negative.")
                return

            self.details[name]["capacity"] = capacity

            print("Production capacity updated.")

        except ValueError:
            print("Invalid value.")

    # --------------------------------------------------------
    # 42. Demand tracking
    # --------------------------------------------------------

    def demand_tracking(self):

        print("\n========== DEMAND TRACKING ==========")

        for company, data in self.details.items():
            print(company, ":", data["demand"], "units")

    # --------------------------------------------------------
    # 43. Supply shortage estimation
    # --------------------------------------------------------

    def shortage_estimation(self):

        print("\n========== SHORTAGE ESTIMATION ==========")

        for company, data in self.details.items():

            shortage = max(
                0,
                data["demand"] - data["inventory"]
            )

            print(company, "| Estimated Shortage:", shortage)

    # --------------------------------------------------------
    # 44. Recovery recommendations
    # --------------------------------------------------------

    def recovery_recommendations(self):

        print("\n========== RECOVERY RECOMMENDATIONS ==========")

        if not self.failed:
            print("All companies are active.")
            return

        for company in self.failed:

            print("\nFailed:", company)
            print("1. Restore company operations.")
            print("2. Identify alternative suppliers.")
            print("3. Increase backup inventory.")
            print("4. Review dependent companies.")

    # --------------------------------------------------------
    # 45. Risk mitigation
    # --------------------------------------------------------

    def risk_mitigation(self):

        print("\n========== RISK MITIGATION ==========")

        for company in self.graph:

            if company in self.failed:
                continue

            risk = self.details[company]["failure_probability"]

            if risk >= 70:
                print(company, ": Establish backup suppliers.")
            elif risk >= 30:
                print(company, ": Monitor inventory and demand.")
            else:
                print(company, ": Continue regular monitoring.")

    # --------------------------------------------------------
    # 46. Company status
    # --------------------------------------------------------

    def company_status(self):

        print("\n========== COMPANY STATUS ==========")

        for company, data in self.details.items():
            print(company, ":", data["status"])

    # --------------------------------------------------------
    # 47. Export company data to CSV
    # --------------------------------------------------------

    def export_csv(self):

        filename = "atmograph_report.csv"

        try:

            with open(filename, "w", newline="") as file:

                writer = csv.writer(file)

                writer.writerow([
                    "Company",
                    "Status",
                    "Inventory",
                    "Capacity",
                    "Demand",
                    "Failure Probability"
                ])

                for company, data in self.details.items():

                    writer.writerow([
                        company,
                        data["status"],
                        data["inventory"],
                        data["capacity"],
                        data["demand"],
                        data["failure_probability"]
                    ])

            print("CSV exported successfully:", filename)

        except OSError as error:
            print("Export failed:", error)

    def export_dashboard_json(self):
        filename = Path("atmograph_dashboard.json")
        payload = self.dashboard_data()
        payload["simulation_history"] = self.history

        try:
            with filename.open("w", encoding="utf-8") as file:
                json.dump(payload, file, indent=2, ensure_ascii=False)
            print("Dashboard data exported successfully:", filename)
        except OSError as error:
            print("JSON export failed:", error)

    # --------------------------------------------------------
    # 48. Simulation timestamp
    # --------------------------------------------------------

    def current_timestamp(self):

        print("\nCurrent Date and Time:")
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

    # --------------------------------------------------------
    # 49. Reset network
    # --------------------------------------------------------

    def reset_network(self):

        confirmation = input(
            "Reset all simulation data? (yes/no): "
        ).strip().lower()

        if confirmation == "yes":

            self.__init__()

            print("Network reset successfully.")

        else:
            print("Reset cancelled.")

    # --------------------------------------------------------
    # 50. Final summary report
    # --------------------------------------------------------

    def summary_report(self):

        print("\n========== FINAL SUMMARY REPORT ==========")

        print("Total Companies:", len(self.graph))
        print("Total Connections:", sum(
            len(x) for x in self.graph.values()
        ))

        print("Failed Companies:", len(self.failed))
        print("Active Companies:", len(self.graph) - len(self.failed))

        print("Simulation Count:", len(self.history))

        if self.failed:
            print(
                "Failed Company List:",
                sorted(self.failed.intersection(self.graph), key=str.casefold)
            )
        else:
            print("No failed companies.")

        print("==========================================")


# ============================================================
# 51. MAIN MENU
# ============================================================

def main():
    system = AtmoGraph()
    actions = {
        1: system.display_network,
        2: system.network_statistics,
        3: system.add_company,
        4: system.remove_company,
        5: system.add_connection,
        6: system.remove_connection,
        7: lambda: system.bfs(input("Enter starting company: ").strip()),
        8: lambda: system.dfs(input("Enter starting company: ").strip()),
        9: system.simulate_failure,
        10: system.multiple_failure,
        11: system.risk_analysis,
        12: system.risk_percentage,
        13: system.impact_score,
        14: system.critical_companies,
        15: system.alternative_suppliers,
        16: system.bottleneck_detection,
        17: system.dependency_analysis,
        18: system.supplier_ranking,
        19: system.recover_company,
        20: system.search_company,
        21: system.company_details,
        22: system.show_history,
        23: system.dashboard,
        24: system.visualize_network,
        25: system.shortest_path,
        26: system.path_analysis,
        27: system.disconnected_companies,
        28: system.detect_cycles,
        29: system.validate_network,
        30: system.update_probability,
        31: system.inventory_tracking,
        32: system.inventory_alerts,
        33: system.update_inventory,
        34: system.production_capacity,
        35: system.update_capacity,
        36: system.demand_tracking,
        37: system.shortage_estimation,
        38: system.recovery_recommendations,
        39: system.risk_mitigation,
        40: system.company_status,
        41: system.export_csv,
        42: system.current_timestamp,
        43: system.reset_network,
        44: system.summary_report,
        45: system.predict_ripple_effect,
        46: system.export_dashboard_json,
    }

    while True:
        print("""
====================================================
       ATMOGRAPH - SUPPLY CHAIN RIPPLE PREDICTOR
====================================================

 1. Display Supply Chain Network
 2. Network Statistics
 3. Add Company
 4. Remove Company
 5. Add Connection
 6. Remove Connection
 7. BFS Traversal
 8. DFS Traversal
 9. Simulate Company Failure
10. Multiple Company Failure
11. Risk Analysis
12. Risk Percentage
13. Company Impact Score
14. Critical Company Detection
15. Alternative Supplier Detection
16. Bottleneck Detection
17. Dependency Analysis
18. Supplier Ranking
19. Recover Company
20. Search Company
21. Company Details
22. Failure History
23. Risk Dashboard
24. Network Visualization
25. Shortest Path
26. Path Analysis
27. Disconnected Company Detection
28. Circular Dependency Detection
29. Network Validation
30. Update Failure Probability
31. Inventory Tracking
32. Inventory Alerts
33. Update Inventory
34. Production Capacity
35. Update Capacity
36. Demand Tracking
37. Supply Shortage Estimation
38. Recovery Recommendations
39. Risk Mitigation
40. Company Status
41. Export CSV
42. Current Timestamp
43. Reset Network
44. Final Summary Report
45. Predict Disruption Ripple Effect
46. Export Dashboard Data (JSON)
 0. Exit

====================================================
""")

        try:
            choice = int(input("Enter your choice: "))
        except ValueError:
            print("Please enter a valid number.")
            continue

        if choice == 0:
            print("Thank you for using AtmoGraph!")
            break

        action = actions.get(choice)
        if action is None:
            print("Invalid choice! Select between 0 and 46.")
            continue
        action()


# ============================================================
# 52. PROGRAM EXECUTION
# ============================================================

if __name__ == "__main__":
    main()