"""Build the CSV files in ``data/`` used by the ChiEAC Career Insights Dashboard.

Why a script?
    Every number in ``data/`` is either (a) transcribed from a public source and
    labelled as *approximate*, or (b) a clearly labelled *demonstration* value
    derived from (a) with the documented, deterministic rules below. Keeping the
    derivation in code makes the data auditable and easy to replace with fresh
    downloads from BLS / O*NET / Data USA.

Run from the repository root::

    python scripts/build_demo_data.py

Outputs (all overwritten):
    data/skills.csv
    data/occupations.csv
    data/occupation_skills.csv
    data/bls_national_occupations.csv
    data/locations.csv
    data/wages_by_location.csv
    data/industry_distribution.csv
    data/demo_profiles.csv
    data/dataset_catalog.csv
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
COMPILED_ON = "2026-09-22"
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# 1. Skills taxonomy (curated for this demo; informed by O*NET Technology
#    Skills and common job-posting vocabulary).
# ---------------------------------------------------------------------------
SKILLS: dict[str, list[tuple[str, str]]] = {
    "Programming": [
        ("Python", "General-purpose language used for analytics, ML, automation and back-end services."),
        ("R", "Statistical programming language used in research and analytics."),
        ("Java", "Object-oriented language common in enterprise back-end systems."),
        ("JavaScript", "Language of the web, used in front-end and Node.js back-end development."),
        ("C++", "Systems language used where performance matters."),
        ("Git", "Version control for collaborating on code."),
    ],
    "Data & Databases": [
        ("SQL", "Querying and managing relational databases."),
        ("Data Modeling", "Designing tables, schemas and relationships for analytics or applications."),
        ("ETL / Data Pipelines", "Extracting, transforming and loading data between systems."),
        ("Spark", "Distributed data processing (Apache Spark / PySpark)."),
        ("Kafka", "Event streaming platform for real-time data (Apache Kafka)."),
        ("Airflow", "Workflow orchestration for scheduled data pipelines."),
        ("NoSQL Databases", "Document, key-value and wide-column stores such as MongoDB or DynamoDB."),
    ],
    "AI & Machine Learning": [
        ("Machine Learning", "Building predictive models such as regression, classification and clustering."),
        ("Deep Learning", "Neural networks for vision, language and other complex data."),
        ("NLP", "Natural language processing: working with text data and language models."),
        ("MLOps", "Deploying, monitoring and maintaining ML models in production."),
    ],
    "Analytics & BI": [
        ("Statistics", "Descriptive and inferential statistics, hypothesis testing, regression."),
        ("Excel", "Spreadsheets, pivot tables, formulas and basic modeling."),
        ("Tableau", "Business intelligence and dashboarding tool."),
        ("Power BI", "Microsoft business intelligence and dashboarding tool."),
        ("Data Visualization", "Communicating insights with clear charts and dashboards."),
        ("A/B Testing", "Designing and analyzing controlled experiments."),
    ],
    "Cloud & DevOps": [
        ("AWS", "Amazon Web Services cloud platform."),
        ("Azure", "Microsoft Azure cloud platform."),
        ("GCP", "Google Cloud Platform."),
        ("Docker", "Packaging applications into containers."),
        ("Kubernetes", "Orchestrating containers at scale."),
        ("CI/CD", "Continuous integration and delivery pipelines."),
        ("Terraform", "Infrastructure as code."),
        ("Linux", "Working with Linux servers and the command line."),
    ],
    "Security & Networking": [
        ("Cybersecurity", "Protecting systems and data; threat detection and response."),
        ("Networking", "TCP/IP, DNS, routing, firewalls and network design."),
        ("Risk & Compliance", "Controls, audits and regulatory frameworks (e.g., SOC 2, HIPAA, SOX)."),
    ],
    "Web & Software Engineering": [
        ("HTML/CSS", "Structuring and styling web pages."),
        ("React", "Popular JavaScript library for building user interfaces."),
        ("REST APIs", "Designing and consuming web APIs."),
        ("Testing / QA Automation", "Unit, integration and automated UI testing."),
        ("System Design", "Designing scalable, reliable software architectures."),
    ],
    "Business & Professional": [
        ("Communication", "Explaining technical work clearly in writing and presentations."),
        ("Problem Solving", "Structuring ambiguous problems and reasoning to solutions."),
        ("Stakeholder Management", "Working with business partners to gather needs and align priorities."),
        ("Agile / Scrum", "Iterative team delivery practices."),
        ("Project Management", "Planning scope, schedule, budget and risk."),
        ("Financial Modeling", "Building models for valuation, forecasting and budgeting."),
        ("Business Acumen", "Understanding how organizations create value and measure success."),
    ],
}

# ---------------------------------------------------------------------------
# 2. Career paths and their closest BLS Standard Occupational Classification
#    (SOC) code. Several modern job titles have no standalone SOC code, so a
#    documented proxy is used; this is stated in the UI.
# ---------------------------------------------------------------------------
# (occupation_id, occupation, category, soc_code, is_proxy, group, description)
OCCUPATIONS = [
    ("data_analyst", "Data Analyst", "Data & Analytics", "15-2031", True, "data",
     "Turns raw data into reports, dashboards and recommendations for business teams."),
    ("data_scientist", "Data Scientist", "Data & Analytics", "15-2051", False, "data",
     "Uses statistics and machine learning to answer questions and build predictive models."),
    ("ml_engineer", "Machine Learning Engineer", "AI & Machine Learning", "15-1221", True, "software",
     "Builds, deploys and maintains machine learning systems in production."),
    ("data_engineer", "Data Engineer", "Data & Analytics", "15-1243", True, "data",
     "Designs and maintains the pipelines and warehouses that make data usable."),
    ("software_engineer", "Software Engineer", "Software Development", "15-1252", False, "software",
     "Designs, builds and tests software applications and services."),
    ("cloud_engineer", "Cloud Engineer", "Cloud & Infrastructure", "15-1241", True, "infra",
     "Designs and operates cloud infrastructure on platforms such as AWS, Azure or GCP."),
    ("devops_engineer", "DevOps / Site Reliability Engineer", "Cloud & Infrastructure", "15-1299", True, "infra",
     "Automates delivery pipelines and keeps production systems reliable."),
    ("qa_engineer", "Software QA Engineer", "Software Development", "15-1253", False, "software",
     "Plans and automates testing to ensure software quality."),
    ("web_developer", "Web Developer", "Software Development", "15-1254", False, "software",
     "Builds websites and web applications, front-end and back-end."),
    ("database_admin", "Database Administrator", "Cloud & Infrastructure", "15-1242", False, "infra",
     "Keeps databases secure, performant, backed up and available."),
    ("security_analyst", "Information Security Analyst", "Cybersecurity", "15-1212", False, "infra",
     "Protects an organization's systems and data from security threats."),
    ("systems_analyst", "Computer Systems Analyst", "Business & Technology", "15-1211", False, "business",
     "Bridges business needs and IT systems by analyzing requirements and designing solutions."),
    ("financial_analyst", "Financial Analyst", "Business & Technology", "13-2051", False, "business",
     "Analyzes financial data to guide investment and business decisions."),
    ("market_research_analyst", "Market Research Analyst", "Business & Technology", "13-1161", False, "business",
     "Studies market conditions, customers and campaigns using surveys and data."),
    ("project_manager", "Technical Project Manager", "Business & Technology", "13-1082", True, "business",
     "Plans and coordinates technology projects, people and timelines."),
    ("statistician", "Statistician", "Data & Analytics", "15-2041", False, "data",
     "Designs studies and applies statistical methods to real-world data."),
]

# Skill importance per occupation: 5 = core, 4 = very important, 3 = important,
# 2 = helpful, 1 = nice to have. Curated demo values informed by O*NET
# Technology Skills / Knowledge profiles and common job-posting requirements.
OCCUPATION_SKILLS: dict[str, dict[str, int]] = {
    "data_analyst": {"SQL": 5, "Excel": 5, "Data Visualization": 5, "Communication": 5, "Statistics": 4,
                     "Tableau": 4, "Power BI": 4, "Python": 4, "Business Acumen": 4, "Problem Solving": 4,
                     "A/B Testing": 3, "Stakeholder Management": 3, "R": 2, "Data Modeling": 2},
    "data_scientist": {"Python": 5, "Statistics": 5, "Machine Learning": 5, "SQL": 4, "Data Visualization": 4,
                       "A/B Testing": 4, "Communication": 4, "Problem Solving": 4, "R": 3, "Deep Learning": 3,
                       "Spark": 3, "Git": 3, "NLP": 2, "AWS": 2},
    "ml_engineer": {"Python": 5, "Machine Learning": 5, "Deep Learning": 5, "MLOps": 5, "Docker": 4, "AWS": 4,
                    "Git": 4, "Kubernetes": 3, "SQL": 3, "Spark": 3, "CI/CD": 3, "System Design": 3,
                    "Statistics": 3, "NLP": 3, "REST APIs": 3, "Linux": 3, "GCP": 2},
    "data_engineer": {"SQL": 5, "Python": 5, "ETL / Data Pipelines": 5, "Spark": 5, "Data Modeling": 5,
                      "Kafka": 4, "Airflow": 4, "AWS": 4, "Azure": 3, "Docker": 3, "NoSQL Databases": 3,
                      "Git": 3, "Linux": 3, "Communication": 3, "CI/CD": 2, "Terraform": 2, "Java": 2},
    "software_engineer": {"Git": 5, "Problem Solving": 5, "Java": 4, "Python": 4, "JavaScript": 4,
                          "System Design": 4, "REST APIs": 4, "Testing / QA Automation": 4, "C++": 3, "SQL": 3,
                          "CI/CD": 3, "Docker": 3, "AWS": 3, "Linux": 3, "Agile / Scrum": 3, "Communication": 3},
    "cloud_engineer": {"AWS": 5, "Terraform": 5, "Linux": 5, "Azure": 4, "Networking": 4, "Docker": 4,
                       "Kubernetes": 4, "CI/CD": 4, "GCP": 3, "Python": 3, "Cybersecurity": 3,
                       "System Design": 3, "Git": 3},
    "devops_engineer": {"CI/CD": 5, "Docker": 5, "Kubernetes": 5, "Linux": 5, "Git": 5, "Terraform": 4,
                        "AWS": 4, "Problem Solving": 4, "Azure": 3, "Python": 3, "Networking": 3,
                        "Cybersecurity": 3, "Communication": 3, "Kafka": 2},
    "qa_engineer": {"Testing / QA Automation": 5, "Python": 4, "Java": 4, "CI/CD": 4, "Git": 4,
                    "Agile / Scrum": 4, "Communication": 4, "Problem Solving": 4, "JavaScript": 3, "SQL": 3,
                    "REST APIs": 3, "Docker": 2},
    "web_developer": {"HTML/CSS": 5, "JavaScript": 5, "React": 5, "REST APIs": 4, "Git": 4, "Problem Solving": 4,
                      "SQL": 3, "Testing / QA Automation": 3, "Agile / Scrum": 3, "Communication": 3,
                      "NoSQL Databases": 2, "AWS": 2},
    "database_admin": {"SQL": 5, "Data Modeling": 4, "Linux": 4, "Problem Solving": 4, "NoSQL Databases": 3,
                       "Cybersecurity": 3, "AWS": 3, "Azure": 3, "Risk & Compliance": 3, "Communication": 3,
                       "Python": 2, "Networking": 2},
    "security_analyst": {"Cybersecurity": 5, "Networking": 5, "Risk & Compliance": 5, "Problem Solving": 5,
                         "Linux": 4, "Communication": 4, "Python": 3, "AWS": 3, "Azure": 3, "SQL": 2,
                         "Stakeholder Management": 2},
    "systems_analyst": {"Business Acumen": 5, "Stakeholder Management": 5, "Communication": 5,
                        "Problem Solving": 5, "SQL": 4, "Agile / Scrum": 4, "Data Modeling": 3,
                        "Project Management": 3, "Excel": 3, "System Design": 3, "REST APIs": 2},
    "financial_analyst": {"Excel": 5, "Financial Modeling": 5, "Business Acumen": 5, "Communication": 5,
                          "Statistics": 3, "SQL": 3, "Python": 3, "Power BI": 3, "Tableau": 3,
                          "Data Visualization": 3, "Stakeholder Management": 3, "Risk & Compliance": 3},
    "market_research_analyst": {"Excel": 5, "Communication": 5, "Statistics": 4, "Data Visualization": 4,
                                "A/B Testing": 4, "Business Acumen": 4, "SQL": 3, "R": 3, "Tableau": 3,
                                "Power BI": 3, "Problem Solving": 3, "Python": 2},
    "project_manager": {"Project Management": 5, "Agile / Scrum": 5, "Stakeholder Management": 5,
                        "Communication": 5, "Business Acumen": 4, "Problem Solving": 4, "Excel": 3,
                        "Risk & Compliance": 3, "AWS": 2, "System Design": 2},
    "statistician": {"Statistics": 5, "R": 5, "Python": 4, "Data Visualization": 4, "A/B Testing": 4,
                     "Communication": 4, "Problem Solving": 4, "SQL": 3, "Machine Learning": 3, "Excel": 3},
}

# ---------------------------------------------------------------------------
# 3. National occupation figures. APPROXIMATE values transcribed from:
#    - BLS Occupational Employment and Wage Statistics (OEWS), May 2023,
#      national cross-industry estimates (employment, 10th/50th/90th pct wage)
#    - BLS Employment Projections 2023-2033 (projected % change). Where BLS
#      publishes a combined projection (e.g., software developers + QA), the
#      combined figure is used.
#    These are provided for demonstration and must be verified against
#    https://www.bls.gov/oes/ and https://www.bls.gov/emp/ before citing.
# ---------------------------------------------------------------------------
# soc_code: (soc_title, employment, p10, median, p90, growth_pct, typical_entry_education)
BLS_NATIONAL = {
    "15-2031": ("Operations Research Analysts", 109_660, 50_020, 83_640, 146_830, 23, "Bachelor's degree"),
    "15-2051": ("Data Scientists", 192_710, 61_070, 108_020, 184_090, 36, "Bachelor's degree"),
    "15-1221": ("Computer and Information Research Scientists", 36_600, 82_240, 145_080, 233_110, 26, "Master's degree"),
    "15-1243": ("Database Architects", 61_430, 79_140, 134_700, 200_690, 9, "Bachelor's degree"),
    "15-1252": ("Software Developers", 1_656_880, 77_020, 132_270, 208_620, 17, "Bachelor's degree"),
    "15-1241": ("Computer Network Architects", 175_770, 77_990, 129_840, 197_000, 13, "Bachelor's degree"),
    "15-1299": ("Computer Occupations, All Other", 438_060, 55_180, 104_420, 168_900, 10, "Bachelor's degree"),
    "15-1253": ("Software Quality Assurance Analysts and Testers", 205_590, 58_120, 101_800, 162_520, 17, "Bachelor's degree"),
    "15-1254": ("Web Developers", 85_350, 44_760, 84_960, 153_550, 8, "Bachelor's degree"),
    "15-1242": ("Database Administrators", 78_110, 54_830, 101_510, 157_760, 9, "Bachelor's degree"),
    "15-1212": ("Information Security Analysts", 175_350, 69_660, 120_360, 186_420, 33, "Bachelor's degree"),
    "15-1211": ("Computer Systems Analysts", 511_310, 63_330, 103_800, 161_980, 11, "Bachelor's degree"),
    "13-2051": ("Financial and Investment Analysts", 331_530, 60_540, 99_890, 176_220, 9, "Bachelor's degree"),
    "13-1161": ("Market Research Analysts and Marketing Specialists", 899_250, 40_900, 74_680, 138_730, 8, "Bachelor's degree"),
    "13-1082": ("Project Management Specialists", 834_350, 55_750, 98_580, 159_150, 7, "Bachelor's degree"),
    "15-2041": ("Statisticians", 30_870, 59_920, 104_110, 169_320, 11, "Master's degree"),
}

# ---------------------------------------------------------------------------
# 4. Locations (metro areas use OMB MSA names). Sub-national values are DEMO
#    estimates computed as:
#      employment = national_employment * emp_share * lq_tilt[group]
#      wage       = national_wage * wage_factor * wage_tilt[group]
#    where emp_share approximates the metro's share of total US employment and
#    lq_tilt acts as a location quotient (concentration relative to the US).
# ---------------------------------------------------------------------------
# location_id: (name, short_name, state, lat, lon, emp_share, wage_factor,
#               {group: (lq_tilt, wage_tilt)})
LOCATIONS = {
    "us": ("United States (national)", "United States", "US", 39.83, -98.58, 1.0, 1.0, {}),
    "chicago": ("Chicago-Naperville-Elgin, IL-IN-WI", "Chicago", "IL", 41.88, -87.63, 0.0295, 1.02,
                {"data": (1.10, 1.00), "business": (1.15, 1.02), "software": (0.85, 0.98), "infra": (1.00, 1.00)}),
    "new_york": ("New York-Newark-Jersey City, NY-NJ-PA", "New York", "NY", 40.71, -74.01, 0.0625, 1.14,
                 {"data": (1.15, 1.04), "business": (1.35, 1.08), "software": (0.95, 1.02), "infra": (0.95, 1.00)}),
    "san_francisco": ("San Francisco-Oakland-Fremont, CA", "San Francisco", "CA", 37.77, -122.42, 0.0158, 1.33,
                      {"data": (1.80, 1.06), "business": (1.05, 1.00), "software": (2.10, 1.08), "infra": (1.20, 1.02)}),
    "seattle": ("Seattle-Tacoma-Bellevue, WA", "Seattle", "WA", 47.61, -122.33, 0.0135, 1.20,
                {"data": (1.50, 1.04), "business": (0.95, 0.98), "software": (2.40, 1.06), "infra": (1.40, 1.02)}),
    "austin": ("Austin-Round Rock-San Marcos, TX", "Austin", "TX", 30.27, -97.74, 0.0090, 1.03,
               {"data": (1.30, 1.00), "business": (0.95, 0.97), "software": (1.90, 1.02), "infra": (1.30, 1.00)}),
    "boston": ("Boston-Cambridge-Newton, MA-NH", "Boston", "MA", 42.36, -71.06, 0.0182, 1.16,
               {"data": (1.55, 1.04), "business": (1.10, 1.02), "software": (1.40, 1.02), "infra": (1.05, 1.00)}),
    "dallas": ("Dallas-Fort Worth-Arlington, TX", "Dallas", "TX", 32.78, -96.80, 0.0255, 1.00,
               {"data": (1.05, 0.99), "business": (1.15, 1.00), "software": (1.10, 0.99), "infra": (1.20, 1.00)}),
    "atlanta": ("Atlanta-Sandy Springs-Roswell, GA", "Atlanta", "GA", 33.75, -84.39, 0.0185, 0.98,
                {"data": (1.10, 0.99), "business": (1.10, 0.99), "software": (1.20, 0.98), "infra": (1.25, 1.00)}),
    "washington_dc": ("Washington-Arlington-Alexandria, DC-VA-MD-WV", "Washington, DC", "DC", 38.91, -77.04, 0.0212, 1.15,
                      {"data": (1.45, 1.04), "business": (1.30, 1.04), "software": (1.35, 1.02), "infra": (1.90, 1.06)}),
}

# ---------------------------------------------------------------------------
# 5. Industry mix (DEMO). Illustrative shares of employment by industry for
#    each SOC, modelled on the structure of BLS OEWS industry-specific
#    estimates / Data USA "Industries" profiles. Shares sum to 100.
# ---------------------------------------------------------------------------
INDUSTRY_MIX = {
    "15-2031": {"Finance & Insurance": 24, "Professional, Scientific & Technical Services": 22, "Federal Government": 14,
                "Management of Companies": 12, "Manufacturing": 10, "Transportation & Warehousing": 8, "Other": 10},
    "15-2051": {"Professional, Scientific & Technical Services": 30, "Finance & Insurance": 20, "Information": 14,
                "Management of Companies": 10, "Health Care": 8, "Manufacturing": 6, "Other": 12},
    "15-1221": {"Professional, Scientific & Technical Services": 38, "Information": 16, "Federal Government": 14,
                "Educational Services": 10, "Manufacturing": 10, "Other": 12},
    "15-1243": {"Professional, Scientific & Technical Services": 36, "Finance & Insurance": 16, "Information": 12,
                "Management of Companies": 10, "Health Care": 8, "Other": 18},
    "15-1252": {"Professional, Scientific & Technical Services": 38, "Information": 16, "Finance & Insurance": 10,
                "Manufacturing": 10, "Management of Companies": 8, "Other": 18},
    "15-1241": {"Professional, Scientific & Technical Services": 30, "Information": 22, "Finance & Insurance": 10,
                "Management of Companies": 8, "Educational Services": 6, "Other": 24},
    "15-1299": {"Professional, Scientific & Technical Services": 34, "Information": 12, "Federal Government": 12,
                "Finance & Insurance": 10, "Manufacturing": 8, "Other": 24},
    "15-1253": {"Professional, Scientific & Technical Services": 40, "Information": 14, "Finance & Insurance": 12,
                "Manufacturing": 8, "Management of Companies": 8, "Other": 18},
    "15-1254": {"Professional, Scientific & Technical Services": 36, "Information": 14, "Retail Trade": 8,
                "Educational Services": 8, "Finance & Insurance": 6, "Other": 28},
    "15-1242": {"Professional, Scientific & Technical Services": 28, "Finance & Insurance": 14, "Educational Services": 12,
                "Health Care": 10, "Government": 10, "Other": 26},
    "15-1212": {"Professional, Scientific & Technical Services": 34, "Finance & Insurance": 18, "Government": 12,
                "Management of Companies": 10, "Information": 8, "Other": 18},
    "15-1211": {"Professional, Scientific & Technical Services": 34, "Finance & Insurance": 16, "Government": 12,
                "Health Care": 10, "Management of Companies": 8, "Other": 20},
    "13-2051": {"Finance & Insurance": 46, "Professional, Scientific & Technical Services": 16, "Management of Companies": 14,
                "Manufacturing": 8, "Government": 4, "Other": 12},
    "13-1161": {"Professional, Scientific & Technical Services": 28, "Management of Companies": 10, "Retail Trade": 10,
                "Information": 10, "Finance & Insurance": 8, "Other": 34},
    "13-1082": {"Professional, Scientific & Technical Services": 30, "Construction": 10, "Finance & Insurance": 10,
                "Government": 10, "Manufacturing": 10, "Other": 30},
    "15-2041": {"Federal Government": 24, "Professional, Scientific & Technical Services": 22, "Educational Services": 18,
                "Health Care": 12, "Finance & Insurance": 10, "Other": 14},
}

# ---------------------------------------------------------------------------
# 6. Synthetic demo profiles for the ChiEAC Impact page. Entirely synthetic:
#    no real person, record or ChiEAC program data is represented.
# ---------------------------------------------------------------------------
N_PROFILES = 480
QUARTERS = ["2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"]
LOCATION_WEIGHTS = {"chicago": 42, "new_york": 10, "dallas": 8, "seattle": 7, "san_francisco": 7,
                    "boston": 7, "austin": 6, "atlanta": 6, "washington_dc": 7}
TARGET_WEIGHTS = {"data_analyst": 22, "data_scientist": 16, "software_engineer": 15, "ml_engineer": 10,
                  "data_engineer": 9, "cloud_engineer": 5, "devops_engineer": 3, "qa_engineer": 3,
                  "web_developer": 4, "database_admin": 2, "security_analyst": 4, "systems_analyst": 2,
                  "financial_analyst": 3, "market_research_analyst": 1, "project_manager": 1, "statistician": 1}
EDUCATION_WEIGHTS = {"Bachelor's (in progress)": 18, "Bachelor's (completed)": 20,
                     "Master's (in progress)": 38, "Master's (completed)": 20, "Doctorate": 4}
FIELD_WEIGHTS = {"Computer Science": 30, "Data Science / Analytics": 24, "Information Systems": 12,
                 "Engineering": 12, "Business / Finance": 12, "Mathematics / Statistics": 8, "Other": 2}


def _write(name: str, header: list[str], rows: list[list]) -> None:
    path = DATA_DIR / name
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"wrote {path.relative_to(DATA_DIR.parent)} ({len(rows)} rows)")


def _weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    keys = list(weights)
    return rng.choices(keys, weights=[weights[k] for k in keys], k=1)[0]


def build() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    all_skills = {s for group in SKILLS.values() for s, _ in group}

    # Guard against typos: every occupation skill must exist in the taxonomy.
    for occ, skills in OCCUPATION_SKILLS.items():
        unknown = set(skills) - all_skills
        if unknown:
            raise ValueError(f"{occ} references unknown skills: {unknown}")

    _write("skills.csv", ["skill", "skill_category", "description"],
           [[s, cat, desc] for cat, group in SKILLS.items() for s, desc in group])

    occ_rows = []
    for occ_id, name, category, soc, is_proxy, group, desc in OCCUPATIONS:
        occ_rows.append([occ_id, name, category, soc, BLS_NATIONAL[soc][0], "yes" if is_proxy else "no",
                         group, BLS_NATIONAL[soc][6], desc])
    _write("occupations.csv", ["occupation_id", "occupation", "category", "soc_code", "soc_title",
                               "soc_is_proxy", "location_group", "typical_entry_education", "description"], occ_rows)

    _write("occupation_skills.csv", ["occupation_id", "skill", "importance"],
           [[occ, s, imp] for occ, skills in OCCUPATION_SKILLS.items()
            for s, imp in sorted(skills.items(), key=lambda kv: (-kv[1], kv[0]))])

    _write("bls_national_occupations.csv",
           ["soc_code", "soc_title", "employment", "wage_p10", "wage_median", "wage_p90",
            "projected_growth_pct_2023_2033", "typical_entry_education", "reference_period", "data_status"],
           [[soc, t, e, p10, med, p90, g, edu, "OEWS May 2023; EP 2023-2033", "Approximate public (verify)"]
            for soc, (t, e, p10, med, p90, g, edu) in BLS_NATIONAL.items()])

    _write("locations.csv", ["location_id", "location_name", "short_name", "area_type", "state", "lat", "lon"],
           [[lid, n, sn, "National" if lid == "us" else "Metropolitan Statistical Area", st, lat, lon]
            for lid, (n, sn, st, lat, lon, *_rest) in LOCATIONS.items()])

    # Wages by location. p25 / p75 are interpolated (BLS publishes them, but
    # they were not transcribed here) and therefore always labelled demo.
    soc_group = {soc: group for _, _, _, soc, _, group, _ in OCCUPATIONS}
    wage_rows = []
    for soc, (_t, emp, p10, med, p90, _g, _e) in BLS_NATIONAL.items():
        group = soc_group[soc]
        for lid, (_n, _sn, _st, _lat, _lon, share, wf, tilts) in LOCATIONS.items():
            lq, wt = tilts.get(group, (1.0, 1.0))
            factor = wf * wt
            l_emp = round(emp * share * lq, -1)
            l_p10, l_med, l_p90 = (round(v * factor, -1) for v in (p10, med, p90))
            l_p25 = round(l_med - 0.45 * (l_med - l_p10), -1)
            l_p75 = round(l_med + 0.45 * (l_p90 - l_med), -1)
            status = "Approximate public (verify); p25/p75 interpolated" if lid == "us" else "Demo estimate"
            wage_rows.append([soc, lid, int(l_emp), int(l_p10), int(l_p25), int(l_med), int(l_p75), int(l_p90),
                              round(lq, 2), "May 2023 basis", status])
    _write("wages_by_location.csv",
           ["soc_code", "location_id", "employment", "wage_p10", "wage_p25", "wage_median", "wage_p75",
            "wage_p90", "location_quotient", "reference_period", "data_status"], wage_rows)

    ind_rows = []
    for soc, mix in INDUSTRY_MIX.items():
        if sum(mix.values()) != 100:
            raise ValueError(f"Industry mix for {soc} does not sum to 100")
        ind_rows.extend([soc, ind, share, "Demo estimate"] for ind, share in mix.items())
    _write("industry_distribution.csv", ["soc_code", "industry", "share_pct", "data_status"], ind_rows)

    # Synthetic profiles: skills are sampled from the target occupation's
    # profile (higher importance -> more likely) plus a few unrelated skills.
    rng = random.Random(RANDOM_SEED)
    skill_list = sorted(all_skills)
    profile_rows = []
    for i in range(1, N_PROFILES + 1):
        quarter = QUARTERS[min(len(QUARTERS) - 1, int(rng.random() ** 0.8 * len(QUARTERS)))]
        target = _weighted_choice(rng, TARGET_WEIGHTS)
        # Later cohorts are modelled as slightly better prepared, so the demo
        # "skills gap trend" chart has something to show. This is synthetic.
        maturity = 0.08 * QUARTERS.index(quarter) / (len(QUARTERS) - 1)
        skills = {s for s, imp in OCCUPATION_SKILLS[target].items()
                  if rng.random() < 0.12 + 0.11 * imp + maturity}
        skills.update(rng.sample(skill_list, k=rng.randint(1, 4)))
        profile_rows.append([f"DEMO-{i:04d}", quarter, _weighted_choice(rng, LOCATION_WEIGHTS),
                             _weighted_choice(rng, EDUCATION_WEIGHTS), _weighted_choice(rng, FIELD_WEIGHTS),
                             target, ";".join(sorted(skills)), "yes"])
    _write("demo_profiles.csv", ["record_id", "cohort_quarter", "location_id", "education_level",
                                 "field_of_study", "target_occupation_id", "skills", "is_synthetic"], profile_rows)

    catalog = [
        ["skills", "skills.csv", "Skills taxonomy", "Curated for this project (informed by O*NET Technology Skills)",
         "https://www.onetcenter.org/database.html", "O*NET 29.x vocabulary", COMPILED_ON, "Demo (curated)",
         "Skill names and groupings are simplified for usability."],
        ["occupations", "occupations.csv", "Career paths and SOC crosswalk", "BLS SOC 2018 / O*NET-SOC",
         "https://www.bls.gov/soc/2018/", "SOC 2018", COMPILED_ON, "Public-derived",
         "Some titles (e.g., Data Analyst, ML Engineer) use the closest SOC as a proxy; flagged in soc_is_proxy."],
        ["occupation_skills", "occupation_skills.csv", "Skill importance by career path",
         "Curated for this project (informed by O*NET Technology Skills and job postings)",
         "https://www.onetonline.org/", "O*NET 29.x vocabulary", COMPILED_ON, "Demo (curated)",
         "Importance ratings (1-5) are editorial judgments, not O*NET scores."],
        ["bls_national", "bls_national_occupations.csv", "National employment, wages and projections",
         "U.S. Bureau of Labor Statistics (OEWS; Employment Projections)",
         "https://www.bls.gov/oes/tables.htm", "May 2023 (OEWS); 2023-2033 (EP)", COMPILED_ON,
         "Approximate public (verify)", "Transcribed approximations; verify against the source before citing."],
        ["wages_by_location", "wages_by_location.csv", "Employment and wages by metro area",
         "Derived from BLS OEWS national figures using documented multipliers",
         "https://www.bls.gov/oes/current/oessrcma.htm", "May 2023 basis", COMPILED_ON, "Demo estimate",
         "Metro rows are illustrative estimates, NOT official BLS metro estimates. National row approximates BLS."],
        ["industry_distribution", "industry_distribution.csv", "Industry distribution by occupation",
         "Illustrative, modelled on BLS OEWS industry estimates and Data USA profiles",
         "https://datausa.io/", "May 2023 basis", COMPILED_ON, "Demo estimate",
         "Shares are illustrative and rounded."],
        ["locations", "locations.csv", "Metropolitan areas", "U.S. OMB Metropolitan Statistical Area names",
         "https://www.census.gov/programs-surveys/metro-micro.html", "2023 delineations", COMPILED_ON,
         "Public-derived", "Coordinates are approximate city centers."],
        ["demo_profiles", "demo_profiles.csv", "Synthetic student profiles (ChiEAC Impact demo)",
         "Generated by scripts/build_demo_data.py (random seed 42)", "", "Synthetic", COMPILED_ON,
         "Synthetic demo", "NOT ChiEAC data. No real people are represented."],
    ]
    _write("dataset_catalog.csv", ["dataset_id", "file", "title", "publisher", "source_url", "reference_period",
                                   "compiled_on", "data_status", "notes"], catalog)


if __name__ == "__main__":
    build()
