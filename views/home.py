"""Home page: orientation, key numbers and entry points into each tool."""

import streamlit as st

from career_insights.ui import card, disclaimer, get_data, hero

ds, _model = get_data()

hero(
    "ChiEAC Career Insights Dashboard",
    "Find career paths that fit your skills, see which skills to build next, and explore salaries and demand "
    "across U.S. metro areas. Built for international students and early-career professionals.",
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Career paths", len(ds.occupations))
c2.metric("Skills tracked", len(ds.skills))
c3.metric("Locations", len(ds.locations))
c4.metric("Datasets (all cited)", len(ds.catalog))

st.markdown("#### What you can do here")
row1 = st.columns(2, gap="medium")
row2 = st.columns(2, gap="medium")
tiles = [
    (row1[0], "Career Explorer", "Select your skills and get ranked career matches with a score and a plain-language "
     "reason for each one.", "views/career_explorer.py", ":material/explore:"),
    (row1[1], "Skills Gap Analysis", "Choose a target role to see the skills you already have, the ones to develop, "
     "and which to learn first.", "views/skills_gap.py", ":material/target:"),
    (row2[0], "Location & Salary Insights", "Compare wage ranges, employment demand, required skills and industries "
     "across metro areas.", "views/location_salary.py", ":material/paid:"),
    (row2[1], "ChiEAC Impact", "Aggregated, anonymized trends: common skills, popular roles, locations and skills-gap "
     "trends (demo data).", "views/impact.py", ":material/groups:"),
]
for col, title, body, page, icon in tiles:
    with col:
        card(title, body)
        st.page_link(page, label=f"Open {title}", icon=icon)

st.markdown("#### How it works")
s1, s2, s3 = st.columns(3)
with s1:
    card("1 · Tell us your skills", "Pick from the list, paste them from your résumé, or start from an example profile. "
         "Your selections stay in your browser session.")
with s2:
    card("2 · Compare career paths", "A transparent score combines how much of each role's skill profile you cover "
         "with how distinctive your overlap is.")
with s3:
    card("3 · Plan and download", "Get prioritized skills to learn, salary context for your location, and a "
         "PDF or CSV report.")

st.markdown("#### About the data")
st.info(
    "National wage and employment figures approximate published U.S. Bureau of Labor Statistics (BLS) estimates "
    "(OEWS May 2023, Employment Projections 2023–2033). Metro-level figures, industry mixes and skill ratings are "
    "**demonstration estimates**, and the ChiEAC Impact page uses **synthetic profiles**, not real ChiEAC data. "
    "Every chart shows its source and status. See *About the Project* for details.",
    icon=":material/fact_check:",
)
st.page_link("views/about.py", label="Read the methodology, data sources and limitations", icon=":material/info:")

disclaimer()
