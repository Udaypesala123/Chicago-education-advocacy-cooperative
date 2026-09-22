"""About the Project: purpose, methodology, data sources, limitations and privacy."""

import streamlit as st

from career_insights import AUTHOR, AUTHOR_URL, DISCLAIMER
from career_insights.impact import MIN_GROUP_SIZE
from career_insights.scoring import (HIGH_THRESHOLD, MEDIUM_THRESHOLD, W_BREADTH, W_COVERAGE, W_IMPORTANCE,
                                     W_SIMILARITY)
from career_insights.ui import catalog_table, get_data, hero

ds, _model = get_data()

hero("About the Project", "An open, transparent tool that helps students turn their skills into informed career "
     "decisions, using public labor-market data.")

st.markdown("""
### Why this project exists
International students and early-career professionals often have strong technical skills but limited visibility
into how those skills map to U.S. job titles, which skills employers ask for, and how pay and demand vary by city.
The **ChiEAC Career Insights Dashboard** brings that information together in one place. Advisors and students can
use it in career conversations, workshops and self-guided planning.

### Who it is for
* **Students** exploring which roles fit their current skills and what to learn next.
* **Advisors and mentors** at ChiEAC who want a shared, evidence-based starting point for career conversations.
* **Program staff** who want aggregated, privacy-preserving insight into common skills and gaps.
""")

st.markdown(f"""
### Methodology
**Career match score (0–100)** = 100 × ({W_COVERAGE} × weighted coverage + {W_SIMILARITY} × specificity similarity).
Weighted coverage is the importance-weighted share of a role's skills you have. Specificity similarity is the
cosine similarity between your skills and the role's TF-IDF weighted skill profile (scikit-learn), which gives
distinctive skills more weight than common ones.

**Readiness score** is the importance-weighted share of the target role's skills you have.

**Learning priority** = {W_IMPORTANCE} × (importance ÷ 5) + {W_BREADTH} × breadth, where breadth is the share of career
paths that use the skill. High ≥ {HIGH_THRESHOLD}, Medium ≥ {MEDIUM_THRESHOLD}, otherwise Low.

All weights are defined in `career_insights/scoring.py` and can be reviewed or adjusted.
""")

st.markdown("### Data sources")
st.dataframe(catalog_table(ds), hide_index=True, width="stretch",
             column_config={"source_url": st.column_config.LinkColumn("Source link"),
                            "title": "Dataset", "file": "File", "publisher": "Publisher / basis",
                            "reference_period": "Reference period", "compiled_on": "Compiled",
                            "data_status": "Status", "notes": "Notes"})
st.caption("Status legend: *Approximate public (verify)* = transcribed from a public source and should be checked "
           "against the original before citing. *Demo estimate* / *Demo (curated)* = illustrative values for "
           "demonstration. *Synthetic demo* = generated records, not real people.")

st.markdown(f"""
### Limitations
* **Demo data.** Metro-level wages and employment, industry shares and skill-importance ratings are demonstration
  estimates. Replace them with fresh downloads from BLS OEWS, O*NET and Data USA before making decisions.
* **Occupation proxies.** Some modern titles (e.g., Data Analyst, ML Engineer, Cloud Engineer) have no standalone BLS
  occupation code. The dashboard uses the closest code, so pay and demand for these titles are approximate.
* **Skills only.** Scores ignore experience, education level, portfolio, networking, work authorization and
  employer sponsorship, all of which strongly affect outcomes.
* **Point-in-time.** Wage data describe May 2023 and projections cover 2023–2033. Markets change.
* **Simplified taxonomy.** {len(ds.skills)} skills and {len(ds.occupations)} career paths cannot represent every role
  or specialty.

### Privacy
* The dashboard does not require an account and does not store your selections on a server. They live only in
  your browser session and disappear when it ends.
* Downloadable reports are generated in memory for you and are not saved.
* The ChiEAC Impact page shows only aggregates, suppresses groups smaller than {MIN_GROUP_SIZE}, and in this version
  uses synthetic records.

### Technology
Python · Streamlit · Pandas · Plotly · scikit-learn · fpdf2. The app is designed for Streamlit Community Cloud.
""")

st.markdown(f"""
### Credits
Designed and built by **[{AUTHOR}]({AUTHOR_URL})** for the Chicago Education Advocacy Cooperative (ChiEAC).
""")

st.markdown("### Disclaimer")
st.warning(DISCLAIMER, icon=":material/gavel:")
