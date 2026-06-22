"""Export sources as BibTeX or RIS files for Zotero import."""

import argparse
import json
import re
import sys

from tools.utils import PROJECT_ROOT, load_json, save_json, now_iso, setup_logging

log = setup_logging("export_citations")

TRACKER_PATH = str(PROJECT_ROOT / "data" / "sources" / "source-tracker.json")


def _format_author_bibtex(authors: list) -> str:
    names = []
    for a in authors:
        name = a.get("name", "")
        if not name:
            continue
        if "," in name:
            names.append(name)
        else:
            parts = name.strip().split()
            if len(parts) >= 2:
                names.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
            else:
                names.append(name)
    return " and ".join(names)


def _entry_type(source: dict) -> str:
    stype = (source.get("type") or "").lower()
    if "proceedings" in stype or "conference" in stype:
        return "inproceedings"
    if "book-chapter" in stype or "chapter" in stype:
        return "incollection"
    return "article"


def _to_bibtex(source: dict) -> str:
    key = source.get("bibtex_key", "unknown_0000")
    etype = _entry_type(source)

    fields = []
    if source.get("title"):
        fields.append(f'  title     = {{{source["title"]}}}')
    if source.get("authors"):
        fields.append(f'  author    = {{{_format_author_bibtex(source["authors"])}}}')
    if source.get("venue"):
        if etype == "inproceedings":
            fields.append(f'  booktitle = {{{source["venue"]}}}')
        else:
            fields.append(f'  journal   = {{{source["venue"]}}}')
    if source.get("year"):
        fields.append(f'  year      = {{{source["year"]}}}')
    if source.get("volume"):
        fields.append(f'  volume    = {{{source["volume"]}}}')
    if source.get("issue"):
        fields.append(f'  number    = {{{source["issue"]}}}')
    if source.get("pages"):
        pages = str(source["pages"]).replace("-", "--")
        fields.append(f'  pages     = {{{pages}}}')
    if source.get("doi"):
        fields.append(f'  doi       = {{{source["doi"]}}}')
    if source.get("url"):
        fields.append(f'  url       = {{{source["url"]}}}')

    body = ",\n".join(fields)
    return f"@{etype}{{{key},\n{body}\n}}"


def _format_author_ris(authors: list) -> list[str]:
    lines = []
    for a in authors:
        name = a.get("name", "")
        if not name:
            continue
        if "," in name:
            lines.append(f"AU  - {name}")
        else:
            parts = name.strip().split()
            if len(parts) >= 2:
                lines.append(f"AU  - {parts[-1]}, {' '.join(parts[:-1])}")
            else:
                lines.append(f"AU  - {name}")
    return lines


def _ris_type(source: dict) -> str:
    stype = (source.get("type") or "").lower()
    if "proceedings" in stype or "conference" in stype:
        return "CONF"
    if "book-chapter" in stype or "chapter" in stype:
        return "CHAP"
    return "JOUR"


def _to_ris(source: dict) -> str:
    lines = [f"TY  - {_ris_type(source)}"]
    if source.get("title"):
        lines.append(f"TI  - {source['title']}")
    lines.extend(_format_author_ris(source.get("authors", [])))
    if source.get("year"):
        lines.append(f"PY  - {source['year']}")
    if source.get("venue"):
        lines.append(f"JO  - {source['venue']}")
    if source.get("volume"):
        lines.append(f"VL  - {source['volume']}")
    if source.get("issue"):
        lines.append(f"IS  - {source['issue']}")
    if source.get("pages"):
        pages = str(source["pages"])
        if "--" in pages or "-" in pages:
            parts = re.split(r'--?', pages)
            if len(parts) == 2:
                lines.append(f"SP  - {parts[0].strip()}")
                lines.append(f"EP  - {parts[1].strip()}")
        else:
            lines.append(f"SP  - {pages}")
    if source.get("doi"):
        lines.append(f"DO  - {source['doi']}")
    if source.get("url"):
        lines.append(f"UR  - {source['url']}")
    if source.get("abstract"):
        lines.append(f"AB  - {source['abstract']}")
    lines.append("ER  - ")
    return "\n".join(lines)


def export(fmt: str, output_path: str, filters: dict | None = None, doi: str | None = None) -> dict:
    tracker = load_json(TRACKER_PATH)
    if not tracker:
        return {"status": "error", "message": "No source tracker found. Run a search first."}

    sources = tracker.get("sources", [])

    if doi:
        sources = [s for s in sources if (s.get("doi") or "").strip().lower() == doi.strip().lower()]
    elif filters:
        if "status" in filters:
            sources = [s for s in sources if s.get("status") == filters["status"]]
        if "relevance_tags" in filters:
            tags = set(filters["relevance_tags"])
            sources = [s for s in sources if tags & set(s.get("relevance_tags", []))]
        if "chapter_relevance" in filters:
            chapters = set(filters["chapter_relevance"])
            sources = [s for s in sources if chapters & set(s.get("chapter_relevance", []))]

    if not sources:
        return {"status": "ok", "exported": 0, "message": "No sources match the criteria"}

    if fmt == "bibtex":
        entries = [_to_bibtex(s) for s in sources]
        content = "\n\n".join(entries) + "\n"
    else:
        entries = [_to_ris(s) for s in sources]
        content = "\n\n".join(entries) + "\n"

    from pathlib import Path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"status": "ok", "exported": len(sources), "format": fmt, "output": output_path}


def main():
    parser = argparse.ArgumentParser(description="Export sources as BibTeX or RIS for Zotero")
    parser.add_argument("--format", required=True, choices=["bibtex", "ris"], help="Export format")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--filters", help="JSON filter criteria")
    parser.add_argument("--doi", help="Export a single source by DOI")
    args = parser.parse_args()

    filters = json.loads(args.filters) if args.filters else None
    result = export(args.format, args.output, filters, args.doi)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
