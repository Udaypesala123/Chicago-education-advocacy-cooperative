"""Smoke tests: every page renders without exceptions (Streamlit AppTest)."""

import pytest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"

PAGES = ["views/home.py", "views/career_explorer.py", "views/skills_gap.py", "views/location_salary.py",
         "views/impact.py", "views/about.py"]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    at.switch_page(page).run()
    assert not at.exception, at.exception


def test_career_explorer_with_skills():
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    at.switch_page("views/career_explorer.py").run()
    at.multiselect(key="user_skills").set_value(["Python", "SQL", "Tableau", "Excel"]).run()
    assert not at.exception, at.exception
    assert any("Data Analyst" in m.value for m in at.markdown)


def test_skills_gap_with_skills():
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    at.switch_page("views/skills_gap.py").run()
    at.selectbox(key="target_occ").set_value("ml_engineer").run()
    at.multiselect(key="user_skills").set_value(["Python", "Machine Learning"]).run()
    assert not at.exception, at.exception
    assert any(m.label == "Readiness score" for m in at.metric)
