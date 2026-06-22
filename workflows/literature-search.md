# Literature Search Workflow

## Objective
Find peer-reviewed sources for a specific research sub-topic and add them to the source tracker with Zotero-ready exports.

## Prerequisites
- `.env` populated with at least `OPENALEX_EMAIL` (free, no key needed)
- `data/sources/source-tracker.json` initialised (created automatically on first use)

## Required Inputs
- **Topic focus**: specific research sub-topic or question to search for
- **Year range**: default 2015–2026 (extend to 1999 only when foundational/seminal works needed)
- **Chapter relevance**: which chapter section(s) these sources support

## Phases

### Phase 1: Define Search Parameters
Ask the user:
1. What specific topic or question are you searching for?
2. Any specific authors, journals, or keywords to include?
3. Which chapter section will these sources support? (e.g., `ch1_background`, `ch2_indigenous_knowledge`, `ch2_serious_games`, `ch2_ag_education`)

### Phase 2: Execute Search
Run the literature search tool:
```
python -m tools.search_literature --query "<query>" --output .tmp/search-results-<slug>.json --year-min 2015 --year-max 2026 --max-results 20
```

If results are sparse, try:
- Broader/narrower query terms
- Extended year range (`--year-min 1999`)
- Individual APIs (`--api semantic_scholar`) if one fails

### Phase 3: Screen Results
Present the top results to the user showing: title, authors, year, venue, citation count, and whether it is open access.

For each result, the user decides:
- **Yes**: relevant, import to tracker
- **Maybe**: needs more information (fetch abstract/details)
- **No**: not relevant, skip

For "maybe" papers, use WebSearch or WebFetch to find more details (full abstract, methodology, key findings).

### Phase 4: Import to Tracker
Import screened results:
```
python -m tools.manage_sources --action import-search --input .tmp/search-results-<slug>.json
```

Then update each imported source with relevance tags and chapter assignments:
```
python -m tools.manage_sources --action update --doi "<doi>" --data '{"status": "screened", "relevance_tags": ["indigenous_knowledge"], "chapter_relevance": ["ch2_indigenous_knowledge"]}'
```

### Phase 5: Export for Zotero
Export all newly screened sources as BibTeX:
```
python -m tools.export_citations --format bibtex --output .tmp/export-<date>.bib --filters '{"status": "screened"}'
```

Tell the user:
1. Open Zotero
2. File → Import → select the `.bib` file
3. Sources will appear in the library with DOIs and metadata

### Phase 6: Summary
Present to the user:
- Total papers found across APIs
- Papers imported after screening
- BibTeX file location for Zotero import
- Suggested next search queries based on gaps found

## Error Handling
- **API rate limit (429)**: Wait 60 seconds and retry, or switch to a different API
- **No results**: Try broader terms, check spelling, remove year filter temporarily
- **Missing DOIs**: Sources without DOIs are skipped during import (cannot be tracked reliably)

## Relevance Tag Convention
Use consistent tags across searches:
- `indigenous_knowledge` — IK systems, traditional farming, TEK
- `sustainable_agriculture` — sustainability, food security, climate-smart farming
- `modern_ag_science` — precision agriculture, extension services, technology in farming
- `serious_games` — game-based learning, gamification, educational games
- `multiplayer_simulations` — multiplayer mechanics, farming simulations, peer learning, collaborative play
- `dsr` — design science research methodology
- `southern_africa` — regional focus

## Chapter Relevance Labels
- `ch1_background`, `ch1_problem`
- `ch2_indigenous_knowledge`, `ch2_sustainable_agriculture`, `ch2_modern_ag_science`
- `ch2_serious_games`, `ch2_multiplayer_simulations`
- `ch2_existing_artifacts`, `ch2_framework`, `ch2_research_gap`
- `ch4_game_mechanics`, `ch4_multiplayer_trading`
