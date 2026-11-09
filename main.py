
# ============================================================
# ATMOGRAPH - SUPPLY CHAIN RIPPLE EFFECT PREDICTOR
# Advanced Version 2.0
# ============================================================

import csv
from collections import deque
from datetime import datetime


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
            self.details[company] = {
                "status": "Active",
                "inventory": 100,
                "capacity": 100,
                "demand": 50,
                "failure_probability": 10
            }

        # 4. Simulation history
        self.history = []

        # 5. Failed companies
        self.failed = set()

    # --------------------------------------------------------
    # 6. Display network
    # --------------------------------------------------------

    def display_network(self):

        print("\n========== SUPPLY CHAIN NETWORK ==========")

        for company, connections in self.graph.items():

            print(company, "->", connections)

        print("==========================================")

    # --------------------------------------------------------
    # 7. Display network statistics
    # --------------------------------------------------------

    def network_statistics(self):

        total = len(self.graph)

        connections = sum(
            len(value) for value in self.graph.values()
        )

        suppliers = sum(
            1 for name in self.graph
            if name.startswith("Supplier")
        )

        print("\n========== NETWORK STATISTICS ==========")
        print("Total Companies:", total)
        print("Total Connections:", connections)
        print("Total Suppliers:", suppliers)
        print("Failed Companies:", len(self.failed))
        print("Active Companies:", total - len(self.failed))
        print("========================================")

    # --------------------------------------------------------
    # 8. Add new company
    # --------------------------------------------------------

    def add_company(self):

        name = input("Enter company name: ").strip()

        if not name:
            print("Company name cannot be empty.")
            return

        if name in self.graph:
            print("Company already exists.")
            return

        self.graph[name] = []

        self.details[name] = {
            "status": "Active",
            "inventory": 100,
            "capacity": 100,
            "demand": 50,
            "failure_probability": 10
        }

        print(name, "added successfully.")

    # --------------------------------------------------------
    # 9. Remove company
    # --------------------------------------------------------

    def remove_company(self):

        name = input("Enter company to remove: ").strip()

        if name not in self.graph:
            print("Company not found.")
            return

        del self.graph[name]
        del self.details[name]

        self.failed.discard(name)

        for company in self.graph:
            if name in self.graph[company]:
                self.graph[company].remove(name)

        print("Company removed successfully.")

    # --------------------------------------------------------
    # 10. Add connection
    # --------------------------------------------------------

    def add_connection(self):

        source = input("Enter source company: ").strip()
        destination = input("Enter destination company: ").strip()

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

        print("Connection added successfully.")

    # --------------------------------------------------------
    # 11. Remove connection
    # --------------------------------------------------------

    def remove_connection(self):

        source = input("Enter source company: ").strip()
        destination = input("Enter destination company: ").strip()

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

        visited = set(failed_companies)
        queue = deque(failed_companies)
        levels = {}

        while queue:

            current = queue.popleft()

            for company in self.graph[current]:

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

        failed = input("\nEnter failed company: ").strip()

        if failed not in self.graph:
            print("Invalid company.")
            return

        if failed in self.failed:
            print("Company is already marked as failed.")
            return

        self.failed.add(failed)
        self.details[failed]["status"] = "Failed"

        affected = self.find_affected([failed])

        print("\n========== FAILURE REPORT ==========")
        print("Failed Company:", failed)

        if not affected:
            print("No downstream companies affected.")

        for company, level in affected.items():

            if company in self.failed:
                continue

            if level == 1:
                risk = "HIGH"
            elif level == 2:
                risk = "MEDIUM"
            else:
                risk = "LOW"

            print(
                company,
                "| Level:", level,
                "| Risk:", risk
            )

        print("Total Downstream Companies:", len(affected))

        self.history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "company": failed,
            "affected": len(affected)
        })

        print("====================================")

    # --------------------------------------------------------
    # 16. Multiple company failure
    # --------------------------------------------------------

    def multiple_failure(self):

        names = input(
            "Enter failed companies separated by commas: "
        ).split(",")

        failed = []

        for name in names:

            name = name.strip()

            if name in self.graph:
                if name not in self.failed:
                    self.failed.add(name)
                    self.details[name]["status"] = "Failed"
                    failed.append(name)
            else:
                print("Invalid company:", name)

        if not failed:
            print("No new valid failures selected.")
            return

        affected = self.find_affected(failed)

        print("\nMultiple Failure Analysis")

        for company, level in affected.items():

            if company not in self.failed:
                print(company, "- Level", level)

        self.history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "company": ", ".join(failed),
            "affected": len(affected)
        })

    # --------------------------------------------------------
    # 17. Risk analysis
    # --------------------------------------------------------

    def risk_analysis(self):

        print("\n========== RISK ANALYSIS ==========")

        for company in self.graph:

            if company in self.failed:
                continue

            probability = self.details[company]["failure_probability"]

            if probability >= 70:
                risk = "HIGH"
            elif probability >= 30:
                risk = "MEDIUM"
            else:
                risk = "LOW"

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

        percentage = (len(self.failed) / total) * 100

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
    # 20. Critical company detection
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

        company = input("Enter company name: ").strip()

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

        ranking.sort(key=lambda item: item[1], reverse=True)

        print("\n========== SUPPLIER RANKING ==========")

        for index, (name, score) in enumerate(ranking, 1):
            print(index, name, "| Connections:", score)

    # --------------------------------------------------------
    # 25. Recovery simulation
    # --------------------------------------------------------

    def recover_company(self):

        name = input("Enter company to recover: ").strip()

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

        name = input("Enter company name: ").strip()

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

        total = len(self.graph)
        failed = len(self.failed)
        active = total - failed

        print("\n========== ATMOGRAPH DASHBOARD ==========")

        print("Total Companies:", total)
        print("Active Companies:", active)
        print("Failed Companies:", failed)

        if total > 0:
            print("Network Health:",
                  round(active / total * 100, 2), "%")

        print("Total Simulations:", len(self.history))

        print("=========================================")

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

        start = input("Enter starting company: ").strip()
        end = input("Enter destination company: ").strip()

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

        start = input("Enter starting company: ").strip()

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

            for destination in connections:

                if destination not in self.graph:
                    print("Invalid connection:", company, destination)
                    valid = False

        if valid:
            print("Network validation successful.")

    # --------------------------------------------------------
    # 36. Failure probability update
    # --------------------------------------------------------

    def update_probability(self):

        name = input("Enter company name: ").strip()

        if name not in self.graph:
            print("Company not found.")
            return

        try:
            probability = int(input("Enter failure probability (0-100): "))

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

        name = input("Enter company name: ").strip()

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

        name = input("Enter company name: ").strip()

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
            print("Failed Company List:", list(self.failed))
        else:
            print("No failed companies.")

        print("==========================================")


