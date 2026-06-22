"""Generate weekly feedback reports with pace analysis, quiz trends, and recommendations."""

import argparse
import json
from datetime import datetime, timezone, timedelta

from tools.utils import (
    PROJECT_ROOT, load_json, save_json, today_stamp, now_iso,
    ensure_directories, setup_logging,
)

log = setup_logging("generate_feedback_report")

TRACKER_PATH = str(PROJECT_ROOT / "data" / "sources" / "source-tracker.json")
PROGRESS_PATH = str(PROJECT_ROOT / "data" / "progress" / "progress-tracker.json")
READING_LOG_PATH = str(PROJECT_ROOT / "data" / "progress" / "reading-log.json")

TARGET_PAPERS_PER_WEEK = 5
TARGET_MINUTES_PER_WEEK = 420
TARGET_QUIZ_SCORE_PCT = 70


def _week_key() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.isocalendar()[1]:02d}"


def _get_week_dates() -> list[str]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=now.weekday())
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]


def _reading_pace() -> dict:
    progress = load_json(PROGRESS_PATH) or {"daily_logs": {}}
    dates = _get_week_dates()

    total_min = 0
    sources_read = 0
    active_days = 0
    pomodoros = 0

    for date in dates:
        day = progress.get("daily_logs", {}).get(date)
        if day:
            active_days += 1
            total_min += day.get("total_minutes", 0)
            sources_read += day.get("sources_read", 0)
            pomodoros += day.get("pomodoros_completed", 0)

    return {
        "papers_read": sources_read,
        "target_papers": TARGET_PAPERS_PER_WEEK,
        "on_track": sources_read >= TARGET_PAPERS_PER_WEEK,
        "total_minutes": total_min,
        "target_minutes": TARGET_MINUTES_PER_WEEK,
        "active_days": active_days,
        "pomodoros": pomodoros,
    }


def _quiz_trends() -> dict:
    progress = load_json(PROGRESS_PATH) or {"daily_logs": {}}
    dates = _get_week_dates()

    scores = []
    quiz_count = 0
    for date in dates:
        day = progress.get("daily_logs", {}).get(date)
        if day:
            for q in day.get("quiz_scores", []):
                if q.get("total", 0) > 0:
                    scores.append(q["score"] / q["total"] * 100)
                    quiz_count += 1

    avg = round(sum(scores) / len(scores), 1) if scores else 0
    return {
        "quizzes_completed": quiz_count,
        "average_score_pct": avg,
        "target_score_pct": TARGET_QUIZ_SCORE_PCT,
        "above_target": avg >= TARGET_QUIZ_SCORE_PCT,
        "scores": scores,
    }


def _coverage_analysis() -> dict:
    tracker = load_json(TRACKER_PATH) or {"sources": []}
    sources = tracker["sources"]

    chapter_total = {}
    chapter_read = {}
    for s in sources:
        for ch in s.get("chapter_relevance", []):
            chapter_total[ch] = chapter_total.get(ch, 0) + 1
            if s.get("status") in ("read", "cited"):
                chapter_read[ch] = chapter_read.get(ch, 0) + 1

    chapters = []
    for ch in sorted(set(list(chapter_total.keys()) + list(chapter_read.keys()))):
        total = chapter_total.get(ch, 0)
        read = chapter_read.get(ch, 0)
        chapters.append({
            "chapter": ch,
            "total_sources": total,
            "read_sources": read,
            "pct_read": round(read / total * 100, 1) if total > 0 else 0,
            "needs_attention": read < 3,
        })

    chapters.sort(key=lambda c: c["pct_read"])
    return {"chapters": chapters}


def _streak_history() -> dict:
    progress = load_json(PROGRESS_PATH) or {"streaks": {}, "daily_logs": {}}
    streaks = progress.get("streaks", {})
    daily_logs = progress.get("daily_logs", {})

    last_7 = _get_week_dates()
    active = [d for d in last_7 if d in daily_logs]
    missed = [d for d in last_7 if d not in daily_logs and d <= today_stamp()]

    return {
        "current_streak": streaks.get("current_streak_days", 0),
        "longest_streak": streaks.get("longest_streak_days", 0),
        "active_days_this_week": len(active),
        "missed_days_this_week": len(missed),
        "missed_dates": missed,
    }


def _recommendations(pace: dict, quizzes: dict, coverage: dict, streak: dict) -> list[str]:
    recs = []

    if not pace["on_track"]:
        deficit = pace["target_papers"] - pace["papers_read"]
        recs.append(f"You are {deficit} paper(s) behind your weekly reading target. Try to read {deficit} more papers before the weekend.")

    if pace["active_days"] < 4:
        recs.append(f"You were only active {pace['active_days']} day(s) this week. Aim for at least 5 active days to build strong habits.")

    if not quizzes["above_target"] and quizzes["quizzes_completed"] > 0:
        recs.append(f"Your quiz average ({quizzes['average_score_pct']}%) is below the {TARGET_QUIZ_SCORE_PCT}% target. Re-read papers you scored low on before moving forward.")

    if quizzes["quizzes_completed"] == 0:
        recs.append("No quizzes completed this week. Complete at least one quiz per reading session to track your comprehension.")

    weak_chapters = [c for c in coverage["chapters"] if c["needs_attention"]]
    if weak_chapters:
        labels = [c["chapter"].replace("ch2_", "").replace("ch1_", "").replace("_", " ").title() for c in weak_chapters[:3]]
        recs.append(f"These topics need more reading: {', '.join(labels)}. Prioritise sources tagged with these topics.")

    if streak["missed_days_this_week"]:
        recs.append(f"You missed {len(streak['missed_dates'])} day(s) this week. Consistency matters more than intensity — even 25 minutes counts.")

    if not recs:
        recs.append("Excellent work this week! You are on track across all metrics. Keep the momentum going.")

    return recs


def generate(output_path: str = None) -> dict:
    ensure_directories()
    week = _week_key()

    if not output_path:
        reports_dir = PROJECT_ROOT / "data" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(reports_dir / f"feedback-{week}.json")

    pace = _reading_pace()
    quizzes = _quiz_trends()
    coverage = _coverage_analysis()
    streak = _streak_history()
    recs = _recommendations(pace, quizzes, coverage, streak)

    report = {
        "week": week,
        "generated_at": now_iso(),
        "reading_pace": pace,
        "quiz_trends": quizzes,
        "coverage_analysis": coverage,
        "streak_history": streak,
        "recommendations": recs,
    }

    save_json(output_path, report)
    return {"status": "ok", "week": week, "recommendations": len(recs), "output": output_path}


def main():
    parser = argparse.ArgumentParser(description="Generate weekly feedback report")
    parser.add_argument("--output", help="Output JSON path")
    args = parser.parse_args()
    result = generate(args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
