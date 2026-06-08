"""
Editable plant records + JSON persistence + dataframe builders.

The dataset is stored in `plants_data.json` (created on first run from SEED).
Everything the dashboard charts is derived from these records, so adding /
editing a plant in the UI immediately flows through to every visual.
"""
import json
import os
import numpy as np
import pandas as pd

import data as D

DATA_PATH = os.path.join(os.path.dirname(__file__), "plants_data.json")

# Numeric readiness encoding: Yes=1, Pilot/Studying=0.5, No=0, unknown=None
Y, N, P = 1.0, 0.0, 0.5

# --- SEED (extracted verbatim from Final_Dataset_KOBO.xlsx) -------------------
def _rec(code, plant_name, district, contact_name, designation, mobile, email,
         commissioned, cap, c22, c23, c24, cf, te, mw, readiness):
    r = dict(code=code, plant_name=plant_name, district=district,
             contact_name=contact_name, designation=designation, mobile=mobile,
             email=email, commissioned=commissioned, installed_capacity=cap,
             clinker_2022_23=c22, clinker_2023_24=c23, clinker_2024_25=c24,
             clinker_factor=cf, thermal_kcal=te, peak_mw=mw)
    r.update({k: v for k, v in zip(D.READINESS_KEYS, readiness)})
    return r


SEED = [
    _rec("SC", "Sagar Cements (M) Pvt. Ltd.", "Dhar", "Dr. Akash Pandey", "",
         "8359000293", "akash.pandey@sagarcements.in", 2021, 1_100_000,
         None, 726_900, 755_907, 0.80, 718, 72, [Y,Y,Y,Y,Y,Y,Y,Y,Y,Y,N]),
    _rec("UT-V", "UltraTech Cement Limited, Unit: Vikram Cement Works", "Neemuch",
         "Mr. Avasa Mishra", "Joint President & Unit Head", "9111018397",
         "utcl-vcw.cpcb@adityabirla.com", 1985, 4_000_000,
         3_247_162, 3_068_556, 2_808_487, 0.7104, 698, 40, [Y,Y,Y,Y,Y,N,Y,N,N,Y,N]),
    _rec("UT-S", "UltraTech Cement Ltd. Unit- Sidhi Cement Works", "Sidhi",
         "Mr. B.P. Saggu", "Unit Head", "7247727859",
         "utcl-sdcw.cpcb@adityabirla.com", 2009, 3_000_000,
         2_681_469, 2_755_043, 2_781_839, 0.63, 706.03, 37.5, [N,Y,Y,Y,Y,Y,Y,N,N,Y,N]),
    _rec("JK", "M/s. J K Cement Limited, Panna", "Panna", "Mr. Kapil Agrawal",
         "Unit Head", "9686502172", "saurabh.yadav1@jkcement.com", 2022, 7_920_000,
         416_964, 2_394_022, 2_798_570, 0.6939, 728, 22, [Y,Y,Y,Y,Y,Y,Y,Y,Y,Y,P]),
    _rec("PJL I", "Prism Johnson Limited (Cement Division-Unit-1)", "Satna",
         "Mr. Sumitabh Dwivedi", "Assistant General Manager (Environment)",
         "9109912455", "sumitabh.dwivedi@prismjohnson.in", 1997, 2_500_000,
         1_888_783, 1_822_740, 2_134_091, 0.6789, 726, 30, [Y,Y,Y,Y,Y,Y,Y,Y,N,N,P]),
    _rec("PJL II", "Prism Johnson Limited (Cement Division-Unit-II)", "Satna",
         "Mr. Sumitabh Dwivedi", "Assistant General Manager (Environment)",
         "9109912455", "sumitabh.dwivedi@prismjohnson.in", 2011, 3_000_000,
         2_225_043, 2_684_861, 2_464_534, 0.6789, 734, 45, [Y,Y,Y,Y,Y,Y,Y,Y,N,N,P]),
    _rec("UT-B", "UltraTech Cement Limited, Unit: Bela Cement Works", "Rewa",
         "Santosh Shukla", "", "7247727537", "utcl-bcw.cpcb@adityabirla.com",
         1996, 2_380_000, 2_002_282, 1_708_493, 1_793_851, 0.9376, 706.75, 29,
         [Y,Y,Y,Y,Y,N,Y,N,N,Y,N]),
    _rec("UT-M", "UltraTech Cement Limited, Unit: Maihar Cement Works", "Maihar",
         "Bijneswar Mohanty", "President & Unit Head", "9522220233",
         "mcw.env@adityabirla.com", 1980, 8_000_000,
         2_369_348, 2_457_343, 3_094_172, 0.761, 764.26, 84, [Y,Y,Y,Y,Y,N,Y,N,N,Y,N]),
    _rec("UT-D", "UltraTech Cement Limited, Unit: Dhar Cement Works", "Dhar",
         "Vijay Chhabra", "President & Unit Head", "8889904363",
         "utcl-Dhar.cpcb@adityabirla.com", 2018, 6_000_000,
         2_892_955, 4_874_899, 5_000_370, 0.7212, 698.43, 40, [Y,Y,Y,Y,None,N,Y,N,N,Y,N]),
    _rec("DC", "Diamond Cements, (Clinkerisation Unit 3.1MTPA)", "Damoh",
         "Ashok Tiwari", "Head Environment", "9807886482",
         "ashokkumar.tiwari@heidelbergcement.in", 1983, 3_100_000,
         2_691_550, 3_017_866, 2_700_736, None, 740, 32.5, [Y,Y,Y,Y,Y,Y,Y,N,N,N,P]),
    _rec("ACC", "ACC Cement (Adani)", "Kemare Kalni", "Suresh Patel",
         "Section Head (Environment)", "9893405218", "sureshkumar.patel9@adani.com",
         1923, 1_815_000, 1_167_062, 1_297_852, 144_951, 0.6152, None, None,
         [Y,Y,Y,N,N,Y,N,N,N,N,P]),
    _rec("BCL", "Birla Corporation Limited", "Satna", "Ashwani Karwariya",
         "Regional Cluster Head (Central) Environment & Sustainability",
         "8236989201", "ashwani.karwariya@birlacorp.com", 1960, 3_400_000,
         2_781_916, 2_862_114, 2_940_960, 0.6644, 775.59, 44,
         [Y,Y,Y,N,Y,Y,None,None,None,N,P]),
]


