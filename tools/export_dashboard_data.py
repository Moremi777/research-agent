"""Export all research data as a single JSON file for the web dashboard."""

import argparse
import json

from tools.utils import PROJECT_ROOT, load_json, save_json, now_iso, setup_logging

log = setup_logging("export_dashboard_data")

TRACKER_PATH = str(PROJECT_ROOT / "data" / "sources" / "source-tracker.json")
READING_LOG_PATH = str(PROJECT_ROOT / "data" / "progress" / "reading-log.json")
PROGRESS_PATH = str(PROJECT_ROOT / "data" / "progress" / "progress-tracker.json")
NOTES_DIR = PROJECT_ROOT / "data" / "notes"
QUIZZES_DIR = PROJECT_ROOT / "data" / "quizzes"


def export_all(output_path: str) -> dict:
    tracker = load_json(TRACKER_PATH) or {"sources": []}
    reading_log = load_json(READING_LOG_PATH) or {"readings": []}
    progress = load_json(PROGRESS_PATH) or {"daily_logs": {}, "weekly_summaries": {}, "streaks": {"current_streak_days": 0, "longest_streak_days": 0, "last_active_date": None}}

    notes = {}
    if NOTES_DIR.exists():
        for f in NOTES_DIR.glob("*.json"):
            data = load_json(str(f))
            if data:
                notes[f.stem] = data

    quizzes = []
    if QUIZZES_DIR.exists():
        for f in sorted(QUIZZES_DIR.glob("*.json"), reverse=True):
            data = load_json(str(f))
            if data:
                quizzes.append(data)

    sources = tracker.get("sources", [])
    by_status = {}
    by_year = {}
    by_chapter = {}
    by_tag = {}
    for s in sources:
        st = s.get("status", "unknown")
        by_status[st] = by_status.get(st, 0) + 1
        y = str(s.get("year", "unknown"))
        by_year[y] = by_year.get(y, 0) + 1
        for ch in s.get("chapter_relevance", []):
            by_chapter[ch] = by_chapter.get(ch, 0) + 1
        for tag in s.get("relevance_tags", []):
            by_tag[tag] = by_tag.get(tag, 0) + 1

    read_count = by_status.get("read", 0) + by_status.get("cited", 0)
    total = len(sources)

    dashboard_data = {
        "exported_at": now_iso(),
        "stats": {
            "total_sources": total,
            "by_status": by_status,
            "by_year": dict(sorted(by_year.items())),
            "by_chapter": by_chapter,
            "by_tag": by_tag,
            "reading_progress_pct": round(read_count / total * 100, 1) if total > 0 else 0,
        },
        "streaks": progress.get("streaks", {}),
        "daily_logs": progress.get("daily_logs", {}),
        "sources": [{
            "doi": s.get("doi", ""),
            "title": s.get("title", ""),
            "authors": [a.get("name", "") for a in s.get("authors", [])],
            "year": s.get("year"),
            "venue": s.get("venue", ""),
            "abstract": s.get("abstract", ""),
            "citation_count": s.get("citation_count", 0),
            "is_open_access": s.get("is_open_access", False),
            "open_access_url": s.get("open_access_url"),
            "status": s.get("status", "discovered"),
            "relevance_tags": s.get("relevance_tags", []),
            "chapter_relevance": s.get("chapter_relevance", []),
            "bibtex_key": s.get("bibtex_key", ""),
            "added_date": s.get("added_date", ""),
            "read_date": s.get("read_date"),
        } for s in sources if s.get("status") != "excluded"],
        "readings": reading_log.get("readings", []),
        "quizzes": quizzes[:20],
        "notes": notes,
        "timeline": {
            "milestones": [
                {"date": "2026-06-22", "label": "Start: Finalise scope", "category": "reading"},
                {"date": "2026-06-29", "label": "Intensive reading begins", "category": "reading"},
                {"date": "2026-07-27", "label": "Chapter 1 draft due", "category": "writing"},
                {"date": "2026-07-27", "label": "Lit review begins", "category": "reading"},
                {"date": "2026-08-31", "label": "Chapter 2 draft due", "category": "writing"},
                {"date": "2026-08-31", "label": "Methodology begins", "category": "writing"},
                {"date": "2026-09-28", "label": "Chapter 3 draft due", "category": "writing"},
                {"date": "2026-09-28", "label": "Game design begins", "category": "development"},
                {"date": "2026-10-26", "label": "Chapter 4 specs due", "category": "writing"},
                {"date": "2026-10-26", "label": "Prototype iterations", "category": "development"},
                {"date": "2026-12-01", "label": "Polish all chapters", "category": "review"},
                {"date": "2026-12-31", "label": "Chapters 1-4 complete", "category": "review"},
            ]
        },
    }

    save_json(output_path, dashboard_data)
    return {"status": "ok", "output": output_path, "sources_exported": len(dashboard_data["sources"])}


def main():
    parser = argparse.ArgumentParser(description="Export research data for the web dashboard")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "docs" / "data.json"), help="Output JSON path")
    args = parser.parse_args()
    result = export_all(args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
