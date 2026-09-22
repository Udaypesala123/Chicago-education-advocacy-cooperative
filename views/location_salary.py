"""Location & Salary Insights: wages, demand, skills and industries by job and location."""

import streamlit as st

from career_insights import charts
from career_insights.components import location_picker, target_picker
from career_insights.ui import catalog_table, demo_banner, disclaimer, fmt_money, get_data, show, source_caption

ds, _model = get_data()

st.title("Location & Salary Insights")
st.markdown("Explore salary ranges, employment demand, required skills and industry mix for a career path. "
            "Compare metro areas side by side.")
demo_banner("National figures approximate BLS OEWS May 2023 estimates. Metro-level figures and industry shares "
            "are **demonstration estimates** derived from those national figures, not official BLS metro data.")

f1, f2, f3 = st.columns(3)
categories = ["All career areas"] + sorted(ds.occupations["category"].unique())
category = f1.selectbox("Job category", categories)
with f2:
    target = target_picker(ds, label="Career path")
with f3:
    loc = location_picker(ds)

occ = ds.occupation(target)
if category != "All career areas" and occ["category"] != category:
    st.caption(f"Note: {occ['occupation']} is in *{occ['category']}*. The category filter applies to the "
               "comparison charts below.")
soc = occ["soc_code"]
in_cat = ds.occupations if category == "All career areas" else ds.occupations[ds.occupations["category"] == category]

wages = ds.wages.merge(ds.locations[["location_id", "short_name"]], on="location_id")
occ_wages = wages[wages["soc_code"] == soc]
here = occ_wages[occ_wages["location_id"] == loc]
nat = ds.bls_national[ds.bls_national["soc_code"] == soc]
if here.empty or nat.empty:
    st.error("No wage data is available for this combination. Try another career path or location.")
    disclaimer()
    st.stop()
here, nat = here.iloc[0], nat.iloc[0]

proxy = " (closest BLS proxy)" if occ["soc_is_proxy"] == "yes" else ""
st.markdown(f"#### {occ['occupation']} in {ds.location_name(loc, short=False)}")
st.caption(f"Wage and employment data use BLS SOC **{soc} {occ['soc_title']}**{proxy}.")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Median annual wage", fmt_money(here["wage_median"]),
          delta=f"{(here['wage_median'] / nat['wage_median'] - 1) * 100:+.0f}% vs. U.S." if loc != "us" else None)
m2.metric("Typical range (10th–90th)", f"${here['wage_p10'] / 1000:,.0f}k–${here['wage_p90'] / 1000:,.0f}k")
m3.metric("Estimated employment", f"{here['employment']:,.0f}",
          help="Location quotient > 1 means the job is more concentrated here than nationally.",
          delta=f"LQ {here['location_quotient']:.2f}", delta_color="off")
m4.metric("U.S. projected growth 2023–33", f"{nat['projected_growth_pct_2023_2033']}%")

tab_pay, tab_demand, tab_skills, tab_ind, tab_compare = st.tabs(
    ["Salary range", "Employment demand", "Required skills", "Industries", "Compare roles"])

with tab_pay:
    show(charts.salary_ranges(occ_wages, "short_name", f"{occ['occupation']}: annual wage range by location"),
         key="salary_range")
    source_caption(ds, "wages_by_location", "bls_national")

with tab_demand:
    show(charts.employment_demand(occ_wages[occ_wages["location_id"] != "us"], "short_name",
                                  f"{occ['occupation']}: estimated employment by metro area"), key="demand")
    st.caption("Color shows the location quotient (concentration vs. the national average). The national total is "
               f"{nat['employment']:,.0f}.")
    source_caption(ds, "wages_by_location", "bls_national")

with tab_skills:
    req = ds.occupation_skills[ds.occupation_skills["occupation_id"] == target]
    show(charts.required_skills(req, f"Skills requested for {occ['occupation']}"), key="req_skills")
    source_caption(ds, "occupation_skills")

with tab_ind:
    ind = ds.industries[ds.industries["soc_code"] == soc]
    if ind.empty:
        st.info("No industry breakdown is available for this occupation.")
    else:
        show(charts.industry_distribution(ind, f"Where {occ['soc_title']} work (national)"), key="industries")
        source_caption(ds, "industry_distribution")

with tab_compare:
    cmp_nat = in_cat.merge(ds.bls_national, on="soc_code", suffixes=("", "_bls"))
    show(charts.wage_growth_scatter(cmp_nat, highlight=occ["occupation"]), key="scatter")
    source_caption(ds, "bls_national")
    heat = (wages[wages["soc_code"].isin(in_cat["soc_code"])]
            .merge(in_cat[["soc_code", "occupation"]], on="soc_code")
            .pivot_table(index="occupation", columns="short_name", values="wage_median", aggfunc="mean"))
    order = ["United States"] + [c for c in heat.columns if c != "United States"]
    heat = heat[order].sort_values("United States", ascending=False) / 1000
    show(charts.heatmap(heat, "Median annual wage by role and location ($ thousands)", "$k", ".0f"), key="wage_heat")
    source_caption(ds, "wages_by_location")
    if occ["soc_is_proxy"] == "yes" or in_cat["soc_is_proxy"].eq("yes").any():
        st.caption("Roles marked as proxies share a BLS occupation code with a related job, because BLS does not "
                   "publish a standalone code for that title.")

with st.expander("Datasets used on this page (source and date)", icon=":material/database:"):
    tbl = catalog_table(ds)
    st.dataframe(tbl[tbl["file"].isin(["bls_national_occupations.csv", "wages_by_location.csv",
                                       "industry_distribution.csv", "occupation_skills.csv", "locations.csv"])],
                 hide_index=True, width="stretch",
                 column_config={"source_url": st.column_config.LinkColumn("Source link")})

disclaimer()
