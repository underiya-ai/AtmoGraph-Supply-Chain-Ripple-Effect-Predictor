import sys
import webbrowser
from html import escape
from pathlib import Path

from graph_loader import load_graph
from ripple_simulation import pick_default_source, simulate_ripple, start_impact_for

OUT_DIR = Path(__file__).parent / "output"

COLUMN_GAP = 150
ROW_GAP = 70
MARGIN_X = 90
MARGIN_TOP = 125
RADIUS = 22

COLORS = {
    "source": "#c0392b",
    "HIGH": "#e8590c",
    "MEDIUM": "#f59f00",
    "LOW": "#ffe066",
    "unaffected": "#ced4da",
}


def layer_of(data, top_tier):
    """Column number: tier 4 -> 0, tier 3 -> 1, ..., then factory, warehouse, retailer."""
    if data["node_type"] == "supplier":
        return top_tier - data["tier"]
    return {"factory": top_tier, "warehouse": top_tier + 1, "retailer": top_tier + 2}[
        data["node_type"]
    ]


def short_label(node_id):
    """SUP-I1-R2-T3 -> R2-T3, FAC-I1-2 -> FAC-2"""
    parts = node_id.split("-")
    return "-".join(parts[2:]) if parts[0] == "SUP" else f"{parts[0]}-{parts[2]}"


def draw_svg(G, source, results, start_impact):
    industry = G.nodes[source]["industry"]
    nodes = [n for n, d in G.nodes(data=True) if d["industry"] == industry]
    sub = G.subgraph(nodes)
    info = {r["node_id"]: r for r in results}

    top_tier = max(d["tier"] for _, d in G.nodes(data=True) if d["tier"] is not None)
    n_layers = top_tier + 3
    layers = {i: [] for i in range(n_layers)}
    for n in nodes:
        layers[layer_of(G.nodes[n], top_tier)].append(n)
    max_rows = max(len(v) for v in layers.values())

    # Position of every node
    pos = {}
    for i, members in layers.items():
        members.sort()
        offset = (max_rows - len(members)) / 2 * ROW_GAP
        for row, n in enumerate(members):
            pos[n] = (MARGIN_X + i * COLUMN_GAP, MARGIN_TOP + offset + row * ROW_GAP)

    width = MARGIN_X * 2 + (n_layers - 1) * COLUMN_GAP
    height = MARGIN_TOP + (max_rows - 1) * ROW_GAP + 170

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="Arial, sans-serif">',
        '<defs>'
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#868e96"/></marker>'
        '<marker id="arrowhot" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#c0392b"/></marker>'
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        f'<text x="{width / 2}" y="32" text-anchor="middle" font-size="18" font-weight="bold">'
        f'{escape(industry)}: ripple effect from {escape(G.nodes[source]["name"])}</text>',
        f'<text x="{width / 2}" y="54" text-anchor="middle" font-size="13" fill="#495057">'
        f'Starting impact {start_impact:.1f} | {len(results)} nodes affected downstream | '
        f'hover over a circle for details</text>',
    ]

    # Column titles
    titles = [f"Tier {top_tier - i}" for i in range(top_tier)] + ["Factory", "Warehouse", "Retailer"]
    for i, title in enumerate(titles):
        out.append(
            f'<text x="{MARGIN_X + i * COLUMN_GAP}" y="{MARGIN_TOP - 40}" text-anchor="middle" '
            f'font-size="13" fill="#495057">{title}</text>'
        )

    affected = set(info) | {source}

    # Edges first, so circles are drawn on top
    for u, v in sub.edges():
        hot = u in affected and v in affected
        (x1, y1), (x2, y2) = pos[u], pos[v]
        out.append(
            f'<line x1="{x1 + RADIUS}" y1="{y1}" x2="{x2 - RADIUS - 3}" y2="{y2}" '
            f'stroke="{"#c0392b" if hot else "#adb5bd"}" stroke-width="{2.5 if hot else 1}" '
            f'marker-end="url(#{"arrowhot" if hot else "arrow"})"/>'
        )

    # Nodes
    for n in nodes:
        x, y = pos[n]
        data = G.nodes[n]
        if n == source:
            color, extra = COLORS["source"], "DISRUPTED"
        elif n in info:
            color = COLORS[info[n]["risk_level"]]
            extra = f'impact {info[n]["impact"]} ({info[n]["risk_level"]}), {info[n]["distance"]} step(s) away'
        else:
            color, extra = COLORS["unaffected"], "not affected"
        text_color = "white" if n == source else "#212529"
        out.append(
            f'<g><title>{escape(data["name"])} | {data["node_type"]} | {escape(data["region"])} | {extra}</title>'
            f'<circle cx="{x}" cy="{y}" r="{RADIUS}" fill="{color}" stroke="#495057" stroke-width="1"/>'
            f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-size="11" fill="{text_color}">'
            f'{escape(short_label(n))}</text></g>'
        )

    # Legend
    legend_y = height - 95
    items = [("Disrupted", COLORS["source"]), ("HIGH", COLORS["HIGH"]), ("MEDIUM", COLORS["MEDIUM"]),
             ("LOW", COLORS["LOW"]), ("Not affected", COLORS["unaffected"])]
    for k, (label, color) in enumerate(items):
        lx = MARGIN_X + k * 150
        out.append(f'<circle cx="{lx}" cy="{legend_y}" r="9" fill="{color}" stroke="#495057"/>')
        out.append(f'<text x="{lx + 16}" y="{legend_y + 4}" font-size="12">{label}</text>')

    # Key for the region codes used in the supplier labels
    regions = {}
    for n in nodes:
        if G.nodes[n]["node_type"] == "supplier":
            regions[short_label(n).split("-")[0]] = G.nodes[n]["region"]
    key = "   ".join(f"{code} = {name}" for code, name in sorted(regions.items()))
    out.append(f'<text x="{MARGIN_X - 40}" y="{legend_y + 38}" font-size="12" fill="#495057">Region codes: {escape(key)}</text>')
    out.append(f'<text x="{MARGIN_X - 40}" y="{legend_y + 58}" font-size="12" fill="#495057">'
               f'Synthetic network; disruption values come from the real dataset.</text>')

    out.append("</svg>")
    return "\n".join(out)


def main():
    G = load_graph()
    source = sys.argv[1] if len(sys.argv) > 1 else pick_default_source(G)
    if source not in G:
        print(f"Unknown node: {source}")
        return
    start = float(sys.argv[2]) if len(sys.argv) > 2 else start_impact_for(G, source)

    results = simulate_ripple(G, source, start)
    svg = draw_svg(G, source, results, start)

    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / f"ripple_{source}.svg"
    path.write_text(svg, encoding="utf-8")
    print("Saved picture:", path)
    print("Affected nodes drawn:", len(results))
    webbrowser.open(path.as_uri())


if __name__ == "__main__":
    main()
