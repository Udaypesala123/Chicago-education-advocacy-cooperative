"""Transparent scoring for career matching and skills-gap analysis.

Career match score (0-100)
    match = 100 * (W_COVERAGE * weighted_coverage + W_SIMILARITY * specificity_similarity)

    * weighted_coverage: sum of importance of the occupation's skills the user
      has, divided by the sum of importance of all the occupation's skills.
      "How much of this job's skill profile do you already cover?"
    * specificity_similarity: cosine similarity between the user's skills and
      the occupation's TF-IDF weighted skill profile (scikit-learn). Skills that
      appear in many occupations (e.g., Communication) get lower weight than
      distinctive ones (e.g., Terraform), so this rewards distinctive overlap
      and slightly penalizes skills unrelated to the role.

Skill priority (for skills the user is missing)
    priority_score = W_IMPORTANCE * (importance / 5) + W_BREADTH * breadth

    * importance: 1-5 rating for the target occupation (5 = core).
    * breadth: share of all career paths in the dataset that list the skill,
      i.e., how transferable learning it is.
    High >= HIGH_THRESHOLD, Medium >= MEDIUM_THRESHOLD, otherwise Low.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .data import Datasets

W_COVERAGE = 0.6
W_SIMILARITY = 0.4
W_IMPORTANCE = 0.7
W_BREADTH = 0.3
HIGH_THRESHOLD = 0.65
MEDIUM_THRESHOLD = 0.45
CORE_IMPORTANCE = 4  # importance >= 4 is treated as a "core" skill
PRIORITY_ORDER = ["High", "Medium", "Low"]


@dataclass(frozen=True)
class SkillModel:
    """Occupation x skill matrices used for scoring."""

    occupation_ids: list[str]
    skills: list[str]
    importance: pd.DataFrame  # occupations x skills, 0 when not listed
    tfidf: TfidfTransformer
    tfidf_matrix: np.ndarray


def build_skill_model(ds: Datasets) -> SkillModel:
    importance = (
        ds.occupation_skills.pivot_table(index="occupation_id", columns="skill", values="importance",
                                         aggfunc="max", fill_value=0)
        .reindex(columns=ds.skill_names, fill_value=0)
        .reindex(ds.occupations["occupation_id"], fill_value=0)
    )
    tfidf = TfidfTransformer(norm="l2", smooth_idf=True)
    matrix = tfidf.fit_transform(importance.values).toarray()
    return SkillModel(importance.index.tolist(), importance.columns.tolist(), importance, tfidf, matrix)


def _user_vector(model: SkillModel, user_skills: list[str]) -> np.ndarray:
    vec = np.array([[1.0 if s in set(user_skills) else 0.0 for s in model.skills]])
    return model.tfidf.transform(vec).toarray()


def recommend_occupations(ds: Datasets, model: SkillModel, user_skills: list[str],
                          top_n: int | None = None, min_score: float = 0.0) -> pd.DataFrame:
    """Rank occupations for a set of skills. Returns an empty frame if no skills."""
    cols = ["occupation_id", "occupation", "category", "match_score", "weighted_coverage",
            "specificity_similarity", "matched_skills", "missing_core_skills", "explanation"]
    user_set = set(user_skills)
    if not user_set:
        return pd.DataFrame(columns=cols)

    similarities = cosine_similarity(_user_vector(model, user_skills), model.tfidf_matrix)[0]
    names = ds.occupation_names
    categories = dict(zip(ds.occupations["occupation_id"], ds.occupations["category"]))
    rows = []
    for i, occ_id in enumerate(model.occupation_ids):
        weights = model.importance.loc[occ_id]
        weights = weights[weights > 0].sort_values(ascending=False)
        total = weights.sum()
        matched = [s for s in weights.index if s in user_set]
        coverage = weights[matched].sum() / total if total else 0.0
        sim = float(similarities[i])
        score = 100 * (W_COVERAGE * coverage + W_SIMILARITY * sim)
        missing_core = [s for s, w in weights.items() if w >= CORE_IMPORTANCE and s not in user_set]
        rows.append({
            "occupation_id": occ_id,
            "occupation": names[occ_id],
            "category": categories[occ_id],
            "match_score": round(score, 1),
            "weighted_coverage": round(coverage * 100, 1),
            "specificity_similarity": round(sim * 100, 1),
            "matched_skills": matched,
            "missing_core_skills": missing_core,
            "explanation": explain_match(matched, weights, missing_core),
        })
    df = pd.DataFrame(rows, columns=cols).sort_values(["match_score", "occupation"], ascending=[False, True])
    df = df[df["match_score"] >= min_score]
    return df.head(top_n).reset_index(drop=True) if top_n else df.reset_index(drop=True)


def explain_match(matched: list[str], weights: pd.Series, missing_core: list[str]) -> str:
    """Plain-language reason for a recommendation."""
    if not matched:
        return "None of your selected skills are in this role's profile yet."
    core = [s for s in matched if weights[s] >= CORE_IMPORTANCE]
    other = [s for s in matched if weights[s] < CORE_IMPORTANCE]
    parts = []
    if core:
        parts.append(f"You have {len(core)} core skill{'s' if len(core) != 1 else ''} for this role: "
                     f"{_join(core)}.")
    if other:
        parts.append(f"Supporting skills you have: {_join(other)}.")
    if missing_core:
        parts.append(f"Core skills to build next: {_join(missing_core[:4])}"
                     f"{' and more' if len(missing_core) > 4 else ''}.")
    else:
        parts.append("You already cover every core skill in this profile.")
    return " ".join(parts)


def _join(items: list[str]) -> str:
    if len(items) <= 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def skill_breadth(ds: Datasets) -> pd.Series:
    """Share of occupations (0-1) that list each skill."""
    n = ds.occupations["occupation_id"].nunique()
    return ds.occupation_skills.groupby("skill")["occupation_id"].nunique() / n


def priority_label(score: float) -> str:
    if score >= HIGH_THRESHOLD:
        return "High"
    if score >= MEDIUM_THRESHOLD:
        return "Medium"
    return "Low"


def gap_analysis(ds: Datasets, occupation_id: str, user_skills: list[str]) -> pd.DataFrame:
    """Per-skill gap table for a target occupation."""
    req = ds.occupation_skills[ds.occupation_skills["occupation_id"] == occupation_id]
    if req.empty:
        raise KeyError(f"No skill profile for occupation: {occupation_id}")
    breadth = skill_breadth(ds)
    cats = dict(zip(ds.skills["skill"], ds.skills["skill_category"]))
    user_set = set(user_skills)
    rows = []
    for _, r in req.iterrows():
        b = float(breadth.get(r["skill"], 0.0))
        score = W_IMPORTANCE * (r["importance"] / 5) + W_BREADTH * b
        has = r["skill"] in user_set
        rows.append({
            "skill": r["skill"],
            "skill_category": cats.get(r["skill"], "Other"),
            "importance": int(r["importance"]),
            "is_core": r["importance"] >= CORE_IMPORTANCE,
            "has_skill": has,
            "breadth_pct": round(b * 100, 1),
            "priority_score": round(score, 3),
            "priority": "Already have" if has else priority_label(score),
        })
    df = pd.DataFrame(rows)
    return df.sort_values(["has_skill", "priority_score", "skill"], ascending=[True, False, True]).reset_index(drop=True)


def readiness_score(gap: pd.DataFrame) -> float:
    """Importance-weighted share (0-100) of the target's skills the user has."""
    total = gap["importance"].sum()
    return round(100 * gap.loc[gap["has_skill"], "importance"].sum() / total, 1) if total else 0.0


def category_coverage(gap: pd.DataFrame) -> pd.DataFrame:
    """Importance-weighted coverage by skill category, for radar charts."""
    g = gap.assign(have_weight=gap["importance"] * gap["has_skill"])
    out = g.groupby("skill_category").agg(required=("importance", "sum"), have=("have_weight", "sum"))
    out["coverage_pct"] = (100 * out["have"] / out["required"]).round(1)
    return out.reset_index()
