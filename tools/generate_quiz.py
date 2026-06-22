"""Generate comprehension quizzes from reading notes and source data."""

import argparse
import json
import random

from tools.utils import (
    PROJECT_ROOT, load_json, save_json, today_stamp, now_iso,
    ensure_directories, setup_logging,
)

log = setup_logging("generate_quiz")

TRACKER_PATH = str(PROJECT_ROOT / "data" / "sources" / "source-tracker.json")
NOTES_DIR = PROJECT_ROOT / "data" / "notes"
READING_LOG_PATH = str(PROJECT_ROOT / "data" / "progress" / "reading-log.json")


def _get_recent_sources(days: int = 1) -> list[dict]:
    """Get sources read in the last N days."""
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    reading_log = load_json(READING_LOG_PATH)
    if not reading_log:
        return []

    recent_dois = set()
    for entry in reading_log.get("readings", []):
        if entry.get("date", "") >= cutoff:
            recent_dois.add(entry["doi"])

    if not recent_dois:
        return []

    tracker = load_json(TRACKER_PATH)
    if not tracker:
        return []

    return [s for s in tracker.get("sources", []) if s.get("doi") in recent_dois]


def _get_all_read_sources() -> list[dict]:
    """Get all sources with status 'read' or 'cited'."""
    tracker = load_json(TRACKER_PATH)
    if not tracker:
        return []
    return [s for s in tracker.get("sources", []) if s.get("status") in ("read", "cited")]


def _load_notes_for_source(doi: str) -> dict | None:
    from tools.utils import slugify
    slug = slugify(doi)
    path = NOTES_DIR / f"{slug}.json"
    return load_json(str(path))


def _build_recall_question(source: dict, notes: dict | None) -> dict:
    title = source.get("title", "this paper")
    authors = source.get("authors", [])
    author_name = authors[0]["name"] if authors else "the authors"

    templates = [
        f"What research methodology did {author_name} use in \"{title}\"?",
        f"What were the key findings of \"{title}\" by {author_name}?",
        f"What problem does \"{title}\" aim to address?",
        f"What is the main contribution of \"{title}\"?",
        f"What theoretical framework does \"{title}\" use?",
    ]

    return {
        "type": "recall",
        "question": random.choice(templates),
        "source_doi": source.get("doi", ""),
        "source_title": title,
        "difficulty": "medium",
    }


def _build_comprehension_question(source: dict, notes: dict | None) -> dict:
    title = source.get("title", "this paper")

    templates = [
        f"In your own words, explain the main argument of \"{title}\".",
        f"How does \"{title}\" relate to your research on serious games for indigenous farming knowledge?",
        f"What are the limitations of the approach described in \"{title}\"?",
        f"Explain how the findings of \"{title}\" could inform the design of your serious game.",
        f"What gaps or unanswered questions does \"{title}\" leave?",
    ]

    return {
        "type": "comprehension",
        "question": random.choice(templates),
        "source_doi": source.get("doi", ""),
        "source_title": title,
        "difficulty": "hard",
    }


def _build_critical_analysis_question(source: dict) -> dict:
    title = source.get("title", "this paper")
    authors = source.get("authors", [])
    author_name = authors[0]["name"] if authors else "the authors"

    templates = [
        f"What are the methodological strengths and weaknesses of \"{title}\"? How could the study be improved?",
        f"Critically evaluate the evidence presented in \"{title}\". Is the authors' conclusion fully supported by their data?",
        f"How does \"{title}\" position itself within the broader debate on indigenous knowledge vs modern science? Do you agree with the authors' stance?",
        f"If you were reviewing \"{title}\" for a journal, what would you highlight as its main contribution and its main limitation?",
        f"Compare the theoretical framework used in \"{title}\" with an alternative framework. Which would be more appropriate and why?",
        f"What assumptions does \"{title}\" make about its target audience or context? Are these assumptions valid for Southern Africa?",
    ]

    return {
        "type": "critical_analysis",
        "question": random.choice(templates),
        "source_doi": source.get("doi", ""),
        "source_title": title,
        "difficulty": "hard",
        "scoring_rubric": {
            "0": "No answer or irrelevant",
            "1": "Superficial response without specific references to the paper",
            "2": "Identifies one strength or weakness but lacks depth",
            "3": "Identifies multiple points with some supporting evidence",
            "4": "Well-structured analysis with specific references to the paper's content",
            "5": "Excellent critical analysis demonstrating deep understanding and original thinking",
        },
    }


def _build_application_question(source: dict) -> dict:
    title = source.get("title", "this paper")

    templates = [
        f"How would you apply the concepts from \"{title}\" to your game's crop management system?",
        f"If you were to cite \"{title}\" in Chapter 2, which section would it fit best and why?",
        f"How does \"{title}\" support or challenge your problem statement?",
        f"What design decision in your serious game could be justified using findings from \"{title}\"?",
        f"How could the findings of \"{title}\" influence the multiplayer or trading mechanics in your game?",
        f"Write a paragraph that synthesises the findings of \"{title}\" with two other papers you have read. Use IEEE citation style.",
    ]

    return {
        "type": "application",
        "question": random.choice(templates),
        "source_doi": source.get("doi", ""),
        "source_title": title,
        "difficulty": "hard",
    }


