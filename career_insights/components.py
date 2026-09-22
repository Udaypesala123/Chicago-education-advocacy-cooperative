"""Reusable interactive Streamlit components shared by several pages."""

from __future__ import annotations

import streamlit as st

from .data import Datasets
from .report import ReportData, to_csv, to_pdf
from .scoring import SkillModel, gap_analysis, readiness_score, recommend_occupations
from .ui import get_saved, restore, save, set_saved
from .validation import parse_free_text_skills

SKILLS_KEY = "user_skills"
TARGET_KEY = "target_occ"
LOCATION_KEY = "location"
MAX_SKILLS = 30

PRESETS = {
    "Data analytics student": ["Python", "SQL", "Excel", "Tableau", "Statistics", "Communication"],
    "Cloud / DevOps track": ["Python", "AWS", "Docker", "Linux", "Git", "CI/CD"],
    "Software engineering": ["Java", "Python", "Git", "SQL", "REST APIs", "Problem Solving"],
    "AI / ML focus": ["Python", "Machine Learning", "Deep Learning", "Statistics", "SQL", "Spark"],
}


def _apply_preset(skills: list[str]) -> None:
    st.session_state[SKILLS_KEY] = skills
    save(SKILLS_KEY)
    st.session_state.pop("_skills_feedback", None)


def _add_typed_skills(known: list[str]) -> None:
    parsed = parse_free_text_skills(st.session_state.get("skills_text", ""), known)
    current = list(st.session_state.get(SKILLS_KEY, []))
    added = [s for s in parsed.recognized if s not in current]
    room = MAX_SKILLS - len(current)
    if room < len(added):
        parsed.warnings.append(f"You can select up to {MAX_SKILLS} skills; some entries were not added.")
        added = added[:max(room, 0)]
    st.session_state[SKILLS_KEY] = current + added
    save(SKILLS_KEY)
    st.session_state["skills_text"] = ""
    st.session_state["_skills_feedback"] = {"added": added, "unrecognized": parsed.unrecognized,
                                            "suggestions": parsed.suggestions, "warnings": parsed.warnings}


def skill_picker(ds: Datasets, label: str = "Your skills", show_presets: bool = True) -> list[str]:
    """Multiselect + free-text entry for the user's skills. Returns the current selection."""
    known = ds.skill_names
    restore(SKILLS_KEY, [], allowed=known)
    selected = st.multiselect(
        label, options=known, key=SKILLS_KEY, on_change=save, args=(SKILLS_KEY,),
        max_selections=MAX_SKILLS, placeholder="Start typing, e.g. Python, SQL, Tableau…",
        help="Pick every skill you can use in a project or job today. Your selection is kept as you move "
             "between pages and is never stored on a server.",
    )

    with st.expander("Type or paste skills instead (e.g., from your résumé)"):
        st.text_input("Comma-separated skills", key="skills_text", max_chars=500,
                      placeholder="python, postgres, power bi, k8s")
        st.button("Add typed skills", on_click=_add_typed_skills, args=(known,), type="secondary")
        fb = st.session_state.get("_skills_feedback")
        if fb:
            if fb["added"]:
                st.success("Added: " + ", ".join(fb["added"]))
            elif not fb["unrecognized"]:
                st.info("Those skills are already selected.")
            if fb["unrecognized"]:
                msg = "Not recognized: " + ", ".join(fb["unrecognized"])
                if fb["suggestions"]:
                    msg += ". Did you mean: " + ", ".join(f"{k} → {v}" for k, v in fb["suggestions"].items()) + "?"
                st.warning(msg)
            for w in fb["warnings"]:
                st.warning(w)

    if show_presets:
        st.caption("Or start from an example profile:")
        cols = st.columns(len(PRESETS))
        for col, (name, skills) in zip(cols, PRESETS.items()):
            col.button(name, on_click=_apply_preset, args=(skills,), width="stretch",
                       key=f"preset_{name}")
    return selected


def target_picker(ds: Datasets, label: str = "Target career path") -> str:
    names = ds.occupation_names
    ids = sorted(names, key=names.get)
    restore(TARGET_KEY, "data_analyst", allowed=ids)
    return st.selectbox(label, ids, key=TARGET_KEY, format_func=names.get, on_change=save, args=(TARGET_KEY,))


def location_picker(ds: Datasets, label: str = "Location") -> str:
    ids = ds.locations["location_id"].tolist()
    restore(LOCATION_KEY, "chicago", allowed=ids)
    return st.selectbox(label, ids, key=LOCATION_KEY, format_func=lambda i: ds.location_name(i, short=False),
                        on_change=save, args=(LOCATION_KEY,))


def go_to_gap(occupation_id: str) -> None:
    set_saved(TARGET_KEY, occupation_id)


def report_downloads(ds: Datasets, model: SkillModel) -> None:
    """Download buttons for the personalized report, built from current selections."""
    skills = get_saved(SKILLS_KEY, [])
    target = get_saved(TARGET_KEY)
    loc = get_saved(LOCATION_KEY, "chicago")
    st.subheader("Download your career-readiness report")
    if not skills:
        st.info("Select at least one skill to generate a report.")
        return

    recs = recommend_occupations(ds, model, skills, top_n=6)
    data = ReportData(skills=skills, recommendations=recs)
    if target in ds.occupation_names:
        occ = ds.occupation(target)
        gap = gap_analysis(ds, target, skills)
        data.target_occupation, data.gap, data.readiness = occ["occupation"], gap, readiness_score(gap)
        w = ds.wages[(ds.wages["soc_code"] == occ["soc_code"]) & (ds.wages["location_id"] == loc)]
        nat = ds.bls_national[ds.bls_national["soc_code"] == occ["soc_code"]]
        if not w.empty and not nat.empty:
            w = w.iloc[0]
            data.location = ds.location_name(loc, short=False)
            data.salary = {"soc": occ["soc_code"], "median": w["wage_median"], "p10": w["wage_p10"],
                           "p90": w["wage_p90"], "employment": w["employment"],
                           "growth": nat.iloc[0]["projected_growth_pct_2023_2033"], "data_status": w["data_status"]}

    target_label = data.target_occupation or "no target selected"
    st.caption(f"Includes your {len(skills)} skills, top career matches, a gap analysis for **{target_label}**"
               f"{' and a salary snapshot for ' + ds.location_name(loc) if data.salary else ''}. "
               "Generated in your browser session only.")
    c1, c2 = st.columns(2)
    try:
        pdf_bytes = to_pdf(data)
    except Exception as exc:  # keep CSV available even if PDF rendering fails
        pdf_bytes = None
        st.error(f"PDF could not be generated ({exc}). The CSV report is still available.")
    if pdf_bytes:
        c1.download_button("Download PDF report", pdf_bytes, file_name="chieac-career-readiness-report.pdf",
                           mime="application/pdf", type="primary", width="stretch",
                           icon=":material/picture_as_pdf:")
    c2.download_button("Download CSV report", to_csv(data), file_name="chieac-career-readiness-report.csv",
                       mime="text/csv", width="stretch", icon=":material/table_view:")