# ============================================================
# 51. MAIN MENU
# ============================================================

def main():

    system = AtmoGraph()

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

        elif choice == 1:
            system.display_network()

        elif choice == 2:
            system.network_statistics()

        elif choice == 3:
            system.add_company()

        elif choice == 4:
            system.remove_company()

        elif choice == 5:
            system.add_connection()

        elif choice == 6:
            system.remove_connection()

        elif choice == 7:
            system.bfs(input("Enter starting company: ").strip())

        elif choice == 8:
            system.dfs(input("Enter starting company: ").strip())

        elif choice == 9:
            system.simulate_failure()

        elif choice == 10:
            system.multiple_failure()

        elif choice == 11:
            system.risk_analysis()

        elif choice == 12:
            system.risk_percentage()

        elif choice == 13:
            system.impact_score()

        elif choice == 14:
            system.critical_companies()

        elif choice == 15:
            system.alternative_suppliers()

        elif choice == 16:
            system.bottleneck_detection()

        elif choice == 17:
            system.dependency_analysis()

        elif choice == 18:
            system.supplier_ranking()

        elif choice == 19:
            system.recover_company()

        elif choice == 20:
            system.search_company()

        elif choice == 21:
            system.company_details()

        elif choice == 22:
            system.show_history()

        elif choice == 23:
            system.dashboard()

        elif choice == 24:
            system.visualize_network()

        elif choice == 25:
            system.shortest_path()

        elif choice == 26:
            system.path_analysis()

        elif choice == 27:
            system.disconnected_companies()

        elif choice == 28:
            system.detect_cycles()

        elif choice == 29:
            system.validate_network()

        elif choice == 30:
            system.update_probability()

        elif choice == 31:
            system.inventory_tracking()

        elif choice == 32:
            system.inventory_alerts()

        elif choice == 33:
            system.update_inventory()

        elif choice == 34:
            system.production_capacity()

        elif choice == 35:
            system.update_capacity()

        elif choice == 36:
            system.demand_tracking()

        elif choice == 37:
            system.shortage_estimation()

        elif choice == 38:
            system.recovery_recommendations()

        elif choice == 39:
            system.risk_mitigation()

        elif choice == 40:
            system.company_status()

        elif choice == 41:
            system.export_csv()

        elif choice == 42:
            system.current_timestamp()

        elif choice == 43:
            system.reset_network()

        elif choice == 44:
            system.summary_report()

        else:
            print("Invalid choice! Select between 0 and 44.")


# ============================================================
# 52. PROGRAM EXECUTION
# ============================================================

if __name__ == "__main__":
    main()