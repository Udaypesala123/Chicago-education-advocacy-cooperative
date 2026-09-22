"""Career Explorer: recommend occupations from the user's selected skills."""

import pandas as pd
import streamlit as st

from career_insights import charts
from career_insights.components import go_to_gap, report_downloads, skill_picker
from career_insights.scoring import CORE_IMPORTANCE, W_COVERAGE, W_SIMILARITY, recommend_occupations
from career_insights.ui import disclaimer, get_data, pills, show, source_caption

ds, model = get_data()

st.title("Career Explorer")
st.markdown("Select the skills you have today. We rank career paths by how well your skills match each role's "
            "skill profile and explain every recommendation.")

skills = skill_picker(ds)

if not skills:
    st.info("Select at least one skill above, or start from an example profile, to see recommended career paths.",
            icon=":material/arrow_upward:")
    disclaimer()
    st.stop()

if len(skills) < 3:
    st.caption("Tip: results get more precise with 3 or more skills.")

f1, f2 = st.columns([2, 1])
categories = sorted(ds.occupations["category"].unique())
chosen_cats = f1.multiselect("Filter by career area (optional)", categories, placeholder="All career areas")
top_n = f2.slider("Number of results", min_value=3, max_value=len(ds.occupations), value=6)

recs = recommend_occupations(ds, model, skills)
if chosen_cats:
    recs = recs[recs["category"].isin(chosen_cats)]
recs = recs.head(top_n).reset_index(drop=True)

if recs.empty or recs["match_score"].max() == 0:
    st.warning("None of the career paths match the current filters and skills. Try removing a filter or adding "
               "more skills.")
    disclaimer()
    st.stop()

show(charts.match_scores(recs), key="match_chart")
source_caption(ds, "occupation_skills")

st.subheader("Why these roles?")
for i, rec in recs.iterrows():
    occ = ds.occupation(rec["occupation_id"])
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.markdown(f"**{i + 1}. {rec['occupation']}** · {rec['category']}")
            st.caption(occ["description"])
            st.markdown(rec["explanation"])
            if rec["matched_skills"]:
                st.markdown("You have: " + pills(rec["matched_skills"], "Already have"), unsafe_allow_html=True)
            if rec["missing_core_skills"]:
                st.markdown("Core skills to build: " + pills(rec["missing_core_skills"], "High"),
                            unsafe_allow_html=True)
        with right:
            st.metric("Match score", f"{rec['match_score']:.0f}/100")
            st.caption(f"Coverage {rec['weighted_coverage']:.0f}% · Specificity {rec['specificity_similarity']:.0f}%")
            if st.button("Analyze my gap", key=f"gap_{rec['occupation_id']}", on_click=go_to_gap,
                         args=(rec["occupation_id"],), width="stretch"):
                st.switch_page("views/skills_gap.py")

st.subheader("Your skills across the recommended roles")
st.caption("Heatmap of how important each of your skills is (1–5) to each recommended role. Blank = not part of "
           "that role's profile.")
imp = model.importance.loc[recs["occupation_id"], [s for s in skills if s in model.importance.columns]]
imp = imp.replace(0, pd.NA).astype("Float64")
imp.index = recs["occupation"].tolist()
if imp.shape[1] > 0:
    show(charts.heatmap(imp.astype(float), "Importance of your skills by role", "Importance", ".0f", zmin=1, zmax=5),
         key="skill_heatmap")

with st.expander("How the match score is calculated", icon=":material/calculate:"):
    st.markdown(f"""
**Match score = 100 × ({W_COVERAGE} × weighted coverage + {W_SIMILARITY} × specificity similarity)**

* **Weighted coverage**: each role lists skills rated 1–5 for importance. Coverage is the sum of the ratings
  for skills you have divided by the sum of all the role's ratings. Skills rated {CORE_IMPORTANCE} or 5 count as *core*.
* **Specificity similarity**: cosine similarity between your skills and the role's skill profile after
  TF-IDF weighting (scikit-learn). Skills that many roles share, like Communication, count less than
  distinctive ones, like Terraform. This rewards overlap that is specific to the role.
* Scores are relative indicators of skill alignment. They are not predictions of hiring outcomes.
""")

st.divider()
report_downloads(ds, model)
disclaimer()
