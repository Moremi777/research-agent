"""Search free academic APIs for peer-reviewed papers."""

import argparse
import json
import re
import sys
import time

import requests

from tools.utils import load_env, slugify, save_json, now_iso, setup_logging

log = setup_logging("search_literature")

SEMANTIC_SCHOLAR_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
OPENALEX_WORKS = "https://api.openalex.org/works"
CROSSREF_WORKS = "https://api.crossref.org/works"

PEER_REVIEWED_TYPES = {"JournalArticle", "Journal", "Conference", "journal-article", "proceedings-article", "book-chapter"}


def _headers_semantic_scholar() -> dict:
    import os
    key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if key:
        return {"x-api-key": key}
    return {}


def _search_semantic_scholar(query: str, year_min: int, year_max: int, max_results: int) -> list[dict]:
    params = {
        "query": query,
        "year": f"{year_min}-{year_max}",
        "limit": min(max_results, 100),
        "fields": "title,authors,year,doi,url,abstract,venue,citationCount,isOpenAccess,openAccessPdf,publicationTypes",
    }
    try:
        resp = requests.get(SEMANTIC_SCHOLAR_SEARCH, params=params, headers=_headers_semantic_scholar(), timeout=30)
        if resp.status_code == 429:
            log.warning("Semantic Scholar rate limited, skipping")
            return []
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log.error("Semantic Scholar error: %s", e)
        return []

    results = []
    for paper in data.get("data", []):
        pub_types = set(paper.get("publicationTypes") or [])
        if pub_types and not pub_types & PEER_REVIEWED_TYPES:
            continue

        authors = []
        for a in paper.get("authors") or []:
            name = a.get("name", "")
            if name:
                authors.append({"name": name, "affiliation": None})

        oa_url = None
        oa_pdf = paper.get("openAccessPdf")
        if oa_pdf and isinstance(oa_pdf, dict):
            oa_url = oa_pdf.get("url")

        results.append({
            "source_api": "semantic_scholar",
            "title": paper.get("title", ""),
            "authors": authors,
            "year": paper.get("year"),
            "doi": paper.get("doi") if paper.get("doi") else paper.get("externalIds", {}).get("DOI"),
            "url": paper.get("url", ""),
            "abstract": paper.get("abstract", ""),
            "venue": paper.get("venue", ""),
            "citation_count": paper.get("citationCount", 0),
            "is_open_access": paper.get("isOpenAccess", False),
            "open_access_url": oa_url,
            "paper_id": paper.get("paperId", ""),
            "type": list(pub_types)[0] if pub_types else "unknown",
        })
    return results


