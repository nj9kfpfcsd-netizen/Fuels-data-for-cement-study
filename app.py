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
(t_over, t_prod, t_energy, t_ready, t_fuel, t_qual, t_edit, t_raw) = st.tabs(
    ["📊 Overview", "🏗️ Production", "⚡ Energy & Emissions", "🌱 Readiness",
     "🔥 Fuels", "💬 Barriers & Enablers", "✏️ Edit Data", "📁 Raw Workbook"])

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
        d = SCd.sort_values("Readiness score (%)", ascending=False)[["ID", "Readiness score (%)"]]
        d = d.rename(columns={"ID": "Plant"}).reset_index(drop=True)
        d.index += 1
        st.dataframe(d.style.format({"Readiness score (%)": "{:.0f}%"})
                     .background_gradient(subset=["Readiness score (%)"], cmap="Greens"),
                     use_container_width=True)

# ---- Fuels ----------------------------------------------------------------- #
with t_fuel:
    cL, cR = st.columns(2)
    with cL:
        section("Primary fuels", "Most used for process heat")
        d = pd.DataFrame({"Fuel": D.PRIMARY_FUELS, "Rank": [2, 1]})
        fig = px.bar(d.sort_values("Rank"), x="Rank", y="Fuel", orientation="h",
                     color_discrete_sequence=[D.SLATE], text="Fuel")
        fig.update_traces(textposition="inside", insidetextanchor="start", textfont_color="white")
        fig.update_layout(**PLOT, height=230, showlegend=False, xaxis_visible=False, yaxis_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        section("AFR / power / renewables", "Share of plants")
        d = pd.DataFrame({"Measure": ["AFR co-processing", "On-site power", "Renewables"],
                          "%": [(R["AFR Co-processing"] == 1).mean() * 100,
                                (R["On-site Power Gen"] == 1).mean() * 100,
                                (R["Renewable Procurement"] == 1).mean() * 100]})
        fig = px.bar(d, x="Measure", y="%", color="Measure",
                     color_discrete_sequence=[D.PRIMARY, D.BLUE, D.AMBER],
                     text=d["%"].map(lambda v: f"{v:.0f}%"))
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(**PLOT, height=300, showlegend=False, xaxis_title="",
                          yaxis_title="", yaxis_range=[0, 110])
        st.plotly_chart(fig, use_container_width=True)
    with cR:
        section("Secondary (alternative) fuels", "Co-processed waste streams, ranked")
        d = pd.DataFrame({"Fuel": D.SECONDARY_FUELS,
                          "Rank": list(range(len(D.SECONDARY_FUELS), 0, -1))})
        fig = px.bar(d.sort_values("Rank"), x="Rank", y="Fuel", orientation="h",
                     color="Rank", color_continuous_scale=D.SEQ_GREEN, text="Fuel")
        fig.update_traces(textposition="inside", insidetextanchor="start")
        fig.update_layout(**PLOT, height=560, coloraxis_showscale=False,
                          xaxis_visible=False, yaxis_visible=False)
        st.plotly_chart(fig, use_container_width=True)

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
