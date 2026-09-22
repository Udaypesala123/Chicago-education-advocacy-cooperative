"""Generate the downloadable career-readiness report (PDF and CSV).

Reports are built in memory from the user's current selections only. Nothing
is written to disk or sent anywhere.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import date

import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

from . import AUTHOR, DISCLAIMER


@dataclass
class ReportData:
    skills: list[str]
    recommendations: pd.DataFrame  # from scoring.recommend_occupations
    target_occupation: str | None = None
    readiness: float | None = None
    gap: pd.DataFrame | None = None  # from scoring.gap_analysis
    location: str | None = None
    salary: dict | None = None  # median, p10, p90, employment, growth, data_status
    generated_on: str = field(default_factory=lambda: date.today().isoformat())


def to_csv(r: ReportData) -> bytes:
    """Tidy long-format CSV: section, item, metric, value."""
    rows: list[list] = [["meta", "generated_on", "", r.generated_on]]
    rows += [["your_skills", s, "", "yes"] for s in r.skills]
    for _, rec in r.recommendations.iterrows():
        rows.append(["career_match", rec["occupation"], "match_score", rec["match_score"]])
        rows.append(["career_match", rec["occupation"], "weighted_coverage_pct", rec["weighted_coverage"]])
        rows.append(["career_match", rec["occupation"], "missing_core_skills", "; ".join(rec["missing_core_skills"])])
    if r.target_occupation and r.gap is not None:
        rows.append(["skills_gap", r.target_occupation, "readiness_pct", r.readiness])
        for _, g in r.gap.iterrows():
            rows.append(["skills_gap", g["skill"], "importance", g["importance"]])
            rows.append(["skills_gap", g["skill"], "status", g["priority"]])
    if r.salary and r.location:
        for k, v in r.salary.items():
            rows.append(["location_salary", f"{r.target_occupation} - {r.location}", k, v])
    rows.append(["meta", "disclaimer", "", DISCLAIMER])
    buf = io.StringIO()
    pd.DataFrame(rows, columns=["section", "item", "metric", "value"]).to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def _latin1(text: str) -> str:
    """Core PDF fonts are Latin-1 only; replace common Unicode punctuation."""
    replacements = {"\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                    "\u2022": "-", "\u2026": "...", "\u2265": ">=", "\u2264": "<="}
    for a, b in replacements.items():
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


class _PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(27, 58, 92)
        self.cell(0, 8, "ChiEAC Career Insights Dashboard - Career-Readiness Report",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(47, 109, 181)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, f"ChiEAC Career Insights Dashboard by {AUTHOR} - educational use only. Page {self.page_no()}", align="C")


def _h(pdf: FPDF, text: str) -> None:
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(27, 58, 92)
    pdf.cell(0, 8, _latin1(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(31, 41, 55)


def _p(pdf: FPDF, text: str, size: int = 10, style: str = "") -> None:
    pdf.set_font("Helvetica", style, size)
    pdf.multi_cell(0, 5, _latin1(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _table(pdf: FPDF, header: list[str], rows: list[list[str]], widths: list[float]) -> None:
    pdf.set_font("Helvetica", "", 9)
    heading = FontFace(emphasis="BOLD", color=(27, 58, 92), fill_color=(232, 238, 246))
    with pdf.table(col_widths=widths, text_align="LEFT", line_height=5.5, headings_style=heading,
                   borders_layout="HORIZONTAL_LINES") as table:
        head = table.row()
        for h in header:
            head.cell(_latin1(h))
        for r in rows:
            row = table.row()
            for v in r:
                row.cell(_latin1(str(v)))


def to_pdf(r: ReportData) -> bytes:
    pdf = _PDF(format="Letter")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 12, 15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(27, 58, 92)
    pdf.cell(0, 10, "Your Career-Readiness Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    _p(pdf, f"Generated on {r.generated_on}. This report reflects only the selections you made in the dashboard.",
       9)

    _h(pdf, "1. Your skills")
    _p(pdf, ", ".join(r.skills) if r.skills else "No skills selected.")

    _h(pdf, "2. Top career matches")
    if r.recommendations.empty:
        _p(pdf, "Select skills in Career Explorer to see matches.")
    else:
        rows = [[rec["occupation"], f"{rec['match_score']:.0f}", f"{rec['weighted_coverage']:.0f}%",
                 ", ".join(rec["missing_core_skills"][:4]) or "-"]
                for _, rec in r.recommendations.head(6).iterrows()]
        _table(pdf, ["Career path", "Match", "Coverage", "Core skills to build"], rows, [52, 16, 20, 92])

    if r.target_occupation and r.gap is not None:
        _h(pdf, f"3. Skills gap: {r.target_occupation}")
        _p(pdf, f"Readiness score: {r.readiness:.0f}/100 (importance-weighted share of the role's skills you have).")
        have = r.gap[r.gap["has_skill"]]["skill"].tolist()
        _p(pdf, "Skills you already have: " + (", ".join(have) if have else "none yet"))
        missing = r.gap[~r.gap["has_skill"]]
        if not missing.empty:
            pdf.ln(1)
            rows = [[g["skill"], g["skill_category"], f"{g['importance']}/5", g["priority"]]
                    for _, g in missing.iterrows()]
            _table(pdf, ["Skill to develop", "Category", "Importance", "Priority"], rows, [60, 60, 25, 35])

    if r.salary and r.location:
        _h(pdf, f"4. Salary and demand snapshot: {r.location}")
        s = r.salary
        _p(pdf, f"Median annual wage: ${s['median']:,.0f} (10th-90th percentile: ${s['p10']:,.0f} - ${s['p90']:,.0f}). "
                f"Estimated employment: {s['employment']:,.0f}. National projected growth 2023-2033: {s['growth']}%.")
        _p(pdf, f"Data status: {s['data_status']}. Figures are for the occupation's BLS SOC code "
                f"({s['soc']}); see the dashboard's data sources.", 8, "I")

    _h(pdf, "Methodology")
    _p(pdf, "Match score = 100 x (0.6 x weighted skill coverage + 0.4 x TF-IDF cosine similarity). "
            "Priority = 0.7 x (importance / 5) + 0.3 x breadth (share of career paths using the skill); "
            "High >= 0.65, Medium >= 0.45, else Low.", 9)
    _h(pdf, "Disclaimer")
    _p(pdf, DISCLAIMER, 9, "I")
    return bytes(pdf.output())
