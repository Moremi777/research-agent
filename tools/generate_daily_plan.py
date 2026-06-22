"""Generate daily article suggestions and focus notes based on timeline and progress."""

import argparse
import json
import random
from datetime import datetime, timezone, timedelta

from tools.utils import (
    PROJECT_ROOT, load_json, save_json, today_stamp, now_iso,
    ensure_directories, setup_logging,
)

log = setup_logging("generate_daily_plan")

TRACKER_PATH = str(PROJECT_ROOT / "data" / "sources" / "source-tracker.json")
PROGRESS_PATH = str(PROJECT_ROOT / "data" / "progress" / "progress-tracker.json")
READING_LOG_PATH = str(PROJECT_ROOT / "data" / "progress" / "reading-log.json")

TIMELINE_PHASES = [
    {"start": "2026-06-22", "end": "2026-06-28", "focus": "Finalise research scope, start reading", "chapter": "ch1", "tags": ["indigenous_knowledge", "sustainable_agriculture"]},
    {"start": "2026-06-29", "end": "2026-07-26", "focus": "Intensive reading + annotated bibliography + Chapter 1 draft", "chapter": "ch1", "tags": ["indigenous_knowledge", "sustainable_agriculture", "modern_ag_science"]},
    {"start": "2026-07-27", "end": "2026-08-30", "focus": "Systematic literature review + Chapter 2 draft", "chapter": "ch2", "tags": ["serious_games", "multiplayer_simulations", "indigenous_knowledge"]},
    {"start": "2026-08-31", "end": "2026-09-27", "focus": "Methodology draft + DSR planning", "chapter": "ch3", "tags": ["dsr"]},
    {"start": "2026-09-28", "end": "2026-10-25", "focus": "Game design specifications + architecture", "chapter": "ch4", "tags": ["serious_games", "multiplayer_simulations"]},
    {"start": "2026-10-26", "end": "2026-11-30", "focus": "Prototype iterations + Chapter 4 documentation", "chapter": "ch4", "tags": ["multiplayer_simulations", "serious_games"]},
    {"start": "2026-12-01", "end": "2026-12-31", "focus": "Polish Chapters 1-4 + integrate feedback", "chapter": "all", "tags": []},
]


def _current_phase() -> dict:
    today = today_stamp()
    for phase in TIMELINE_PHASES:
        if phase["start"] <= today <= phase["end"]:
            return phase
    return TIMELINE_PHASES[-1]


def _get_coverage_gaps() -> list[dict]:
    tracker = load_json(TRACKER_PATH) or {"sources": []}
    sources = tracker["sources"]

    chapter_counts = {}
    for s in sources:
        if s.get("status") in ("read", "cited"):
            for ch in s.get("chapter_relevance", []):
                chapter_counts[ch] = chapter_counts.get(ch, 0) + 1

    all_chapters = [
        "ch2_indigenous_knowledge", "ch2_sustainable_agriculture", "ch2_modern_ag_science",
        "ch2_serious_games", "ch2_multiplayer_simulations", "ch1_background",
    ]

    gaps = []
    for ch in all_chapters:
        count = chapter_counts.get(ch, 0)
        if count < 5:
            gaps.append({"chapter": ch, "read_count": count, "target": 10, "priority": "high" if count < 2 else "medium"})
        elif count < 10:
            gaps.append({"chapter": ch, "read_count": count, "target": 10, "priority": "low"})
    return sorted(gaps, key=lambda g: g["read_count"])


def _suggest_articles(n: int = 5) -> list[dict]:
    tracker = load_json(TRACKER_PATH) or {"sources": []}
    sources = tracker["sources"]
    phase = _current_phase()

    unread = [s for s in sources if s.get("status") == "screened"]

    if phase["tags"]:
        tagged = [s for s in unread if set(s.get("relevance_tags", [])) & set(phase["tags"])]
    else:
        tagged = unread

    if not tagged:
        tagged = unread

    recent = [s for s in tagged if (s.get("year") or 0) >= 2020]
    if len(recent) >= n:
        pool = recent
    else:
        pool = tagged

    pool.sort(key=lambda s: s.get("citation_count", 0), reverse=True)

    top = pool[:max(n * 3, 15)]
    if len(top) > n:
        selected = random.sample(top, n)
    else:
        selected = top[:n]

    return [{
        "doi": s.get("doi", ""),
        "title": s.get("title", ""),
        "authors": [a.get("name", "") if isinstance(a, dict) else a for a in s.get("authors", [])[:3]],
        "year": s.get("year"),
        "venue": s.get("venue", ""),
        "citation_count": s.get("citation_count", 0),
        "is_open_access": s.get("is_open_access", False),
        "open_access_url": s.get("open_access_url"),
        "relevance_tags": s.get("relevance_tags", []),
        "reason": f"Relevant to current focus: {phase['focus']}",
    } for s in selected]


def _generate_focus_notes() -> list[str]:
    phase = _current_phase()
    gaps = _get_coverage_gaps()
    progress = load_json(PROGRESS_PATH) or {"daily_logs": {}, "streaks": {}}
    streaks = progress.get("streaks", {})

    notes = []
    notes.append(f"Current phase: {phase['focus']}.")

    today = today_stamp()
    start = phase["start"]
    end = phase["end"]
    total_days = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
    elapsed = (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
    if total_days > 0:
        pct = min(round(elapsed / total_days * 100), 100)
        notes.append(f"You are {pct}% through this phase ({elapsed}/{total_days} days).")

    if gaps:
        top_gap = gaps[0]
        label = top_gap["chapter"].replace("ch2_", "Ch2: ").replace("ch1_", "Ch1: ").replace("_", " ").title()
        notes.append(f"Priority gap: {label} — only {top_gap['read_count']} papers read (target: {top_gap['target']}). Focus your reading here today.")

    streak = streaks.get("current_streak_days", 0)
    if streak == 0:
        notes.append("Your streak is at 0. Read one paper and complete a quiz today to start building momentum.")
    elif streak >= 7:
        notes.append(f"Excellent! {streak}-day streak. Keep the momentum going.")
    else:
        notes.append(f"Current streak: {streak} days. Consistency builds mastery.")

    chapter_tag = phase.get("chapter", "ch1")
    if chapter_tag == "ch1":
        notes.append("Today's writing focus: work on your Chapter 1 outline or draft a subsection.")
    elif chapter_tag == "ch2":
        notes.append("Today's writing focus: synthesise your readings into thematic arguments for Chapter 2.")

    return notes


def generate(output_path: str = None) -> dict:
    ensure_directories()

    if not output_path:
        daily_dir = PROJECT_ROOT / "data" / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(daily_dir / f"plan-{today_stamp()}.json")

    suggestions = _suggest_articles(5)
    focus_notes = _generate_focus_notes()
    gaps = _get_coverage_gaps()

    plan = {
        "date": today_stamp(),
        "generated_at": now_iso(),
        "phase": _current_phase(),
        "daily_suggestions": suggestions,
        "focus_notes": focus_notes,
        "coverage_gaps": gaps,
    }

    save_json(output_path, plan)
    return {"status": "ok", "date": plan["date"], "suggestions": len(suggestions), "output": output_path}


def main():
    parser = argparse.ArgumentParser(description="Generate daily article suggestions and focus notes")
    parser.add_argument("--output", help="Output JSON path (default: data/daily/plan-<date>.json)")
    args = parser.parse_args()
    result = generate(args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