# --- Persistence -------------------------------------------------------------
def load() -> list:
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                recs = json.load(f)
            if isinstance(recs, list) and recs:
                return _normalise(recs)
        except Exception:
            pass
    return _normalise([dict(r) for r in SEED])


def save(records: list) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def reset_to_seed() -> list:
    recs = _normalise([dict(r) for r in SEED])
    save(recs)
    return recs


def _normalise(records: list) -> list:
    """Ensure every record has all keys + a stable anonymous id (P01, P02 …)."""
    keys = ["code", "plant_name", "district", "contact_name", "designation",
            "mobile", "email", "commissioned", "installed_capacity",
            "clinker_2022_23", "clinker_2023_24", "clinker_2024_25",
            "clinker_factor", "thermal_kcal", "peak_mw"] + D.READINESS_KEYS
    out = []
    for i, r in enumerate(records):
        rec = {k: r.get(k) for k in keys}
        rec["anon_id"] = f"P{i + 1:02d}"
        if not rec.get("code"):
            rec["code"] = rec["anon_id"]
        out.append(rec)
    return out


# --- Derived dataframes ------------------------------------------------------
def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def plants_df(records: list) -> pd.DataFrame:
    rows = []
    for r in records:
        c1, c2, c3 = _num(r["clinker_2022_23"]), _num(r["clinker_2023_24"]), _num(r["clinker_2024_25"])
        avg = np.nanmean([c1, c2, c3]) if not all(np.isnan([c1, c2, c3])) else np.nan
        cap = _num(r["installed_capacity"])
        yr = r.get("commissioned")
        rows.append({
            "Code": r["code"], "AnonID": r["anon_id"], "Plant": r["plant_name"],
            "District": r["district"], "Contact": r["contact_name"],
            "Designation": r["designation"], "Mobile": r["mobile"], "Email": r["email"],
            "Commissioned": yr,
            "Age (yrs)": (2025 - int(yr)) if yr not in (None, "") else np.nan,
            "Installed capacity (T/yr)": cap,
            "Clinker 2022-23": c1, "Clinker 2023-24": c2, "Clinker 2024-25": c3,
            "Avg annual clinker (3y)": round(avg) if not np.isnan(avg) else np.nan,
            "Capacity utilisation": (avg / cap) if (cap and not np.isnan(avg)) else np.nan,
            "Clinker factor": _num(r["clinker_factor"]),
            "Thermal energy (kcal/kg)": _num(r["thermal_kcal"]),
            "Peak demand (MW)": _num(r["peak_mw"]),
        })
    return pd.DataFrame(rows)