def _search_openalex(query: str, year_min: int, year_max: int, max_results: int) -> list[dict]:
    import os
    email = os.getenv("OPENALEX_EMAIL", "").strip()
    params = {
        "search": query,
        "filter": f"from_publication_date:{year_min}-01-01,to_publication_date:{year_max}-12-31,type:article|book-chapter",
        "per_page": min(max_results, 50),
        "sort": "relevance_score:desc",
    }
    if email:
        params["mailto"] = email

    try:
        resp = requests.get(OPENALEX_WORKS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log.error("OpenAlex error: %s", e)
        return []

    results = []
    for work in data.get("results", []):
        authors = []
        for authorship in work.get("authorships", []):
            name = authorship.get("author", {}).get("display_name", "")
            inst = ""
            insts = authorship.get("institutions", [])
            if insts:
                inst = insts[0].get("display_name", "")
            if name:
                authors.append({"name": name, "affiliation": inst or None})

        doi_raw = work.get("doi", "")
        doi = doi_raw.replace("https://doi.org/", "") if doi_raw else None

        oa = work.get("open_access", {})

        results.append({
            "source_api": "openalex",
            "title": work.get("display_name", ""),
            "authors": authors,
            "year": work.get("publication_year"),
            "doi": doi,
            "url": work.get("doi", "") or work.get("id", ""),
            "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
            "venue": ((work.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
            "citation_count": work.get("cited_by_count", 0),
            "is_open_access": oa.get("is_oa", False),
            "open_access_url": oa.get("oa_url"),
            "paper_id": work.get("id", ""),
            "type": work.get("type", "unknown"),
        })
    return results


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions)


def _search_crossref(query: str, year_min: int, year_max: int, max_results: int) -> list[dict]:
    params = {
        "query": query,
        "filter": f"from-pub-date:{year_min},until-pub-date:{year_max},type:journal-article",
        "rows": min(max_results, 50),
        "sort": "relevance",
    }
    headers = {"User-Agent": "ResearchAgent/1.0 (mailto:research@example.com)"}

    try:
        resp = requests.get(CROSSREF_WORKS, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log.error("CrossRef error: %s", e)
        return []

    results = []
    for item in data.get("message", {}).get("items", []):
        authors = []
        for a in item.get("author", []):
            given = a.get("given", "")
            family = a.get("family", "")
            name = f"{given} {family}".strip()
            affil = ""
            if a.get("affiliation"):
                affil = a["affiliation"][0].get("name", "")
            if name:
                authors.append({"name": name, "affiliation": affil or None})

        title_list = item.get("title", [])
        title = title_list[0] if title_list else ""

        container = item.get("container-title", [])
        venue = container[0] if container else ""

        year = None
        date_parts = item.get("published", {}).get("date-parts", [[]])
        if date_parts and date_parts[0]:
            year = date_parts[0][0]

        abstract = item.get("abstract", "")
        if abstract:
            abstract = re.sub(r"<[^>]+>", "", abstract).strip()

        results.append({
            "source_api": "crossref",
            "title": title,
            "authors": authors,
            "year": year,
            "doi": item.get("DOI"),
            "url": item.get("URL", ""),
            "abstract": abstract,
            "venue": venue,
            "citation_count": item.get("is-referenced-by-count", 0),
            "is_open_access": False,
            "open_access_url": None,
            "paper_id": item.get("DOI", ""),
            "type": item.get("type", "unknown"),
        })
    return results


def _deduplicate(results: list[dict]) -> list[dict]:
    seen_dois = set()
    seen_titles = set()
    unique = []
    for r in results:
        doi = (r.get("doi") or "").strip().lower()
        title_norm = re.sub(r'[^\w]', '', (r.get("title") or "").lower())

        if doi and doi in seen_dois:
            continue
        if title_norm and title_norm in seen_titles:
            continue

        if doi:
            seen_dois.add(doi)
        if title_norm:
            seen_titles.add(title_norm)
        unique.append(r)
    return unique


def search(query: str, year_min: int = 2015, year_max: int = 2026,
           max_results: int = 20, api: str = "all") -> dict:
    load_env()
    all_results = []

    apis = {
        "semantic_scholar": _search_semantic_scholar,
        "openalex": _search_openalex,
        "crossref": _search_crossref,
    }

    targets = apis if api == "all" else {api: apis[api]}

    for name, fn in targets.items():
        log.info("Searching %s for: %s", name, query)
        results = fn(query, year_min, year_max, max_results)
        log.info("  %s returned %d results", name, len(results))
        all_results.extend(results)
        time.sleep(1)

    total_raw = len(all_results)
    all_results.sort(key=lambda r: r.get("citation_count", 0), reverse=True)
    unique = _deduplicate(all_results)

    output = {
        "query": query,
        "searched_at": now_iso(),
        "parameters": {
            "year_min": year_min,
            "year_max": year_max,
            "max_results": max_results,
            "apis": list(targets.keys()),
        },
        "results": unique,
        "total_found": total_raw,
        "deduplicated_count": len(unique),
    }
    return output


def main():
    parser = argparse.ArgumentParser(description="Search academic APIs for peer-reviewed papers")
    parser.add_argument("--query", required=True, help="Search query string")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--year-min", type=int, default=2015, help="Earliest publication year (default: 2015)")
    parser.add_argument("--year-max", type=int, default=2026, help="Latest publication year (default: 2026)")
    parser.add_argument("--max-results", type=int, default=20, help="Max results per API (default: 20)")
    parser.add_argument("--api", choices=["all", "semantic_scholar", "openalex", "crossref"], default="all")
    args = parser.parse_args()

    result = search(args.query, args.year_min, args.year_max, args.max_results, args.api)
    save_json(args.output, result)
    print(json.dumps({"status": "ok", "query": args.query, "total_found": result["total_found"],
                       "deduplicated_count": result["deduplicated_count"], "output": args.output}, indent=2))


if __name__ == "__main__":
    main()
