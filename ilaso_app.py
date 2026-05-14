
# ============================================================
# ILASO
# Intelligent Lecturer Allocation with Stability-Aware Optimization
# Standalone Streamlit App
# ============================================================
# Run:
# streamlit run ilaso_app.py
#
# Install:
# pip install streamlit pandas numpy openpyxl pulp plotly
# ============================================================

import io
import math
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd
import streamlit as st

try:
    import plotly.express as px
except Exception:
    px = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ILASO",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# THEME CSS
# ============================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #F7F9FC;
    }
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }
    .ilaso-hero {
        background: linear-gradient(135deg, #071A3D 0%, #0B2F6B 55%, #123C7C 100%);
        padding: 28px 34px;
        border-radius: 24px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 14px 40px rgba(7, 26, 61, 0.18);
    }
    .ilaso-title {
        font-size: 38px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    .ilaso-subtitle {
        font-size: 17px;
        color: #E8EEF9;
        margin-bottom: 10px;
    }
    .ilaso-tag {
        display: inline-block;
        background: rgba(245, 197, 66, 0.18);
        color: #F8D66D;
        border: 1px solid rgba(248, 214, 109, 0.55);
        padding: 7px 12px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 13px;
    }
    .metric-card {
        background: white;
        border-radius: 18px;
        padding: 18px 18px;
        box-shadow: 0 8px 28px rgba(20, 55, 130, 0.08);
        border: 1px solid #E8EDF5;
        min-height: 118px;
    }
    .metric-label {
        font-size: 13px;
        color: #667085;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .metric-value {
        font-size: 30px;
        color: #071A3D;
        font-weight: 850;
        margin-top: 5px;
    }
    .metric-note {
        font-size: 12px;
        color: #7A869A;
        margin-top: 4px;
    }
    .section-title {
        color: #071A3D;
        font-size: 22px;
        font-weight: 800;
        margin-top: 12px;
        margin-bottom: 8px;
    }
    .soft-box {
        background: white;
        border-radius: 18px;
        padding: 18px;
        border: 1px solid #E8EDF5;
        box-shadow: 0 8px 24px rgba(20, 55, 130, 0.06);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="ilaso-hero">
        <div class="ilaso-title">ILASO</div>
        <div class="ilaso-subtitle">Intelligent Lecturer Allocation with Stability-Aware Optimization</div>
        <span class="ilaso-tag">Fair. Stable. Intelligent Academic Allocation.</span>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# SIDEBAR SETTINGS
# ============================================================

st.sidebar.title("⚙️ ILASO Control Panel")

st.sidebar.subheader("Semester")
semester_weeks = st.sidebar.number_input("Jumlah minggu semester", 1, 30, 14, 1)

st.sidebar.subheader("Workload")
default_min = st.sidebar.number_input("Default minimum kredit", 0, 40, 15, 1)
default_max = st.sidebar.number_input("Default maksimum kredit", 0, 40, 18, 1)
target_credit = st.sidebar.number_input("Target kredit adil", 1, 40, 15, 1)

st.sidebar.subheader("Teaching Limits")
max_subjects = st.sidebar.number_input("Maksimum subjek unik per pensyarah", 1, 5, 2, 1)
max_kelas_baru_per_subject = st.sidebar.number_input(
    "Maksimum kelas_baru bagi subjek sama",
    1, 10, 2, 1
)

st.sidebar.subheader("Preference Score")
score_p1 = st.sidebar.number_input("Pilihan 1", -1000, 1000, 100, 5)
score_p2 = st.sidebar.number_input("Pilihan 2", -1000, 1000, 80, 5)
score_p3 = st.sidebar.number_input("Pilihan 3", -1000, 1000, 60, 5)
score_p4 = st.sidebar.number_input("Pilihan 4", -1000, 1000, 40, 5)
score_p5 = st.sidebar.number_input("Pilihan 5", -1000, 1000, 20, 5)
score_not_pref = st.sidebar.number_input("Bukan pilihan", -1000, 1000, -20, 5)

st.sidebar.subheader("Optimization Weights")
w_fairness = st.sidebar.number_input("Fairness / balance", 1, 100000, 3000, 100)
w_under_min = st.sidebar.number_input("Penalti bawah minimum", 1, 100000, 5000, 100)
w_no_class = st.sidebar.number_input("Penalti pensyarah aktif tiada kelas", 1, 100000, 8000, 100)
w_preference = st.sidebar.number_input("Preference reward", 1, 100000, 70, 10)
w_stability = st.sidebar.number_input("Stability / kekalkan agihan lama", 0, 100000, 2500, 100)
w_partial = st.sidebar.number_input("Penalti partial availability", 0, 100000, 300, 50)

st.sidebar.subheader("Mode")
mode = st.sidebar.radio(
    "Mode Agihan",
    [
        "Initial Allocation",
        "Stability-Aware Rebalance"
    ],
    index=0
)

force_lock = st.sidebar.checkbox(
    "Paksa kekalkan lock_agihan = YA",
    value=True,
    help="Jika ON, kelas yang ada pensyarah_asal dan lock_agihan=YA akan dikekalkan selagi kelas masih BUKA/BARU."
)

allow_partial = st.sidebar.checkbox(
    "Benarkan pensyarah partial semester diberi loading",
    value=True
)

# ============================================================
# FILE UPLOAD
# ============================================================

st.markdown('<div class="section-title">1. Upload Data</div>', unsafe_allow_html=True)

u1, u2 = st.columns(2)

with u1:
    file_classes = st.file_uploader(
        "Upload Jadual Kelas / Kelas_Baru (.xlsx / .csv)",
        type=["xlsx", "csv"],
        help="Wajib ada: kod_kursus, kelas_baru, jam_kredit. Optional: status_kelas, pensyarah_asal, lock_agihan."
    )

with u2:
    file_lect = st.file_uploader(
        "Upload Pensyarah + Preference + Availability (.xlsx / .csv)",
        type=["xlsx", "csv"],
        help="Wajib ada: Nama Pensyarah, Peranan, Minimum Jam Kredit, Maksimum Jam Kredit, Pilihan 1-5."
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def read_file(uploaded_file, expected_sheet=None):
    name = uploaded_file.name.lower()

    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file, encoding="utf-8-sig")

    xl = pd.ExcelFile(uploaded_file)

    if expected_sheet and expected_sheet in xl.sheet_names:
        return pd.read_excel(uploaded_file, sheet_name=expected_sheet)

    return pd.read_excel(uploaded_file, sheet_name=xl.sheet_names[0])


def clean_text(x):
    if pd.isna(x):
        return ""
    x = str(x).strip().upper()
    if x in ["NAN", "NONE", "-", ""]:
        return ""
    return x


def clean_name(x):
    if pd.isna(x):
        return ""
    return str(x).strip()


def standardize_status(x):
    x = clean_text(x)
    if x in ["", "OPEN", "AKTIF"]:
        return "BUKA"
    if x in ["CLOSE", "CLOSED", "CANCEL", "CANCELLED", "BATAL"]:
        return "TUTUP"
    if x in ["NEW", "BAHARU"]:
        return "BARU"
    return x


def load_data(file_classes, file_lect):
    dfc = read_file(file_classes, expected_sheet="Jadual_Kelas")
    dfl_raw = read_file(file_lect, expected_sheet="Pensyarah")

    required_classes = ["kod_kursus", "kelas_baru", "jam_kredit"]
    missing_classes = [c for c in required_classes if c not in dfc.columns]
    if missing_classes:
        st.error(f"Fail kelas tiada column wajib: {missing_classes}")
        st.stop()

    required_lect = [
        "Nama Pensyarah",
        "Peranan",
        "Minimum Jam Kredit",
        "Maksimum Jam Kredit"
    ]
    missing_lect = [c for c in required_lect if c not in dfl_raw.columns]
    if missing_lect:
        st.error(f"Fail pensyarah tiada column wajib: {missing_lect}")
        st.stop()

    # -------------------------------
    # Classes
    # -------------------------------
    dfc = dfc.copy()

    dfc["kod_kursus"] = dfc["kod_kursus"].map(clean_text)
    dfc["kelas_baru"] = dfc["kelas_baru"].astype(str).str.strip()
    dfc["jam_kredit"] = pd.to_numeric(dfc["jam_kredit"], errors="coerce").fillna(0).astype(int)

    if "saiz_kelas" not in dfc.columns:
        dfc["saiz_kelas"] = ""
    else:
        dfc["saiz_kelas"] = pd.to_numeric(dfc["saiz_kelas"], errors="coerce").fillna(0).astype(int)

    for col in ["campuran_group", "perincian", "kredit_info"]:
        if col not in dfc.columns:
            dfc[col] = ""

    if "status_kelas" not in dfc.columns:
        dfc["status_kelas"] = "BUKA"

    dfc["status_kelas"] = dfc["status_kelas"].map(standardize_status)

    if "pensyarah_asal" not in dfc.columns:
        dfc["pensyarah_asal"] = ""
    dfc["pensyarah_asal"] = dfc["pensyarah_asal"].map(clean_name)

    if "lock_agihan" not in dfc.columns:
        dfc["lock_agihan"] = "TIDAK"
    dfc["lock_agihan"] = dfc["lock_agihan"].map(clean_text)
    dfc["lock_agihan"] = dfc["lock_agihan"].replace({"YES": "YA", "Y": "YA", "TRUE": "YA", "1": "YA"})

    if "minggu_mula_kelas" not in dfc.columns:
        dfc["minggu_mula_kelas"] = 1
    if "minggu_akhir_kelas" not in dfc.columns:
        dfc["minggu_akhir_kelas"] = semester_weeks

    dfc["minggu_mula_kelas"] = pd.to_numeric(dfc["minggu_mula_kelas"], errors="coerce").fillna(1).astype(int)
    dfc["minggu_akhir_kelas"] = pd.to_numeric(dfc["minggu_akhir_kelas"], errors="coerce").fillna(semester_weeks).astype(int)

    dfc = dfc[
        (dfc["kod_kursus"] != "") &
        (dfc["kelas_baru"] != "") &
        (dfc["jam_kredit"] > 0)
    ].copy()

    dfc["kelas_id"] = dfc["kod_kursus"] + "-" + dfc["kelas_baru"].astype(str)
    dfc = dfc.drop_duplicates(subset=["kelas_id"], keep="first").copy()

    closed_df = dfc[dfc["status_kelas"] == "TUTUP"].copy()
    active_classes = dfc[dfc["status_kelas"].isin(["BUKA", "BARU"])].copy()

    # -------------------------------
    # Lecturers
    # -------------------------------
    dfl = dfl_raw.rename(columns={
        "Nama Pensyarah": "nama",
        "Peranan": "peranan",
        "Minimum Jam Kredit": "min_kredit",
        "Maksimum Jam Kredit": "max_kredit"
    }).copy()

    dfl["nama"] = dfl["nama"].map(clean_name)
    dfl["peranan"] = dfl["peranan"].astype(str).str.strip()

    dfl["min_kredit"] = pd.to_numeric(dfl["min_kredit"], errors="coerce").fillna(default_min).astype(int)
    dfl["max_kredit"] = pd.to_numeric(dfl["max_kredit"], errors="coerce").fillna(default_max).astype(int)
    dfl.loc[dfl["min_kredit"] > dfl["max_kredit"], "min_kredit"] = dfl["max_kredit"]

    for i in range(1, 6):
        col = f"Pilihan {i}"
        if col in dfl_raw.columns:
            dfl[col] = dfl_raw[col].map(clean_text)
        else:
            dfl[col] = ""

    if "minggu_mula_available" not in dfl.columns:
        dfl["minggu_mula_available"] = 1
    if "minggu_akhir_available" not in dfl.columns:
        dfl["minggu_akhir_available"] = semester_weeks

    dfl["minggu_mula_available"] = pd.to_numeric(
        dfl["minggu_mula_available"], errors="coerce"
    ).fillna(1).astype(int)

    dfl["minggu_akhir_available"] = pd.to_numeric(
        dfl["minggu_akhir_available"], errors="coerce"
    ).fillna(semester_weeks).astype(int)

    if "status" not in dfl.columns:
        dfl["status"] = "AKTIF"
    dfl["status"] = dfl["status"].map(clean_text)
    dfl["status"] = dfl["status"].replace({"": "AKTIF"})

    if "allow_partial_loading" not in dfl.columns:
        dfl["allow_partial_loading"] = "TIDAK"
    dfl["allow_partial_loading"] = dfl["allow_partial_loading"].map(clean_text)
    dfl["allow_partial_loading"] = dfl["allow_partial_loading"].replace({
        "YES": "YA", "Y": "YA", "TRUE": "YA", "1": "YA"
    })

    if "catatan" not in dfl.columns:
        dfl["catatan"] = ""

    dfl["available_weeks"] = (
        dfl["minggu_akhir_available"] - dfl["minggu_mula_available"] + 1
    ).clip(lower=0, upper=semester_weeks)

    dfl["availability_ratio"] = dfl["available_weeks"] / float(semester_weeks)

    # Effective max/min for partial availability
    dfl["effective_max_kredit"] = dfl["max_kredit"]
    dfl["effective_min_kredit"] = dfl["min_kredit"]

    partial_mask = dfl["available_weeks"] < semester_weeks

    if allow_partial:
        dfl.loc[partial_mask, "effective_max_kredit"] = np.floor(
            dfl.loc[partial_mask, "max_kredit"] * dfl.loc[partial_mask, "availability_ratio"]
        ).astype(int)

        dfl.loc[partial_mask, "effective_min_kredit"] = np.floor(
            dfl.loc[partial_mask, "min_kredit"] * dfl.loc[partial_mask, "availability_ratio"]
        ).astype(int)
    else:
        dfl.loc[partial_mask, ["effective_max_kredit", "effective_min_kredit"]] = 0

    # Cuti penuh or no availability
    cuti_mask = (
        dfl["peranan"].str.lower().str.contains("cuti", na=False) |
        dfl["status"].isin(["CUTI", "CUTI_BERSALIN", "SABBATICAL", "TIDAK_AKTIF"])
    ) & (dfl["allow_partial_loading"] != "YA")

    dfl.loc[cuti_mask, ["effective_max_kredit", "effective_min_kredit"]] = 0

    dfl["active"] = dfl["effective_max_kredit"] > 0

    dfl = dfl[dfl["nama"] != ""].drop_duplicates(subset=["nama"], keep="first").copy()

    return active_classes, closed_df, dfl


def build_preference_score(dfl):
    rank_score = {
        1: score_p1,
        2: score_p2,
        3: score_p3,
        4: score_p4,
        5: score_p5,
    }

    pref_score = {}

    for _, row in dfl.iterrows():
        lname = row["nama"]
        for i in range(1, 6):
            subj = clean_text(row.get(f"Pilihan {i}", ""))
            if subj:
                pref_score[(lname, subj)] = max(
                    pref_score.get((lname, subj), -9999),
                    rank_score[i]
                )

    return pref_score


def get_pref_score(lname, subject, pref_score):
    return int(pref_score.get((lname, subject), score_not_pref))


def get_pref_label(lname, subject, dfl):
    row = dfl[dfl["nama"] == lname]
    if row.empty:
        return "Tidak diketahui"

    row = row.iloc[0]
    for i in range(1, 6):
        if clean_text(row.get(f"Pilihan {i}", "")) == subject:
            return f"Pilihan {i}"
    return "Bukan pilihan"


def is_available_for_class(lect_row, class_row):
    # Simple overlap requirement:
    # lecturer must overlap with class at least 1 week.
    # For full-semester allocation, the system still uses effective loading.
    lm = int(lect_row["minggu_mula_available"])
    le = int(lect_row["minggu_akhir_available"])
    cm = int(class_row["minggu_mula_kelas"])
    ce = int(class_row["minggu_akhir_kelas"])
    return max(lm, cm) <= min(le, ce)


def build_coverage(dfc, dfl):
    rows = []
    for s in sorted(dfc["kod_kursus"].unique()):
        pemilih = []
        for _, r in dfl.iterrows():
            for i in range(1, 6):
                if clean_text(r.get(f"Pilihan {i}", "")) == s:
                    pemilih.append(f"{r['nama']} (P{i})")

        rows.append({
            "kod_kursus": s,
            "bil_kelas_baru": int((dfc["kod_kursus"] == s).sum()),
            "jumlah_kredit": int(dfc.loc[dfc["kod_kursus"] == s, "jam_kredit"].sum()),
            "bil_pemilih": len(pemilih),
            "senarai_pemilih": "; ".join(pemilih)
        })
    return pd.DataFrame(rows)


def solve_milp(dfc, dfl, pref_score):
    import pulp as pl

    classes = dfc["kelas_id"].tolist()
    lecturers = dfl["nama"].tolist()
    subjects = sorted(dfc["kod_kursus"].unique().tolist())

    credit = dfc.set_index("kelas_id")["jam_kredit"].astype(int).to_dict()
    cls_subject = dfc.set_index("kelas_id")["kod_kursus"].to_dict()
    cls_status = dfc.set_index("kelas_id")["status_kelas"].to_dict()
    cls_pensyarah_asal = dfc.set_index("kelas_id")["pensyarah_asal"].to_dict()
    cls_lock = dfc.set_index("kelas_id")["lock_agihan"].to_dict()

    min_k = dfl.set_index("nama")["effective_min_kredit"].astype(int).to_dict()
    max_k = dfl.set_index("nama")["effective_max_kredit"].astype(int).to_dict()
    active = dfl.set_index("nama")["active"].to_dict()
    available_weeks = dfl.set_index("nama")["available_weeks"].astype(int).to_dict()

    prob = pl.LpProblem("ILASO_Stability_Aware_Allocation", pl.LpMinimize)

    x = pl.LpVariable.dicts("x", (classes, lecturers), 0, 1, cat="Binary")
    y = pl.LpVariable.dicts("y", (lecturers, subjects), 0, 1, cat="Binary")
    z = pl.LpVariable.dicts("z", lecturers, 0, 1, cat="Binary")

    under_min = pl.LpVariable.dicts("under_min", lecturers, lowBound=0, cat="Continuous")
    over_target = pl.LpVariable.dicts("over_target", lecturers, lowBound=0, cat="Continuous")
    under_target = pl.LpVariable.dicts("under_target", lecturers, lowBound=0, cat="Continuous")

    # --------------------------------------------------------
    # Every active class must be assigned exactly once
    # --------------------------------------------------------
    for c in classes:
        prob += pl.lpSum(x[c][l] for l in lecturers) == 1

    # --------------------------------------------------------
    # Inactive lecturers cannot teach
    # --------------------------------------------------------
    for l in lecturers:
        if not active[l]:
            for c in classes:
                prob += x[c][l] == 0

    # --------------------------------------------------------
    # Availability overlap
    # --------------------------------------------------------
    lect_rows = dfl.set_index("nama")
    class_rows = dfc.set_index("kelas_id")

    for c in classes:
        crow = class_rows.loc[c]
        for l in lecturers:
            lrow = lect_rows.loc[l]
            if not is_available_for_class(lrow, crow):
                prob += x[c][l] == 0

    # --------------------------------------------------------
    # Force lock old allocation if selected
    # --------------------------------------------------------
    valid_lecturers = set(lecturers)

    if mode == "Stability-Aware Rebalance" and force_lock:
        for c in classes:
            asal = str(cls_pensyarah_asal.get(c, "")).strip()
            lock = str(cls_lock.get(c, "")).strip().upper()

            if asal in valid_lecturers and lock == "YA":
                # Only force if lecturer is active and available for that class
                if active.get(asal, False) and is_available_for_class(lect_rows.loc[asal], class_rows.loc[c]):
                    for l in lecturers:
                        prob += x[c][l] == (1 if l == asal else 0)

    # --------------------------------------------------------
    # Max workload credit
    # --------------------------------------------------------
    for l in lecturers:
        load = pl.lpSum(credit[c] * x[c][l] for c in classes)
        prob += load <= max_k[l]

    # --------------------------------------------------------
    # Link x to subject y
    # --------------------------------------------------------
    for c in classes:
        s = cls_subject[c]
        for l in lecturers:
            prob += x[c][l] <= y[l][s]

    # --------------------------------------------------------
    # Max unique subjects per lecturer
    # --------------------------------------------------------
    for l in lecturers:
        prob += pl.lpSum(y[l][s] for s in subjects) <= int(max_subjects)

    # --------------------------------------------------------
    # Max kelas_baru for same subject per lecturer
    # --------------------------------------------------------
    for l in lecturers:
        for s in subjects:
            subject_classes = [c for c in classes if cls_subject[c] == s]
            prob += pl.lpSum(x[c][l] for c in subject_classes) <= int(max_kelas_baru_per_subject)

    # --------------------------------------------------------
    # Lecturer has class indicator
    # --------------------------------------------------------
    big_m = len(classes)
    for l in lecturers:
        total_class_l = pl.lpSum(x[c][l] for c in classes)
        prob += total_class_l <= big_m * z[l]
        if active[l]:
            prob += total_class_l >= z[l]
        else:
            prob += z[l] == 0

    # --------------------------------------------------------
    # Fairness
    # --------------------------------------------------------
    for l in lecturers:
        load = pl.lpSum(credit[c] * x[c][l] for c in classes)

        if active[l]:
            effective_target = min(int(target_credit), max_k[l])
            prob += load + under_min[l] >= min_k[l]
            prob += load - effective_target <= over_target[l]
            prob += effective_target - load <= under_target[l]
        else:
            prob += under_min[l] == 0
            prob += over_target[l] == 0
            prob += under_target[l] == 0

    # --------------------------------------------------------
    # Objective
    # --------------------------------------------------------
    preference_reward = pl.lpSum(
        credit[c] * get_pref_score(l, cls_subject[c], pref_score) * x[c][l]
        for c in classes
        for l in lecturers
    )

    fairness_penalty = pl.lpSum(
        under_target[l] + over_target[l]
        for l in lecturers
        if active[l]
    )

    under_min_penalty = pl.lpSum(
        under_min[l]
        for l in lecturers
        if active[l]
    )

    no_class_penalty = pl.lpSum(
        1 - z[l]
        for l in lecturers
        if active[l]
    )

    # Stability reward: preserve old assignment without forcing it
    stability_reward = 0
    if mode == "Stability-Aware Rebalance":
        stability_reward = pl.lpSum(
            x[c][l]
            for c in classes
            for l in lecturers
            if str(cls_pensyarah_asal.get(c, "")).strip() == l
        )

    # Partial penalty: avoid using partial lecturers unless needed/preferred
    partial_penalty = pl.lpSum(
        (semester_weeks - available_weeks[l]) * x[c][l]
        for c in classes
        for l in lecturers
        if active[l] and available_weeks[l] < semester_weeks
    )

    prob += (
        w_fairness * fairness_penalty
        + w_under_min * under_min_penalty
        + w_no_class * no_class_penalty
        - w_preference * preference_reward
        - w_stability * stability_reward
        + w_partial * partial_penalty
    )

    solver = pl.PULP_CBC_CMD(msg=False, timeLimit=240)
    prob.solve(solver)

    status = pl.LpStatus[prob.status]

    x_assign = {}
    for c in classes:
        for l in lecturers:
            x_assign[(c, l)] = float(pl.value(x[c][l]) or 0)

    return status, x_assign


def build_outputs(dfc, dfl, pref_score, x_assign):
    rows = []
    lect_lookup = dfl.set_index("nama")

    for (cid, lname), val in x_assign.items():
        if val > 0.5:
            r = dfc[dfc["kelas_id"] == cid].iloc[0]
            subj = r["kod_kursus"]
            lrow = lect_lookup.loc[lname]

            asal = str(r.get("pensyarah_asal", "")).strip()
            changed = "YA" if asal and asal != lname else "TIDAK"

            rows.append({
                "kelas_id": cid,
                "kod_kursus": subj,
                "kelas_baru": r["kelas_baru"],
                "status_kelas": r["status_kelas"],
                "saiz_kelas": r.get("saiz_kelas", ""),
                "campuran_group_asal": r.get("campuran_group", ""),
                "perincian_group_asal": r.get("perincian", ""),
                "jam_kredit": int(r["jam_kredit"]),
                "minggu_mula_kelas": int(r["minggu_mula_kelas"]),
                "minggu_akhir_kelas": int(r["minggu_akhir_kelas"]),
                "pensyarah": lname,
                "peranan": lrow["peranan"],
                "status_pensyarah": lrow["status"],
                "available_weeks": int(lrow["available_weeks"]),
                "padanan_pilihan": get_pref_label(lname, subj, dfl),
                "skor_pilihan": get_pref_score(lname, subj, pref_score),
                "pensyarah_asal": asal,
                "lock_agihan": r.get("lock_agihan", ""),
                "berubah_dari_asal": changed,
            })

    df_assign = pd.DataFrame(rows)

    if not df_assign.empty:
        df_assign = df_assign.sort_values(["pensyarah", "kod_kursus", "kelas_baru"])

    assigned_ids = set(df_assign["kelas_id"]) if not df_assign.empty else set()
    all_ids = set(dfc["kelas_id"])
    df_unassigned = dfc[dfc["kelas_id"].isin(sorted(all_ids - assigned_ids))].copy()

    summary_rows = []

    for _, row in dfl.iterrows():
        lname = row["nama"]
        active = bool(row["active"])

        tmp = df_assign[df_assign["pensyarah"] == lname] if not df_assign.empty else pd.DataFrame()

        total_credit = int(tmp["jam_kredit"].sum()) if not tmp.empty else 0
        total_kelas = int(len(tmp)) if not tmp.empty else 0
        unique_subjects = sorted(tmp["kod_kursus"].unique()) if not tmp.empty else []

        ikut_pilihan = 0
        bukan_pilihan = 0
        berubah = 0

        if not tmp.empty:
            ikut_pilihan = int(tmp["padanan_pilihan"].str.startswith("Pilihan").sum())
            bukan_pilihan = int((tmp["padanan_pilihan"] == "Bukan pilihan").sum())
            berubah = int((tmp["berubah_dari_asal"] == "YA").sum())

        min_eff = int(row["effective_min_kredit"])
        max_eff = int(row["effective_max_kredit"])
        effective_target = min(int(target_credit), max_eff) if max_eff > 0 else 0

        summary_rows.append({
            "pensyarah": lname,
            "peranan": row["peranan"],
            "status_pensyarah": row["status"],
            "aktif": active,
            "minggu_mula_available": int(row["minggu_mula_available"]),
            "minggu_akhir_available": int(row["minggu_akhir_available"]),
            "available_weeks": int(row["available_weeks"]),
            "minimum_asal": int(row["min_kredit"]),
            "maksimum_asal": int(row["max_kredit"]),
            "minimum_efektif": min_eff,
            "maksimum_efektif": max_eff,
            "target_efektif": effective_target,
            "jumlah_kelas_baru_ajar": total_kelas,
            "jumlah_jam_kredit": total_credit,
            "bil_subjek_unik": len(unique_subjects),
            "senarai_subjek": ", ".join(unique_subjects),
            "kelas_baru_ikut_pilihan": ikut_pilihan,
            "kelas_baru_bukan_pilihan": bukan_pilihan,
            "kelas_berubah_dari_asal": berubah,
            "kurang_minimum": max(min_eff - total_credit, 0) if active else 0,
            "lebih_target": max(total_credit - effective_target, 0) if active else 0,
            "status_agihan": "OK" if (not active or total_kelas > 0) else "TIADA KELAS"
        })

    df_summary = pd.DataFrame(summary_rows)

    df_subject_check = pd.DataFrame()
    if not df_assign.empty:
        df_subject_check = (
            df_assign
            .groupby(["pensyarah", "kod_kursus"])
            .agg(
                bil_kelas_baru=("kelas_baru", "count"),
                senarai_kelas_baru=("kelas_baru", lambda x: ", ".join(map(str, x)))
            )
            .reset_index()
        )

    total_classes = len(dfc)
    assigned_classes = len(df_assign)
    total_pref = int(df_assign["padanan_pilihan"].str.startswith("Pilihan").sum()) if not df_assign.empty else 0
    changed_count = int((df_assign["berubah_dari_asal"] == "YA").sum()) if not df_assign.empty else 0
    old_count = int(df_assign["pensyarah_asal"].astype(str).str.strip().ne("").sum()) if not df_assign.empty else 0

    preference_rate = round((total_pref / assigned_classes) * 100, 1) if assigned_classes else 0
    stability_rate = round(((old_count - changed_count) / old_count) * 100, 1) if old_count else 100

    loads = df_summary[df_summary["aktif"] == True]["jumlah_jam_kredit"].tolist()
    fairness_score = 100
    if loads:
        fairness_score = max(0, round(100 - (np.std(loads) * 10), 1))

    df_status = pd.DataFrame([{
        "jumlah_kelas_baru": total_classes,
        "kelas_baru_diagih": assigned_classes,
        "kelas_baru_tidak_diagih": len(df_unassigned),
        "jumlah_kredit": int(dfc["jam_kredit"].sum()),
        "kredit_diagih": int(df_assign["jam_kredit"].sum()) if not df_assign.empty else 0,
        "pensyarah_aktif": int(dfl["active"].sum()),
        "pensyarah_aktif_tiada_kelas": int(
            ((df_summary["aktif"] == True) & (df_summary["jumlah_kelas_baru_ajar"] == 0)).sum()
        ),
        "preference_satisfaction_rate_%": preference_rate,
        "stability_rate_%": stability_rate,
        "fairness_score": fairness_score,
        "kelas_berubah_dari_asal": changed_count
    }])

    return df_assign, df_unassigned, df_summary, df_status, df_subject_check


def make_locked_next_input(dfc, df_assign):
    updated = dfc.copy()

    assign_map = df_assign.set_index("kelas_id")["pensyarah"].to_dict() if not df_assign.empty else {}

    updated["pensyarah_asal"] = updated["kelas_id"].map(assign_map).fillna(updated.get("pensyarah_asal", ""))
    updated["lock_agihan"] = "YA"

    return updated


def to_excel_bytes(dfs: Dict[str, pd.DataFrame]):
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for name, df in dfs.items():
                df.to_excel(writer, index=False, sheet_name=name[:31])
        return buffer.getvalue()


def metric_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# MAIN
# ============================================================

if file_classes is not None and file_lect is not None:

    dfc, df_closed, dfl = load_data(file_classes, file_lect)
    pref_score = build_preference_score(dfl)
    coverage_df = build_coverage(dfc, dfl)

    st.markdown('<div class="section-title">2. Data Readiness</div>', unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        metric_card("Kelas_Baru Aktif", len(dfc), "BUKA + BARU")
    with m2:
        metric_card("Subjek Unik", dfc["kod_kursus"].nunique(), "Kod kursus")
    with m3:
        metric_card("Jumlah Kredit", int(dfc["jam_kredit"].sum()), "Keperluan mengajar")
    with m4:
        metric_card("Pensyarah Aktif", int(dfl["active"].sum()), "Berdasarkan effective max")
    with m5:
        metric_card("Kapasiti Efektif", int(dfl["effective_max_kredit"].sum()), "Selepas availability")

    if int(dfl["effective_max_kredit"].sum()) < int(dfc["jam_kredit"].sum()):
        st.error(
            "Kapasiti efektif pensyarah tidak cukup untuk cover semua kelas_baru. "
            "Naikkan maksimum kredit, benarkan partial loading, atau tambah pensyarah."
        )

    with st.expander("Lihat coverage subjek dan kelas ditutup", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.write("Coverage Subjek")
            st.dataframe(coverage_df, use_container_width=True, height=260)
        with c2:
            st.write("Kelas Ditutup")
            st.dataframe(df_closed, use_container_width=True, height=260)

    no_pref = coverage_df[coverage_df["bil_pemilih"] == 0]
    if not no_pref.empty:
        st.warning(
            "Ada subjek tiada pemilih. ILASO tetap akan agih kelas tersebut demi coverage dan fairness."
        )

    st.markdown('<div class="section-title">3. Optimization Engine</div>', unsafe_allow_html=True)

    if st.button("🚀 Run ILASO Allocation", use_container_width=True):

        try:
            status, x_assign = solve_milp(dfc, dfl, pref_score)
        except Exception as e:
            st.error(f"Solver gagal. Pastikan install PuLP: pip install pulp. Error: {e}")
            st.stop()

        if status == "Optimal":
            st.success("ILASO Optimization Status: Optimal")
        else:
            st.warning(f"ILASO Optimization Status: {status}. Result mungkin tidak optimum penuh.")

        df_assign, df_unassigned, df_summary, df_status, df_subject_check = build_outputs(
            dfc, dfl, pref_score, x_assign
        )

        st.markdown('<div class="section-title">4. Executive Dashboard</div>', unsafe_allow_html=True)

        s = df_status.iloc[0].to_dict()

        k1, k2, k3, k4, k5 = st.columns(5)

        with k1:
            metric_card("Coverage", f"{int(s['kelas_baru_diagih'])}/{int(s['jumlah_kelas_baru'])}", "Kelas_Baru diagih")
        with k2:
            metric_card("Preference", f"{s['preference_satisfaction_rate_%']}%", "Ikut pilihan")
        with k3:
            metric_card("Stability", f"{s['stability_rate_%']}%", "Kekal agihan asal")
        with k4:
            metric_card("Fairness", f"{s['fairness_score']}", "Load balance score")
        with k5:
            metric_card("Changed", int(s["kelas_berubah_dari_asal"]), "Perubahan minimum")

        tabs = st.tabs([
            "📌 Allocation",
            "👤 Lecturer Summary",
            "📊 Analytics",
            "🔍 Audit & Checks",
            "📥 Export"
        ])

        with tabs[0]:
            st.subheader("Agihan Kelas_Baru")
            st.dataframe(df_assign, use_container_width=True, height=520)

        with tabs[1]:
            st.subheader("Ringkasan Pensyarah")
            st.dataframe(df_summary, use_container_width=True, height=520)

        with tabs[2]:
            st.subheader("Analytics")

            a1, a2 = st.columns(2)

            with a1:
                if px is not None and not df_summary.empty:
                    fig = px.bar(
                        df_summary.sort_values("jumlah_jam_kredit", ascending=True),
                        x="jumlah_jam_kredit",
                        y="pensyarah",
                        orientation="h",
                        title="Lecturer Workload Distribution",
                        labels={"jumlah_jam_kredit": "Jam Kredit", "pensyarah": "Pensyarah"},
                    )
                    fig.update_layout(height=640)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(df_summary[["pensyarah", "jumlah_jam_kredit"]], use_container_width=True)

            with a2:
                if px is not None and not df_assign.empty:
                    pref_counts = (
                        df_assign["padanan_pilihan"]
                        .value_counts()
                        .reset_index()
                    )
                    pref_counts.columns = ["padanan_pilihan", "count"]

                    fig2 = px.pie(
                        pref_counts,
                        names="padanan_pilihan",
                        values="count",
                        title="Preference Satisfaction Composition",
                        hole=0.45
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.dataframe(df_assign["padanan_pilihan"].value_counts(), use_container_width=True)

            st.subheader("Coverage Subjek")
            st.dataframe(coverage_df, use_container_width=True, height=280)

        with tabs[3]:
            st.subheader("Audit & Checks")

            if len(df_unassigned) == 0:
                st.success("Semua kelas_baru berjaya diagih.")
            else:
                st.error("Ada kelas_baru tidak diagih.")
                st.dataframe(df_unassigned, use_container_width=True)

            empty_active = df_summary[
                (df_summary["aktif"] == True) &
                (df_summary["jumlah_kelas_baru_ajar"] == 0)
            ]

            if empty_active.empty:
                st.success("Semua pensyarah aktif mendapat sekurang-kurangnya satu kelas_baru.")
            else:
                st.warning("Ada pensyarah aktif tiada kelas.")
                st.dataframe(empty_active, use_container_width=True)

            violation = df_subject_check[
                df_subject_check["bil_kelas_baru"] > int(max_kelas_baru_per_subject)
            ] if not df_subject_check.empty else pd.DataFrame()

            if violation.empty:
                st.success("Had maksimum kelas_baru bagi subjek sama dipatuhi.")
            else:
                st.error("Ada pelanggaran maksimum kelas_baru bagi subjek sama.")
                st.dataframe(violation, use_container_width=True)

            st.subheader("Semakan Pensyarah-Subjek")
            st.dataframe(df_subject_check, use_container_width=True, height=300)

        with tabs[4]:
            st.subheader("Export Results")

            locked_next_input = make_locked_next_input(dfc, df_assign)

            output_xlsx = to_excel_bytes({
                "Status": df_status,
                "Agihan_ILASO": df_assign,
                "Ringkasan_Pensyarah": df_summary,
                "Coverage_Subjek": coverage_df,
                "Kelas_Baru_Tidak_Diagih": df_unassigned,
                "Kelas_Ditutup": df_closed,
                "Semakan_Subjek": df_subject_check,
                "Next_Input_Locked": locked_next_input,
            })

            st.download_button(
                "📥 Download ILASO Result Excel",
                data=output_xlsx,
                file_name="ILASO_allocation_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            next_input_xlsx = to_excel_bytes({
                "Jadual_Kelas": locked_next_input,
                "Kelas_Ditutup": df_closed
            })

            st.download_button(
                "🔒 Download Next Input with Locked Allocation",
                data=next_input_xlsx,
                file_name="ILASO_next_input_locked.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

else:
    st.info("Upload kedua-dua fail untuk mula menggunakan ILASO.")

    with st.expander("Format minimum fail", expanded=True):
        st.markdown(
            """
            **Fail Jadual Kelas**
            - `kod_kursus`
            - `kelas_baru`
            - `jam_kredit`
            - optional: `saiz_kelas`, `campuran_group`, `perincian`, `status_kelas`, `pensyarah_asal`, `lock_agihan`,
              `minggu_mula_kelas`, `minggu_akhir_kelas`

            **Fail Pensyarah**
            - `Nama Pensyarah`
            - `Peranan`
            - `Minimum Jam Kredit`
            - `Maksimum Jam Kredit`
            - `Pilihan 1` hingga `Pilihan 5`
            - optional: `minggu_mula_available`, `minggu_akhir_available`, `status`, `allow_partial_loading`, `catatan`
            """
        )


st.divider()
st.caption(
    "ILASO focuses on lecturer-subject allocation only. It does not generate timetable slots, rooms, or student clash resolution."
)
