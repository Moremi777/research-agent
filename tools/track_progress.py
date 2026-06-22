"""Track daily/weekly progress, reading sessions, quiz scores, and streaks."""

import argparse
import json
from datetime import datetime, timezone, timedelta

from tools.utils import (
    PROJECT_ROOT, load_json, save_json, today_stamp, now_iso,
    ensure_directories, setup_logging,
)

log = setup_logging("track_progress")

READING_LOG_PATH = str(PROJECT_ROOT / "data" / "progress" / "reading-log.json")
PROGRESS_PATH = str(PROJECT_ROOT / "data" / "progress" / "progress-tracker.json")


def _load_reading_log() -> dict:
    data = load_json(READING_LOG_PATH)
    if data is None:
        data = {"version": 1, "readings": []}
    return data


def _load_progress() -> dict:
    data = load_json(PROGRESS_PATH)
    if data is None:
        data = {
            "version": 1,
            "daily_logs": {},
            "weekly_summaries": {},
            "streaks": {
                "current_streak_days": 0,
                "longest_streak_days": 0,
                "last_active_date": None,
            },
        }
    return data


def _get_today_log(progress: dict) -> dict:
    today = today_stamp()
    if today not in progress["daily_logs"]:
        progress["daily_logs"][today] = {
            "tasks_completed": [],
            "total_minutes": 0,
            "sources_read": 0,
            "quiz_scores": [],
            "pomodoros_completed": 0,
        }
    return progress["daily_logs"][today]


def _update_streak(progress: dict):
    today = today_stamp()
    streaks = progress["streaks"]
    last = streaks.get("last_active_date")

    if last == today:
        return

    if last:
        last_date = datetime.strptime(last, "%Y-%m-%d").date()
        today_date = datetime.strptime(today, "%Y-%m-%d").date()
        diff = (today_date - last_date).days

        if diff == 1:
            streaks["current_streak_days"] += 1
        elif diff > 1:
            streaks["current_streak_days"] = 1
    else:
        streaks["current_streak_days"] = 1

    if streaks["current_streak_days"] > streaks["longest_streak_days"]:
        streaks["longest_streak_days"] = streaks["current_streak_days"]

    streaks["last_active_date"] = today


def _current_week_key() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.isocalendar()[1]:02d}"


def log_reading(doi: str, data: dict) -> dict:
    ensure_directories()
    reading_log = _load_reading_log()
    progress = _load_progress()

    entry = {
        "doi": doi,
        "date": today_stamp(),
        "duration_min": data.get("duration_min", 25),
        "comprehension_self_score": data.get("comprehension_self_score"),
        "notes_taken": data.get("notes_taken", False),
        "key_takeaways": data.get("key_takeaways", []),
    }
    reading_log["readings"].append(entry)
    save_json(READING_LOG_PATH, reading_log)

    today_log = _get_today_log(progress)
    today_log["sources_read"] += 1
    today_log["total_minutes"] += entry["duration_min"]
    today_log["pomodoros_completed"] += 1
    _update_streak(progress)
    save_json(PROGRESS_PATH, progress)

    return {"status": "ok", "action": "log-reading", "doi": doi, "date": entry["date"]}


def log_task(data: dict) -> dict:
    ensure_directories()
    progress = _load_progress()
    today_log = _get_today_log(progress)

    task = {
        "task": data.get("task", ""),
        "category": data.get("category", "general"),
        "duration_min": data.get("duration_min", 25),
    }
    today_log["tasks_completed"].append(task)
    today_log["total_minutes"] += task["duration_min"]
    today_log["pomodoros_completed"] += 1
    _update_streak(progress)
    save_json(PROGRESS_PATH, progress)

    return {"status": "ok", "action": "log-task", "task": task["task"]}


def log_quiz(data: dict) -> dict:
    ensure_directories()
    progress = _load_progress()
    today_log = _get_today_log(progress)

    quiz = {
        "quiz_type": data.get("quiz_type", "daily"),
        "score": data.get("score", 0),
        "total": data.get("total", 5),
        "quiz_path": data.get("quiz_path"),
    }
    today_log["quiz_scores"].append(quiz)
    _update_streak(progress)
    save_json(PROGRESS_PATH, progress)

    pct = round(quiz["score"] / quiz["total"] * 100) if quiz["total"] > 0 else 0
    return {"status": "ok", "action": "log-quiz", "score": f"{quiz['score']}/{quiz['total']} ({pct}%)"}


def daily_summary() -> dict:
    progress = _load_progress()
    today = today_stamp()
    today_log = progress["daily_logs"].get(today)

    if not today_log:
        return {
            "status": "ok",
            "date": today,
            "message": "No activity logged today yet.",
            "streak": progress["streaks"],
        }

    quiz_avg = 0
    if today_log["quiz_scores"]:
        scores = [q["score"] / q["total"] for q in today_log["quiz_scores"] if q["total"] > 0]
        quiz_avg = round(sum(scores) / len(scores) * 100) if scores else 0

    return {
        "status": "ok",
        "date": today,
        "total_minutes": today_log["total_minutes"],
        "pomodoros_completed": today_log["pomodoros_completed"],
        "sources_read": today_log["sources_read"],
        "tasks_completed": len(today_log["tasks_completed"]),
        "task_details": today_log["tasks_completed"],
        "quiz_avg_pct": quiz_avg,
        "streak": progress["streaks"],
    }


def weekly_summary() -> dict:
    progress = _load_progress()
    week_key = _current_week_key()

    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    dates_this_week = [(week_start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    total_min = 0
    total_sources = 0
    total_tasks = 0
    quiz_scores = []
    active_days = 0

    for date in dates_this_week:
        day_log = progress["daily_logs"].get(date)
        if day_log:
            active_days += 1
            total_min += day_log.get("total_minutes", 0)
            total_sources += day_log.get("sources_read", 0)
            total_tasks += len(day_log.get("tasks_completed", []))
            for q in day_log.get("quiz_scores", []):
                if q["total"] > 0:
                    quiz_scores.append(q["score"] / q["total"])

    quiz_avg = round(sum(quiz_scores) / len(quiz_scores) * 100) if quiz_scores else 0

    return {
        "status": "ok",
        "week": week_key,
        "active_days": active_days,
        "total_minutes": total_min,
        "total_hours": round(total_min / 60, 1),
        "sources_read": total_sources,
        "tasks_completed": total_tasks,
        "quiz_avg_pct": quiz_avg,
        "streak": progress["streaks"],
    }


def streak() -> dict:
    progress = _load_progress()
    return {"status": "ok", "streaks": progress["streaks"]}


def main():
    parser = argparse.ArgumentParser(description="Track research progress and reading sessions")
    parser.add_argument("--action", required=True,
                        choices=["log-reading", "log-task", "log-quiz", "daily-summary", "weekly-summary", "streak"])
    parser.add_argument("--doi", help="DOI of the source (for log-reading)")
    parser.add_argument("--data", help="JSON string with log data")
    args = parser.parse_args()

    if args.action == "log-reading":
        if not args.doi:
            parser.error("--doi required for log-reading")
        data = json.loads(args.data) if args.data else {}
        result = log_reading(args.doi, data)
    elif args.action == "log-task":
        data = json.loads(args.data) if args.data else {}
        result = log_task(data)
    elif args.action == "log-quiz":
        data = json.loads(args.data) if args.data else {}
        result = log_quiz(data)
    elif args.action == "daily-summary":
        result = daily_summary()
    elif args.action == "weekly-summary":
        result = weekly_summary()
    elif args.action == "streak":
        result = streak()
    else:
        result = {"status": "error", "message": f"Unknown action: {args.action}"}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
