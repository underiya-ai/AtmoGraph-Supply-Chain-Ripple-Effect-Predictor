
# AtmoGraph - Supply Chain Ripple Effect Predictor

def create_supply_chain():
    supply_chain = {
        "Supplier_A": ["Manufacturer"],
        "Supplier_B": ["Manufacturer"],
        "Manufacturer": ["Distributor"],
        "Distributor": ["Retailer"],
        "Retailer": []
    }
    return supply_chain


def display_supply_chain(graph):
    print("\nSupply Chain Network:")
    for company, connections in graph.items():
        print(company, "->", connections)


def main():
    print("Welcome to AtmoGraph!")
    graph = create_supply_chain()
    display_supply_chain(graph)


if __name__ == "__main__":
    main()