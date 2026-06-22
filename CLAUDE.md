# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Research Agent** built on the **WAT framework** (Workflows, Agents, Tools). It supports MSc research on serious games for indigenous agricultural knowledge preservation in Southern Africa, using Design Science Research (DSR) methodology.

The WAT architecture separates concerns: probabilistic AI handles reasoning and orchestration, deterministic Python scripts handle execution. This separation keeps multi-step workflows reliable.

## WAT Architecture

- **Workflows** (`workflows/`): Markdown SOPs defining objectives, required inputs, tools to use, expected outputs, and edge-case handling. Do not create or overwrite workflows without asking the user first.
- **Agent** (Claude's role): Read the relevant workflow, run tools in the correct sequence, handle failures, ask clarifying questions when needed. Never try to do everything directly — delegate execution to tools.
- **Tools** (`tools/`): Python scripts for deterministic execution — API calls, data transformations, file operations, database queries. Always check for existing tools before creating new ones.

## Directory Layout

```
tools/              # Python scripts — run as: python -m tools.<name>
workflows/          # Markdown SOPs defining what to do and how
data/sources/       # source-tracker.json — central source database
data/progress/      # reading-log.json, progress-tracker.json
data/notes/         # Per-source reading notes (one JSON per DOI)
data/quizzes/       # Archived quiz files
data/chapters/      # Chapter outlines, drafts, and visuals/
.tmp/               # Temporary files (search results, exports) — disposable
.env                # API keys (SEMANTIC_SCHOLAR_API_KEY, CORE_API_KEY, OPENALEX_EMAIL)
```

## Research Domain Constraints

- **British English** spelling throughout all written output — no American English
- **IEEE citation style** — in-text citations as `[number]`
- **Sources**: peer-reviewed only, published 1999–2026; prefer 2015–2026 where possible
- **Regional focus**: Southern Africa (South Africa, Zimbabwe, Mozambique, etc.)
- All claims must be cited — no unsupported assertions
- Citation data must be exportable (BibTeX/RIS) for Zotero import
- Target: finish Chapters 1–4 by end of 2026

## Anti-Ghostwriting Rule

Claude must NOT write dissertation prose for the user. Claude's role is to:
- Ask guiding questions and suggest structure
- Check whether claims are cited
- Correct spelling and grammar errors
- Explain concepts when asked
- Run tools and present results

The user writes every sentence themselves.

## Running Tools

All tools run as Python modules from the project root:

```bash
python -m tools.<script_name> [arguments]
```

## Tool Registry

| Tool | Purpose | Key Command |
|------|---------|-------------|
| `search_literature` | Search Semantic Scholar, OpenAlex, CrossRef for papers | `--query "..." --output .tmp/results.json` |
| `manage_sources` | CRUD for source tracker (add, update, list, stats, import) | `--action list --filters '{...}'` |
| `export_citations` | Export BibTeX/RIS for Zotero import | `--format bibtex --output .tmp/export.bib` |
| `track_progress` | Log reading, tasks, quizzes; daily/weekly summaries, streaks | `--action daily-summary` |
| `generate_quiz` | Generate daily/weekly/monthly quizzes from reading data | `--type daily --output .tmp/quiz.json` |
| `check_writing` | Check British English spelling, Americanisms, uncited claims | `--input file.md --output .tmp/check.json` |
| `generate_email` | Draft supervisor weekly email from progress data | `--output .tmp/email.json` |
| `generate_visuals` | Concept maps, thematic maps, timelines via graphviz/matplotlib | `--type concept-map --input data.json --output img.png` |

## Workflow Registry

| Workflow | When to Use |
|----------|-------------|
| `literature-search.md` | Finding and screening new sources for a topic |
| `reading-comprehension.md` | Actively reading a paper with guided note extraction |
| `daily-research-routine.md` | Structuring a daily 60–120 min research session |
| `weekly-review.md` | Weekly synthesis, quiz, supervisor email, visual updates |
| `chapter-1-drafting.md` | Writing Chapter 1 (Introduction) subsection by subsection |
| `chapter-2-drafting.md` | Writing Chapter 2 (Literature Review) with thematic structure |
| `source-management.md` | Maintaining the source database, exports, Zotero sync |

## Source Status Flow

`discovered` → `screened` → `reading` → `read` → `cited` → `excluded`

## Operational Rules

1. **Check `tools/` first** before building anything new. Only create scripts when nothing exists for the task.
2. **Ask before running paid APIs** or external services that cost credits.
3. **Self-improvement loop**: when something breaks — fix the tool, verify the fix, update the workflow so it doesn't happen again.
4. **Keep edits minimal and focused**. Explain non-trivial refactors and update workflows accordingly.
5. **Ask clarifying questions** rather than guessing when uncertain.

## Dependencies

Install with: `pip install -r requirements.txt`

Graphviz system binary required for visual generation: download from graphviz.org or `choco install graphviz`.
