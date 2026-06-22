"""Central source tracker — CRUD for the academic source database."""

import argparse
import json
import re
import sys

from tools.utils import (
    PROJECT_ROOT, load_json, save_json, slugify, today_stamp, now_iso,
    ensure_directories, setup_logging,
)

log = setup_logging("manage_sources")

TRACKER_PATH = str(PROJECT_ROOT / "data" / "sources" / "source-tracker.json")
VALID_STATUSES = {"discovered", "screened", "reading", "read", "cited", "excluded"}


def _load_tracker() -> dict:
    data = load_json(TRACKER_PATH)
    if data is None:
        data = {"version": 1, "last_updated": now_iso(), "sources": []}
    return data


def _save_tracker(data: dict):
    data["last_updated"] = now_iso()
    save_json(TRACKER_PATH, data)


def _find_source(sources: list, doi: str) -> int:
    doi_lower = doi.strip().lower()
    for i, s in enumerate(sources):
        if (s.get("doi") or "").strip().lower() == doi_lower:
            return i
    return -1


def _generate_bibtex_key(source: dict) -> str:
    authors = source.get("authors", [])
    surname = "unknown"
    if authors:
        name = authors[0].get("name", "")
        parts = re.split(r'[,\s]+', name)
        surname = parts[-1] if len(parts) > 1 else parts[0]
        surname = re.sub(r'[^\w]', '', surname).lower()

    year = source.get("year", "0000")
    title = source.get("title", "")
    words = re.findall(r'\w+', title.lower())
    short = words[0] if words else "untitled"

    return f"{surname}_{year}_{short}"


def action_add(doi: str, data: dict) -> dict:
    ensure_directories()
    tracker = _load_tracker()

    if _find_source(tracker["sources"], doi) >= 0:
        return {"status": "exists", "message": f"Source with DOI {doi} already exists"}

    source = {
        "doi": doi,
        "title": data.get("title", ""),
        "authors": data.get("authors", []),
        "year": data.get("year"),
        "venue": data.get("venue", ""),
        "volume": data.get("volume"),
        "issue": data.get("issue"),
        "pages": data.get("pages"),
        "url": data.get("url", ""),
        "abstract": data.get("abstract", ""),
        "citation_count": data.get("citation_count", 0),
        "is_open_access": data.get("is_open_access", False),
        "open_access_url": data.get("open_access_url"),
        "source_api": data.get("source_api", "manual"),
        "status": data.get("status", "discovered"),
        "relevance_tags": data.get("relevance_tags", []),
        "chapter_relevance": data.get("chapter_relevance", []),
        "reading_notes_path": None,
        "user_rating": None,
        "added_date": today_stamp(),
        "read_date": None,
        "bibtex_key": None,
        "last_updated": now_iso(),
    }
    source["bibtex_key"] = _generate_bibtex_key(source)
    tracker["sources"].append(source)
    _save_tracker(tracker)
    return {"status": "added", "doi": doi, "bibtex_key": source["bibtex_key"]}


def action_update(doi: str, data: dict) -> dict:
    tracker = _load_tracker()
    idx = _find_source(tracker["sources"], doi)
    if idx < 0:
        return {"status": "not_found", "message": f"No source with DOI {doi}"}

    source = tracker["sources"][idx]
    for key, value in data.items():
        if key in source and key not in ("doi", "added_date"):
            source[key] = value
    source["last_updated"] = now_iso()

    if "status" in data and data["status"] not in VALID_STATUSES:
        return {"status": "error", "message": f"Invalid status: {data['status']}. Valid: {VALID_STATUSES}"}

    tracker["sources"][idx] = source
    _save_tracker(tracker)
    return {"status": "updated", "doi": doi}


def action_read(doi: str) -> dict:
    tracker = _load_tracker()
    idx = _find_source(tracker["sources"], doi)
    if idx < 0:
        return {"status": "not_found", "message": f"No source with DOI {doi}"}
    return {"status": "ok", "source": tracker["sources"][idx]}


def action_list(filters: dict | None = None) -> dict:
    tracker = _load_tracker()
    sources = tracker["sources"]

    if filters:
        if "status" in filters:
            sources = [s for s in sources if s.get("status") == filters["status"]]
        if "year_min" in filters:
            sources = [s for s in sources if (s.get("year") or 0) >= filters["year_min"]]
        if "year_max" in filters:
            sources = [s for s in sources if (s.get("year") or 9999) <= filters["year_max"]]
        if "relevance_tags" in filters:
            tags = set(filters["relevance_tags"])
            sources = [s for s in sources if tags & set(s.get("relevance_tags", []))]
        if "chapter_relevance" in filters:
            chapters = set(filters["chapter_relevance"])
            sources = [s for s in sources if chapters & set(s.get("chapter_relevance", []))]

    return {"status": "ok", "count": len(sources), "sources": sources}


def action_stats() -> dict:
    tracker = _load_tracker()
    sources = tracker["sources"]
    total = len(sources)

    by_status = {}
    for s in sources:
        st = s.get("status", "unknown")
        by_status[st] = by_status.get(st, 0) + 1

    by_year = {}
    for s in sources:
        y = s.get("year", "unknown")
        by_year[str(y)] = by_year.get(str(y), 0) + 1

    by_chapter = {}
    for s in sources:
        for ch in s.get("chapter_relevance", []):
            by_chapter[ch] = by_chapter.get(ch, 0) + 1

    read_count = by_status.get("read", 0) + by_status.get("cited", 0)
    read_pct = round(read_count / total * 100, 1) if total > 0 else 0

    return {
        "status": "ok",
        "total_sources": total,
        "by_status": by_status,
        "by_year": dict(sorted(by_year.items())),
        "by_chapter": by_chapter,
        "reading_progress_pct": read_pct,
    }


def action_import_search(input_path: str) -> dict:
    ensure_directories()
    search_data = load_json(input_path)
    if not search_data:
        return {"status": "error", "message": f"Could not load {input_path}"}

    results = search_data.get("results", [])
    added = 0
    skipped = 0

    for r in results:
        doi = r.get("doi")
        if not doi:
            skipped += 1
            continue
        result = action_add(doi, r)
        if result["status"] == "added":
            added += 1
        else:
            skipped += 1

    return {"status": "ok", "imported": added, "skipped": skipped, "total_in_file": len(results)}


def main():
    parser = argparse.ArgumentParser(description="Manage the academic source tracker")
    parser.add_argument("--action", required=True,
                        choices=["add", "update", "read", "list", "stats", "import-search"])
    parser.add_argument("--doi", help="DOI of the source")
    parser.add_argument("--data", help="JSON string with source data")
    parser.add_argument("--filters", help="JSON string with filter criteria (for list action)")
    parser.add_argument("--input", help="Input file path (for import-search action)")
    args = parser.parse_args()

    if args.action == "add":
        if not args.doi or not args.data:
            parser.error("--doi and --data required for add")
        result = action_add(args.doi, json.loads(args.data))
    elif args.action == "update":
        if not args.doi or not args.data:
            parser.error("--doi and --data required for update")
        result = action_update(args.doi, json.loads(args.data))
    elif args.action == "read":
        if not args.doi:
            parser.error("--doi required for read")
        result = action_read(args.doi)
    elif args.action == "list":
        filters = json.loads(args.filters) if args.filters else None
        result = action_list(filters)
    elif args.action == "stats":
        result = action_stats()
    elif args.action == "import-search":
        if not args.input:
            parser.error("--input required for import-search")
        result = action_import_search(args.input)
    else:
        result = {"status": "error", "message": f"Unknown action: {args.action}"}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
