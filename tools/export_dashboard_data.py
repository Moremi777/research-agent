"""Export all research data as a single JSON file for the web dashboard."""

import argparse
import json
from datetime import datetime, timezone

from tools.utils import PROJECT_ROOT, load_json, save_json, now_iso, today_stamp, setup_logging

log = setup_logging("export_dashboard_data")

TRACKER_PATH = str(PROJECT_ROOT / "data" / "sources" / "source-tracker.json")
READING_LOG_PATH = str(PROJECT_ROOT / "data" / "progress" / "reading-log.json")
PROGRESS_PATH = str(PROJECT_ROOT / "data" / "progress" / "progress-tracker.json")
NOTES_DIR = PROJECT_ROOT / "data" / "notes"
QUIZZES_DIR = PROJECT_ROOT / "data" / "quizzes"
DAILY_DIR = PROJECT_ROOT / "data" / "daily"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
CHAPTERS_DIR = PROJECT_ROOT / "data" / "chapters"


def _load_latest_daily_plan() -> dict | None:
    if not DAILY_DIR.exists():
        return None
    files = sorted(DAILY_DIR.glob("plan-*.json"), reverse=True)
    if files:
        return load_json(str(files[0]))
    return None


def _load_latest_feedback_report() -> dict | None:
    if not REPORTS_DIR.exists():
        return None
    files = sorted(REPORTS_DIR.glob("feedback-*.json"), reverse=True)
    if files:
        return load_json(str(files[0]))
    return None


def _load_all_feedback_reports() -> list[dict]:
    if not REPORTS_DIR.exists():
        return []
    reports = []
    for f in sorted(REPORTS_DIR.glob("feedback-*.json"), reverse=True):
        data = load_json(str(f))
        if data:
            reports.append(data)
    return reports[:12]


def _load_daily_plans(days: int = 7) -> list[dict]:
    if not DAILY_DIR.exists():
        return []
    plans = []
    for f in sorted(DAILY_DIR.glob("plan-*.json"), reverse=True):
        data = load_json(str(f))
        if data:
            plans.append(data)
        if len(plans) >= days:
            break
    return plans


def _load_writing_checks() -> list[dict]:
    tmp_dir = PROJECT_ROOT / ".tmp"
    checks = []
    if tmp_dir.exists():
        for f in sorted(tmp_dir.glob("writing-check-*.json"), reverse=True):
            data = load_json(str(f))
            if data:
                checks.append(data)
    return checks[:5]


def _check_streak_penalty() -> dict:
    progress = load_json(PROGRESS_PATH) or {"daily_logs": {}, "streaks": {}}
    streaks = progress.get("streaks", {})
    daily_logs = progress.get("daily_logs", {})

    today = today_stamp()
    last_active = streaks.get("last_active_date")

    if not last_active:
        return {"streak_broken": False, "days_missed": 0, "must_redo_quizzes": False}

    last_date = datetime.strptime(last_active, "%Y-%m-%d").date()
    today_date = datetime.strptime(today, "%Y-%m-%d").date()
    diff = (today_date - last_date).days

    if diff > 1:
        return {
            "streak_broken": True,
            "days_missed": diff - 1,
            "must_redo_quizzes": True,
            "last_active": last_active,
            "message": f"You missed {diff - 1} day(s)! Your streak has been reset. Complete today's quiz to rebuild.",
        }

    return {"streak_broken": False, "days_missed": 0, "must_redo_quizzes": False}


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
        "streak_penalty": _check_streak_penalty(),
        "daily_logs": progress.get("daily_logs", {}),
        "sources": [{
            "doi": s.get("doi", ""),
            "title": s.get("title", ""),
            "authors": [a.get("name", "") if isinstance(a, dict) else a for a in s.get("authors", [])],
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
        "quizzes": quizzes[:30],
        "notes": notes,
        "daily_plan": _load_latest_daily_plan(),
        "daily_plans_history": _load_daily_plans(7),
        "feedback_report": _load_latest_feedback_report(),
        "feedback_reports_history": _load_all_feedback_reports(),
        "writing_checks": _load_writing_checks(),
        "dissertation_structure": {
            "chapters": [
                {"id": "ch1", "title": "Introduction", "sections": [
                    {"id": "1.1", "title": "Introduction"},
                    {"id": "1.2", "title": "Background and Context"},
                    {"id": "1.3", "title": "Problem Statement"},
                    {"id": "1.4", "title": "Research Question"},
                    {"id": "1.5", "title": "Research Aim and Objectives"},
                    {"id": "1.6", "title": "Purpose and Value of the Research"},
                    {"id": "1.7", "title": "Scope and Limitations"},
                    {"id": "1.8", "title": "Structure of the Research"},
                    {"id": "1.9", "title": "Conclusion"},
                ]},
                {"id": "ch2", "title": "Literature Review", "sections": [
                    {"id": "2.1", "title": "Introduction"},
                    {"id": "2.2", "title": "Thematic Review of the Problem Domain"},
                    {"id": "2.2.1", "title": "Indigenous Farming Knowledge"},
                    {"id": "2.2.2", "title": "Sustainable Agriculture"},
                    {"id": "2.2.3", "title": "Modern Agricultural Science"},
                    {"id": "2.3", "title": "Thematic Review of the Solution Domain"},
                    {"id": "2.3.1", "title": "Serious Games"},
                    {"id": "2.3.2", "title": "Multiplayer and Simulations"},
                    {"id": "2.4", "title": "Existing Artefacts and Their Limitations"},
                    {"id": "2.5", "title": "Theoretical / Conceptual Framework"},
                    {"id": "2.6", "title": "Identification of the Research Gap"},
                    {"id": "2.7", "title": "Conclusion"},
                ]},
                {"id": "ch3", "title": "Research Methodology", "sections": [
                    {"id": "3.1", "title": "Introduction"},
                    {"id": "3.2", "title": "Design Science Research Methodology"},
                    {"id": "3.2.1", "title": "Justification for Using DSR"},
                    {"id": "3.2.2", "title": "DSR Framework Selected"},
                    {"id": "3.3", "title": "Research Cycles"},
                    {"id": "3.3.1", "title": "Relevance Cycle"},
                    {"id": "3.3.2", "title": "Rigour Cycle"},
                    {"id": "3.3.3", "title": "Design Cycle"},
                    {"id": "3.4", "title": "Research Strategy and Data Collection Methods"},
                    {"id": "3.5", "title": "Data Analysis Techniques"},
                    {"id": "3.6", "title": "Evaluation Strategy and Metrics"},
                    {"id": "3.7", "title": "Ethical Considerations"},
                    {"id": "3.8", "title": "Conclusion"},
                ]},
                {"id": "ch4", "title": "Game Design", "sections": [
                    {"id": "4.1", "title": "Introduction"},
                    {"id": "4.2", "title": "Requirements Specifications"},
                    {"id": "4.2.1", "title": "Functional Requirements"},
                    {"id": "4.2.2", "title": "Non-Functional Requirements"},
                    {"id": "4.2.3", "title": "Game Mechanics and Learning Objectives Mapping"},
                    {"id": "4.3", "title": "Design of the Artefact"},
                    {"id": "4.3.1", "title": "Architecture Model"},
                    {"id": "4.3.2", "title": "Details of the Proposed Artefact"},
                    {"id": "4.3.3", "title": "Multiplayer and Trading System Design"},
                    {"id": "4.4", "title": "Iterative Development Process"},
                    {"id": "4.5", "title": "Final Artefact Implementation"},
                    {"id": "4.6", "title": "Conclusion"},
                ]},
            ],
        },
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
