"""Load and validate the CSV datasets in ``data/``.

All loaders are pure functions so they can be unit-tested; the Streamlit layer
wraps :func:`load_all` in ``st.cache_data``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Expected columns per file. Loading fails loudly if a file is missing or a
# column was renamed, instead of producing confusing charts later.
SCHEMA: dict[str, list[str]] = {
    "skills.csv": ["skill", "skill_category", "description"],
    "occupations.csv": ["occupation_id", "occupation", "category", "soc_code", "soc_title", "soc_is_proxy",
                        "location_group", "typical_entry_education", "description"],
    "occupation_skills.csv": ["occupation_id", "skill", "importance"],
    "bls_national_occupations.csv": ["soc_code", "soc_title", "employment", "wage_p10", "wage_median",
                                     "wage_p90", "projected_growth_pct_2023_2033", "typical_entry_education",
                                     "reference_period", "data_status"],
    "locations.csv": ["location_id", "location_name", "short_name", "area_type", "state", "lat", "lon"],
    "wages_by_location.csv": ["soc_code", "location_id", "employment", "wage_p10", "wage_p25", "wage_median",
                              "wage_p75", "wage_p90", "location_quotient", "reference_period", "data_status"],
    "industry_distribution.csv": ["soc_code", "industry", "share_pct", "data_status"],
    "demo_profiles.csv": ["record_id", "cohort_quarter", "location_id", "education_level", "field_of_study",
                          "target_occupation_id", "skills", "is_synthetic"],
    "dataset_catalog.csv": ["dataset_id", "file", "title", "publisher", "source_url", "reference_period",
                            "compiled_on", "data_status", "notes"],
}


class DataError(RuntimeError):
    """Raised when a dataset is missing or malformed."""


@dataclass(frozen=True)
class Datasets:
    skills: pd.DataFrame
    occupations: pd.DataFrame
    occupation_skills: pd.DataFrame
    bls_national: pd.DataFrame
    locations: pd.DataFrame
    wages: pd.DataFrame
    industries: pd.DataFrame
    profiles: pd.DataFrame
    catalog: pd.DataFrame

    @property
    def skill_names(self) -> list[str]:
        return sorted(self.skills["skill"].tolist(), key=str.lower)

    @property
    def occupation_names(self) -> dict[str, str]:
        """Map occupation_id -> display name."""
        return dict(zip(self.occupations["occupation_id"], self.occupations["occupation"]))

    def occupation(self, occupation_id: str) -> pd.Series:
        match = self.occupations[self.occupations["occupation_id"] == occupation_id]
        if match.empty:
            raise KeyError(f"Unknown occupation: {occupation_id}")
        return match.iloc[0]

    def location_name(self, location_id: str, short: bool = True) -> str:
        col = "short_name" if short else "location_name"
        match = self.locations.loc[self.locations["location_id"] == location_id, col]
        return match.iloc[0] if not match.empty else location_id

    def catalog_entry(self, dataset_id: str) -> pd.Series:
        return self.catalog[self.catalog["dataset_id"] == dataset_id].iloc[0]


def _read(name: str, data_dir: Path) -> pd.DataFrame:
    path = data_dir / name
    if not path.exists():
        raise DataError(f"Missing data file: {path}. Run `python scripts/build_demo_data.py`.")
    try:
        df = pd.read_csv(path, dtype={"soc_code": str}, keep_default_na=False, na_values=[""])
    except Exception as exc:  # pragma: no cover - pandas error types vary
        raise DataError(f"Could not read {name}: {exc}") from exc
    missing = set(SCHEMA[name]) - set(df.columns)
    if missing:
        raise DataError(f"{name} is missing columns: {sorted(missing)}")
    if df.empty:
        raise DataError(f"{name} is empty.")
    return df


def load_all(data_dir: Path = DATA_DIR) -> Datasets:
    """Load every dataset and run referential-integrity checks."""
    frames = {name: _read(name, data_dir) for name in SCHEMA}
    ds = Datasets(
        skills=frames["skills.csv"],
        occupations=frames["occupations.csv"],
        occupation_skills=frames["occupation_skills.csv"],
        bls_national=frames["bls_national_occupations.csv"],
        locations=frames["locations.csv"],
        wages=frames["wages_by_location.csv"],
        industries=frames["industry_distribution.csv"],
        profiles=frames["demo_profiles.csv"],
        catalog=frames["dataset_catalog.csv"],
    )

    unknown_skills = set(ds.occupation_skills["skill"]) - set(ds.skills["skill"])
    if unknown_skills:
        raise DataError(f"occupation_skills.csv references unknown skills: {sorted(unknown_skills)}")
    unknown_occ = set(ds.occupation_skills["occupation_id"]) - set(ds.occupations["occupation_id"])
    if unknown_occ:
        raise DataError(f"occupation_skills.csv references unknown occupations: {sorted(unknown_occ)}")
    if not ds.occupation_skills["importance"].between(1, 5).all():
        raise DataError("Skill importance must be between 1 and 5.")
    return ds
