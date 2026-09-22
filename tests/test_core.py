"""Unit tests for data loading, scoring, validation, impact aggregates and reports."""

import pandas as pd
import pytest

from career_insights import impact
from career_insights.data import load_all
from career_insights.report import ReportData, to_csv, to_pdf
from career_insights.scoring import (build_skill_model, gap_analysis, priority_label, readiness_score,
                                     recommend_occupations)
from career_insights.validation import clean_selection, parse_free_text_skills


@pytest.fixture(scope="module")
def ds():
    return load_all()


@pytest.fixture(scope="module")
def model(ds):
    return build_skill_model(ds)


def test_datasets_load_and_are_labelled(ds):
    assert len(ds.occupations) == 16
    assert set(ds.catalog["data_status"])  # every dataset carries a status
    assert (ds.profiles["is_synthetic"] == "yes").all()
    required = {"Python", "SQL", "Java", "AWS", "Azure", "Docker", "Kubernetes", "Machine Learning",
                "Deep Learning", "Tableau", "Power BI", "Excel", "Statistics", "Spark", "Kafka", "Communication"}
    assert required <= set(ds.skill_names)


def test_recommendations_rank_sensible_roles(ds, model):
    recs = recommend_occupations(ds, model, ["Python", "SQL", "Tableau", "Excel", "Statistics"], top_n=3)
    assert recs.iloc[0]["occupation_id"] == "data_analyst"
    assert recs["match_score"].between(0, 100).all()
    cloud = recommend_occupations(ds, model, ["AWS", "Terraform", "Linux", "Docker", "Kubernetes"], top_n=2)
    assert set(cloud["occupation_id"]) & {"cloud_engineer", "devops_engineer"}


def test_empty_skills_returns_empty(ds, model):
    assert recommend_occupations(ds, model, []).empty


def test_gap_analysis_and_readiness(ds):
    gap = gap_analysis(ds, "data_engineer", ["SQL", "Python"])
    assert gap.loc[gap["skill"] == "SQL", "priority"].item() == "Already have"
    assert 0 < readiness_score(gap) < 100
    assert readiness_score(gap_analysis(ds, "data_engineer", [])) == 0
    full = ds.occupation_skills[ds.occupation_skills["occupation_id"] == "data_engineer"]["skill"].tolist()
    assert readiness_score(gap_analysis(ds, "data_engineer", full)) == 100
    with pytest.raises(KeyError):
        gap_analysis(ds, "astronaut", [])


def test_priority_thresholds():
    assert priority_label(0.9) == "High"
    assert priority_label(0.5) == "Medium"
    assert priority_label(0.1) == "Low"


def test_free_text_parsing(ds):
    parsed = parse_free_text_skills("python, postgres; k8s\nPowerBI, pythn, underwater basket weaving", ds.skill_names)
    assert parsed.recognized == ["Python", "SQL", "Kubernetes", "Power BI"]
    assert "pythn" in parsed.unrecognized and parsed.suggestions["pythn"] == "Python"
    assert parse_free_text_skills("   ", ds.skill_names).recognized == []
    assert parse_free_text_skills("x" * 2000, ds.skill_names).warnings


def test_clean_selection():
    assert clean_selection(["A", "Z", "A", "B"], ["A", "B"]) == ["A", "B"]
    assert clean_selection(None, ["A"]) == []


def test_impact_aggregates_suppress_small_groups(ds):
    for df in (impact.top_skills(ds), impact.top_occupations(ds), impact.geographic_distribution(ds)):
        assert (df["profiles"] >= impact.MIN_GROUP_SIZE).all()
        assert "record_id" not in df.columns
    trend = impact.gap_trend_by_quarter(ds)
    assert trend["avg_readiness"].between(0, 100).all()
    assert not impact.missing_core_heatmap(ds).empty


def test_reports(ds, model):
    skills = ["Python", "SQL", "Tableau"]
    gap = gap_analysis(ds, "data_analyst", skills)
    data = ReportData(skills=skills, recommendations=recommend_occupations(ds, model, skills, top_n=5),
                      target_occupation="Data Analyst", gap=gap, readiness=readiness_score(gap),
                      location="Chicago", salary={"soc": "15-2031", "median": 85000, "p10": 50000, "p90": 150000,
                                                  "employment": 3500, "growth": 23, "data_status": "Demo estimate"})
    pdf = to_pdf(data)
    assert pdf.startswith(b"%PDF")
    csv = pd.read_csv(pd.io.common.BytesIO(to_csv(data)))
    assert {"section", "item", "metric", "value"} == set(csv.columns)
    assert (csv["section"] == "skills_gap").any()
