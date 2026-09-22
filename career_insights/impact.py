"""Aggregated, anonymized statistics for the ChiEAC Impact page.

Privacy rules applied to every aggregate:
    * Only counts/averages are returned; no row-level records leave this module.
    * Groups with fewer than ``MIN_GROUP_SIZE`` profiles are suppressed (small
      cell suppression), so rare combinations cannot identify an individual.
"""

from __future__ import annotations

import pandas as pd

from .data import Datasets
from .scoring import CORE_IMPORTANCE

MIN_GROUP_SIZE = 10


def _profiles_long(ds: Datasets) -> pd.DataFrame:
    p = ds.profiles.assign(skill=ds.profiles["skills"].fillna("").str.split(";"))
    p = p.explode("skill")
    return p[p["skill"].str.len() > 0]


def suppress_small(df: pd.DataFrame, count_col: str = "profiles") -> pd.DataFrame:
    return df[df[count_col] >= MIN_GROUP_SIZE].reset_index(drop=True)


def headline_metrics(ds: Datasets) -> dict[str, object]:
    p = ds.profiles
    names = ds.occupation_names
    return {
        "profiles": len(p),
        "distinct_skills": _profiles_long(ds)["skill"].nunique(),
        "top_skill": _profiles_long(ds)["skill"].value_counts().idxmax(),
        "top_occupation": names.get(p["target_occupation_id"].value_counts().idxmax(), "-"),
        "top_location": ds.location_name(p["location_id"].value_counts().idxmax()),
        "quarters": sorted(p["cohort_quarter"].unique()),
    }


def top_skills(ds: Datasets, n: int = 15) -> pd.DataFrame:
    long = _profiles_long(ds)
    counts = long.groupby("skill")["record_id"].nunique().rename("profiles").reset_index()
    counts["share_pct"] = (100 * counts["profiles"] / len(ds.profiles)).round(1)
    return suppress_small(counts).sort_values("profiles", ascending=False).head(n).reset_index(drop=True)


def top_occupations(ds: Datasets) -> pd.DataFrame:
    counts = ds.profiles["target_occupation_id"].value_counts().rename_axis("occupation_id")
    df = counts.rename("profiles").reset_index()
    df["occupation"] = df["occupation_id"].map(ds.occupation_names)
    df["share_pct"] = (100 * df["profiles"] / len(ds.profiles)).round(1)
    return suppress_small(df)


def geographic_distribution(ds: Datasets) -> pd.DataFrame:
    counts = ds.profiles["location_id"].value_counts().rename("profiles").rename_axis("location_id").reset_index()
    df = counts.merge(ds.locations[["location_id", "short_name", "lat", "lon"]], on="location_id")
    df["share_pct"] = (100 * df["profiles"] / len(ds.profiles)).round(1)
    return suppress_small(df)


def _profile_readiness(ds: Datasets) -> pd.DataFrame:
    """Importance-weighted readiness of each profile for its own target occupation."""
    long = _profiles_long(ds)[["record_id", "skill"]]
    req = ds.occupation_skills.rename(columns={"occupation_id": "target_occupation_id"})
    merged = ds.profiles[["record_id", "cohort_quarter", "target_occupation_id"]].merge(req, on="target_occupation_id")
    have = long.assign(has=True)
    merged = merged.merge(have, on=["record_id", "skill"], how="left")
    merged["has"] = merged["has"].fillna(False).astype(bool)
    return merged


def gap_trend_by_quarter(ds: Datasets) -> pd.DataFrame:
    m = _profile_readiness(ds)
    m["have_w"] = m["importance"] * m["has"]
    per = m.groupby(["record_id", "cohort_quarter"]).agg(req=("importance", "sum"), have=("have_w", "sum"))
    per["readiness"] = 100 * per["have"] / per["req"]
    core = m[m["importance"] >= CORE_IMPORTANCE]
    missing_core = (~core["has"]).groupby(core["record_id"]).sum().rename("missing_core")
    per = per.reset_index().merge(missing_core.reset_index(), on="record_id", how="left")
    out = per.groupby("cohort_quarter").agg(profiles=("record_id", "nunique"),
                                            avg_readiness=("readiness", "mean"),
                                            avg_missing_core=("missing_core", "mean")).reset_index()
    out["avg_readiness"] = out["avg_readiness"].round(1)
    out["avg_missing_core"] = out["avg_missing_core"].round(2)
    return suppress_small(out).sort_values("cohort_quarter").reset_index(drop=True)


def missing_core_heatmap(ds: Datasets, top_skills_n: int = 12) -> pd.DataFrame:
    """Share (%) of profiles targeting each occupation that lack each core skill.

    Occupations with fewer than MIN_GROUP_SIZE profiles are suppressed.
    """
    m = _profile_readiness(ds)
    core = m[m["importance"] >= CORE_IMPORTANCE]
    sizes = ds.profiles["target_occupation_id"].value_counts()
    keep = sizes[sizes >= MIN_GROUP_SIZE].index
    core = core[core["target_occupation_id"].isin(keep)]
    pct = (~core["has"]).groupby([core["target_occupation_id"], core["skill"]]).mean().mul(100).round(1)
    table = pct.unstack(fill_value=float("nan"))
    top_cols = (~core["has"]).groupby(core["skill"]).sum().sort_values(ascending=False).head(top_skills_n).index
    table = table.reindex(columns=top_cols)
    table.index = [ds.occupation_names[i] for i in table.index]
    return table
