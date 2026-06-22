"""Generate weekly supervisor update email drafts from progress data."""

import argparse
import json
import os

from tools.utils import (
    PROJECT_ROOT, load_json, save_json, today_stamp, now_iso,
    load_env, ensure_directories, setup_logging,
)

log = setup_logging("generate_email")

PROGRESS_PATH = str(PROJECT_ROOT / "data" / "progress" / "progress-tracker.json")
READING_LOG_PATH = str(PROJECT_ROOT / "data" / "progress" / "reading-log.json")
TRACKER_PATH = str(PROJECT_ROOT / "data" / "sources" / "source-tracker.json")


def _get_week_stats() -> dict:
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    dates = [(week_start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    progress = load_json(PROGRESS_PATH) or {"daily_logs": {}}
    reading_log = load_json(READING_LOG_PATH) or {"readings": []}
    tracker = load_json(TRACKER_PATH) or {"sources": []}

    total_min = 0
    sources_read = 0
    tasks = []
    quiz_scores = []

    for date in dates:
        day = progress.get("daily_logs", {}).get(date)
        if day:
            total_min += day.get("total_minutes", 0)
            sources_read += day.get("sources_read", 0)
            tasks.extend(day.get("tasks_completed", []))
            for q in day.get("quiz_scores", []):
                if q["total"] > 0:
                    quiz_scores.append(q["score"] / q["total"])

    total_sources = len(tracker.get("sources", []))
    read_sources = len([s for s in tracker.get("sources", []) if s.get("status") in ("read", "cited")])

    return {
        "total_minutes": total_min,
        "total_hours": round(total_min / 60, 1),
        "sources_read_this_week": sources_read,
        "total_sources_tracked": total_sources,
        "total_sources_read": read_sources,
        "tasks": tasks,
        "quiz_avg": round(sum(quiz_scores) / len(quiz_scores) * 100) if quiz_scores else None,
        "week_start": dates[0],
    }


def generate_weekly_update(supervisor_name: str = None, student_name: str = None) -> dict:
    load_env()
    ensure_directories()

    if not supervisor_name:
        supervisor_name = os.getenv("SUPERVISOR_NAME", "Prof. [Name]")
    if not student_name:
        student_name = os.getenv("STUDENT_NAME", "[Your Name]")

    stats = _get_week_stats()

    progress_bullets = []
    if stats["sources_read_this_week"] > 0:
        progress_bullets.append(
            f"Read and extracted notes from {stats['sources_read_this_week']} peer-reviewed source(s) "
            f"({stats['total_sources_read']}/{stats['total_sources_tracked']} total sources read)."
        )

    writing_tasks = [t for t in stats["tasks"] if t.get("category") == "writing"]
    if writing_tasks:
        descs = [t["task"] for t in writing_tasks[:3]]
        progress_bullets.append("Writing progress: " + "; ".join(descs) + ".")

    if stats["total_hours"] > 0:
        progress_bullets.append(
            f"Total research time this week: {stats['total_hours']} hours across "
            f"{len([t for t in stats['tasks']])} tasks."
        )

    if stats["quiz_avg"] is not None:
        progress_bullets.append(f"Comprehension quiz average: {stats['quiz_avg']}%.")

    if not progress_bullets:
        progress_bullets.append("[Describe your progress this week]")

    subject = f"Weekly update — Week starting {stats['week_start']} — MSc research progress"

    body_lines = [
        f"Dear {supervisor_name},",
        "",
        "Brief progress:",
    ]
    for bullet in progress_bullets:
        body_lines.append(f"- {bullet}")

    body_lines.extend([
        "",
        "Planned next week:",
        "- [What you plan to read or write next week]",
        "- [Any specific focus areas]",
        "",
        "Questions / decisions needed:",
        "1. [Any questions for your supervisor]",
        "",
        "Attachments: (annotated bibliography, draft subsection — if applicable)",
        "",
        "Regards,",
        student_name,
    ])

    body = "\n".join(body_lines)

    return {
        "generated_at": now_iso(),
        "email_type": "weekly-update",
        "subject": subject,
        "body": body,
        "progress_data_used": stats,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate supervisor weekly email drafts")
    parser.add_argument("--type", default="weekly-update", choices=["weekly-update"])
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--supervisor-name", help="Supervisor name (overrides .env)")
    parser.add_argument("--student-name", help="Student name (overrides .env)")
    args = parser.parse_args()

    result = generate_weekly_update(args.supervisor_name, args.student_name)
    save_json(args.output, result)

    print(json.dumps({
        "status": "ok",
        "subject": result["subject"],
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
