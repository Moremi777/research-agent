# Chapter 1 Drafting Workflow — Introduction

## Objective
Guide the user through writing Chapter 1 (Introduction) subsection by subsection. Claude prompts, questions, and checks — the user writes every sentence.

## Prerequisites
- At least 5–10 sources read and in the tracker with status `read` or `cited`
- Notes extracted for key background sources
- User has a clear research question in mind

## Chapter 1 Structure

### Section 1.1 — Introduction
**Purpose**: Set the scene in 1–2 paragraphs. What is the broad topic? Why does it matter?
**Prompts for the user**:
- "Start with the global challenge — why is indigenous farming knowledge important and what threatens it?"
- "In the second paragraph, introduce the idea that serious games could help. What makes games suitable for this?"
**Citation guidance**: Every factual claim needs an IEEE citation `[number]`. Aim for 3–5 citations in this section.

### Section 1.2 — Background and Context
**Purpose**: Provide detailed context on indigenous farming knowledge in Southern Africa, agricultural education gaps, and the role of technology.
**Prompts**:
- "What is indigenous farming knowledge? Give a definition from the literature."
- "What is the current state of agricultural education in Southern Africa?"
- "How have digital tools or games been used in education in this region?"
**Citation guidance**: This is context-heavy — aim for 8–12 citations.

### Section 1.3 — Problem Statement
**Purpose**: Clearly articulate the problem this research addresses.
**Prompts**:
- "What specific problem exists? (Indigenous knowledge being lost, not integrated with modern science, not accessible through current education)"
- "Why haven't existing solutions solved this problem?"
- "Write this as 2–3 focused paragraphs."
**Citation guidance**: 3–5 citations supporting the problem's existence.

### Section 1.4 — Research Question
**Purpose**: State the main research question and any sub-questions.
**Prompts**:
- "What is the single overarching question your research answers?"
- "What sub-questions break this down? (e.g., How can IK be represented in a game? What design principles apply?)"
**Format**: The main RQ should be clearly stated, followed by numbered sub-questions.

### Section 1.5 — Research Aim and Objectives
**Purpose**: State the aim (what you want to achieve) and 3–5 measurable objectives.
**Prompts**:
- "The aim should directly respond to the research question."
- "Each objective should be specific and measurable — use verbs like: investigate, design, develop, evaluate."
- "Objectives should map to chapters (Obj 1 → Ch2, Obj 2 → Ch3, etc.)"

### Section 1.6 — Purpose and Value of the Research
**Purpose**: Explain academic and practical contributions.
**Prompts**:
- "What does this research contribute to knowledge? (DSR design principles, framework for IK-game integration)"
- "What practical value does the artefact have? (Tool for farmers, educators, extension workers)"

### Section 1.7 — Scope and Limitations
**Purpose**: Define boundaries and acknowledge constraints.
**Prompts**:
- "What is included? (Southern African IK, specific farming activities, specific game features)"
- "What is excluded? (Other regions, commercial deployment, long-term impact studies)"
- "What are known limitations? (Sample size, time constraints, technology access)"

### Section 1.8 — Structure of the Research
**Purpose**: Brief overview of each chapter.
**Format**: One paragraph per chapter describing its purpose and content.

### Section 1.9 — Conclusion
**Purpose**: Summarise the chapter in 1–2 paragraphs and transition to Chapter 2.

## Quality Check
After completing a draft, run:
```
python -m tools.check_writing --input data/chapters/ch1-draft.md --output .tmp/writing-check-ch1.json
```

Review the output for:
- Americanisms (must use British English)
- Uncited claims (every assertion needs `[number]`)
- Word count (Chapter 1 typically 3,000–5,000 words)

## Export Citations
```
python -m tools.export_citations --format bibtex --output .tmp/ch1-references.bib --filters '{"status": "cited"}'
```

## Critical Rule
Claude does NOT write prose for the user. Claude:
- Asks guiding questions
- Suggests paragraph structure
- Checks whether claims are cited
- Corrects spelling and grammar when asked
- Explains what each section should achieve

The user writes every word themselves.
