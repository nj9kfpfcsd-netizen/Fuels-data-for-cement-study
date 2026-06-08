"""
Shared constants, palette, schema keys and the raw-workbook reader.
Editable plant records + persistence live in store.py.
"""
import os
import re
import pandas as pd

WORKBOOK_PATH = os.path.join(os.path.dirname(__file__), "Final_Dataset_KOBO.xlsx")

# --- Palette (light, modern) -------------------------------------------------
PRIMARY = "#1F7A5C"
PRIMARY_LT = "#3FA37E"
BLUE = "#2563EB"
AMBER = "#F59E0B"
RED = "#DC2626"
SLATE = "#475569"
INK = "#0F172A"
SEQ_GREEN = ["#E7F3EE", "#BFE3D4", "#86C9AE", "#4FAE88", "#2E8E6A", "#1F7A5C"]
CATEGORY = [PRIMARY, BLUE, AMBER, "#8B5CF6", "#0891B2", "#DC2626",
            "#65A30D", "#DB2777", "#F97316", "#0EA5E9", "#14B8A6", "#A16207"]

# --- Schema ------------------------------------------------------------------
# Confidential fields are hidden / redacted when "Confidential mode" is on.
CONFIDENTIAL_FIELDS = ["plant_name", "contact_name", "designation", "mobile", "email"]

# Readiness indicators: storage key -> display label
READINESS_KEYS = [
    "r_whr", "r_afr", "r_power", "r_re", "r_enmgmt", "r_co2",
    "r_altraw", "r_roadmap", "r_team", "r_lowcarbon", "r_ccs",
]
READINESS_LABELS = [
    "Waste Heat Recovery", "AFR Co-processing", "On-site Power Gen",
    "Renewable Procurement", "Energy Mgmt System (ISO 50001)", "CO\u2082 Measurement",
    "Alternative Raw Materials", "Decarb Roadmap / Budget", "Cross-functional Team",
    "Low-carbon Products", "Carbon Capture (CCS/CCU)",
]
READINESS_KEY2LABEL = dict(zip(READINESS_KEYS, READINESS_LABELS))
READINESS_LABEL2KEY = dict(zip(READINESS_LABELS, READINESS_KEYS))

# Readiness <-> editable text
NUM2TXT = {1.0: "Yes", 0.5: "Pilot", 0.0: "No"}
TXT2NUM = {"Yes": 1.0, "Pilot": 0.5, "No": 0.0, "\u2014": None, "": None}
READINESS_TXT_OPTIONS = ["Yes", "Pilot", "No", "\u2014"]

# --- Qualitative (from the workbook's Graphs/Analysis sheets) -----------------
TOP_ENABLERS = [
    "Waste Heat Recovery Systems (WHRS)",
    "Alternative Fuels & Raw Materials (AFR)",
    "Strong Management / Leadership Commitment",
    "Strong Financial Position / Group Support",
    "Energy Efficiency & Process Optimization",
]
TOP_BARRIERS = [
    "High Capital Cost / Investment Constraints",
    "AFR Supply, Quality & Availability Issues",
    "Process Emissions from Limestone Calcination",
    "High Cost & Complexity of Carbon Capture",
    "Regulatory, Market & Demand Uncertainty",
]
PRIMARY_FUELS = ["Coal (Domestic / Imported)", "Pet Coke (Domestic / Imported)"]
SECONDARY_FUELS = ["Biomass", "RDF (Refuse-Derived Fuel)", "Plastic Waste",
                   "Solid Hazardous Waste", "Liquid Hazardous Waste"]


def load_raw_sheets() -> dict:
    """Read every sheet/cell of the original workbook verbatim."""
    xl = pd.ExcelFile(WORKBOOK_PATH)
    return {sn: pd.read_excel(xl, sheet_name=sn, header=None) for sn in xl.sheet_names}


# Positional confidential columns in the raw "Dataset" sheet
RAW_DATASET_CONF_COLS = [1, 3, 4, 5, 6]   # plant name, contact, designation, mobile, email
REDACT_TOKEN = "\U0001F512 REDACTED"


def redact_sheet(sheet_name: str, df: pd.DataFrame, secret_values: set) -> pd.DataFrame:
    """Return a copy with confidential values masked (for confidential mode)."""
    out = df.copy()
    # 1) positional redaction for the Dataset sheet's known confidential columns
    if sheet_name == "Dataset":
        for c in RAW_DATASET_CONF_COLS:
            if c in out.columns:
                mask = out.index >= 2  # keep the two header rows readable
                out.loc[mask, c] = out.loc[mask, c].where(out.loc[mask, c].isna(), REDACT_TOKEN)
    # 2) string redaction anywhere a known secret appears (names, emails, mobiles)
    secrets = [s for s in secret_values if isinstance(s, str) and len(s.strip()) >= 4]
    if secrets:
        pat = re.compile("|".join(re.escape(s) for s in secrets), re.IGNORECASE)
        mask = lambda v: REDACT_TOKEN if isinstance(v, str) and pat.search(v) else v
        for c in out.columns:
            out[c] = out[c].map(mask)
    return out
