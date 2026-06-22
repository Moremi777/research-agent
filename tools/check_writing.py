"""Check writing for British English spelling, Americanisms, and uncited claims."""

import argparse
import json
import re
from pathlib import Path

from tools.utils import save_json, now_iso, setup_logging

log = setup_logging("check_writing")

AMERICAN_TO_BRITISH = {
    "analyze": "analyse", "analyzing": "analysing", "analyzed": "analysed",
    "behavior": "behaviour", "behavioral": "behavioural",
    "catalog": "catalogue", "cataloged": "catalogued",
    "center": "centre", "centered": "centred",
    "color": "colour", "colored": "coloured", "colorful": "colourful",
    "defense": "defence", "defensive": "defensive",
    "dialog": "dialogue",
    "favor": "favour", "favorable": "favourable", "favorite": "favourite",
    "fiber": "fibre",
    "fulfill": "fulfil", "fulfillment": "fulfilment",
    "gray": "grey",
    "honor": "honour", "honorable": "honourable",
    "humor": "humour",
    "initialize": "initialise", "initializing": "initialising", "initialized": "initialised",
    "labor": "labour",
    "license": "licence",
    "maximize": "maximise", "maximizing": "maximising",
    "minimize": "minimise", "minimizing": "minimising",
    "modeling": "modelling", "modeled": "modelled",
    "neighbor": "neighbour", "neighborhood": "neighbourhood",
    "offense": "offence",
    "optimize": "optimise", "optimizing": "optimising", "optimized": "optimised",
    "optimization": "optimisation",
    "organize": "organise", "organizing": "organising", "organized": "organised",
    "organization": "organisation",
    "paralyze": "paralyse",
    "practice": "practise",
    "prioritize": "prioritise", "prioritizing": "prioritising",
    "program": "programme",
    "realize": "realise", "realizing": "realising", "realized": "realised",
    "recognize": "recognise", "recognizing": "recognising", "recognized": "recognised",
    "specialize": "specialise", "specializing": "specialising", "specialized": "specialised",
    "standardize": "standardise", "standardizing": "standardising",
    "summarize": "summarise", "summarizing": "summarising", "summarized": "summarised",
    "theater": "theatre",
    "traveled": "travelled", "traveling": "travelling", "traveler": "traveller",
    "utilize": "utilise", "utilizing": "utilising", "utilized": "utilised",
    "utilization": "utilisation",
    "vigor": "vigour",
}

ASSERTION_PATTERNS = [
    r'\b(?:has been|have been|is|are|was|were)\b.{5,}(?:increasing|decreasing|declining|growing|rising|falling)',
    r'\b(?:shows? that|indicates? that|suggests? that|demonstrates? that|reveals? that)',
    r'\b(?:it is|this is)\b.{3,}\b(?:important|critical|essential|necessary|significant|crucial)',
    r'\b(?:research|studies|evidence)\b.{3,}\b(?:shows?|indicates?|suggests?|confirms?)',
    r'\b(?:according to|as noted by|as stated by)',
    r'\b(?:many|most|several|numerous|various)\b.{3,}\b(?:researchers?|scholars?|studies|authors?)',
    r'\b(?:widely|commonly|generally|traditionally|historically)\b.{3,}\b(?:accepted|recognised|known|used|practiced)',
]

IEEE_CITATION = re.compile(r'\[[\d,\s\-]+\]')


def _check_americanisms(lines: list[str]) -> list[dict]:
    issues = []
    for line_num, line in enumerate(lines, 1):
        words = re.findall(r'\b[a-zA-Z]+\b', line.lower())
        for word in words:
            if word in AMERICAN_TO_BRITISH:
                context_start = max(0, line.lower().find(word) - 20)
                context_end = min(len(line), line.lower().find(word) + len(word) + 20)
                issues.append({
                    "american": word,
                    "british": AMERICAN_TO_BRITISH[word],
                    "line": line_num,
                    "context": f"...{line[context_start:context_end].strip()}...",
                })
    return issues


def _check_spelling(lines: list[str]) -> list[dict]:
    try:
        from spellchecker import SpellChecker
    except ImportError:
        log.warning("pyspellchecker not installed, skipping spelling check")
        return []

    spell = SpellChecker(language="en")
    issues = []
    skip_words = set(AMERICAN_TO_BRITISH.values()) | {"et", "al", "ie", "eg", "doi", "isbn", "url"}

    for line_num, line in enumerate(lines, 1):
        clean = re.sub(r'\[[\d,\s\-]+\]', '', line)
        clean = re.sub(r'https?://\S+', '', clean)
        clean = re.sub(r'\b\d+\b', '', clean)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', clean)

        for word in words:
            lower = word.lower()
            if lower in skip_words:
                continue
            if spell.unknown([lower]):
                candidates = spell.candidates(lower)
                suggestion = list(candidates)[0] if candidates else None
                if suggestion and suggestion != lower:
                    issues.append({
                        "word": word,
                        "suggestion": suggestion,
                        "line": line_num,
                        "context": line.strip()[:80],
                    })
    return issues


