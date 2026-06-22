# Daily Research Routine Workflow

## Objective
Structure a daily 60–120 minute research session using Pomodoro blocks (25 minutes each). Build consistency through tracking and streaks.

## Phases

### Phase 1: Start of Day Check-in (5 minutes)
Show yesterday's progress and current streak:
```
python -m tools.track_progress --action daily-summary
python -m tools.track_progress --action streak
```

Present:
- Yesterday's reading count, time spent, quiz score
- Current streak and longest streak
- Today's suggested focus based on the timeline

### Phase 2: Pomodoro 1 — Reading (25 minutes)
Follow the `reading-comprehension.md` workflow for one paper:
1. Select a screened paper from the tracker
2. Pre-reading questions
3. Guided reading
4. Note extraction

If no papers are screened, run a quick literature search first using `literature-search.md`.

### Phase 3: Pomodoro 2 — Note Extraction (25 minutes)
Continue with the same paper (if still reading) or:
- Start a second paper
- Expand notes from the first paper
- Write key quotes with page numbers for citation later

### Phase 4: Pomodoro 3 — Writing or Synthesis (25 minutes)
Choose one:
- **Writing**: Work on a chapter subsection (follow `chapter-1-drafting.md` or `chapter-2-drafting.md`)
- **Synthesis**: Connect today's reading to existing notes — how do the sources relate to each other?
- **Outlining**: Update chapter outlines in `data/chapters/`

Log the task:
```
python -m tools.track_progress --action log-task --data '{"task": "Wrote outline for Ch1 section 1.2", "category": "writing", "duration_min": 25}'
```

### Phase 5: Daily Quiz (10 minutes)
```
python -m tools.generate_quiz --type daily --output .tmp/quiz-<date>.json
```
Present questions to the user. They answer in their own words. Claude evaluates.

Log the result:
```
python -m tools.track_progress --action log-quiz --data '{"quiz_type": "daily", "score": 4, "total": 5}'
```

### Phase 6: Plan Next Day (5 minutes)
- Which paper to read tomorrow?
- Which section to work on?
- Any deadlines or supervisor meetings coming up?

Show updated daily summary:
```
python -m tools.track_progress --action daily-summary
```

## Weekly Timeline Alignment
Adjust the daily focus based on the research timeline:

| Period | Daily Focus |
|--------|-------------|
| 22 Jun – 26 Jul | Reading + annotated bibliography + Chapter 1 drafting |
| 27 Jul – 30 Aug | Systematic lit review + thematic synthesis + Chapter 2 drafting |
| 31 Aug – 27 Sep | Methodology reading + Chapter 3 drafting |
| 28 Sep – 25 Oct | Game design literature + Chapter 4 specifications |
| 26 Oct – 30 Nov | Prototype documentation + Chapter 4 iterations |
| 1 Dec – 31 Dec | Polish all chapters + integrate feedback |

## Flexibility
- Minimum viable day: 1 Pomodoro (25 min reading) + daily quiz = keeps the streak alive
- Full day: 3 Pomodoros + quiz + planning = ~100 minutes
- Extended day: add a 4th Pomodoro for extra writing or a second paper
