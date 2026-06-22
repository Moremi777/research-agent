# Reading Comprehension Workflow

## Objective
Guide the user through actively reading and extracting notes from a paper. The emphasis is on the user's own understanding — Claude asks questions, never summarises.

## Prerequisites
- Source must exist in `data/sources/source-tracker.json` with status `screened` or higher
- User has access to the paper (open access link, PDF, or university library)

## Phases

### Phase 1: Select Paper
Show unread papers:
```
python -m tools.manage_sources --action list --filters '{"status": "screened"}'
```
User selects one. Update status:
```
python -m tools.manage_sources --action update --doi "<doi>" --data '{"status": "reading"}'
```

### Phase 2: Pre-Reading (5 minutes)
Ask the user before they start reading:
1. "What do you already know about this topic?"
2. "Based on the title and abstract, what do you expect this paper to argue?"
3. "What specific question do you want this paper to answer for your research?"

This activates prior knowledge and sets a reading purpose.

### Phase 3: Guided Reading (20-25 minutes)
The user reads the paper section by section. For each section, ask:
- "What is the main argument or finding in this section?"
- "How does this connect to what you read in the previous section?"
- "Is there anything you found surprising or that contradicts what you expected?"

If the user asks Claude to explain a difficult concept:
- Explain clearly using analogies where helpful
- Always follow up with: "Can you explain this back to me in your own words?"
- Never just hand over a summary — the user must process the information themselves

### Phase 4: Note Extraction (10-15 minutes)
Prompt the user to write their own notes:
1. "What is the paper's research question or objective?"
2. "What methodology did they use?"
3. "What were the 3 most important findings?"
4. "What are the limitations they acknowledge?"
5. "How is this relevant to YOUR research question?"
6. "Which chapter section(s) could you cite this in?"

Save their notes to `data/notes/<doi-slug>.json`:
```json
{
  "doi": "<doi>",
  "title": "<title>",
  "date_read": "<today>",
  "research_question": "<user's summary>",
  "methodology": "<user's summary>",
  "key_findings": ["...", "...", "..."],
  "limitations": "<user's summary>",
  "relevance_to_my_research": "<user's explanation>",
  "chapter_sections": ["ch2_indigenous_knowledge"],
  "key_quotes": ["<quote with page number>"],
  "user_comprehension_score": 4
}
```

### Phase 5: Comprehension Check
Generate a quick quiz on the paper just read:
```
python -m tools.generate_quiz --type daily --output .tmp/quiz-<date>.json
```
Present 3-5 questions. The user answers in their own words. Claude evaluates whether the answer demonstrates understanding (not just keyword matching).

### Phase 6: Log Progress
```
python -m tools.track_progress --action log-reading --doi "<doi>" --data '{"duration_min": 25, "comprehension_self_score": 4, "notes_taken": true}'
```

Update source status:
```
python -m tools.manage_sources --action update --doi "<doi>" --data '{"status": "read", "read_date": "<today>", "reading_notes_path": "data/notes/<doi-slug>.json"}'
```

## Critical Rule: No Ghostwriting
Claude's role in this workflow is to **ask questions**, not to **provide answers**. The user must:
- Read the paper themselves
- Write notes in their own words
- Formulate their own understanding
- Answer quiz questions without Claude's help

Claude may:
- Explain concepts the user asks about
- Correct factual misunderstandings
- Suggest connections the user might have missed
- Point out which chapter section(s) a finding supports