def readiness_df(records: list) -> pd.DataFrame:
    data = {}
    for r in records:
        data[r["code"]] = [_num(r.get(k)) for k in D.READINESS_KEYS]
    df = pd.DataFrame(data, index=D.READINESS_LABELS).T
    df.index.name = "Code"
    return df


def production_long(records: list) -> pd.DataFrame:
    rows = []
    for r in records:
        for yr, key in [("2022-23", "clinker_2022_23"), ("2023-24", "clinker_2023_24"),
                        ("2024-25", "clinker_2024_25")]:
            rows.append({"Code": r["code"], "Year": yr, "Clinker (tonnes)": _num(r[key])})
    return pd.DataFrame(rows)


def readiness_score(records: list) -> pd.DataFrame:
    r = readiness_df(records)
    s = (r.mean(axis=1, skipna=True) * 100).reset_index()
    s.columns = ["Code", "Readiness score (%)"]
    return s.sort_values("Readiness score (%)", ascending=False)


def secret_values(records: list) -> set:
    out = set()
    for r in records:
        for f in D.CONFIDENTIAL_FIELDS:
            v = r.get(f)
            if isinstance(v, str) and v.strip():
                out.add(v.strip())
    return out


# --- Editable table <-> records ---------------------------------------------
EDIT_COLS = [
    "code", "plant_name", "district", "contact_name", "designation", "mobile",
    "email", "commissioned", "installed_capacity",
    "clinker_2022_23", "clinker_2023_24", "clinker_2024_25",
    "clinker_factor", "thermal_kcal", "peak_mw",
] + D.READINESS_KEYS

EDIT_LABELS = {
    "code": "Code", "plant_name": "Plant name", "district": "District",
    "contact_name": "Contact", "designation": "Designation", "mobile": "Mobile",
    "email": "Email", "commissioned": "Commissioned", "installed_capacity": "Capacity (T/yr)",
    "clinker_2022_23": "Clinker 22-23", "clinker_2023_24": "Clinker 23-24",
    "clinker_2024_25": "Clinker 24-25", "clinker_factor": "Clinker factor",
    "thermal_kcal": "Thermal kcal/kg", "peak_mw": "Peak MW",
}
EDIT_LABELS.update(D.READINESS_KEY2LABEL)


def to_editor_df(records: list) -> pd.DataFrame:
    rows = []
    for r in records:
        row = {EDIT_LABELS[k]: r.get(k) for k in EDIT_COLS}
        for k in D.READINESS_KEYS:
            row[EDIT_LABELS[k]] = D.NUM2TXT.get(_num(r.get(k)), "\u2014")
        rows.append(row)
    return pd.DataFrame(rows, columns=[EDIT_LABELS[k] for k in EDIT_COLS])


def from_editor_df(df: pd.DataFrame) -> list:
    inv = {v: k for k, v in EDIT_LABELS.items()}
    records = []
    for _, row in df.iterrows():
        if all((pd.isna(row[c]) or str(row[c]).strip() == "") for c in df.columns):
            continue
        rec = {}
        for col in df.columns:
            key = inv.get(col, col)
            val = row[col]
            if key in D.READINESS_KEYS:
                rec[key] = D.TXT2NUM.get(str(val).strip(), None)
            elif key in ("commissioned",):
                rec[key] = int(val) if pd.notna(val) and str(val).strip() != "" else None
            elif key in ("code", "plant_name", "district", "contact_name",
                         "designation", "mobile", "email"):
                rec[key] = "" if pd.isna(val) else str(val).strip()
            else:
                rec[key] = None if (pd.isna(val) or str(val).strip() == "") else float(val)
        records.append(rec)
    return _normalise(records)
