"""Skills Gap Analysis: compare the user's skills to a target occupation's profile."""

import streamlit as st

from career_insights import charts
from career_insights.components import report_downloads, skill_picker, target_picker
from career_insights.scoring import (CORE_IMPORTANCE, HIGH_THRESHOLD, MEDIUM_THRESHOLD, PRIORITY_ORDER,
                                     W_BREADTH, W_IMPORTANCE, category_coverage, gap_analysis, readiness_score)
from career_insights.ui import disclaimer, get_data, pills, show, source_caption

ds, model = get_data()

st.title("Skills Gap Analysis")
st.markdown("Choose a target career path and compare it with your current skills. You will see what you already "
            "have, what to develop, and which skills to learn first.")

c1, c2 = st.columns([1, 2], gap="large")
with c1:
    target = target_picker(ds)
    occ = ds.occupation(target)
    st.caption(occ["description"])
    st.caption(f"Typical entry education (BLS): {occ['typical_entry_education']}")
with c2:
    skills = skill_picker(ds, label="Your current skills", show_presets=False)

gap = gap_analysis(ds, target, skills)
readiness = readiness_score(gap)
have = gap[gap["has_skill"]]
missing = gap[~gap["has_skill"]]
counts = missing["priority"].value_counts()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Readiness score", f"{readiness:.0f}/100", help="Importance-weighted share of this role's skills you have.")
m2.metric("Skills you have", f"{len(have)} of {len(gap)}")
m3.metric("High-priority gaps", int(counts.get("High", 0)))
m4.metric("Core skills missing", int(missing["is_core"].sum()))
st.progress(min(readiness / 100, 1.0), text=f"{readiness:.0f}% ready for {occ['occupation']} (skill profile only)")

if not skills:
    st.info("Add your skills above to see what you already have. Until then, all of this role's skills are shown "
            "as gaps so you can see its full profile.", icon=":material/info:")

col_have, col_dev = st.columns(2, gap="large")
with col_have:
    st.markdown("##### Skills you already have")
    if have.empty:
        st.caption("None yet for this role.")
    else:
        st.markdown(pills(have["skill"].tolist(), "Already have"), unsafe_allow_html=True)
with col_dev:
    st.markdown("##### Skills to develop")
    if missing.empty:
        st.success("You cover every skill in this role's profile.")
    for level in PRIORITY_ORDER:
        items = missing[missing["priority"] == level]["skill"].tolist()
        if items:
            st.markdown(f"**{level} priority**<br>" + pills(items, level), unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")
with left:
    show(charts.coverage_radar(category_coverage(gap), "Your coverage by skill area"), key="radar")
with right:
    show(charts.gap_bars(gap), key="gap_bars")
source_caption(ds, "occupation_skills", "skills")

st.subheader("Suggested learning priorities")
if missing.empty:
    st.markdown("You have every skill in this profile. Consider deepening core skills with portfolio projects.")
else:
    plan = missing.head(8)
    for n, (_, r) in enumerate(plan.iterrows(), start=1):
        why = "a core skill for this role" if r["is_core"] else f"rated {r['importance']}/5 for this role"
        st.markdown(f"{n}. **{r['skill']}** ({r['priority']} priority): {why}; used in "
                    f"{r['breadth_pct']:.0f}% of the career paths in this dashboard.")
    st.dataframe(
        missing[["skill", "skill_category", "importance", "breadth_pct", "priority_score", "priority"]],
        hide_index=True, width="stretch",
        column_config={
            "skill": "Skill", "skill_category": "Skill area",
            "importance": st.column_config.NumberColumn("Importance (1–5)"),
            "breadth_pct": st.column_config.NumberColumn("Used across paths", format="%.0f%%"),
            "priority_score": st.column_config.ProgressColumn("Priority score", min_value=0, max_value=1,
                                                              format="%.2f"),
            "priority": "Priority",
        },
    )

with st.expander("Methodology: how readiness and priority are scored", icon=":material/calculate:"):
    st.markdown(f"""
**Readiness score** = (sum of importance ratings for the role's skills you have) ÷ (sum of all the role's
importance ratings) × 100.

**Priority score** for each missing skill = {W_IMPORTANCE} × (importance ÷ 5) + {W_BREADTH} × breadth

* *Importance* (1–5) is how central the skill is to the role (5 = core; {CORE_IMPORTANCE}+ counts as core).
* *Breadth* is the share of all career paths in this dashboard that also list the skill. A broad skill is
  more transferable if you change your target later.
* **High** ≥ {HIGH_THRESHOLD}, **Medium** ≥ {MEDIUM_THRESHOLD}, otherwise **Low**.

Importance ratings are curated demo values informed by O*NET Technology Skills and common job-posting
requirements. They are not official O*NET scores. The score only covers skills. It does not account for
experience, education, work authorization or the hiring market.
""")

st.divider()
report_downloads(ds, model)
disclaimer()
