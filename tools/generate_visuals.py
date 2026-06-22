"""Generate concept maps, thematic maps, and timelines as PNG/SVG images."""

import argparse
import json
import sys
from pathlib import Path

from tools.utils import load_json, save_json, now_iso, ensure_directories, setup_logging

log = setup_logging("generate_visuals")

GROUP_COLOURS = {
    "problem_domain": "#E8D5B7",
    "solution_domain": "#B7D5E8",
    "methodology": "#D5E8B7",
    "framework": "#E8B7D5",
    "game_design": "#B7E8D5",
    "default": "#D5D5D5",
}


def _generate_concept_map(data: dict, output_path: str, fmt: str):
    try:
        import graphviz
    except ImportError:
        log.error("graphviz Python package not installed. Run: pip install graphviz")
        return {"status": "error", "message": "graphviz not installed"}

    title = data.get("title", "Concept Map")
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    dot = graphviz.Digraph(comment=title, format=fmt)
    dot.attr(rankdir="TB", label=title, fontsize="16", fontname="Arial",
             bgcolor="white", pad="0.5")
    dot.attr("node", shape="box", style="rounded,filled", fontname="Arial",
             fontsize="11", margin="0.2,0.1")
    dot.attr("edge", fontname="Arial", fontsize="9")

    for node in nodes:
        colour = GROUP_COLOURS.get(node.get("group", "default"), GROUP_COLOURS["default"])
        dot.node(node["id"], node["label"], fillcolor=colour)

    for edge in edges:
        dot.edge(edge["from"], edge["to"], label=edge.get("label", ""))

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stem = str(out_path.with_suffix(""))
    dot.render(stem, cleanup=True)
    log.info("Concept map saved to %s", output_path)
    return {"status": "ok", "output": output_path}


def _generate_thematic_map(data: dict, output_path: str, fmt: str):
    try:
        import graphviz
    except ImportError:
        log.error("graphviz Python package not installed. Run: pip install graphviz")
        return {"status": "error", "message": "graphviz not installed"}

    title = data.get("title", "Thematic Map")
    themes = data.get("themes", [])

    dot = graphviz.Digraph(comment=title, format=fmt)
    dot.attr(rankdir="LR", label=title, fontsize="16", fontname="Arial",
             bgcolor="white", pad="0.5")
    dot.attr("node", fontname="Arial", fontsize="10")
    dot.attr("edge", fontname="Arial", fontsize="8")

    dot.node("central", data.get("central_topic", "Research Topic"),
             shape="ellipse", style="filled", fillcolor="#FFD700",
             fontsize="13", fontname="Arial Bold")

    for i, theme in enumerate(themes):
        theme_id = f"theme_{i}"
        colour = list(GROUP_COLOURS.values())[i % len(GROUP_COLOURS)]
        dot.node(theme_id, theme["label"], shape="box", style="rounded,filled",
                 fillcolor=colour, fontsize="11")
        dot.edge("central", theme_id, style="bold")

        for j, sub in enumerate(theme.get("sub_themes", [])):
            sub_id = f"sub_{i}_{j}"
            dot.node(sub_id, sub, shape="box", style="filled",
                     fillcolor=colour + "80", fontsize="9")
            dot.edge(theme_id, sub_id)

        for gap in theme.get("gaps", []):
            gap_id = f"gap_{i}_{len(theme.get('sub_themes', []))}"
            dot.node(gap_id, f"GAP: {gap}", shape="box", style="dashed,filled",
                     fillcolor="#FFB3B3", fontsize="9")
            dot.edge(theme_id, gap_id, style="dashed", color="red")

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stem = str(out_path.with_suffix(""))
    dot.render(stem, cleanup=True)
    log.info("Thematic map saved to %s", output_path)
    return {"status": "ok", "output": output_path}


def _generate_timeline(data: dict, output_path: str, fmt: str):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import datetime
    except ImportError:
        log.error("matplotlib not installed. Run: pip install matplotlib")
        return {"status": "error", "message": "matplotlib not installed"}

    title = data.get("title", "Research Timeline")
    milestones = data.get("milestones", [])

    fig, ax = plt.subplots(figsize=(14, 6))

    dates = []
    labels = []
    colours = []
    colour_map = {
        "reading": "#4CAF50",
        "writing": "#2196F3",
        "development": "#FF9800",
        "review": "#9C27B0",
        "default": "#607D8B",
    }

    for m in milestones:
        try:
            d = datetime.strptime(m["date"], "%Y-%m-%d")
            dates.append(d)
            labels.append(m["label"])
            colours.append(colour_map.get(m.get("category", "default"), colour_map["default"]))
        except (ValueError, KeyError):
            continue

    if not dates:
        return {"status": "error", "message": "No valid milestones in input data"}

    levels = []
    for i in range(len(dates)):
        levels.append(1.5 if i % 2 == 0 else -1.5)

    ax.vlines(dates, 0, levels, color=colours, linewidth=2)
    ax.plot(dates, [0] * len(dates), "ko", markersize=4)

    for d, l, level, c in zip(dates, labels, levels, colours):
        ax.annotate(l, xy=(d, level), fontsize=8, ha="center",
                    va="bottom" if level > 0 else "top",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=c, alpha=0.3))

    ax.axhline(0, color="black", linewidth=0.5)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=45, ha="right")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylim(-3, 3)
    ax.get_yaxis().set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    plt.tight_layout()

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close()
    log.info("Timeline saved to %s", output_path)
    return {"status": "ok", "output": output_path}


def generate(visual_type: str, input_path: str, output_path: str, fmt: str = "png") -> dict:
    data = load_json(input_path)
    if not data:
        return {"status": "error", "message": f"Could not load input file: {input_path}"}

    if visual_type == "concept-map":
        return _generate_concept_map(data, output_path, fmt)
    elif visual_type == "thematic-map":
        return _generate_thematic_map(data, output_path, fmt)
    elif visual_type == "timeline":
        return _generate_timeline(data, output_path, fmt)
    else:
        return {"status": "error", "message": f"Unknown visual type: {visual_type}"}


def main():
    parser = argparse.ArgumentParser(description="Generate concept maps, thematic maps, and timelines")
    parser.add_argument("--type", required=True, choices=["concept-map", "thematic-map", "timeline"])
    parser.add_argument("--input", required=True, help="Input JSON file with graph/map data")
    parser.add_argument("--output", required=True, help="Output image file path")
    parser.add_argument("--format", default="png", choices=["png", "svg"], help="Output format (default: png)")
    args = parser.parse_args()

    result = generate(args.type, args.input, args.output, args.format)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
