# Weekly Review Workflow

## Objective
Weekly synthesis session — connect the week's readings, run a substantial quiz, draft a supervisor email, and update visuals.

## Schedule
Run this workflow once per week, ideally on Friday or Saturday. Allow 2–4 hours.

## Phases

### Phase 1: Review the Week (10 minutes)
```
python -m tools.track_progress --action weekly-summary
python -m tools.manage_sources --action stats
```

Present:
- Sources read this week
- Total research time
- Quiz score averages
- Current streak
- Overall source tracker stats (how many discovered vs read vs cited)

### Phase 2: Synthesis (30-60 minutes)
This is the most important phase. Guide the user to connect readings:

1. "What themes emerged across this week's readings?"
2. "Did any papers contradict each other? How?"
3. "What new questions came up that you hadn't considered before?"
4. "How has your understanding of the research area changed this week?"
5. "Can you identify any gap that multiple authors mention but none address?"

The user should write a short synthesis paragraph (200–400 words) connecting the week's readings. Save to `data/chapters/weekly-synthesis-<date>.md`.

### Phase 3: Update Chapter Outlines (15 minutes)
Based on the synthesis, update chapter outlines:
- Add new sources to relevant sections
- Refine arguments or themes
- Note any structural changes needed

### Phase 4: Weekly Test (30-45 minutes)
```
python -m tools.generate_quiz --type weekly --output .tmp/quiz-weekly-<date>.json
```

Present 10–15 questions spanning the week's readings. Include:
- Recall questions (definitions, methods)
- Comprehension questions (explain in own words)
- Comparison questions (contrast two papers)
- Application questions (how does this inform your game design?)

Log the result:
```
python -m tools.track_progress --action log-quiz --data '{"quiz_type": "weekly", "score": <score>, "total": <total>}'
```

### Phase 5: Supervisor Email (15 minutes)
```
python -m tools.generate_email --type weekly-update --output .tmp/supervisor-email-<date>.json
```

The tool generates a draft from actual progress data. The user should:
1. Review and personalise the progress bullets
2. Fill in planned activities for next week
3. Add any specific questions for the supervisor
4. Attach relevant documents (bibliography, draft section) if applicable

### Phase 6: Export New Citations (5 minutes)
```
python -m tools.export_citations --format bibtex --output .tmp/export-weekly-<date>.bib --filters '{"status": "read"}'
```

Remind the user to import the new `.bib` file into Zotero.

### Phase 7: Update Visuals (15-30 minutes, if enough sources)
If at least 10 sources have been read, generate or update:

**Thematic map** — showing literature themes and gaps:
Claude constructs the input JSON based on the user's synthesis, then runs:
```
python -m tools.generate_visuals --type thematic-map --input .tmp/thematic-map-data.json --output data/chapters/visuals/thematic-map-ch2.png
```

**Concept map** — showing relationships between key concepts:
```
python -m tools.generate_visuals --type concept-map --input .tmp/concept-map-data.json --output data/chapters/visuals/concept-map.png
```

### Phase 8: Plan Next Week (10 minutes)
- Which papers to read next week?
- Which chapter section to focus on?
- Any upcoming deadlines or supervisor meetings?
- Monthly assignment due?
