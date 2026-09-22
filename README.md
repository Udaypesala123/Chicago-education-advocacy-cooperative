# ChiEAC Career Insights Dashboard

A Streamlit web application that helps **international students and early-career professionals** find career
paths that fit their skills, see which skills to develop next, and explore salary and demand trends across U.S.
metro areas using public labor-market data.

> **Disclaimer.** This dashboard provides educational career insights based on publicly available and/or
> demonstration data. It is not immigration, legal, employment, or salary advice. Results should not be interpreted
> as guarantees of employment.

---

## What it does

| Page | What you get |
| --- | --- |
| **Home** | Overview, key numbers and entry points into each tool. |
| **Career Explorer** | Choose skills (Python, SQL, Java, AWS, Azure, Docker, Kubernetes, Machine Learning, Deep Learning, Tableau, Power BI, Excel, Statistics, Spark, Kafka, Communication and more). Get ranked career paths, each with a 0–100 **match score**, a plain-language **explanation**, and a heatmap of how your skills matter to each role. |
| **Skills Gap Analysis** | Choose a target role and see the skills you **already have**, the skills **to develop**, and each gap's **priority (High / Medium / Low)**. Includes a readiness score, a radar chart by skill area, and a written learning plan. |
| **Location & Salary Insights** | Choose a job category, career path and location. See the **salary range** (10th–90th percentile), **employment demand** with location quotient, **required skills**, **industry distribution**, a wage-vs-growth **scatter plot** and a role × location wage **heatmap**. Every chart cites its source and date. |
| **ChiEAC Impact** | Aggregated, anonymized statistics: profiles analyzed, most common skills, most requested roles, geographic distribution and **skills-gap trends**. Uses small-cell suppression and currently runs on **synthetic demo data**. |
| **About the Project** | Purpose, methodology, the full data-source catalog, limitations, privacy and disclaimer. |

A personalized **career-readiness report** is available as **PDF** or **CSV** from the Career Explorer and Skills
Gap pages. It includes your skills, top matches, the gap analysis for your target role and a salary snapshot for
your chosen location.

Other usability details:
- You can type or paste skills. Aliases such as `k8s`, `postgres`, `powerbi` and `pyspark` are recognized, and
  misspellings get "did you mean" suggestions.
- Example profiles give you a one-click starting point.
- Selections stay with you as you move between pages, and the layout works on desktop and mobile.

## Why it is useful to ChiEAC

- **For students:** a clear, explainable starting point for career planning. It shows which U.S. job titles match
  their skills, what to learn next, and what pay and demand look like in the cities they are considering.
- **For advisors and mentors:** a shared, evidence-based tool for one-on-one sessions and workshops. The scoring
  is transparent, so advisors can explain *why* a role is suggested.
- **For program staff:** a privacy-preserving view of common skills, target roles and skill gaps across cohorts
  that can inform workshop topics and partnerships. Once real data is connected, it can also support impact
  reporting.

## Quick start

Requirements: Python 3.10+ (3.11 or 3.12 recommended).

```bash
git clone <your-repo-url> chieac-career-insights
cd chieac-career-insights
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at <http://localhost:8501>. To pick a port: `streamlit run app.py --server.port 8631`.

### Run the tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests cover data integrity, scoring, input validation, privacy suppression and report generation. They also
render every page headlessly with Streamlit's `AppTest`.

### Regenerate the data

```bash
python scripts/build_demo_data.py
```

## Project structure

```
app.py                      # Entry point: page config + navigation (streamlit run app.py)
views/                      # One file per page
  home.py  career_explorer.py  skills_gap.py  location_salary.py  impact.py  about.py
career_insights/            # Application logic (UI-independent where possible)
  data.py                   # CSV loading, schema and referential-integrity checks
  scoring.py                # Match score, readiness and priority scoring (documented formulas)
  impact.py                 # Anonymized aggregates with small-cell suppression
  validation.py             # Free-text skill parsing, aliases, input limits
  charts.py                 # Plotly charts + accessible "chieac" template
  report.py                 # PDF (fpdf2) and CSV report generation
  components.py, ui.py      # Shared Streamlit widgets, styling, citations