def _build_comparison_question(source_a: dict, source_b: dict) -> dict:
    title_a = source_a.get("title", "the first paper")
    title_b = source_b.get("title", "the second paper")

    templates = [
        f"Compare the approaches used in \"{title_a}\" and \"{title_b}\". Where do they agree or disagree?",
        f"How do \"{title_a}\" and \"{title_b}\" each contribute to understanding indigenous farming knowledge?",
        f"Which of these two papers — \"{title_a}\" or \"{title_b}\" — is more relevant to your research, and why?",
    ]

    return {
        "type": "comparison",
        "question": random.choice(templates),
        "source_doi_a": source_a.get("doi", ""),
        "source_doi_b": source_b.get("doi", ""),
        "source_title_a": title_a,
        "source_title_b": title_b,
        "difficulty": "hard",
    }


def generate_daily(num_questions: int = 12) -> dict:
    sources = _get_recent_sources(days=1)
    if not sources:
        sources = _get_all_read_sources()
    if not sources:
        return {
            "quiz_type": "daily",
            "generated_at": now_iso(),
            "message": "No sources have been read yet. Read some papers first.",
            "questions": [],
            "must_redo": False,
        }

    questions = []
    q_id = 1
    builders = [
        _build_recall_question,
        _build_comprehension_question,
    ]

    for source in sources[:4]:
        notes = _load_notes_for_source(source.get("doi", ""))
        for builder in builders:
            if len(questions) < num_questions:
                q = builder(source, notes) if builder in [_build_recall_question, _build_comprehension_question] else builder(source)
                q["id"] = q_id
                q.setdefault("scoring_rubric", {
                    "0": "No answer", "1": "Minimal effort", "2": "Basic understanding",
                    "3": "Good understanding", "4": "Strong understanding with evidence", "5": "Excellent, demonstrates mastery",
                })
                questions.append(q)
                q_id += 1

    while len(questions) < num_questions and sources:
        source = random.choice(sources)
        builder = random.choice([_build_application_question, _build_critical_analysis_question])
        q = builder(source)
        q["id"] = q_id
        q.setdefault("scoring_rubric", {
            "0": "No answer", "1": "Minimal effort", "2": "Basic understanding",
            "3": "Good understanding", "4": "Strong understanding with evidence", "5": "Excellent, demonstrates mastery",
        })
        questions.append(q)
        q_id += 1

    if len(sources) >= 2:
        pair = random.sample(sources, 2)
        q = _build_comparison_question(pair[0], pair[1])
        q["id"] = q_id
        q.setdefault("scoring_rubric", {
            "0": "No answer", "1": "Minimal effort", "2": "Basic understanding",
            "3": "Good understanding", "4": "Strong understanding with evidence", "5": "Excellent, demonstrates mastery",
        })
        questions.append(q)

    return {
        "quiz_type": "daily",
        "generated_at": now_iso(),
        "based_on_sources": list(set(s.get("doi", "") for s in sources)),
        "must_redo": False,
        "questions": questions[:num_questions],
        "writing_prompt": None,
    }


def generate_weekly() -> dict:
    sources = _get_recent_sources(days=7)
    if not sources:
        sources = _get_all_read_sources()
    if not sources:
        return {
            "quiz_type": "weekly",
            "generated_at": now_iso(),
            "message": "No sources have been read this week.",
            "questions": [],
        }

    questions = []
    q_id = 1

    for source in sources:
        notes = _load_notes_for_source(source.get("doi", ""))
        q = _build_recall_question(source, notes)
        q["id"] = q_id
        questions.append(q)
        q_id += 1

        q = _build_comprehension_question(source, notes)
        q["id"] = q_id
        questions.append(q)
        q_id += 1

    if len(sources) >= 2:
        pairs = [(sources[i], sources[i + 1]) for i in range(0, len(sources) - 1, 2)]
        for a, b in pairs[:3]:
            q = _build_comparison_question(a, b)
            q["id"] = q_id
            questions.append(q)
            q_id += 1

    for source in random.sample(sources, min(3, len(sources))):
        q = _build_application_question(source)
        q["id"] = q_id
        questions.append(q)
        q_id += 1

    random.shuffle(questions)
    for i, q in enumerate(questions, 1):
        q["id"] = i

    return {
        "quiz_type": "weekly",
        "generated_at": now_iso(),
        "based_on_sources": list(set(s.get("doi", "") for s in sources)),
        "questions": questions[:15],
        "writing_prompt": None,
    }


def generate_monthly() -> dict:
    sources = _get_all_read_sources()

    prompts = [
        "Write a 500–1000 word subsection synthesising what the literature says about indigenous farming knowledge systems in Southern Africa. Use IEEE citation style and cite at least 5 sources.",
        "Write a 500–1000 word subsection reviewing how serious games have been used in agricultural education. Identify common design patterns and gaps. Use IEEE citation style.",
        "Write a 500–1000 word critical comparison of at least 3 existing serious games or digital tools for agricultural education. Identify their limitations and what your proposed game could do differently.",
    ]

    return {
        "quiz_type": "monthly",
        "generated_at": now_iso(),
        "based_on_sources": [s.get("doi", "") for s in sources],
        "questions": [],
        "writing_prompt": random.choice(prompts),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate comprehension quizzes from reading data")
    parser.add_argument("--type", required=True, choices=["daily", "weekly", "monthly"],
                        help="Quiz type: daily (5 Qs), weekly (10-15 Qs), monthly (writing assignment)")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    ensure_directories()

    if args.type == "daily":
        result = generate_daily()
    elif args.type == "weekly":
        result = generate_weekly()
    else:
        result = generate_monthly()

    save_json(args.output, result)

    from pathlib import Path
    quiz_archive = PROJECT_ROOT / "data" / "quizzes" / Path(args.output).name
    save_json(str(quiz_archive), result)

    summary = {
        "status": "ok",
        "quiz_type": args.type,
        "questions_count": len(result.get("questions", [])),
        "has_writing_prompt": result.get("writing_prompt") is not None,
        "output": args.output,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
