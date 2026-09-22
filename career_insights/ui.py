"""Shared Streamlit helpers: cached data, persistent selections, styling, citations."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from . import DISCLAIMER
from .data import Datasets, DataError, load_all
from .scoring import SkillModel, build_skill_model
from .validation import clean_selection


@st.cache_data(show_spinner="Loading datasets…")
def _cached_datasets() -> Datasets:
    return load_all()


@st.cache_resource(show_spinner=False)
def _cached_model(_ds: Datasets) -> SkillModel:
    return build_skill_model(_ds)


def get_data() -> tuple[Datasets, SkillModel]:
    """Load datasets once per session; stop the page with a clear error if they are broken."""
    try:
        ds = _cached_datasets()
        return ds, _cached_model(ds)
    except DataError as exc:
        st.error(f"The dashboard could not load its data. {exc}")
        st.stop()


# --- Persistent selections --------------------------------------------------
# Streamlit discards a widget's state when you navigate to a page where it is
# not rendered. We mirror each shared value into a "_store" key so selections
# (skills, target role, location) follow the user across pages.

def _store(key: str) -> str:
    return f"_store_{key}"


def restore(key: str, default, allowed=None) -> None:
    """Call before rendering a widget with ``key`` to restore its saved value."""
    value = st.session_state.get(_store(key), default)
    if allowed is not None:
        if isinstance(value, list):
            value = clean_selection(value, allowed)
        elif value not in allowed:
            value = default
    st.session_state[key] = value
    st.session_state[_store(key)] = value


def save(key: str) -> None:
    """``on_change`` callback that saves a widget's value to the persistent store."""
    st.session_state[_store(key)] = st.session_state[key]


def get_saved(key: str, default=None):
    return st.session_state.get(_store(key), default)


def set_saved(key: str, value) -> None:
    st.session_state[_store(key)] = value


# --- Layout helpers ---------------------------------------------------------

CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1200px;}
.ci-hero {background: linear-gradient(135deg, #1B3A5C 0%, #2F6DB5 100%); color: #fff;
          padding: 2rem 2.2rem; border-radius: 14px; margin-bottom: 1.2rem;}
.ci-hero h1 {color: #fff; margin: 0 0 .4rem 0; font-size: 2.1rem; line-height: 1.2;}
.ci-hero p {color: #E8EEF6; font-size: 1.05rem; margin: 0; max-width: 780px;}
.ci-card {border: 1px solid #E3E8EF; border-radius: 12px; padding: 1rem 1.1rem; background: #fff; height: 100%;}
.ci-card h4 {margin: 0 0 .35rem 0; color: #1B3A5C; font-size: 1.02rem;}
.ci-card p {margin: 0; color: #4B5563; font-size: .92rem;}
.ci-pill {display:inline-block; padding: .12rem .55rem; border-radius: 999px; font-size: .78rem;
          font-weight: 600; margin: 0 .3rem .3rem 0; border: 1px solid transparent;}
.ci-have {background:#E3F4F1; color:#1E6F65; border-color:#BFE3DD;}
.ci-high {background:#FBE7E6; color:#9B2C27; border-color:#F2C3C0;}
.ci-medium {background:#FDF0E2; color:#9A4E0C; border-color:#F6D5B3;}
.ci-low {background:#EEF1F5; color:#4B5563; border-color:#D5DBE3;}
.ci-demo {background:#FFF7E0; color:#7A5B00; border-color:#F2DF9B;}
.ci-disclaimer {font-size: .82rem; color: #6B7280; border-top: 1px solid #E3E8EF; padding-top: .8rem;
                margin-top: 2rem;}
@media (max-width: 640px) {
  .ci-hero {padding: 1.3rem 1.2rem;}
  .ci-hero h1 {font-size: 1.55rem;}
}
</style>
"""


def page_setup() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="ci-hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def card(title: str, body: str) -> None:
    st.markdown(f'<div class="ci-card"><h4>{title}</h4><p>{body}</p></div>', unsafe_allow_html=True)


PILL_CLASS = {"Already have": "ci-have", "High": "ci-high", "Medium": "ci-medium", "Low": "ci-low",
              "Demo": "ci-demo"}


def pills(items: list[str], kind: str) -> str:
    cls = PILL_CLASS.get(kind, "ci-low")
    return "".join(f'<span class="ci-pill {cls}">{i}</span>' for i in items)


def disclaimer() -> None:
    st.markdown(f'<div class="ci-disclaimer"><b>Disclaimer.</b> {DISCLAIMER}</div>', unsafe_allow_html=True)


def source_caption(ds: Datasets, *dataset_ids: str) -> None:
    """Show source, reference period, compile date and status for each dataset used by a chart."""
    parts = []
    for did in dataset_ids:
        e = ds.catalog_entry(did)
        src = f"[{e['publisher']}]({e['source_url']})" if isinstance(e["source_url"], str) and e["source_url"] else e["publisher"]
        parts.append(f"**{e['title']}** — {src}; reference period: {e['reference_period']}; "
                     f"compiled {e['compiled_on']}; status: *{e['data_status']}*")
    st.caption("Source: " + " · ".join(parts))


def demo_banner(text: str) -> None:
    st.warning(text, icon=":material/science:")


def show(fig, key: str | None = None) -> None:
    """Render a Plotly figure with the project template (theme=None keeps our accessible styling)."""
    st.plotly_chart(fig, width="stretch", theme=None, key=key,
                    config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})


def fmt_money(v: float) -> str:
    return f"${v:,.0f}"


def catalog_table(ds: Datasets) -> pd.DataFrame:
    return ds.catalog[["title", "file", "publisher", "reference_period", "compiled_on", "data_status",
                       "source_url", "notes"]]