data/                       # CSV datasets, DATA_DICTIONARY.md, dataset_catalog.csv
scripts/build_demo_data.py  # Reproducible build of every CSV in data/
tests/                      # pytest suite
.streamlit/config.toml      # Theme and server settings
```

## Data sources

| Dataset | Source | Reference period | Status |
| --- | --- | --- | --- |
| National employment and wages | [BLS Occupational Employment and Wage Statistics](https://www.bls.gov/oes/tables.htm) | May 2023 | Approximate public (verify) |
| Projected growth | [BLS Employment Projections](https://www.bls.gov/emp/) | 2023–2033 | Approximate public (verify) |
| Occupation codes | [BLS SOC 2018](https://www.bls.gov/soc/2018/) / O*NET-SOC | SOC 2018 | Public-derived |
| Skills vocabulary and importance | Curated, informed by [O*NET](https://www.onetcenter.org/database.html) Technology Skills and job postings | O*NET 29.x vocabulary | Demo (curated) |
| Metro wages and employment | Derived from BLS national figures with documented multipliers | May 2023 basis | **Demo estimate** |
| Industry distribution | Illustrative, modelled on BLS OEWS industry estimates and [Data USA](https://datausa.io/) | May 2023 basis | **Demo estimate** |
| Metro names and coordinates | [OMB Metropolitan Statistical Areas](https://www.census.gov/programs-surveys/metro-micro.html) | 2023 | Public-derived |
| Student profiles (Impact page) | Generated by `scripts/build_demo_data.py` | Synthetic | **Synthetic demo, not ChiEAC data** |

The app shows the source, reference period, compile date and status under **every chart**. Full column-level
documentation is in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md), and the machine-readable registry is
[`data/dataset_catalog.csv`](data/dataset_catalog.csv).

**Important:** national figures are approximate transcriptions of published BLS estimates and should be verified
before citing. Metro figures, industry shares and skill ratings are illustrative. Before the dashboard is used for
real advising, replace them with official downloads; the data dictionary explains how.

## Methodology

All formulas and weights are in [`career_insights/scoring.py`](career_insights/scoring.py) and are also explained
in the app.

**Career match score (0–100)**

```
match = 100 × (0.6 × weighted_coverage + 0.4 × specificity_similarity)
```

- **Weighted coverage** = Σ importance of the role's skills you have ÷ Σ importance of all the role's skills.
  Importance is rated 1–5, and skills rated 4–5 count as *core*.
- **Specificity similarity** = cosine similarity between your skill vector and the role's **TF-IDF** weighted
  skill profile (scikit-learn `TfidfTransformer`). Skills shared by many roles (e.g., Communication) count less
  than distinctive ones (e.g., Terraform), so a role ranks higher when your overlap with it is distinctive.
- Every recommendation lists the core skills you have, the supporting skills you have and the core skills to
  build next.

**Readiness score (0–100)** = importance-weighted share of the target role's skills you have.

**Learning priority** for each missing skill:

```
priority = 0.7 × (importance / 5) + 0.3 × breadth
High ≥ 0.65 · Medium ≥ 0.45 · Low otherwise
```

where *breadth* is the share of the dashboard's career paths that also use the skill (its transferability).

**Impact aggregates:** counts, shares and averages only. Groups with fewer than 10 profiles are suppressed.

## Limitations

- **Demonstration data.** Metro-level wages and employment, industry shares and skill-importance ratings are
  illustrative estimates, and the Impact page uses synthetic records.
- **Occupation proxies.** BLS has no standalone code for titles such as Data Analyst, ML Engineer, Data Engineer,
  Cloud Engineer, DevOps Engineer or Technical Project Manager. The dashboard uses the closest SOC code (flagged in
  the UI), so wages and demand for these titles are approximate.
- **Skills only.** Scores ignore experience, degree level, portfolio, interviews, networking, work authorization
  and employer sponsorship, all of which strongly affect outcomes.
- **Point-in-time data.** Wages describe May 2023 and projections cover 2023–2033.
- **Simplified taxonomy.** 46 skills and 16 career paths cannot cover every specialty or seniority level.
- **Not advice.** See the disclaimer above.

## Privacy considerations

- **No accounts and no server-side storage.** Skills and selections live only in the user's Streamlit session
  and are gone when it ends. Nothing is written to disk or a database.
- **Reports are generated in memory** and streamed straight to the user's browser.
- **The Impact page shows aggregates only**, with small-cell suppression (k = 10). It never displays row-level
  records.
- **The demo profile schema holds no direct identifiers.** It has no names, emails, dates of birth, nationality,
  visa status or free text.
- Usage statistics collection is disabled in `.streamlit/config.toml` (`gatherUsageStats = false`).
- **Before connecting real ChiEAC data:** get informed consent, strip or hash identifiers before loading, keep raw
  data out of the repository (`data/private/` is git-ignored), store it in an access-controlled location,
  consider raising the suppression threshold, and review the approach with ChiEAC leadership. Never commit
  `.streamlit/secrets.toml`.

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub (public, or private with Streamlit access granted).
2. Go to <https://share.streamlit.io>, sign in with GitHub and click **Create app → Deploy a public app from
   GitHub**.
3. Select the repository and branch, and set **Main file path** to `app.py`.
4. Under **Advanced settings**, choose Python **3.12**. No secrets are required.
5. Click **Deploy**. Streamlit installs `requirements.txt` and starts the app. Later pushes to the branch
   redeploy automatically.

The app uses only relative paths and bundled CSVs, needs no external API calls, and reads its theme from
`.streamlit/config.toml`, so it runs unchanged on Community Cloud.

## Contributing / extending

- **Add a career path:** add it to `OCCUPATIONS`, `OCCUPATION_SKILLS` and (if it is a new SOC) `BLS_NATIONAL` and
  `INDUSTRY_MIX` in `scripts/build_demo_data.py`. Then rebuild the data and run `pytest`.
- **Add a skill:** add it to `SKILLS` (and optional aliases in `career_insights/validation.py`).
- **Tune the scoring:** adjust the weights at the top of `career_insights/scoring.py`. The UI text updates
  automatically.