def _check_citations(lines: list[str]) -> list[dict]:
    issues = []
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        if len(stripped) < 20:
            continue

        for pattern in ASSERTION_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                if not IEEE_CITATION.search(stripped):
                    issues.append({
                        "sentence": stripped[:120],
                        "line": line_num,
                        "reason": "Assertion without IEEE citation [number]",
                    })
                    break
    return issues


def _check_academic_tone(lines: list[str]) -> list[dict]:
    issues = []
    informal_words = {
        "a lot": "numerous", "lots of": "numerous", "big": "significant",
        "get": "obtain", "got": "obtained", "getting": "obtaining",
        "thing": "aspect", "things": "aspects", "stuff": "material",
        "kind of": "somewhat", "sort of": "somewhat",
        "really": "significantly", "very": "highly",
        "pretty much": "largely", "basically": "fundamentally",
        "obviously": "evidently", "of course": "naturally",
        "anyway": "", "anyways": "", "gonna": "going to",
        "wanna": "want to", "gotta": "have to",
        "ok": "acceptable", "okay": "acceptable",
        "etc": "and so forth", "etc.": "and so forth",
    }

    contraction_map = {
        "don't": "do not", "doesn't": "does not", "didn't": "did not",
        "can't": "cannot", "won't": "will not", "wouldn't": "would not",
        "shouldn't": "should not", "couldn't": "could not",
        "isn't": "is not", "aren't": "are not", "wasn't": "was not",
        "weren't": "were not", "hasn't": "has not", "haven't": "have not",
        "it's": "it is", "that's": "that is", "there's": "there is",
        "i'm": "I am", "we're": "we are", "they're": "they are",
        "i've": "I have", "we've": "we have", "they've": "they have",
    }

    first_person_pattern = re.compile(r'\b(I|my|me|mine)\b(?!\s*\[)', re.IGNORECASE)
    passive_heavy = re.compile(r'\b(was|were|is|are|been|being)\b\s+\w+ed\b')

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        lower = stripped.lower()

        for informal, formal in informal_words.items():
            if informal in lower:
                suggestion = f"Replace '{informal}' with '{formal}'" if formal else f"Remove '{informal}'"
                issues.append({
                    "type": "informal_language",
                    "issue": informal,
                    "suggestion": suggestion,
                    "line": line_num,
                    "context": stripped[:80],
                })

        for contraction, expansion in contraction_map.items():
            if contraction in lower:
                issues.append({
                    "type": "contraction",
                    "issue": contraction,
                    "suggestion": f"Expand '{contraction}' to '{expansion}'",
                    "line": line_num,
                    "context": stripped[:80],
                })

        if first_person_pattern.search(stripped):
            issues.append({
                "type": "first_person",
                "issue": "First person pronoun",
                "suggestion": "Use third person or passive voice in academic writing (e.g., 'the researcher' instead of 'I')",
                "line": line_num,
                "context": stripped[:80],
            })

        if stripped.endswith("!"):
            issues.append({
                "type": "exclamation",
                "issue": "Exclamation mark",
                "suggestion": "Avoid exclamation marks in academic writing",
                "line": line_num,
                "context": stripped[:80],
            })

        if stripped.startswith("And ") or stripped.startswith("But ") or stripped.startswith("So "):
            issues.append({
                "type": "sentence_starter",
                "issue": f"Sentence starts with '{stripped.split()[0]}'",
                "suggestion": f"Rephrase to avoid starting with a conjunction",
                "line": line_num,
                "context": stripped[:80],
            })

    return issues


def check_file(input_path: str, checks: list[str]) -> dict:
    path = Path(input_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {input_path}"}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    words = re.findall(r'\b\w+\b', content)

    result = {
        "file": input_path,
        "checked_at": now_iso(),
        "word_count": len(words),
        "line_count": len(lines),
    }

    if "spelling" in checks or "all" in checks:
        result["spelling_issues"] = _check_spelling(lines)

    if "americanisms" in checks or "all" in checks:
        result["americanisms_found"] = _check_americanisms(lines)

    if "citations" in checks or "all" in checks:
        result["uncited_claims"] = _check_citations(lines)
        citation_count = len(IEEE_CITATION.findall(content))
        result["citation_count"] = citation_count

    if "tone" in checks or "all" in checks:
        result["academic_tone_issues"] = _check_academic_tone(lines)

    total_issues = (
        len(result.get("spelling_issues", []))
        + len(result.get("americanisms_found", []))
        + len(result.get("uncited_claims", []))
        + len(result.get("academic_tone_issues", []))
    )
    result["total_issues"] = total_issues

    return result


def main():
    parser = argparse.ArgumentParser(description="Check writing for British English, spelling, and citations")
    parser.add_argument("--input", required=True, help="Path to the text file to check")
    parser.add_argument("--output", required=True, help="Output JSON report path")
    parser.add_argument("--check", default="all",
                        help="Comma-separated checks: spelling, americanisms, citations, all (default: all)")
    args = parser.parse_args()

    checks = [c.strip() for c in args.check.split(",")]
    result = check_file(args.input, checks)
    save_json(args.output, result)
    print(json.dumps({
        "status": "ok",
        "file": args.input,
        "word_count": result.get("word_count", 0),
        "total_issues": result.get("total_issues", 0),
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
