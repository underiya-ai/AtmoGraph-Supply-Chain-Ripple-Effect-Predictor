# AtmoGraph - Supply Chain Ripple Effect Predictor


# Step 1: Create Supply Chain Network
def create_supply_chain():

    supply_chain = {
        "Supplier_A": ["Manufacturer"],
        "Supplier_B": ["Manufacturer"],
        "Manufacturer": ["Distributor"],
        "Distributor": ["Retailer"],
        "Retailer": []
    }

    return supply_chain


# Step 2: Display Supply Chain Network
def display_supply_chain(graph):

    print("\nSupply Chain Network:")

    for company, connections in graph.items():
        print(company, "->", connections)


# Step 3: Simulate Supplier Failure
def simulate_supplier_failure(graph, failed_supplier):

    print("\n--- Supplier Failure Simulation ---")

    affected = []
    queue = [failed_supplier]
    visited = [failed_supplier]

    while queue:

        current = queue.pop(0)

        for company in graph[current]:

            if company not in visited:

                visited.append(company)
                affected.append(company)
                queue.append(company)

    print("Failed Company:", failed_supplier)

    print("\nAffected Companies:")

    for company in affected:
        print("->", company)

    print("\nTotal Affected Companies:", len(affected))


# Step 4: Ripple Effect and Risk Analysis
def analyze_ripple_effect(graph, failed_supplier):

    print("\n--- Ripple Effect Risk Analysis ---")

    queue = [(failed_supplier, 0)]
    visited = [failed_supplier]

    risk_count = 0

    while queue:

        current, level = queue.pop(0)

        for company in graph[current]:

            if company not in visited:

                visited.append(company)

                next_level = level + 1

                queue.append((company, next_level))

                if next_level == 1:
                    risk = "High"
                elif next_level == 2:
                    risk = "Medium"
                else:
                    risk = "Low"

                print(company, ":", risk, "Risk")

                risk_count += 1

    print("\nTotal Companies at Risk:", risk_count)


# Step 5: Interactive Supplier Selection
def select_failed_supplier():

    print("\nSelect the supplier that has failed:")
    print("1. Supplier_A")
    print("2. Supplier_B")

    while True:

        choice = input("\nEnter your choice (1 or 2): ").strip()

        if choice == "1":
            return "Supplier_A"

        elif choice == "2":
            return "Supplier_B"

        else:
            print("Invalid choice! Please enter 1 or 2.")


# Step 6: Main Function
def main():

    print("Welcome to AtmoGraph!")

    graph = create_supply_chain()

    display_supply_chain(graph)

    failed_supplier = select_failed_supplier()

    simulate_supplier_failure(graph, failed_supplier)

    analyze_ripple_effect(graph, failed_supplier)


# Step 7: Program Execution
if __name__ == "__main__":
    main()