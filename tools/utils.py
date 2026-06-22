import json
import os
import re
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_env():
    load_dotenv(PROJECT_ROOT / ".env")


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def ensure_directories() -> dict:
    dirs = {
        "sources": PROJECT_ROOT / "data" / "sources",
        "progress": PROJECT_ROOT / "data" / "progress",
        "notes": PROJECT_ROOT / "data" / "notes",
        "quizzes": PROJECT_ROOT / "data" / "quizzes",
        "chapters": PROJECT_ROOT / "data" / "chapters",
        "visuals": PROJECT_ROOT / "data" / "chapters" / "visuals",
        "tmp": PROJECT_ROOT / ".tmp",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return {k: str(v) for k, v in dirs.items()}


def load_json(filepath: str) -> dict | list | None:
    path = Path(filepath)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: str, data: dict | list) -> str:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return str(path)


def today_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def setup_logging(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(name)s | %(levelname)s | %(message)s"))
    logger.addHandler(console)

    log_dir = PROJECT_ROOT / ".tmp"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "tool.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(file_handler)

    return logger
