"""Plotly chart builders with a shared, accessible visual style.

The palette is colorblind-friendly (based on Okabe-Ito / Tableau-10 hues with
sufficient contrast on white). Every chart has a title, labelled axes, and
hover text, and does not rely on color alone (values are also printed).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

NAVY = "#1B3A5C"
BLUE = "#2F6DB5"
TEAL = "#2A9D8F"
ORANGE = "#E07A1F"
RED = "#C2413B"
GRAY = "#8A94A6"
LIGHT = "#E8EEF6"
PALETTE = [BLUE, TEAL, ORANGE, "#7B5EA7", RED, "#4C9F38", "#D4A017", NAVY, GRAY]
PRIORITY_COLORS = {"High": RED, "Medium": ORANGE, "Low": GRAY, "Already have": TEAL}
SEQUENTIAL = [[0, "#F2F6FB"], [0.5, "#7FA7D9"], [1, NAVY]]

pio.templates["chieac"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Inter, Segoe UI, Helvetica, Arial, sans-serif", size=13, color="#1F2937"),
        title=dict(font=dict(size=16, color=NAVY), x=0, xanchor="left"),
        colorway=PALETTE,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=56, b=10),
        xaxis=dict(gridcolor="#EEF1F5", zerolinecolor="#D5DBE3", automargin=True),
        yaxis=dict(gridcolor="#EEF1F5", zerolinecolor="#D5DBE3", automargin=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(font_size=13),
    )
)
pio.templates.default = "chieac"


def _money(v: float) -> str:
    return f"${v / 1000:,.0f}k"


def match_scores(recs: pd.DataFrame) -> go.Figure:
    df = recs.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=df["match_score"], y=df["occupation"], orientation="h", marker_color=BLUE,
        text=[f"{v:.0f}" for v in df["match_score"]], textposition="outside",
        customdata=df[["weighted_coverage", "specificity_similarity"]],
        hovertemplate="<b>%{y}</b><br>Match score: %{x:.1f}<br>Weighted coverage: %{customdata[0]:.1f}%"
                      "<br>Specificity similarity: %{customdata[1]:.1f}%<extra></extra>",
    ))
    fig.update_layout(title="Career match score (0–100)", xaxis=dict(range=[0, 105], title="Match score"),
                      yaxis_title=None, height=max(260, 44 * len(df) + 80))
    return fig


def coverage_radar(cov: pd.DataFrame, title: str) -> go.Figure:
    cats = [c.replace(" & ", " &<br>") for c in cov["skill_category"]]
    vals = cov["coverage_pct"].tolist()
    if len(cats) < 3:  # a radar needs >= 3 axes; fall back to a bar chart
        fig = go.Figure(go.Bar(x=cats, y=vals, marker_color=TEAL, text=[f"{v:.0f}%" for v in vals],
                               textposition="outside"))
        fig.update_layout(title=title, yaxis=dict(range=[0, 110], title="Coverage %"))
        return fig
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[100] * len(cats) + [100], theta=cats + cats[:1], name="Role profile",
                                  line=dict(color=GRAY, dash="dot"), fill=None, hoverinfo="skip"))
    fig.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], name="Your coverage",
                                  fill="toself", line=dict(color=TEAL), fillcolor="rgba(42,157,143,0.25)",
                                  hovertemplate="%{theta}: %{r:.0f}%<extra></extra>"))
    fig.update_layout(title=dict(text=f"{title}<br><sup>Shaded = your coverage · dotted = full role profile</sup>"),
                      height=470, margin=dict(l=70, r=70, t=90, b=40), showlegend=False,
                      polar=dict(radialaxis=dict(range=[0, 100], ticksuffix="%", gridcolor="#E3E8EF", angle=45,
                                                 tickangle=45, tickfont=dict(size=10, color="#6B7280")),
                                 angularaxis=dict(gridcolor="#E3E8EF")))
    return fig


def gap_bars(gap: pd.DataFrame) -> go.Figure:
    df = gap.sort_values(["importance", "skill"], ascending=[True, False])
    fig = go.Figure()
    for status in ["Already have", "High", "Medium", "Low"]:
        sub = df[df["priority"] == status]
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            x=sub["importance"], y=sub["skill"], orientation="h", name=status,
            marker_color=PRIORITY_COLORS[status], text=[status] * len(sub), textposition="inside",
            insidetextanchor="start",
            hovertemplate="<b>%{y}</b><br>Importance: %{x}/5<br>Status: " + status + "<extra></extra>",
        ))
    fig.update_layout(title="Skills for this role, by importance and your status", barmode="overlay",
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
                      margin=dict(l=10, r=10, t=90, b=10),
                      xaxis=dict(title="Importance to role (1–5)", range=[0, 5.3], dtick=1),
                      yaxis_title=None, height=max(320, 26 * len(df) + 100),
                      yaxis=dict(categoryorder="array", categoryarray=df["skill"].tolist()))
    return fig


def salary_ranges(df: pd.DataFrame, label_col: str, title: str) -> go.Figure:
    """Floating bars: thin = 10th–90th percentile, thick = 25th–75th, dot = median."""
    df = df.sort_values("wage_median")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=df[label_col], x=df["wage_p90"] - df["wage_p10"], base=df["wage_p10"],
                         orientation="h", marker_color=LIGHT, name="10th–90th percentile", width=0.55,
                         hovertemplate="%{y}<br>10th: $%{base:,.0f}<br>90th: $%{customdata:,.0f}<extra></extra>",
                         customdata=df["wage_p90"]))
    fig.add_trace(go.Bar(y=df[label_col], x=df["wage_p75"] - df["wage_p25"], base=df["wage_p25"],
                         orientation="h", marker_color="#9DB9DE", name="25th–75th percentile", width=0.55,
                         hovertemplate="%{y}<br>25th: $%{base:,.0f}<br>75th: $%{customdata:,.0f}<extra></extra>",
                         customdata=df["wage_p75"]))
    fig.add_trace(go.Scatter(y=df[label_col], x=df["wage_median"], mode="markers+text", name="Median",
                             marker=dict(color=NAVY, size=11, symbol="diamond"),
                             text=[_money(v) for v in df["wage_median"]], textposition="top center",
                             hovertemplate="%{y}<br>Median: $%{x:,.0f}<extra></extra>"))
    fig.update_layout(title=title, barmode="overlay", xaxis=dict(title="Annual wage (USD)", tickprefix="$",
                      tickformat=",.0f"), yaxis_title=None, height=max(300, 48 * len(df) + 110))
    return fig


def employment_demand(df: pd.DataFrame, label_col: str, title: str) -> go.Figure:
    df = df.sort_values("employment")
    fig = go.Figure(go.Bar(
        x=df["employment"], y=df[label_col], orientation="h",
        marker=dict(color=df["location_quotient"], colorscale=SEQUENTIAL, cmin=0.5, cmax=2.5,
                    colorbar=dict(title="Location<br>quotient", thickness=12)),
        text=[f"{v:,.0f}" for v in df["employment"]], textposition="outside",
        customdata=df["location_quotient"],
        hovertemplate="<b>%{y}</b><br>Employment: %{x:,.0f}<br>Location quotient: %{customdata:.2f}<extra></extra>",
    ))
    fig.update_layout(title=title, xaxis=dict(title="Estimated employment", tickformat=","), yaxis_title=None,
                      height=max(300, 42 * len(df) + 110))
    return fig


def wage_growth_scatter(df: pd.DataFrame, highlight: str | None = None) -> go.Figure:
    colors = [ORANGE if o == highlight else BLUE for o in df["occupation"]]
    fig = go.Figure(go.Scatter(
        x=df["projected_growth_pct_2023_2033"], y=df["wage_median"], mode="markers+text",
        text=df["occupation"], textposition="top center", textfont=dict(size=11),
        marker=dict(size=(df["employment"] ** 0.5) / 12 + 8, color=colors, opacity=0.8,
                    line=dict(color="white", width=1)),
        customdata=df[["employment"]],
        hovertemplate="<b>%{text}</b><br>Median wage: $%{y:,.0f}<br>Projected growth: %{x}%"
                      "<br>Employment: %{customdata[0]:,.0f}<extra></extra>",
    ))
    fig.update_layout(title="Median wage vs. projected growth (bubble size = employment)",
                      xaxis=dict(title="Projected employment change 2023–2033 (%)", ticksuffix="%"),
                      yaxis=dict(title="Median annual wage", tickprefix="$", tickformat=",.0f"), height=520)
    return fig


def required_skills(df: pd.DataFrame, title: str) -> go.Figure:
    df = df.sort_values(["importance", "skill"], ascending=[True, False])
    fig = go.Figure(go.Bar(x=df["importance"], y=df["skill"], orientation="h", marker_color=TEAL,
                           text=df["importance"], textposition="outside",
                           hovertemplate="%{y}: %{x}/5<extra></extra>"))
    fig.update_layout(title=title, xaxis=dict(title="Importance (1–5)", range=[0, 5.6], dtick=1),
                      yaxis_title=None, height=max(300, 24 * len(df) + 100))
    return fig


def industry_distribution(df: pd.DataFrame, title: str) -> go.Figure:
    df = df.sort_values("share_pct")
    fig = go.Figure(go.Bar(x=df["share_pct"], y=df["industry"], orientation="h", marker_color=ORANGE,
                           text=[f"{v:.0f}%" for v in df["share_pct"]], textposition="outside",
                           hovertemplate="%{y}: %{x:.0f}%<extra></extra>"))
    fig.update_layout(title=title, xaxis=dict(title="Share of employment (%)", ticksuffix="%",
                      range=[0, df["share_pct"].max() * 1.2]), yaxis_title=None,
                      height=max(280, 40 * len(df) + 100))
    return fig


def heatmap(table: pd.DataFrame, title: str, colorbar_title: str, fmt: str, zmin=None, zmax=None,
            height: int | None = None) -> go.Figure:
    text = table.map(lambda v: "" if pd.isna(v) else format(v, fmt))
    fig = go.Figure(go.Heatmap(
        z=table.values, x=table.columns.tolist(), y=table.index.tolist(), colorscale=SEQUENTIAL,
        zmin=zmin, zmax=zmax, text=text.values, texttemplate="%{text}", textfont=dict(size=11),
        colorbar=dict(title=colorbar_title, thickness=12), hoverongaps=False,
        hovertemplate="%{y}<br>%{x}: %{text}<extra></extra>",
    ))
    fig.update_layout(title=title, height=height or max(360, 34 * len(table) + 160),
                      xaxis=dict(tickangle=-35, side="bottom", showgrid=False),
                      yaxis=dict(autorange="reversed", showgrid=False))
    return fig


def simple_bar(df: pd.DataFrame, x: str, y: str, title: str, x_title: str, color: str = BLUE,
               suffix: str = "") -> go.Figure:
    df = df.sort_values(x)
    fig = go.Figure(go.Bar(x=df[x], y=df[y], orientation="h", marker_color=color,
                           text=[f"{v:,.0f}{suffix}" for v in df[x]], textposition="outside",
                           hovertemplate="%{y}: %{x:,}" + suffix + "<extra></extra>"))
    fig.update_layout(title=title, xaxis=dict(title=x_title, range=[0, df[x].max() * 1.18]), yaxis_title=None,
                      height=max(300, 30 * len(df) + 110))
    return fig


def geo_bubbles(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure(go.Scattergeo(
        lat=df["lat"], lon=df["lon"], text=df["short_name"], mode="markers+text", textposition="top center",
        marker=dict(size=(df["profiles"] ** 0.5) * 3.2 + 6, color=BLUE, opacity=0.75,
                    line=dict(color="white", width=1)),
        customdata=df[["profiles", "share_pct"]],
        hovertemplate="<b>%{text}</b><br>Profiles: %{customdata[0]}<br>Share: %{customdata[1]}%<extra></extra>",
    ))
    fig.update_layout(title=title, height=440, geo=dict(scope="usa", projection_type="albers usa",
                      showland=True, landcolor="#F3F6FA", subunitcolor="#CBD5E1", countrycolor="#CBD5E1"))
    return fig


def trend_lines(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["cohort_quarter"], y=df["avg_readiness"], mode="lines+markers+text",
                             name="Avg. readiness for target role (%)", line=dict(color=TEAL, width=3),
                             text=[f"{v:.0f}%" for v in df["avg_readiness"]], textposition="top center"))
    fig.add_trace(go.Bar(x=df["cohort_quarter"], y=df["avg_missing_core"], name="Avg. missing core skills",
                         marker_color="rgba(224,122,31,0.55)", yaxis="y2",
                         hovertemplate="%{x}: %{y:.2f} missing core skills<extra></extra>"))
    fig.update_layout(title="Skills gap trend by cohort quarter", height=420,
                      yaxis=dict(title="Readiness (%)", range=[0, 100], ticksuffix="%"),
                      yaxis2=dict(title="Missing core skills", overlaying="y", side="right", showgrid=False,
                                  range=[0, max(6, df["avg_missing_core"].max() * 1.4)]),
                      xaxis_title="Cohort quarter")
    return fig
