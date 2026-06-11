"""
Cement Sector Decarbonisation Dashboard  —  editable + confidentiality-aware.

Run with:
    pip install -r requirements.txt
    streamlit run app.py
"""
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data as D
import store as S

st.set_page_config(page_title="Cement Decarbonisation Dashboard",
                   page_icon="🏭", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family:'Inter',sans-serif; }
.stApp { background:#F7F8FA; }
#MainMenu, footer, header { visibility:hidden; }
.block-container { padding-top:1.4rem; padding-bottom:3rem; max-width:1320px; }
.hero { background:linear-gradient(120deg,#1F7A5C 0%,#2E8E6A 55%,#3FA37E 100%);
  border-radius:20px; padding:28px 32px; color:#fff; box-shadow:0 10px 30px rgba(31,122,92,.22); }
.hero h1 { font-size:2rem; font-weight:800; margin:0 0 6px 0; letter-spacing:-.5px; }
.hero p { font-size:1rem; margin:0; opacity:.92; }
.pill { display:inline-block; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.35);
  padding:4px 12px; border-radius:999px; font-size:.78rem; font-weight:600; margin-top:14px; }
.metric-card { background:#fff; border:1px solid #ECEFF3; border-radius:16px; padding:18px 20px;
  box-shadow:0 1px 2px rgba(16,24,40,.04); height:100%; }
.metric-card .label { color:#64748B; font-size:.8rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em; }
.metric-card .value { color:#0F172A; font-size:1.9rem; font-weight:800; line-height:1.15; margin-top:4px; }
.metric-card .sub { color:#1F7A5C; font-size:.82rem; font-weight:600; margin-top:2px; }
.sec { font-size:1.15rem; font-weight:700; color:#0F172A; margin:6px 0 2px 0; }
.sec-sub { color:#64748B; font-size:.88rem; margin-bottom:8px; }
.conf-banner { background:#FEF3C7; border:1px solid #FCD34D; color:#92400E; border-radius:12px;
  padding:10px 16px; font-weight:600; font-size:.9rem; margin-bottom:6px; }
.stTabs [data-baseweb="tab-list"] { gap:6px; flex-wrap:wrap; }
.stTabs [data-baseweb="tab"] { background:#fff; border:1px solid #ECEFF3; border-radius:10px; padding:8px 14px; font-weight:600; }
.stTabs [aria-selected="true"] { background:#1F7A5C !important; color:#fff !important; border-color:#1F7A5C; }
div[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; border:1px solid #ECEFF3; }
</style>
""", unsafe_allow_html=True)

PLOT = dict(template="plotly_white",
            font=dict(family="Inter, sans-serif", color=D.INK, size=13),
            margin=dict(l=10, r=10, t=48, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            title=dict(font=dict(size=16, color=D.INK)))

# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
if "records" not in st.session_state:
    st.session_state.records = S.load()
records = st.session_state.records


def card(label, value, sub=""):
    sub = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="metric-card"><div class="label">{label}</div>'
                f'<div class="value">{value}</div>{sub}</div>', unsafe_allow_html=True)


def section(t, s=""):
    st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)
    if s:
        st.markdown(f'<div class="sec-sub">{s}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### 🏭 Cement Decarbonisation")
    st.caption(f"{len(records)} plants · Madhya Pradesh, India")
    st.divider()
    confidential = st.toggle("🔒 Confidential mode", value=False,
                             help="Anonymise plant names and hide all contact "
                                  "details — safe to screen-share or present.")
    st.divider()
    all_codes = [r["code"] for r in records]
    label_for = {r["code"]: (r["anon_id"] if confidential else r["code"]) for r in records}
    pick_labels = st.multiselect("Filter plants",
                                 options=[label_for[c] for c in all_codes],
                                 default=[label_for[c] for c in all_codes])
    inv_label = {v: k for k, v in label_for.items()}
    sel = [inv_label[l] for l in pick_labels] or all_codes
    st.divider()
    st.caption("Add or edit plants on the **✏️ Edit Data** tab. Original survey "
               "lives in **📁 Raw Workbook**.")

# Derived frames
plants = S.plants_df(records)
ready = S.readiness_df(records)
prod_long = S.production_long(records)
score = S.readiness_score(records)
# Load restructured cleaned Excel workbook
cleaned_sheets = D.load_cleaned_workbook()

plant_master = cleaned_sheets["Plant_Master"]
fuel_df = cleaned_sheets["Fuel_Data"]
os_power_df = cleaned_sheets["OS_Power_Data"]
re_df = cleaned_sheets["RE_Data"]
scm_df = cleaned_sheets["SCM_Data"]
arm_df = cleaned_sheets["ARM_Data"]
whr_df = cleaned_sheets["WHR_Data"]
low_carbon_df = cleaned_sheets["Low_Carbon_Product_Data"]
pilot_df = cleaned_sheets["Pilot_Tech_Data"]
co2_df = cleaned_sheets["CO2_Data"]
packaging_df = cleaned_sheets["Packaging_Data"]
decarb_df = cleaned_sheets["Decarbonization_Data"]
raw_material_df = cleaned_sheets["Raw_Material_Consumption"]
# Apply selection + display labels
plants["ID"] = plants["AnonID"] if confidential else plants["Code"]
P = plants[plants["Code"].isin(sel)].copy()
lab = dict(zip(plants["Code"], plants["ID"]))
R = ready.loc[[c for c in ready.index if c in sel]].rename(index=lab)
PL = prod_long[prod_long["Code"].isin(sel)].copy()
PL["ID"] = PL["Code"].map(lab)
SCd = score[score["Code"].isin(sel)].copy()
SCd["ID"] = SCd["Code"].map(lab)

# --------------------------------------------------------------------------- #
# Hero
# --------------------------------------------------------------------------- #
st.markdown(f"""
<div class="hero">
  <h1>Decarbonisation Pathways in the Cement Sector</h1>
  <p>Capacity, energy intensity, fuels, emissions readiness & qualitative insights.</p>
  <span class="pill">{len(records)} plants</span>&nbsp;
  <span class="pill">3 production years</span>&nbsp;
  <span class="pill">{'🔒 Confidential view' if confidential else 'Full detail view'}</span>
</div>
""", unsafe_allow_html=True)
st.write("")
if confidential:
    st.markdown('<div class="conf-banner">🔒 Confidential mode is ON — plant names '
                'shown as P01, P02… and all contact details are hidden/redacted.</div>',
                unsafe_allow_html=True)

# KPIs
total_cap = P["Installed capacity (T/yr)"].sum()
avg_util = P["Capacity utilisation"].mean(skipna=True)
avg_cf = P["Clinker factor"].mean(skipna=True)
whr_share = (R["Waste Heat Recovery"] == 1).mean() * 100 if len(R) else 0
c1, c2, c3, c4, c5 = st.columns(5)
with c1: card("Plants", f"{len(P)}", "in selection")
with c2: card("Installed capacity", f"{total_cap/1e6:.1f} Mt", "clinker / year")
with c3: card("Capacity utilisation", f"{avg_util*100:.0f}%" if pd.notna(avg_util) else "—", "avg, last 3 yrs")
with c4: card("Clinker factor", f"{avg_cf:.2f}" if pd.notna(avg_cf) else "—", "avg (lower better)")
with c5: card("WHR adoption", f"{whr_share:.0f}%", "of plants")
st.write("")

# --------------------------------------------------------------------------- #
# Tabs
# --------------------------------------------------------------------------- #
(t_over, t_prod, t_energy, t_ready, t_fuel, t_elec, t_re, t_materials,
 t_whr, t_co2, t_cost, t_qual, t_edit, t_raw) = st.tabs(
    ["📊 Overview", "🏗️ Production", "⚡ Energy & Emissions", "🌱 Readiness",
     "🔥 Fuels", "🔌 Electricity", "☀️ RE & On-site Power", "♻️ Materials & SCMs",
     "🏭 WHR Systems", "🌍 CO₂ & Products", "💰 Decarb Cost",
     "💬 Barriers & Enablers", "✏️ Edit Data", "📁 Raw Workbook"])

# ---- Overview -------------------------------------------------------------- #
with t_over:
    cL, cR = st.columns([1.25, 1])
    with cL:
        section("Installed clinker capacity by plant", "Tonnes per year")
        d = P.sort_values("Installed capacity (T/yr)")
        fig = px.bar(d, x="Installed capacity (T/yr)", y="ID", orientation="h",
                     text=d["Installed capacity (T/yr)"].map(lambda v: f"{v/1e6:.2f} Mt"),
                     color_discrete_sequence=[D.PRIMARY])
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(**PLOT, height=430, showlegend=False, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with cR:
        section("Decarbonisation readiness", "Composite score, 11 indicators")
        d = SCd.sort_values("Readiness score (%)")
        fig = px.bar(d, x="Readiness score (%)", y="ID", orientation="h",
                     color="Readiness score (%)", color_continuous_scale=D.SEQ_GREEN,
                     text=d["Readiness score (%)"].map(lambda v: f"{v:.0f}%"))
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(**PLOT, height=430, coloraxis_showscale=False,
                          xaxis_title="", yaxis_title="", xaxis_range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)

    section("Plant directory")
    if confidential:
        show = P[["ID", "District", "Commissioned", "Installed capacity (T/yr)",
                  "Capacity utilisation", "Clinker factor", "Thermal energy (kcal/kg)"]]
        show = show.rename(columns={"ID": "Plant"})
    else:
        show = P[["Code", "Plant", "District", "Contact", "Designation", "Mobile",
                  "Email", "Commissioned", "Installed capacity (T/yr)",
                  "Capacity utilisation", "Clinker factor", "Thermal energy (kcal/kg)"]]
    st.dataframe(show.style.format({
        "Installed capacity (T/yr)": "{:,.0f}", "Capacity utilisation": "{:.0%}",
        "Clinker factor": "{:.3f}", "Thermal energy (kcal/kg)": "{:.1f}",
    }, na_rep="—"), use_container_width=True, hide_index=True)

# ---- Production ------------------------------------------------------------ #
with t_prod:
    section("Clinker production over 3 years", "2022-23 → 2024-25 (tonnes)")
    fig = px.line(PL, x="Year", y="Clinker (tonnes)", color="ID", markers=True,
                  color_discrete_sequence=D.CATEGORY)
    fig.update_layout(**PLOT, height=440, legend_title_text="", xaxis_title="",
                      yaxis_title="Clinker (tonnes)")
    st.plotly_chart(fig, use_container_width=True)
    cL, cR = st.columns(2)
    with cL:
        section("Installed capacity vs. actual output", "Latest 3-yr average")
        d = P.sort_values("Installed capacity (T/yr)", ascending=False)
        fig = go.Figure()
        fig.add_bar(name="Installed capacity", x=d["ID"], y=d["Installed capacity (T/yr)"], marker_color="#CBD5E1")
        fig.add_bar(name="Avg actual (3y)", x=d["ID"], y=d["Avg annual clinker (3y)"], marker_color=D.PRIMARY)
        fig.update_layout(**PLOT, height=420, barmode="overlay",
                          legend=dict(orientation="h", y=1.12), yaxis_title="Tonnes/yr")
        fig.update_traces(opacity=.95)
        st.plotly_chart(fig, use_container_width=True)
    with cR:
        section("Capacity utilisation", "Average output ÷ installed capacity")
        d = P.dropna(subset=["Capacity utilisation"]).sort_values("Capacity utilisation")
        fig = px.bar(d, x="Capacity utilisation", y="ID", orientation="h",
                     color="Capacity utilisation", color_continuous_scale=D.SEQ_GREEN,
                     text=d["Capacity utilisation"].map(lambda v: f"{v:.0%}"))
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(**PLOT, height=420, coloraxis_showscale=False,
                          xaxis_tickformat=".0%", xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

# ---- Energy ---------------------------------------------------------------- #
with t_energy:
    cL, cR = st.columns(2)
    rd_scale = ["#1F7A5C", "#86C9AE", "#FDE68A", "#F59E0B", "#DC2626"]
    with cL:
        section("Kiln thermal energy intensity", "kcal/kg clinker — lower is better")
        d = P.dropna(subset=["Thermal energy (kcal/kg)"]).sort_values("Thermal energy (kcal/kg)")
        fig = px.bar(d, x="Thermal energy (kcal/kg)", y="ID", orientation="h",
                     color="Thermal energy (kcal/kg)", color_continuous_scale=rd_scale,
                     text=d["Thermal energy (kcal/kg)"].map(lambda v: f"{v:.0f}"))
        fig.update_traces(textposition="outside", cliponaxis=False)
        if len(d):
            fig.add_vline(x=d["Thermal energy (kcal/kg)"].mean(), line_dash="dash",
                          line_color=D.SLATE)
        fig.update_layout(**PLOT, height=430, coloraxis_showscale=False, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with cR:
        section("Clinker factor by plant", "Share of clinker in cement — lower cuts CO₂")
        d = P.dropna(subset=["Clinker factor"]).sort_values("Clinker factor")
        fig = px.bar(d, x="Clinker factor", y="ID", orientation="h",
                     color="Clinker factor", color_continuous_scale=rd_scale,
                     text=d["Clinker factor"].map(lambda v: f"{v:.2f}"))
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(**PLOT, height=430, coloraxis_showscale=False, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    section("Energy intensity vs. clinker factor", "Bubble size = installed capacity")
    d = P.dropna(subset=["Thermal energy (kcal/kg)", "Clinker factor"])
    fig = px.scatter(d, x="Clinker factor", y="Thermal energy (kcal/kg)",
                     size="Installed capacity (T/yr)", color="ID", text="ID",
                     color_discrete_sequence=D.CATEGORY, size_max=46)
    fig.update_traces(textposition="top center")
    fig.update_layout(**PLOT, height=460, showlegend=False,
                      xaxis_title="Clinker factor (lower better)",
                      yaxis_title="Thermal energy kcal/kg (lower better)")
    st.plotly_chart(fig, use_container_width=True)

# ---- Readiness ------------------------------------------------------------- #
with t_ready:
    section("Decarbonisation readiness matrix",
            "Green = in place · Amber = pilot/studying · Red = not adopted · grey = no data")
    z = R.values.astype(float)
    txt = np.where(np.isnan(z), "—", np.where(z == 1, "Yes", np.where(z == .5, "Pilot", "No")))
    fig = go.Figure(go.Heatmap(z=z, x=R.columns.tolist(), y=R.index.tolist(),
                    text=txt, texttemplate="%{text}", textfont=dict(size=11),
                    colorscale=[[0, "#FCA5A5"], [.5, "#FCD34D"], [1, "#3FA37E"]],
                    zmin=0, zmax=1, showscale=False, xgap=3, ygap=3,
                    hovertemplate="<b>%{y}</b><br>%{x}: %{text}<extra></extra>"))
    fig.update_layout(**PLOT, height=70 + 34 * len(R),
                      xaxis=dict(side="top", tickangle=-35), yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)
    cL, cR = st.columns(2)
    with cL:
        section("Adoption rate per measure", "% of selected plants with measure in place")
        rate = ((R == 1).mean().sort_values() * 100).reset_index()
        rate.columns = ["Measure", "Adoption (%)"]
        fig = px.bar(rate, x="Adoption (%)", y="Measure", orientation="h",
                     color="Adoption (%)", color_continuous_scale=D.SEQ_GREEN,
                     text=rate["Adoption (%)"].map(lambda v: f"{v:.0f}%"))
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(**PLOT, height=460, coloraxis_showscale=False,
                          xaxis_title="", yaxis_title="", xaxis_range=[0, 110])
        st.plotly_chart(fig, use_container_width=True)
        
    with cR:
        section("Readiness leaderboard")

        d = SCd.sort_values(
            "Readiness score (%)",
            ascending=False
        )[["ID", "Readiness score (%)"]]

        d = d.rename(
            columns={"ID": "Plant"}
        ).reset_index(drop=True)

        d.index += 1

        st.dataframe(
            d.style.format(
                {"Readiness score (%)": "{:.0f}%"}
            ),
            use_container_width=True
        )
# ---- Fuels ----------------------------------------------------------------- #
with t_fuel:
    section("Fuel mix and sourcing", "Fuel use, calorific value, suppliers and origin country")

    fuel_df["Fuel_Calorific_Value"] = D.clean_numeric_column(fuel_df["Fuel_Calorific_Value"])
    fuel_df["Fuel_Annual_Quantity"] = D.clean_numeric_column(fuel_df["Fuel_Annual_Quantity"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Fuel entries", f"{len(fuel_df)}", "records")
    with c2:
        card("Fuel types", f"{fuel_df['Fuel_Type'].nunique()}", "unique fuels")
    with c3:
        card("Suppliers", f"{fuel_df['Fuel_Supplier'].nunique()}", "unique suppliers")
    with c4:
        card("Countries", f"{fuel_df['Fuel_supplier_Country'].nunique()}", "source countries")

    cL, cR = st.columns(2)

    with cL:
        section("Fuel type frequency", "Number of recorded fuel entries")
        d = fuel_df["Fuel_Type"].dropna().astype(str).str.strip().value_counts().reset_index()
        d.columns = ["Fuel_Type", "Count"]

        fig = px.bar(d, x="Count", y="Fuel_Type", orientation="h",
                     text="Count", color_discrete_sequence=[D.PRIMARY])
        fig.update_layout(**PLOT, height=520, xaxis_title="Count", yaxis_title="Fuel type")
        st.plotly_chart(fig, use_container_width=True)

    with cR:
        section("Average calorific value by fuel", "MJ/kg")
        d = fuel_df.dropna(subset=["Fuel_Type", "Fuel_Calorific_Value"])
        d = d.groupby("Fuel_Type", as_index=False)["Fuel_Calorific_Value"].mean()
        d = d.sort_values("Fuel_Calorific_Value")

        fig = px.bar(d, x="Fuel_Calorific_Value", y="Fuel_Type", orientation="h",
                     text="Fuel_Calorific_Value", color_discrete_sequence=[D.BLUE])
        fig.update_traces(texttemplate="%{text:.2f}")
        fig.update_layout(**PLOT, height=520, xaxis_title="Average calorific value (MJ/kg)", yaxis_title="Fuel type")
        st.plotly_chart(fig, use_container_width=True)

    cL, cR = st.columns(2)

    with cL:
        section("Fuel sourcing by country", "Number of entries by country")
        d = fuel_df["Fuel_supplier_Country"].dropna().astype(str).str.strip().value_counts().reset_index()
        d.columns = ["Country", "Count"]

        fig = px.bar(d, x="Count", y="Country", orientation="h",
                     text="Count", color_discrete_sequence=[D.AMBER])
        fig.update_layout(**PLOT, height=420, xaxis_title="Count", yaxis_title="Country")
        st.plotly_chart(fig, use_container_width=True)

    with cR:
        section("Fuel annual quantity by fuel", "Total annual quantity where available")
        d = fuel_df.dropna(subset=["Fuel_Type", "Fuel_Annual_Quantity"])
        d = d.groupby("Fuel_Type", as_index=False)["Fuel_Annual_Quantity"].sum()
        d = d.sort_values("Fuel_Annual_Quantity")

        fig = px.bar(d, x="Fuel_Annual_Quantity", y="Fuel_Type", orientation="h",
                     text="Fuel_Annual_Quantity", color_discrete_sequence=[D.PRIMARY_LT])
        fig.update_traces(texttemplate="%{text:,.0f}")
        fig.update_layout(**PLOT, height=420, xaxis_title="Annual quantity", yaxis_title="Fuel type")
        st.plotly_chart(fig, use_container_width=True)

# ---- Electricity ----------------------------------------------------------- #
with t_elec:
    section("Electricity consumption by section", "Plant-wise electricity use across major sections")

    elec_cols = ["Electricity_Clinker", "Electricity_Grinding", "Electricity_Auxiliaries",
                 "Electricity_Offices", "Electricity_Others"]

    elec = plant_master[["Abbreviation"] + elec_cols].copy()

    for col in elec_cols:
        elec[col] = D.clean_numeric_column(elec[col])

    elec_long = elec.melt(
        id_vars="Abbreviation",
        value_vars=elec_cols,
        var_name="Section",
        value_name="Electricity"
    ).dropna()

    fig = px.bar(
        elec_long,
        x="Abbreviation",
        y="Electricity",
        color="Section",
        barmode="stack",
        color_discrete_sequence=D.CATEGORY
    )
    fig.update_layout(**PLOT, height=520, xaxis_title="Plant", yaxis_title="Electricity consumption")
    st.plotly_chart(fig, use_container_width=True)

    cL, cR = st.columns(2)

    with cL:
        section("Peak electrical demand", "MW")
        d = plant_master[["Abbreviation", "Peak_Demand_Elec"]].copy()
        d["Peak_Demand_Elec"] = D.clean_numeric_column(d["Peak_Demand_Elec"])
        d = d.dropna().sort_values("Peak_Demand_Elec")

        fig = px.bar(d, x="Peak_Demand_Elec", y="Abbreviation", orientation="h",
                     text="Peak_Demand_Elec", color_discrete_sequence=[D.BLUE])
        fig.update_layout(**PLOT, height=420, xaxis_title="Peak demand (MW)", yaxis_title="Plant")
        st.plotly_chart(fig, use_container_width=True)

    with cR:
        section("Clinker-specific electrical consumption", "Average clinker-specific electricity consumption")
        d = plant_master[["Abbreviation", "Average_clinker_electrical_cons"]].copy()
        d["Average_clinker_electrical_cons"] = D.clean_numeric_column(d["Average_clinker_electrical_cons"])
        d = d.dropna().sort_values("Average_clinker_electrical_cons")

        fig = px.bar(d, x="Average_clinker_electrical_cons", y="Abbreviation", orientation="h",
                     text="Average_clinker_electrical_cons", color_discrete_sequence=[D.PRIMARY])
        fig.update_layout(**PLOT, height=420, xaxis_title="Specific electricity consumption", yaxis_title="Plant")
        st.plotly_chart(fig, use_container_width=True)

# ---- RE & On-site Power ---------------------------------------------------- #
with t_re:
    section("Renewable energy and on-site power", "Capacity and generation by technology type")

    re_df["RE_Capacity"] = D.clean_numeric_column(re_df["RE_Capacity"])
    re_df["RE_Annual_Generation"] = D.clean_numeric_column(re_df["RE_Annual_Generation"])
    os_power_df["OS_power_generation_Capacity"] = D.clean_numeric_column(os_power_df["OS_power_generation_Capacity"])

    cL, cR = st.columns(2)

    with cL:
        section("Renewable energy capacity by type", "Capacity where available")
        d = re_df.dropna(subset=["RE_Type", "RE_Capacity"])
        d = d.groupby("RE_Type", as_index=False)["RE_Capacity"].sum().sort_values("RE_Capacity")

        fig = px.bar(d, x="RE_Capacity", y="RE_Type", orientation="h",
                     text="RE_Capacity", color_discrete_sequence=[D.PRIMARY])
        fig.update_layout(**PLOT, height=480, xaxis_title="RE capacity", yaxis_title="RE type")
        st.plotly_chart(fig, use_container_width=True)

    with cR:
        section("Renewable energy annual generation", "Annual generation where available")
        d = re_df.dropna(subset=["RE_Type", "RE_Annual_Generation"])
        d = d.groupby("RE_Type", as_index=False)["RE_Annual_Generation"].sum().sort_values("RE_Annual_Generation")

        fig = px.bar(d, x="RE_Annual_Generation", y="RE_Type", orientation="h",
                     text="RE_Annual_Generation", color_discrete_sequence=[D.BLUE])
        fig.update_traces(texttemplate="%{text:,.0f}")
        fig.update_layout(**PLOT, height=480, xaxis_title="Annual generation", yaxis_title="RE type")
        st.plotly_chart(fig, use_container_width=True)

    section("On-site power generation capacity", "Capacity by generation type")
    d = os_power_df.dropna(subset=["OS_power_generation_Type", "OS_power_generation_Capacity"])
    d = d.groupby("OS_power_generation_Type", as_index=False)["OS_power_generation_Capacity"].sum().sort_values("OS_power_generation_Capacity")

    fig = px.bar(d, x="OS_power_generation_Capacity", y="OS_power_generation_Type", orientation="h",
                 text="OS_power_generation_Capacity", color_discrete_sequence=[D.AMBER])
    fig.update_layout(**PLOT, height=500, xaxis_title="Capacity", yaxis_title="On-site power type")
    st.plotly_chart(fig, use_container_width=True)

# ---- Materials & SCMs ------------------------------------------------------ #
with t_materials:
    section("SCMs and alternative raw materials", "Material substitution and consumption trends")

    scm_df["SCM_Cement_Share"] = D.clean_numeric_column(scm_df["SCM_Cement_Share"])

    cL, cR = st.columns(2)

    with cL:
        section("SCM type frequency", "Number of entries by SCM type")
        d = scm_df["SCM_Type"].dropna().astype(str).str.strip().value_counts().reset_index()
        d.columns = ["SCM_Type", "Count"]

        fig = px.bar(d, x="Count", y="SCM_Type", orientation="h",
                     text="Count", color_discrete_sequence=[D.PRIMARY])
        fig.update_layout(**PLOT, height=460, xaxis_title="Count", yaxis_title="SCM type")
        st.plotly_chart(fig, use_container_width=True)

    with cR:
        section("Average SCM share in cement", "Share of cement where available")
        d = scm_df.dropna(subset=["SCM_Type", "SCM_Cement_Share"])
        d = d.groupby("SCM_Type", as_index=False)["SCM_Cement_Share"].mean().sort_values("SCM_Cement_Share")

        fig = px.bar(d, x="SCM_Cement_Share", y="SCM_Type", orientation="h",
                     text="SCM_Cement_Share", color_discrete_sequence=[D.BLUE])
        fig.update_layout(**PLOT, height=460, xaxis_title="Average share", yaxis_title="SCM type")
        st.plotly_chart(fig, use_container_width=True)

    section("Alternative raw material quantity trend", "2022-23 to 2024-25")

    for col in ["ARM_quantity_2022_23", "ARM_quantity_2023_24", "ARM_quantity_2024_25"]:
        arm_df[col] = D.clean_numeric_column(arm_df[col])

    arm_long = arm_df.melt(
        id_vars=["Abbreviation", "ARM"],
        value_vars=["ARM_quantity_2022_23", "ARM_quantity_2023_24", "ARM_quantity_2024_25"],
        var_name="Year",
        value_name="Quantity"
    ).dropna()

    arm_long["Year"] = arm_long["Year"].replace({
        "ARM_quantity_2022_23": "2022-23",
        "ARM_quantity_2023_24": "2023-24",
        "ARM_quantity_2024_25": "2024-25"
    })

    d = arm_long.groupby(["Year", "ARM"], as_index=False)["Quantity"].sum()

    fig = px.bar(d, x="Year", y="Quantity", color="ARM",
                 barmode="group", color_discrete_sequence=D.CATEGORY)
    fig.update_layout(**PLOT, height=520, xaxis_title="Year", yaxis_title="Quantity")
    st.plotly_chart(fig, use_container_width=True)

# ---- WHR Systems ----------------------------------------------------------- #
with t_whr:
    section("Waste Heat Recovery systems", "Technology, capacity and annual generation")

    whr_df["WHR_Technology_Capacity"] = D.clean_numeric_column(whr_df["WHR_Technology_Capacity"])
    whr_df["WHR_Annual_Generation"] = D.clean_numeric_column(whr_df["WHR_Annual_Generation"])

    cL, cR = st.columns(2)

    with cL:
        section("WHR capacity by technology", "MW")
        d = whr_df.dropna(subset=["WHR_Technology", "WHR_Technology_Capacity"])
        d = d.groupby("WHR_Technology", as_index=False)["WHR_Technology_Capacity"].sum().sort_values("WHR_Technology_Capacity")

        fig = px.bar(d, x="WHR_Technology_Capacity", y="WHR_Technology", orientation="h",
                     text="WHR_Technology_Capacity", color_discrete_sequence=[D.PRIMARY])
        fig.update_layout(**PLOT, height=450, xaxis_title="Capacity (MW)", yaxis_title="WHR technology")
        st.plotly_chart(fig, use_container_width=True)

    with cR:
        section("WHR annual generation", "MWh")
        d = whr_df.dropna(subset=["WHR_Technology", "WHR_Annual_Generation"])
        d = d.groupby("WHR_Technology", as_index=False)["WHR_Annual_Generation"].sum().sort_values("WHR_Annual_Generation")

        fig = px.bar(d, x="WHR_Annual_Generation", y="WHR_Technology", orientation="h",
                     text="WHR_Annual_Generation", color_discrete_sequence=[D.BLUE])
        fig.update_traces(texttemplate="%{text:,.0f}")
        fig.update_layout(**PLOT, height=450, xaxis_title="Annual generation (MWh)", yaxis_title="WHR technology")
        st.plotly_chart(fig, use_container_width=True)

# ---- CO2 & Products -------------------------------------------------------- #
with t_co2:
    section("CO₂ emissions and low-carbon products", "Emission sources and product-level CO₂ intensity")

    co2_df["CO2_emissions_quantity"] = D.clean_numeric_column(co2_df["CO2_emissions_quantity"])
    low_carbon_df["low_carbon_Product_Estimated_CO2"] = D.clean_numeric_column(low_carbon_df["low_carbon_Product_Estimated_CO2"])

    cL, cR = st.columns(2)

    with cL:
        section("CO₂ emissions by source", "kg CO₂ where available")
        d = co2_df.dropna(subset=["Annual_CO2_Emission_Source", "CO2_emissions_quantity"])
        d = d.groupby("Annual_CO2_Emission_Source", as_index=False)["CO2_emissions_quantity"].sum().sort_values("CO2_emissions_quantity")

        fig = px.bar(d, x="CO2_emissions_quantity", y="Annual_CO2_Emission_Source", orientation="h",
                     text="CO2_emissions_quantity", color_discrete_sequence=[D.RED])
        fig.update_traces(texttemplate="%{text:,.0f}")
        fig.update_layout(**PLOT, height=480, xaxis_title="CO₂ emissions (kg)", yaxis_title="Emission source")
        st.plotly_chart(fig, use_container_width=True)

    with cR:
        section("Low-carbon product CO₂ intensity", "Estimated CO₂ intensity where available")
        d = low_carbon_df.dropna(subset=["low_carbon_Product_Name", "low_carbon_Product_Estimated_CO2"])
        d = d.groupby("low_carbon_Product_Name", as_index=False)["low_carbon_Product_Estimated_CO2"].mean().sort_values("low_carbon_Product_Estimated_CO2")

        fig = px.bar(d, x="low_carbon_Product_Estimated_CO2", y="low_carbon_Product_Name", orientation="h",
                     text="low_carbon_Product_Estimated_CO2", color_discrete_sequence=[D.PRIMARY])
        fig.update_layout(**PLOT, height=480, xaxis_title="Estimated CO₂ intensity", yaxis_title="Low-carbon product")
        st.plotly_chart(fig, use_container_width=True)

# ---- Decarbonization Cost -------------------------------------------------- #
with t_cost:
    section("Capital cost for decarbonization technologies", "Cost by technology where available")

    decarb_df["decarbonization_technology_Cost"] = D.clean_numeric_column(decarb_df["decarbonization_technology_Cost"])

    d = decarb_df.dropna(subset=["decarbonization_technology", "decarbonization_technology_Cost"])
    d = d.groupby("decarbonization_technology", as_index=False)["decarbonization_technology_Cost"].sum().sort_values("decarbonization_technology_Cost")

    fig = px.bar(d, x="decarbonization_technology_Cost", y="decarbonization_technology", orientation="h",
                 text="decarbonization_technology_Cost", color_discrete_sequence=[D.AMBER])
    fig.update_traces(texttemplate="%{text:,.2f}")
    fig.update_layout(**PLOT, height=520, xaxis_title="Cost (crores)", yaxis_title="Technology")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(decarb_df, use_container_width=True)



# ---- Qualitative ----------------------------------------------------------- #
with t_qual:
    cL, cR = st.columns(2)
    with cL:
        section("Top 5 enablers", "Most-cited strengths")
        for i, e in enumerate(D.TOP_ENABLERS, 1):
            st.markdown(f'<div class="metric-card" style="margin-bottom:10px;border-left:4px solid {D.PRIMARY};">'
                        f'<span style="color:{D.PRIMARY};font-weight:800;font-size:1.1rem;">#{i}</span>&nbsp;&nbsp;'
                        f'<span style="font-weight:600;">{e}</span></div>', unsafe_allow_html=True)
    with cR:
        section("Top 5 barriers", "Most-cited obstacles")
        for i, b in enumerate(D.TOP_BARRIERS, 1):
            st.markdown(f'<div class="metric-card" style="margin-bottom:10px;border-left:4px solid {D.RED};">'
                        f'<span style="color:{D.RED};font-weight:800;font-size:1.1rem;">#{i}</span>&nbsp;&nbsp;'
                        f'<span style="font-weight:600;">{b}</span></div>', unsafe_allow_html=True)

# ---- Edit Data ------------------------------------------------------------- #
with t_edit:
    section("Add, edit or remove plants",
            "Edit any cell. Use the ＋ at the bottom of the table to add a plant, "
            "or select a row's checkbox and press ⌫ to delete. Then click Save.")
    if confidential:
        st.info("🔒 Confidential mode is ON — identifying columns are locked. "
                "Turn it off in the sidebar to edit names/contacts. Numbers and "
                "readiness stay editable, and existing contact data is preserved on save.")

    edf = S.to_editor_df(records)
    conf_cols = [S.EDIT_LABELS[k] for k in D.CONFIDENTIAL_FIELDS]
    if confidential:
        for c in conf_cols:
            edf[c] = "🔒"

    colcfg = {}
    for k in D.READINESS_KEYS:
        colcfg[S.EDIT_LABELS[k]] = st.column_config.SelectboxColumn(
            S.EDIT_LABELS[k], options=D.READINESS_TXT_OPTIONS, width="small")
    for k, fmt in [("installed_capacity", "%d"), ("clinker_2022_23", "%d"),
                   ("clinker_2023_24", "%d"), ("clinker_2024_25", "%d"),
                   ("clinker_factor", "%.4f"), ("thermal_kcal", "%.2f"),
                   ("peak_mw", "%.1f"), ("commissioned", "%d")]:
        colcfg[S.EDIT_LABELS[k]] = st.column_config.NumberColumn(S.EDIT_LABELS[k], format=fmt)

    edited = st.data_editor(
        edf, num_rows="dynamic", use_container_width=True, height=460,
        column_config=colcfg,
        disabled=conf_cols if confidential else [],
        key="editor",
    )

    b1, b2, b3, b4 = st.columns([1, 1, 1.3, 2])
    with b1:
        if st.button("💾 Save changes", type="primary", use_container_width=True):
            new_recs = S.from_editor_df(edited)
            if confidential:  # restore locked confidential fields by code
                prev = {r["code"]: r for r in records}
                for nr in new_recs:
                    if nr["code"] in prev:
                        for f in D.CONFIDENTIAL_FIELDS:
                            nr[f] = prev[nr["code"]].get(f, "")
            st.session_state.records = new_recs
            S.save(new_recs)
            st.success(f"Saved — {len(new_recs)} plants.")
            st.rerun()
    with b2:
        if st.button("↩️ Reset to original", use_container_width=True):
            st.session_state.records = S.reset_to_seed()
            st.rerun()
    with b3:
        st.download_button("⬇️ Export dataset (JSON)",
                           json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name="plants_data.json", mime="application/json",
                           use_container_width=True)
    with b4:
        up = st.file_uploader("⬆️ Import dataset (JSON)", type="json", label_visibility="collapsed")
        if up is not None:
            try:
                recs = json.load(up)
                st.session_state.records = S._normalise(recs)
                S.save(st.session_state.records)
                st.success("Imported.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not import: {e}")

# ---- Raw workbook ---------------------------------------------------------- #
with t_raw:
    section("Original workbook — every sheet & cell",
            "Read live from Final_Dataset_KOBO.xlsx." +
            (" Confidential mode redacts identifying values below." if confidential else ""))
    raw = D.load_raw_sheets()
    secrets = S.secret_values(records) if confidential else set()
    sheet = st.radio("Sheet", list(raw.keys()), horizontal=True)
    df = raw[sheet]
    if confidential:
        df = D.redact_sheet(sheet, df, secrets)
    st.caption(f"`{sheet}` — {df.shape[0]} rows × {df.shape[1]} columns")
    disp = df.astype(object).where(df.notna(), "").astype(str)
    disp.columns = [str(c) for c in disp.columns]
    st.dataframe(disp, use_container_width=True, height=520)
    st.download_button("⬇️ Download this sheet as CSV",
                       df.to_csv(index=False).encode("utf-8"),
                       file_name=f"{sheet}{'_redacted' if confidential else ''}.csv",
                       mime="text/csv")

st.write("")
st.caption("Built with Streamlit + Plotly · figures are placeholders pending verification.")
