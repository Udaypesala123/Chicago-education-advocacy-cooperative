"""Input validation and normalization for free-text skill entry."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

MAX_FREE_TEXT_CHARS = 500
MAX_FREE_TEXT_ITEMS = 40

# Common spellings/abbreviations -> canonical skill names in data/skills.csv.
ALIASES: dict[str, str] = {
    "py": "Python", "python3": "Python",
    "js": "JavaScript", "node": "JavaScript", "nodejs": "JavaScript", "typescript": "JavaScript", "ts": "JavaScript",
    "cpp": "C++", "c plus plus": "C++",
    "github": "Git", "gitlab": "Git",
    "mysql": "SQL", "postgres": "SQL", "postgresql": "SQL", "sql server": "SQL", "tsql": "SQL", "plsql": "SQL",
    "etl": "ETL / Data Pipelines", "data pipelines": "ETL / Data Pipelines", "elt": "ETL / Data Pipelines",
    "pyspark": "Spark", "apache spark": "Spark", "databricks": "Spark",
    "apache kafka": "Kafka", "apache airflow": "Airflow",
    "mongodb": "NoSQL Databases", "mongo": "NoSQL Databases", "dynamodb": "NoSQL Databases",
    "cassandra": "NoSQL Databases", "nosql": "NoSQL Databases",
    "ml": "Machine Learning", "scikit learn": "Machine Learning", "sklearn": "Machine Learning",
    "dl": "Deep Learning", "pytorch": "Deep Learning", "tensorflow": "Deep Learning", "neural networks": "Deep Learning",
    "natural language processing": "NLP", "llm": "NLP", "llms": "NLP",
    "stats": "Statistics", "statistical analysis": "Statistics",
    "ms excel": "Excel", "microsoft excel": "Excel", "spreadsheets": "Excel",
    "powerbi": "Power BI", "power bi": "Power BI",
    "data viz": "Data Visualization", "dataviz": "Data Visualization", "visualization": "Data Visualization",
    "ab testing": "A/B Testing", "experimentation": "A/B Testing",
    "amazon web services": "AWS", "microsoft azure": "Azure", "google cloud": "GCP", "google cloud platform": "GCP",
    "k8s": "Kubernetes", "cicd": "CI/CD", "ci cd": "CI/CD", "github actions": "CI/CD", "jenkins": "CI/CD",
    "iac": "Terraform", "unix": "Linux", "bash": "Linux", "shell": "Linux",
    "security": "Cybersecurity", "infosec": "Cybersecurity", "compliance": "Risk & Compliance",
    "html": "HTML/CSS", "css": "HTML/CSS", "reactjs": "React", "react js": "React",
    "api": "REST APIs", "apis": "REST APIs", "rest": "REST APIs", "rest api": "REST APIs",
    "testing": "Testing / QA Automation", "qa": "Testing / QA Automation", "selenium": "Testing / QA Automation",
    "unit testing": "Testing / QA Automation",
    "agile": "Agile / Scrum", "scrum": "Agile / Scrum",
    "communication skills": "Communication", "presentation": "Communication", "public speaking": "Communication",
    "problem-solving": "Problem Solving", "critical thinking": "Problem Solving",
    "pm": "Project Management", "financial analysis": "Financial Modeling",
}


def _key(text: str) -> str:
    """Normalize text for matching: lowercase, collapse separators, keep + and #."""
    text = text.lower().strip()
    text = re.sub(r"[._\-/]+", " ", text)
    text = re.sub(r"[^a-z0-9+# &]", "", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class ParsedSkills:
    recognized: list[str] = field(default_factory=list)
    unrecognized: list[str] = field(default_factory=list)
    suggestions: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def parse_free_text_skills(text: str, known_skills: list[str]) -> ParsedSkills:
    """Parse a comma/semicolon/newline separated list of skills.

    Returns canonical skill names that were recognized, entries that were not,
    and "did you mean" suggestions for close misspellings.
    """
    result = ParsedSkills()
    if not text or not text.strip():
        return result
    if len(text) > MAX_FREE_TEXT_CHARS:
        result.warnings.append(f"Input was truncated to {MAX_FREE_TEXT_CHARS} characters.")
        text = text[:MAX_FREE_TEXT_CHARS]

    items = [t.strip() for t in re.split(r"[,;\n]+", text) if t.strip()]
    if len(items) > MAX_FREE_TEXT_ITEMS:
        result.warnings.append(f"Only the first {MAX_FREE_TEXT_ITEMS} entries were used.")
        items = items[:MAX_FREE_TEXT_ITEMS]

    canonical = {_key(s): s for s in known_skills}
    aliases = {_key(a): s for a, s in ALIASES.items()}
    for raw in items:
        k = _key(raw)
        if not k:
            continue
        match = canonical.get(k) or aliases.get(k)
        if match:
            if match not in result.recognized:
                result.recognized.append(match)
            continue
        result.unrecognized.append(raw[:60])
        close = difflib.get_close_matches(k, list(canonical) + list(aliases), n=1, cutoff=0.75)
        if close:
            result.suggestions[raw[:60]] = canonical.get(close[0]) or aliases[close[0]]
    return result


def clean_selection(values, allowed) -> list[str]:
    """Drop values that are not in ``allowed`` (e.g., stale session state), preserving order."""
    allowed_set = set(allowed)
    seen: set[str] = set()
    out = []
    for v in values or []:
        if v in allowed_set and v not in seen:
            seen.add(v)
            out.append(v)
    return out
