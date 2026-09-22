"""ChiEAC Career Insights Dashboard — Streamlit entry point.

Run locally with:  streamlit run app.py
"""

import streamlit as st

from career_insights import APP_NAME, AUTHOR, AUTHOR_URL, DISCLAIMER
from career_insights.ui import get_saved, page_setup

st.set_page_config(
    page_title=f"{APP_NAME} | by {AUTHOR}",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"About": f"{APP_NAME} by {AUTHOR}: educational career exploration for international "
                         "students and early-career professionals. " + DISCLAIMER},
)
page_setup()

pages = {
    "Explore": [
        st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
        st.Page("views/career_explorer.py", title="Career Explorer", icon=":material/explore:"),
        st.Page("views/skills_gap.py", title="Skills Gap Analysis", icon=":material/target:"),
        st.Page("views/location_salary.py", title="Location & Salary Insights", icon=":material/paid:"),
    ],
    "Community": [
        st.Page("views/impact.py", title="ChiEAC Impact", icon=":material/groups:"),
        st.Page("views/about.py", title="About the Project", icon=":material/info:"),
    ],
}
nav = st.navigation(pages)

with st.sidebar:
    st.markdown("### ChiEAC Career Insights")
    st.caption(f"Built by [{AUTHOR}]({AUTHOR_URL})")
    skills = get_saved("user_skills", [])
    st.caption("Your current selections (kept only in this browser session):")
    st.markdown(f"**Skills:** {len(skills)} selected")
    st.caption(DISCLAIMER)

nav.run()
