# -*- coding: utf-8 -*-
"""
CJ Diagnostics — Farm Report (English, combo-box selection)

Run:
    streamlit run diag.py

What it does:
- Cascading combo boxes (Specie -> Farm -> Disease -> Result -> Period)
- Pick a single Farm via selectbox (not multi-filter), then build the dashboard + report
- KPIs, charts, disease summary, details
- Download HTML farm report (open in browser → print to PDF)
- Optional CSV/XLSX upload; uses embedded sample if empty
- Uses cj.jpg (logo) and cj_light.ttf (font) if present
"""

from __future__ import annotations
import io
import base64
from datetime import datetime, date, timedelta
from textwrap import dedent

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# ----------------------------------------------------
# Page / Theme
# ----------------------------------------------------
st.set_page_config(
    page_title="CJ Diagnostics — Farm Report",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom font / styles (optional)
FONT_CSS = dedent(
    """
    <style>
      @font-face { font-family: 'CJLight'; src: url('cj_light.ttf') format('truetype'); font-weight: 400; }
      html, body, [class^="css"], .stMarkdown, .stButton > button, .stMetric, .stDataFrame, .stTable, .stSelectbox, .stMultiSelect, .stTextInput, .stDateInput, .stSlider {
        font-family: 'CJLight', system-ui, -apple-system, Segoe UI, Roboto, 'Noto Sans KR', Arial, sans-serif !important;
        letter-spacing: .1px;
      }
      .hero { display:flex; align-items:center; gap:16px; }
      .hero img { border-radius: 10px; }
      .hero-title { font-size: 26px; font-weight: 800; }
      .hero-sub { color:#64748b; font-size: 13px; }
      .badge { display:inline-block; padding:4px 8px; border-radius:999px; font-size:12px; font-weight:600; color:white; }
      .pos { background:#d62828; }
      .neg { background:#2a9d8f; }
      .rea { background:#fb8500; }
      .card { border:1px solid #e9ecef; border-radius:16px; padding:16px; box-shadow: 0 2px 10px rgba(0,0,0,.04); background:#fff; height:100%; }
      .card h4 { margin:0 0 8px 0; font-weight:800; }
      .muted { color:#6c757d; font-size:13px; }
      .kpi { font-size:24px; font-weight:800; }
      .kpi-sub { font-size:12px; color:#6c757d; }
      .footnote { color:#8c8c8c; font-size: 12px; }
      .tbl th { background:#f7f7f7; }
    </style>
    """
)
st.markdown(FONT_CSS, unsafe_allow_html=True)

# ----------------------------------------------------
# Assets (logo optional)
# ----------------------------------------------------
logo_b64 = None
try:
    with open("cj.jpg", "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")
except Exception:
    pass

# ----------------------------------------------------
# Sample Data (embedded)
# ----------------------------------------------------
RAW = """number\tSample ID\tSpecie\tFarm Name\tDisease\tTest Date\tCT Value\tResult
1\t2025-001\tSwine\tAbcede\tASF\t2025.10.28\tNo Ct\tNegative
2\t2025-002\tSwine\tAbcede\tASF\t2025.10.28\tNo Ct\tNegative
3\t2025-003\tSwine\tAbcede\tASF\t2025.10.28\tNo Ct\tNegative
4\t2025-004\tSwine\tAbcede\tASF\t2025.10.28\tNo Ct\tNegative
5\t2025-005\tSwine\tAbcede\tASF\t2025.10.28\tNo Ct\tNegative
6\t2025-006\tSwine\tAbcede\tASF\t2025.10.28\tNo Ct\tNegative
7\t2025-007\tBroiler\tCJOY\tIBD\t2025.10.30\t31.5\tPositive
8\t2025-008\tBroiler\tCJOY\tIBD\t2025.10.30\t33.9\tRe-analysis
9\t2025-009\tBroiler\tCJOY\tReovirus\t2025.10.30\t29.2\tPositive
10\t2025-010\tBroiler\tCJOY\tReovirus\t2025.10.30\t35.6\tRe-analysis
11\t2025-011\tBroiler\tCJOY\tIBD\t2025.10.30\tNo Ct\tNegative
12\t2025-012\tBroiler\tCJOY\tIBD\t2025.10.30\t30.7\tPositive
13\t2025-013\tBroiler\tCJOY\tIBD\t2025.11.02\t34\tRe-analysis
14\t2025-014\tBroiler\tCJOY\tIBD\t2025.11.02\t31.8\tPositive
15\t2025-015\tBroiler\tCJOY\tIBD\t2025.11.02\t30.4\tPositive
16\t2025-016\tBroiler\tCJOY\tIBD\t2025.11.02\t33.7\tRe-analysis
17\t2025-017\tBroiler\tCJOY\tReovirus\t2025.11.02\t29.5\tPositive
18\t2025-018\tBroiler\tCJOY\tReovirus\t2025.11.02\t34.8\tRe-analysis
19\t2025-019\tBroiler\tCJOY\tIBD\t2025.11.03\t31.2\tPositive
20\t2025-020\tBroiler\tCJOY\tIBD\t2025.11.03\t34.7\tRe-analysis
21\t2025-021\tBroiler\tCJOY\tReovirus\t2025.11.03\t29.4\tPositive
22\t2025-022\tBroiler\tCJOY\tReovirus\t2025.11.03\t35.3\tRe-analysis
23\t2025-023\tSwine\tCreekview\tPRRS\t2025.10.28\t28.7\tPositive
24\t2025-024\tSwine\tCreekview\tPRRS\t2025.10.28\t31.4\tPositive
25\t2025-025\tSwine\tCreekview\tPRRS\t2025.10.28\t34.9\tRe-analysis
26\t2025-026\tSwine\tCreekview\tASF\t2025.10.28\tNo Ct\tNegative
27\t2025-027\tSwine\tCreekview\tPRRS\t2025.11.02\t28.9\tPositive
28\t2025-028\tSwine\tCreekview\tPRRS\t2025.11.02\t35.5\tRe-analysis
29\t2025-029\tSwine\tCreekview\tPRRS\t2025.11.02\t27.9\tPositive
30\t2025-030\tSwine\tCreekview\tPRRS\t2025.11.02\t35.4\tRe-analysis
31\t2025-031\tSwine\tCreekview\tPED\t2025.11.03\t30.2\tPositive
32\t2025-032\tSwine\tCreekview\tPED\t2025.11.03\t34.6\tRe-analysis
33\t2025-033\tSwine\tCreekview\tPED\t2025.11.03\t28.1\tPositive
34\t2025-034\tSwine\tCreekview\tPED\t2025.11.03\t34.5\tRe-analysis
35\t2025-035\tSwine\tDiamond Field\tASF\t2025.10.28\tNo Ct\tNegative
36\t2025-036\tSwine\tDiamond Field\tASF\t2025.10.28\tNo Ct\tNegative
37\t2025-037\tSwine\tDiamond Field\tASF\t2025.10.28\tNo Ct\tNegative
38\t2025-038\tSwine\tDiamond Field\tASF\t2025.10.28\tNo Ct\tNegative
39\t2025-039\tSwine\tDiamond Field\tPRRS\t2025.10.28\tNo Ct\tNegative
40\t2025-040\tSwine\tDiamond Field\tPRRS\t2025.10.28\tNo Ct\tNegative
41\t2025-041\tSwine\tDiamond Field\tPRRS\t2025.10.28\tNo Ct\tNegative
42\t2025-042\tSwine\tDiamond Field\tPRRS\t2025.10.28\tNo Ct\tNegative
43\t2025-043\tSwine\tFC Farm\tPED\t2025.11.09\t29.3\tPositive
44\t2025-044\tSwine\tFC Farm\tPED\t2025.11.09\t26.8\tPositive
45\t2025-045\tSwine\tFC Farm\tPED\t2025.11.09\tNo Ct\tNegative
46\t2025-046\tSwine\tFC Farm\tPED\t2025.11.09\tNo Ct\tNegative
47\t2025-047\tSwine\tFC Farm\tPED\t2025.11.09\t34.5\tRe-analysis
48\t2025-048\tSwine\tFC Farm\tPED\t2025.11.09\tNo Ct\tNegative
49\t2025-049\tSwine\tFC Farm\tPED\t2025.11.09\t32.1\tPositive
50\t2025-050\tSwine\tFC Farm\tPED\t2025.11.09\t35.8\tRe-analysis
51\t2025-051\tLayer\tFC Farm\tIBD\t2025.11.10\t30.2\tPositive
52\t2025-052\tLayer\tFC Farm\tIBD\t2025.11.10\t32.7\tPositive
53\t2025-053\tLayer\tFC Farm\tIBD\t2025.11.10\t32.5\tPositive
54\t2025-054\tLayer\tFC Farm\tIBD\t2025.11.10\t33.3\tRe-analysis
55\t2025-055\tSwine\tFC Farm\tPED\t2025.11.10\t28.5\tPositive
56\t2025-056\tSwine\tFC Farm\tPED\t2025.11.10\t35.1\tRe-analysis
57\t2025-057\tLayer\tFC Farm\tIBD\t2025.11.10\t33.8\tRe-analysis
58\t2025-058\tLayer\tFC Farm\tIBD\t2025.11.10\t32.9\tPositive
59\t2025-059\tLayer\tFML Agriventures Corp\tIBD\t2025.11.11\t34.2\tRe-analysis
60\t2025-060\tLayer\tFML Agriventures Corp\tIBD\t2025.11.11\t30.6\tPositive
61\t2025-061\tLayer\tFML Agriventures Corp\tIBD\t2025.11.11\t35\tRe-analysis
62\t2025-062\tLayer\tFML Agriventures Corp\tIBD\t2025.11.11\t35.2\tRe-analysis
63\t2025-063\tLayer\tFML Agriventures Corp\tIBD\t2025.11.11\t35.4\tRe-analysis
64\t2025-064\tLayer\tGuansing Farm\tReovirus\t2025.11.12\t31.6\tPositive
65\t2025-065\tLayer\tGuansing Farm\tReovirus\t2025.11.12\t28.4\tPositive
66\t2025-066\tLayer\tGuansing Farm\tReovirus\t2025.11.12\t33.4\tRe-analysis
67\t2025-067\tLayer\tGuansing Farm\tReovirus\t2025.11.12\t31.4\tPositive
68\t2025-068\tLayer\tGuansing Farm\tReovirus\t2025.11.12\t31.1\tPositive
69\t2025-069\tLayer\tKeena Farm\tIBD\t2025.11.19\t33.1\tRe-analysis
70\t2025-070\tLayer\tKeena Farm\tIBD\t2025.11.19\t33\tRe-analysis
71\t2025-071\tLayer\tKeena Farm\tIBD\t2025.11.19\t34.1\tRe-analysis
72\t2025-072\tLayer\tKeena Farm\tIBD\t2025.11.19\t34.3\tRe-analysis
73\t2025-073\tLayer\tKeena Farm\tIBD\t2025.11.19\t34.2\tRe-analysis
74\t2025-074\tLayer\tMiler Farm\tReovirus\t2025.11.20\t29.8\tPositive
75\t2025-075\tLayer\tMiler Farm\tReovirus\t2025.11.20\t35.3\tRe-analysis
76\t2025-076\tLayer\tMiler Farm\tReovirus\t2025.11.20\t31.9\tPositive
77\t2025-077\tLayer\tMiler Farm\tReovirus\t2025.11.20\t32.5\tPositive
78\t2025-078\tLayer\tMiler Farm\tReovirus\t2025.11.20\t32.3\tPositive
79\t2025-079\tSwine\tMM Farm\tASF\t2025.11.21\tNo Ct\tNegative
80\t2025-080\tLayer\tMM Farm\tReovirus\t2025.11.21\t28.9\tPositive
81\t2025-081\tSwine\tMM Farm\tASF\t2025.11.21\tNo Ct\tNegative
82\t2025-082\tLayer\tMM Farm\tReovirus\t2025.11.21\t34.1\tRe-analysis
83\t2025-083\tSwine\tMM Farm\tASF\t2025.11.21\tNo Ct\tNegative
84\t2025-084\tLayer\tMM Farm\tReovirus\t2025.11.21\t29.7\tPositive
85\t2025-085\tSwine\tMM Farm\tASF\t2025.11.21\tNo Ct\tNegative
86\t2025-086\tLayer\tMM Farm\tReovirus\t2025.11.21\t30\tPositive
87\t2025-087\tSwine\tMM Farm\tASF\t2025.11.21\tNo Ct\tNegative
88\t2025-088\tLayer\tMM Farm\tReovirus\t2025.11.21\t30.5\tPositive
89\t2025-089\tSwine\tMM Farm\tASF\t2025.11.22\tNo Ct\tNegative
90\t2025-090\tSwine\tPorkland\tPRRS\t2025.11.25\t33.5\tRe-analysis
91\t2025-091\tSwine\tPorkland\tPRRS\t2025.11.25\t29.9\tPositive
92\t2025-092\tSwine\tPorkland\tPRRS\t2025.11.25\t30.3\tPositive
93\t2025-093\tSwine\tPorkland\tPRRS\t2025.11.25\t30.8\tPositive
94\t2025-094\tSwine\tPorkland\tPRRS\t2025.11.25\t28.9\tPositive
95\t2025-095\tSwine\tPorkland\tPRRS\t2025.11.25\t29.7\tPositive
96\t2025-096\tLayer\tRamos Farm\tReovirus\t2025.11.26\t35.2\tRe-analysis
97\t2025-097\tLayer\tRamos Farm\tReovirus\t2025.11.26\t35.7\tRe-analysis
98\t2025-098\tLayer\tRamos Farm\tReovirus\t2025.11.26\t35.6\tRe-analysis
99\t2025-099\tLayer\tRamos Farm\tReovirus\t2025.11.26\t35.1\tRe-analysis
100\t2025-100\tLayer\tRamos Farm\tReovirus\t2025.11.26\t34.9\tRe-analysis
101\t2025-101\tSwine\tSinag\tASF\t2025.11.27\tNo Ct\tNegative
102\t2025-102\tSwine\tSinag\tASF\t2025.11.27\tNo Ct\tNegative
103\t2025-103\tSwine\tSinag\tASF\t2025.11.27\tNo Ct\tNegative
104\t2025-104\tSwine\tSinag\tASF\t2025.11.27\tNo Ct\tNegative
105\t2025-105\tSwine\tSinag\tASF\t2025.11.27\tNo Ct\tNegative
106\t2025-106\tSwine\tSinag\tASF\t2025.11.27\tNo Ct\tNegative
107\t2025-107\tLayer\tSLC Agri\tReovirus\t2025.11.28\tNo Ct\tNegative
108\t2025-108\tLayer\tSLC Agri\tReovirus\t2025.11.28\t31.2\tPositive
109\t2025-109\tLayer\tSLC Agri\tReovirus\t2025.11.28\t28.5\tPositive
110\t2025-110\tLayer\tSLC Agri\tReovirus\t2025.11.28\t29.9\tPositive
111\t2025-111\tLayer\tSLC Agri\tReovirus\t2025.11.28\t29.7\tPositive
112\t2025-112\tSwine\tSouthern Swine Paradise\tASF\t2025.11.29\tNo Ct\tNegative
113\t2025-113\tSwine\tSouthern Swine Paradise\tASF\t2025.11.29\tNo Ct\tNegative
114\t2025-114\tSwine\tSouthern Swine Paradise\tASF\t2025.11.29\tNo Ct\tNegative
115\t2025-115\tSwine\tSouthern Swine Paradise\tASF\t2025.11.29\tNo Ct\tNegative
116\t2025-116\tSwine\tSouthern Swine Paradise\tASF\t2025.11.29\tNo Ct\tNegative
117\t2025-117\tSwine\tSouthern Swine Paradise\tASF\t2025.11.29\tNo Ct\tNegative
118\t2025-118\tLayer\tVeriño’s Farm\tIBD\t2025.11.30\tNo Ct\tNegative
119\t2025-119\tLayer\tVeriño’s Farm\tIBD\t2025.11.30\tNo Ct\tNegative
120\t2025-120\tLayer\tVeriño’s Farm\tIBD\t2025.11.30\tNo Ct\tNegative
121\t2025-121\tLayer\tVeriño’s Farm\tIBD\t2025.11.30\tNo Ct\tNegative
122\t2025-122\tLayer\tVeriño’s Farm\tIBD\t2025.11.30\tNo Ct\tNegative
"""

# ----------------------------------------------------
# Data utils
# ----------------------------------------------------
def _std_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    need = {"number","Sample_ID","Specie","Farm_Name","Disease","Test_Date","CT_Value","Result"}
    miss = need - set(df.columns)
    if miss:
        raise ValueError(f"Missing columns: {sorted(miss)}")
    return df

def _parse_date_any(s: str) -> date:
    s = str(s).strip()
    for fmt in ("%Y.%m.%d","%Y-%m-%d","%Y/%m/%d","%m/%d/%Y","%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    # excel serial?
    try:
        base = datetime(1899,12,30)
        return (base + timedelta(days=float(s))).date()
    except Exception:
        raise ValueError(f"Failed to parse date: {s}")

def _to_float_ct(x):
    s = str(x).strip().lower()
    if s in {"", "na", "none", "nan", "no ct", "n/a"}:
        return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan

@st.cache_data(show_spinner=False)
def load_sample() -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(RAW), sep='\t')
    df = _std_columns(df)
    df['Test_Date'] = df['Test_Date'].astype(str).str.replace('.', '-', regex=False)
    df['Test_Date'] = df['Test_Date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d').date())
    df['CT_Value_Num'] = df['CT_Value'].apply(_to_float_ct)
    df['Result'] = (df['Result'].astype(str).str.strip().str.title()
                        .replace({'Re-Analysis':'Re-analysis','Re-Analysis':'Re-analysis'}))
    df['is_positive'] = df['Result'].eq('Positive')
    return df.sort_values(['Test_Date','Farm_Name','Disease','Sample_ID']).reset_index(drop=True)

