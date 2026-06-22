# Source Management Workflow

## Objective
Maintain the source database — view stats, export citations, update metadata, tag sources, and keep the tracker clean.

## When to Use
- After importing new search results
- Before exporting citations for Zotero
- When preparing a chapter draft and need to check source coverage
- During weekly review to assess progress

## Phases

### Phase 1: View Current Stats
```
python -m tools.manage_sources --action stats
```

Review:
- Total sources by status (discovered → screened → reading → read → cited → excluded)
- Distribution by year
- Coverage by chapter section
- Reading progress percentage

### Phase 2: Tag and Categorise Sources
For untagged sources, update relevance tags and chapter assignments:
```
python -m tools.manage_sources --action update --doi "<doi>" --data '{"relevance_tags": ["indigenous_knowledge", "southern_africa"], "chapter_relevance": ["ch2_indigenous_knowledge"]}'
```

Use consistent tags from `workflows/literature-search.md`.

### Phase 3: Export Citations
Export by format:
```
python -m tools.export_citations --format bibtex --output .tmp/export-<date>.bib
python -m tools.export_citations --format ris --output .tmp/export-<date>.ris
```

Export filtered sets:
```
python -m tools.export_citations --format bibtex --output .tmp/ch1-refs.bib --filters '{"chapter_relevance": ["ch1_background", "ch1_problem"]}'
python -m tools.export_citations --format bibtex --output .tmp/ch2-refs.bib --filters '{"chapter_relevance": ["ch2_indigenous_knowledge", "ch2_serious_games", "ch2_ag_education"]}'
```

### Phase 4: Identify Coverage Gaps
Check which chapter sections have fewer than 5 sources:
```
python -m tools.manage_sources --action stats
```

If a section has low coverage, run a targeted literature search using `workflows/literature-search.md`.

### Phase 5: Update Source Metadata
For sources with incomplete metadata (missing volume, issue, pages):
- Use CrossRef API via `search_literature.py --api crossref --query "<exact title>"` to find complete metadata
- Update the source: `python -m tools.manage_sources --action update --doi "<doi>" --data '{"volume": "12", "issue": "3", "pages": "45-60"}'`

### Phase 6: Mark Sources as Cited
When a source is used in a chapter draft, update its status:
```
python -m tools.manage_sources --action update --doi "<doi>" --data '{"status": "cited"}'
```

## Zotero Import Reminder
After any export:
1. Open Zotero
2. File → Import → select the `.bib` or `.ris` file
3. Check that metadata imported correctly (title, authors, year, DOI)
4. Use Zotero's browser connector to attach PDFs where available
5. Add to the `MSc_SeriousGame_2026` collection