@st.cache_data(show_spinner=False)
def read_any_file(uploaded) -> pd.DataFrame:
    if uploaded.name.lower().endswith('.csv'):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
    df = _std_columns(df)
    df['Test_Date'] = df['Test_Date'].apply(_parse_date_any)
    df['CT_Value_Num'] = df['CT_Value'].apply(_to_float_ct)
    df['Result'] = (df['Result'].astype(str).str.strip().str.title()
                        .replace({'Re-Analysis':'Re-analysis','Re-Analysis':'Re-analysis'}))
    df['is_positive'] = df['Result'].eq('Positive')
    return df.sort_values(['Test_Date','Farm_Name','Disease','Sample_ID']).reset_index(drop=True)

# ----------------------------------------------------
# Header
# ----------------------------------------------------
col_logo, col_title = st.columns([1,7], vertical_alignment="center")
with col_logo:
    if logo_b64:
        st.markdown(f"<div class='hero'><img src='data:image/jpeg;base64,{logo_b64}' width='64'/></div>", unsafe_allow_html=True)
    else:
        st.write(":triangular_flag_on_post: CJ F&C")
with col_title:
    st.markdown(
        """
        <div class='hero'>
          <div>
            <div class='hero-title'>CJ Diagnostics — Farm Report</div>
            <div class='hero-sub'>Cascading combo boxes with a single Farm selection</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ----------------------------------------------------
# Data source (upload or sample)
# ----------------------------------------------------
up = st.file_uploader("Upload data (CSV/XLSX). Leave empty to use the embedded sample.", type=["csv","xlsx","xls"])
DF = read_any_file(up) if up is not None else load_sample()

# ----------------------------------------------------
# Cascading combo boxes (Specie -> Farm -> Disease -> Result -> Period)
# ----------------------------------------------------
st.subheader("Selections")

ALL = "All"

# 1) Specie
specie_opts = [ALL] + sorted(DF["Specie"].unique().tolist())
specie = st.selectbox("Specie", specie_opts, index=0)

df1 = DF if specie == ALL else DF[DF["Specie"] == specie]

# 2) Farm (single select via combo box)
farm_opts = [ALL] + sorted(df1["Farm_Name"].unique().tolist())
farm = st.selectbox("Farm", farm_opts, index=0)

df2 = df1 if farm == ALL else df1[df1["Farm_Name"] == farm]

# 3) Disease (narrowed by previous)
disease_opts = [ALL] + sorted(df2["Disease"].unique().tolist())
disease = st.selectbox("Disease", disease_opts, index=0)

# 4) Result
result = st.selectbox("Result", [ALL, "Positive", "Negative", "Re-analysis"], index=0)

# 5) Period (auto range based on current candidate df2)
dmin, dmax = df2["Test_Date"].min(), df2["Test_Date"].max()
date_range = st.date_input("Period", (dmin, dmax))
if isinstance(date_range, tuple):
    d_start, d_end = date_range
else:
    d_start, d_end = dmin, dmax

# Build filtered dataframe safely (date-type safe)
TD = pd.to_datetime(df2["Test_Date"]).dt.date
mask = (TD >= d_start) & (TD <= d_end)
if disease != ALL:
    mask &= df2["Disease"].eq(disease)
if result != ALL:
    mask &= df2["Result"].eq(result)

fdf = df2.loc[mask].copy()

# ----------------------------------------------------
# KPIs
# ----------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

total = len(fdf)
pos = int(fdf['is_positive'].sum())
neg = int((fdf['Result'] == 'Negative').sum())
rea = int((fdf['Result'].str.lower() == 're-analysis').sum())
rate = (pos / total * 100.0) if total else 0.0

col1.metric("Total Tests", f"{total:,}")
col2.metric("Positive", f"{pos:,}")
col3.metric("Negative", f"{neg:,}")
col4.metric("Re-analysis", f"{rea:,}")
col5.metric("Positive Rate(%)", f"{rate:.1f}%")

st.caption("Note: CT≲30 strong positive, 33–36 borderline (re-test). 'No Ct' recorded as negative.")

# ----------------------------------------------------
# Overview Cards (for whichever farms remain in fdf)
# ----------------------------------------------------
st.subheader("Farms — Overview")
farms = sorted(fdf['Farm_Name'].unique())
cols = st.columns(3)
for i, fm in enumerate(farms):
    sub = fdf[fdf['Farm_Name'] == fm]
    if sub.empty:
        continue
    t = len(sub)
    p = int(sub['is_positive'].sum())
    n = int((sub['Result'] == 'Negative').sum())
    r = int((sub['Result'].str.lower() == 're-analysis').sum())
    pr = (p / t * 100.0) if t else 0
    last_date = sub['Test_Date'].max()
    with cols[i % 3]:
        st.markdown(
            f"""
            <div class='card'>
              <h4>{fm}</h4>
              <div class='muted'>Last test: {last_date}</div>
              <div style='margin:10px 0 12px 0;'>
                <span class='badge pos'>Positive {p}</span>
                <span class='badge neg' style='margin-left:6px;'>Negative {n}</span>
                <span class='badge rea' style='margin-left:6px;'>Re-analysis {r}</span>
              </div>
              <div class='kpi'>{pr:.1f}% <span class='kpi-sub'>Positive rate</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ----------------------------------------------------
# Charts
# ----------------------------------------------------
left, right = st.columns(2)
with left:
    st.subheader("By Specie × Result")
    if not fdf.empty:
        chart1 = alt.Chart(fdf).mark_bar().encode(
            x=alt.X('Specie:N', title='Specie'),
            y=alt.Y('count():Q', title='Count'),
            color=alt.Color('Result:N', legend=alt.Legend(title='Result')),
            column=alt.Column('Result:N', header=alt.Header(labelOrient='bottom', title=None)),
            tooltip=['Specie', 'Result', 'count()']
        ).properties(height=250)
        st.altair_chart(chart1, use_container_width=True)
    else:
        st.info('No data')

with right:
    st.subheader("By Disease × Result")
    if not fdf.empty:
        tmp = fdf.copy()
        tmp['Res2'] = tmp['Result'].replace({'Re-analysis':'Re-analysis'})
        chart2 = alt.Chart(tmp).mark_bar().encode(
            x=alt.X('Disease:N', title='Disease'),
            y=alt.Y('count():Q', title='Count'),
            color=alt.Color('Res2:N', legend=alt.Legend(title='Result')),
            tooltip=['Disease', 'Res2', 'count()']
        ).properties(height=250)
        st.altair_chart(chart2, use_container_width=True)
    else:
        st.info('No data')

st.subheader("Positive trend by Disease")
if not fdf.empty:
    line_df = fdf.groupby(['Test_Date','Disease'])['is_positive'].sum().reset_index(name='Positive_Count')
    chart3 = alt.Chart(line_df).mark_line(point=True).encode(
        x=alt.X('Test_Date:T', title='Date'),
        y=alt.Y('Positive_Count:Q', title='Positive (count)'),
        color='Disease:N',
        tooltip=['Test_Date:T','Disease:N','Positive_Count:Q']
    ).properties(height=280)
    st.altair_chart(chart3, use_container_width=True)
else:
    st.info('No data')

# ----------------------------------------------------
# Farm Report (English) — download HTML
# ----------------------------------------------------
st.subheader("Farm Report (English)")

# Default report farm = currently selected combo-box farm (if not ALL)
if farm != ALL and farm in farms:
    default_idx = farms.index(farm)
else:
    default_idx = 0 if farms else None

rep_farm = st.selectbox("Choose a farm for the report", options=farms, index=default_idx)

if rep_farm:
    rep = fdf[fdf['Farm_Name'] == rep_farm].copy()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Samples", f"{len(rep):,}")
    c2.metric("Positive", int(rep['is_positive'].sum()))
    c3.metric("Negative", int((rep['Result'] == 'Negative').sum()))
    c4.metric("Re-analysis", int((rep['Result'].str.lower() == 're-analysis').sum()))

    pivot = (rep.pivot_table(index='Disease', columns='Result', values='number', aggfunc='count', fill_value=0)
                .reset_index().rename_axis(None, axis=1))

    st.write("By disease (summary)")
    st.dataframe(pivot, use_container_width=True)

    view_cols = ['Sample_ID','Specie','Disease','Test_Date','CT_Value','Result']
    rep_view = rep.loc[:, view_cols].sort_values(['Disease','Test_Date','Sample_ID'])
    st.write("Details")
    st.dataframe(rep_view, use_container_width=True, hide_index=True)

    # HTML report generator (English)
    def df_to_html_table(df: pd.DataFrame) -> str:
        df2 = df.copy()
        if 'Test_Date' in df2.columns:
            df2['Test_Date'] = df2['Test_Date'].astype(str)
        return df2.to_html(index=False, classes='tbl', border=0, justify='center')

    def make_farm_report_html(farm_name: str) -> bytes:
        sub = rep.copy().sort_values(['Disease','Test_Date','Sample_ID'])
        total = len(sub)
        pos_cnt = int(sub['is_positive'].sum())
        neg_cnt = int((sub['Result'] == 'Negative').sum())
        rea_cnt = int((sub['Result'].str.lower() == 're-analysis').sum())
        rate = (pos_cnt/total*100.0) if total else 0.0
        last_date = sub['Test_Date'].max()

        logo_html = f"<img src='data:image/jpeg;base64,{logo_b64}' width='80'/>" if logo_b64 else "<b>CJ F&C</b>"
        summary_rows = [
            ("Total Tests", f"{total:,}"),
            ("Positive", f"{pos_cnt:,}"),
            ("Negative", f"{neg_cnt:,}"),
            ("Re-analysis", f"{rea_cnt:,}"),
            ("Positive Rate", f"{rate:.1f}%"),
            ("Last Test Date", str(last_date)),
        ]
        summary_html = "".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in summary_rows])

        pivot_html = df_to_html_table(pivot)
        table_html = df_to_html_table(sub[view_cols])

        html = f"""
        <html>
        <head>
          <meta charset='utf-8'/>
          <style>
            @font-face {{ font-family: CJLight; src: url('cj_light.ttf') format('truetype'); }}
            body {{ font-family: CJLight, -apple-system, Segoe UI, Roboto, 'Noto Sans KR', Arial; margin: 24px; color:#111; }}
            .hdr {{ display:flex; align-items:center; gap:14px; margin-bottom: 12px; }}
            .title {{ font-size: 22px; font-weight: 800; }}
            .sub {{ color:#666; }}
            .grid {{ display:grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 10px 0 16px; }}
            .card {{ border:1px solid #eaeaea; border-radius: 12px; padding: 12px; }}
            table.tbl {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
            table.tbl th, table.tbl td {{ border:1px solid #ececec; padding: 8px 10px; text-align:center; }}
            table.tbl th {{ background:#f7f7f7; }}
            .foot {{ margin-top: 16px; color:#888; font-size: 12px; }}
          </style>
        </head>
        <body>
          <div class='hdr'>{logo_html} <div><div class='title'>Farm Report — {farm_name}</div><div class='sub'>Summary of diagnostics results</div></div></div>
          <div class='grid'>
            <div class='card'>
              <b>Key Metrics</b>
              <table class='tbl' style='margin-top:8px;'>
                {summary_html}
              </table>
            </div>
            <div class='card'>
              <b>By Disease</b>
              <div style='margin-top:8px;'>{pivot_html}</div>
            </div>
          </div>
          <div class='card'>
            <b>Details</b>
            <div style='margin-top:8px;'>{table_html}</div>
          </div>
          <div class='foot'>Note: CT≲30 strong positive, 33–36 borderline (re-test). 'No Ct' recorded as negative.</div>
        </body>
        </html>
        """
        return html.encode('utf-8')

    html_bytes = make_farm_report_html(rep_farm)
    st.download_button(
        label="📄 Download HTML Report",
        data=html_bytes,
        file_name=f"{rep_farm.replace(' ', '_')}_report.html",
        mime="text/html",
        help="Open the HTML and print to PDF for a ready-to-share report."
    )

# ----------------------------------------------------
# Raw table
# ----------------------------------------------------
st.divider()
st.subheader("Filtered Data")
show_cols = ['number','Sample_ID','Specie','Farm_Name','Disease','Test_Date','CT_Value','Result']
st.dataframe(fdf[show_cols], use_container_width=True, hide_index=True)

st.markdown("<div class='footnote'>© CJ Feed & Care — Diagnostics Dashboard</div>", unsafe_allow_html=True)
