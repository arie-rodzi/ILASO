# ============================================================
# ILASO FAIR KS ENGINE
# pip install streamlit pandas numpy openpyxl pulp plotly
# streamlit run ilaso_app.py
# ============================================================

import io
import numpy as np
import pandas as pd
import streamlit as st

try:
    import pulp as pl
except Exception:
    pl = None

try:
    import plotly.express as px
except Exception:
    px = None


SEMESTER_WEEKS = 14
DEFAULT_MIN = 15
DEFAULT_MAX = 17
TARGET_KS = 16
FAIR_MIN_KS = 15
FAIR_MAX_KS = 17
EMERGENCY_MAX_KS = 18
LATE_ENTRY_CUTOFF_WEEK = 10

MAX_SUBJECTS = 2
MAX_CLASSES_SAME_SUBJECT = 3

SCORE_PREF = {1: 100, 2: 80, 3: 60, 4: 40, 5: 20}
SCORE_NOT_PREF = -30

W_PREF = 20
W_UNDER = 120000
W_BALANCE = 80000
W_RANGE = 150000
W_ZERO = 250000
W_EMERGENCY = 200000
W_SHARE = 30000


st.set_page_config(
    page_title="ILASO",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main { background-color: #F8FAFC; }

.block-container {
    padding-top: 1.2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E5E7EB;
}

.ilaso-hero {
    background: linear-gradient(135deg, #061A40 0%, #0B3678 60%, #123C7C 100%);
    padding: 34px 42px;
    border-radius: 0 0 28px 28px;
    color: white;
    margin-bottom: 30px;
    box-shadow: 0 18px 45px rgba(6, 26, 64, 0.18);
}

.ilaso-title {
    font-size: 48px;
    font-weight: 900;
}

.ilaso-subtitle {
    font-size: 20px;
    color: #E8EEF9;
    margin-top: 8px;
}

.ilaso-tag {
    display: inline-block;
    margin-top: 18px;
    background: rgba(245, 197, 66, 0.16);
    color: #FFE38A;
    border: 1px solid rgba(248, 214, 109, 0.65);
    padding: 10px 18px;
    border-radius: 999px;
    font-weight: 800;
}

.metric-card {
    background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
    border: 1px solid rgba(148, 163, 184, .24);
    border-left: 6px solid #C9A227;
    border-radius: 22px;
    padding: 20px 22px;
    box-shadow: 0 14px 35px rgba(2, 6, 23, .08);
    min-height: 118px;
}
.metric-label {font-size: 13px; color:#64748B; text-transform:uppercase; letter-spacing:.08em; font-weight:800;}
.metric-value {font-size:34px; color:#061A40; font-weight:950; margin-top:8px;}
.metric-note {font-size:13px; color:#64748B; margin-top:6px;}
.section-title {font-size:26px; font-weight:950; color:#061A40; margin: 28px 0 6px 0;}
.section-note {font-size:15px; color:#64748B; margin-bottom: 16px;}
.soft-card {background:#FFFFFF; border:1px solid #E5E7EB; border-radius:22px; padding:22px; box-shadow:0 12px 28px rgba(15,23,42,.06);}
.footer {margin-top:36px; padding:20px; color:#64748B; text-align:center; border-top:1px solid #E5E7EB;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ilaso-hero">
    <div class="ilaso-title">ILASO</div>
    <div class="ilaso-subtitle">
        Intelligent Lecturer Allocation System • Fair KS Distribution Engine
    </div>
    <div class="ilaso-tag">
        Target 16 KS • Fair range 15–17 KS • Late-entry lecturer supported
    </div>
</div>
""", unsafe_allow_html=True)


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
    if x in ["", "BUKA", "OPEN", "AKTIF", "ACTIVE"]:
        return "BUKA"
    if x in ["BARU", "BAHARU", "NEW"]:
        return "BARU"
    if x in ["TUTUP", "CLOSE", "CLOSED", "BATAL", "CANCEL", "CANCELLED"]:
        return "TUTUP"
    return x


def yes_no(x):
    x = clean_text(x)
    if x in ["YA", "YES", "Y", "TRUE", "1"]:
        return "YA"
    return "TIDAK"


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


def read_file(uploaded_file, expected_sheet=None):
    name = uploaded_file.name.lower()

    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file, encoding="utf-8-sig")

    xl = pd.ExcelFile(uploaded_file)

    if expected_sheet and expected_sheet in xl.sheet_names:
        return pd.read_excel(uploaded_file, sheet_name=expected_sheet)

    return pd.read_excel(uploaded_file, sheet_name=xl.sheet_names[0])


def to_excel_bytes(dfs):
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for name, df in dfs.items():
                df.to_excel(writer, index=False, sheet_name=name[:31])
        return buffer.getvalue()

# ============================================================
# DATA PREPARATION
# ============================================================

def prepare_class_data(file_classes):

    df = read_file(file_classes, expected_sheet="Jadual_Kelas").copy()

    required = ["kod_kursus", "kelas_baru", "ks"]

    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"Fail Jadual Kelas tiada column wajib: {missing}")
        st.stop()

    df["kod_kursus"] = df["kod_kursus"].map(clean_text)
    df["kelas_baru"] = df["kelas_baru"].astype(str).str.strip()

    df["ks"] = (
        pd.to_numeric(df["ks"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    if "status_kelas" not in df.columns:
        df["status_kelas"] = "BUKA"

    df["status_kelas"] = df["status_kelas"].map(standardize_status)

    if "saiz_kelas" not in df.columns:
        df["saiz_kelas"] = 0

    df["saiz_kelas"] = (
        pd.to_numeric(df["saiz_kelas"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    for col in [
        "campuran_group",
        "perincian",
        "pensyarah_asal",
        "lock_agihan"
    ]:
        if col not in df.columns:
            df[col] = ""

    df["lock_agihan"] = df["lock_agihan"].map(yes_no)

    if "minggu_mula_kelas" not in df.columns:
        df["minggu_mula_kelas"] = 1

    if "minggu_akhir_kelas" not in df.columns:
        df["minggu_akhir_kelas"] = SEMESTER_WEEKS

    df["minggu_mula_kelas"] = (
        pd.to_numeric(df["minggu_mula_kelas"], errors="coerce")
        .fillna(1)
        .astype(int)
    )

    df["minggu_akhir_kelas"] = (
        pd.to_numeric(df["minggu_akhir_kelas"], errors="coerce")
        .fillna(SEMESTER_WEEKS)
        .astype(int)
    )

    if "share_allowed" not in df.columns:
        df["share_allowed"] = "TIDAK"

    df["share_allowed"] = df["share_allowed"].map(yes_no)

    df = df[
        (df["kod_kursus"] != "") &
        (df["kelas_baru"] != "") &
        (df["ks"] > 0)
    ].copy()

    df["kelas_id"] = (
        df["kod_kursus"] + "-" + df["kelas_baru"]
    )

    df = df.drop_duplicates(
        subset=["kelas_id"],
        keep="first"
    ).copy()

    return df


def prepare_lecturer_data(file_lect):

    raw = read_file(file_lect, expected_sheet="Pensyarah").copy()

    required = [
        "Nama Pensyarah",
        "Peranan",
        "Minimum KS",
        "Maksimum KS"
    ]

    missing = [c for c in required if c not in raw.columns]

    if missing:
        st.error(f"Fail Pensyarah tiada column wajib: {missing}")
        st.stop()

    df = raw.rename(columns={
        "Nama Pensyarah": "nama",
        "Peranan": "peranan",
        "Minimum KS": "min_ks",
        "Maksimum KS": "max_ks"
    }).copy()

    df["nama"] = df["nama"].map(clean_name)

    df["min_ks"] = (
        pd.to_numeric(df["min_ks"], errors="coerce")
        .fillna(DEFAULT_MIN)
        .astype(int)
    )

    df["max_ks"] = (
        pd.to_numeric(df["max_ks"], errors="coerce")
        .fillna(DEFAULT_MAX)
        .astype(int)
    )

    for i in range(1, 6):

        col = f"Pilihan {i}"

        if col not in df.columns:
            df[col] = ""

        df[col] = df[col].map(clean_text)

    if "status" not in df.columns:
        df["status"] = "AKTIF"

    df["status"] = df["status"].map(clean_text)

    if "minggu_mula_available" not in df.columns:
        df["minggu_mula_available"] = 1

    if "minggu_akhir_available" not in df.columns:
        df["minggu_akhir_available"] = SEMESTER_WEEKS

    df["minggu_mula_available"] = (
        pd.to_numeric(df["minggu_mula_available"], errors="coerce")
        .fillna(1)
        .astype(int)
    )

    df["minggu_akhir_available"] = (
        pd.to_numeric(df["minggu_akhir_available"], errors="coerce")
        .fillna(SEMESTER_WEEKS)
        .astype(int)
    )

    cuti_mask = (
        df["status"].isin([
            "CUTI",
            "TIDAK_AKTIF",
            "SABBATICAL"
        ])
    )

    df["active"] = ~cuti_mask

    df = df[
        df["nama"] != ""
    ].drop_duplicates(
        subset=["nama"],
        keep="first"
    ).copy()

    return df


# ============================================================
# PREFERENCE
# ============================================================

def build_preference_score(dfl):

    pref = {}

    for _, row in dfl.iterrows():

        lname = row["nama"]

        for i in range(1, 6):

            subj = clean_text(
                row.get(f"Pilihan {i}", "")
            )

            if subj:
                pref[(lname, subj)] = SCORE_PREF[i]

    return pref


def get_pref_score(lname, subject, pref):

    return int(
        pref.get(
            (lname, subject),
            SCORE_NOT_PREF
        )
    )


def get_pref_label(lname, subject, dfl):

    row = dfl[dfl["nama"] == lname]

    if row.empty:
        return "Tidak diketahui"

    row = row.iloc[0]

    for i in range(1, 6):

        if clean_text(
            row.get(f"Pilihan {i}", "")
        ) == subject:

            return f"Pilihan {i}"

    return "Bukan pilihan"


def is_available_for_class(lect_row, class_row):

    return max(
        int(lect_row["minggu_mula_available"]),
        int(class_row["minggu_mula_kelas"])
    ) <= min(
        int(lect_row["minggu_akhir_available"]),
        int(class_row["minggu_akhir_kelas"])
    )

# ============================================================
# OPTIMIZER
# ============================================================

def solve_allocation(dfc, dfl, pref):

    if pl is None:
        st.error("PuLP belum install. Sila install: pip install pulp")
        st.stop()

    classes = dfc["kelas_id"].tolist()
    lecturers = dfl["nama"].tolist()
    subjects = sorted(dfc["kod_kursus"].unique().tolist())

    credit = dfc.set_index("kelas_id")["ks"].astype(int).to_dict()
    cls_subject = dfc.set_index("kelas_id")["kod_kursus"].to_dict()

    active = dfl.set_index("nama")["active"].to_dict()
    class_rows = dfc.set_index("kelas_id")
    lect_rows = dfl.set_index("nama")

    wajib_ajar = [
        l for l in lecturers
        if active[l]
        and int(lect_rows.loc[l, "minggu_mula_available"]) <= LATE_ENTRY_CUTOFF_WEEK
    ]

    target_ks = round(int(dfc["ks"].sum()) / max(len(wajib_ajar), 1))

    prob = pl.LpProblem("ILASO_Fair_KS", pl.LpMinimize)

    x = pl.LpVariable.dicts("x", (classes, lecturers), 0, 1, cat="Binary")
    y = pl.LpVariable.dicts("y", (lecturers, subjects), 0, 1, cat="Binary")

    under = pl.LpVariable.dicts("under", lecturers, lowBound=0)
    over = pl.LpVariable.dicts("over", lecturers, lowBound=0)

    # 1 kelas = 1 pensyarah
    for c in classes:
        prob += pl.lpSum(x[c][l] for l in lecturers) == 1

    # Pensyarah tidak aktif tidak boleh mengajar
    for l in lecturers:
        if not active[l]:
            for c in classes:
                prob += x[c][l] == 0

    # Availability
    for c in classes:
        for l in lecturers:
            if not is_available_for_class(lect_rows.loc[l], class_rows.loc[c]):
                prob += x[c][l] == 0

    # Workload ikut min/max individu
    for l in lecturers:

        total_load = pl.lpSum(
            credit[c] * x[c][l]
            for c in classes
        )

        start_week = int(lect_rows.loc[l, "minggu_mula_available"])

        if l in wajib_ajar:

            personal_min = int(lect_rows.loc[l, "min_ks"])
            personal_max = int(lect_rows.loc[l, "max_ks"])

            prob += total_load >= personal_min
            prob += total_load <= personal_max

            prob += pl.lpSum(x[c][l] for c in classes) >= 1

            personal_target = min(
                max(target_ks, personal_min),
                personal_max
            )

            prob += personal_target - total_load <= under[l]
            prob += total_load - personal_target <= over[l]

        else:
            prob += under[l] == 0
            prob += over[l] == 0

            if active[l] and start_week > LATE_ENTRY_CUTOFF_WEEK:
                prob += total_load == 0

    # Link lecturer-subject
    for c in classes:
        s = cls_subject[c]
        for l in lecturers:
            prob += x[c][l] <= y[l][s]

    # Maksimum 2 subjek berbeza
    for l in lecturers:
        prob += pl.lpSum(y[l][s] for s in subjects) <= MAX_SUBJECTS

    # Maksimum kelas subjek sama
    for l in lecturers:
        for s in subjects:
            subject_classes = [
                c for c in classes
                if cls_subject[c] == s
            ]
            prob += pl.lpSum(x[c][l] for c in subject_classes) <= MAX_CLASSES_SAME_SUBJECT

    preference_reward = pl.lpSum(
        credit[c] * get_pref_score(l, cls_subject[c], pref) * x[c][l]
        for c in classes
        for l in lecturers
    )

    fairness_penalty = pl.lpSum(
        under[l] + over[l]
        for l in wajib_ajar
    )

    prob += (
        100000 * fairness_penalty
        - 10 * preference_reward
    )

    solver = pl.PULP_CBC_CMD(msg=False, timeLimit=240)
    prob.solve(solver)

    status = pl.LpStatus[prob.status]

    assigned_rows = []

    if status == "Optimal":
        for c in classes:
            for l in lecturers:
                val = float(pl.value(x[c][l]) or 0)

                if val > 0.5:
                    assigned_rows.append({
                        "kelas_id": c,
                        "pensyarah": l
                    })

        st.info(f"Target purata sistem: {target_ks} KS. Agihan ikut min/max individu.")

    return status, pd.DataFrame(assigned_rows)
# ============================================================
# OUTPUT BUILDER
# ============================================================

def build_outputs(dfc_active, df_closed, dfl, pref, assigned_df):

    lect_lookup = dfl.set_index("nama")
    class_lookup = dfc_active.set_index("kelas_id")

    rows = []

    if assigned_df.empty:
        df_assign = pd.DataFrame()

    else:
        for _, ar in assigned_df.iterrows():

            cid = ar["kelas_id"]
            lname = ar["pensyarah"]

            r = class_lookup.loc[cid]
            subj = r["kod_kursus"]
            lrow = lect_lookup.loc[lname]

            start_week = int(lrow["minggu_mula_available"])

            needs_temp_cover = (
                start_week > int(r["minggu_mula_kelas"])
                and start_week <= LATE_ENTRY_CUTOFF_WEEK
            )

            rows.append({
                "kelas_id": cid,
                "kod_kursus": subj,
                "kelas_baru": r["kelas_baru"],
                "status_kelas": r["status_kelas"],
                "KS": int(r["ks"]),
                "saiz_kelas": int(r.get("saiz_kelas", 0)),
                "pensyarah_utama": lname,
                "peranan": lrow["peranan"],
                "padanan_pilihan": get_pref_label(lname, subj, dfl),
                "skor_pilihan": get_pref_score(lname, subj, pref),
                "minggu_mula_kelas": int(r["minggu_mula_kelas"]),
                "minggu_akhir_kelas": int(r["minggu_akhir_kelas"]),
                "minggu_mula_pensyarah": start_week,
                "minggu_akhir_pensyarah": int(lrow["minggu_akhir_available"]),
                "perlu_cover_sementara": "YA" if needs_temp_cover else "TIDAK",
                "minggu_cover_sementara": (
                    f"{int(r['minggu_mula_kelas'])}-{start_week - 1}"
                    if needs_temp_cover
                    else ""
                ),
                "pensyarah_cover_sementara": "",
                "catatan": (
                    "Pensyarah masuk lewat. Perlu pensyarah sementara cover minggu awal."
                    if needs_temp_cover
                    else ""
                ),
                "perincian": r.get("perincian", "")
            })

        df_assign = pd.DataFrame(rows)

        # Cari pensyarah cover sementara selepas df_assign siap
        for idx, row in df_assign.iterrows():

            if row["perlu_cover_sementara"] == "YA":

                subj = row["kod_kursus"]
                lname = row["pensyarah_utama"]

                same_subject = df_assign[
                    (df_assign["kod_kursus"] == subj)
                    & (df_assign["pensyarah_utama"] != lname)
                ].copy()

                if not same_subject.empty:

                    lecturer_load = (
                        df_assign.groupby("pensyarah_utama")["KS"]
                        .sum()
                        .reset_index()
                        .rename(columns={
                            "pensyarah_utama": "calon_cover",
                            "KS": "jumlah_KS"
                        })
                    )

                    candidate = same_subject[
                        ["pensyarah_utama"]
                    ].drop_duplicates().rename(columns={
                        "pensyarah_utama": "calon_cover"
                    })

                    candidate = candidate.merge(
                        lecturer_load,
                        on="calon_cover",
                        how="left"
                    ).sort_values(
                        "jumlah_KS",
                        ascending=True
                    )

                    if not candidate.empty:
                        df_assign.loc[idx, "pensyarah_cover_sementara"] = candidate.iloc[0]["calon_cover"]

    summary_rows = []

    for _, lrow in dfl.iterrows():

        lname = lrow["nama"]

        if df_assign.empty:
            tmp = pd.DataFrame()
        else:
            tmp = df_assign[df_assign["pensyarah_utama"] == lname]

        total_ks = int(tmp["KS"].sum()) if not tmp.empty else 0
        total_class = int(tmp["kelas_id"].nunique()) if not tmp.empty else 0
        subjects = sorted(tmp["kod_kursus"].unique().tolist()) if not tmp.empty else []

        if not bool(lrow["active"]):
            status_load = "TIDAK AKTIF / CUTI"
        elif int(lrow["minggu_mula_available"]) > LATE_ENTRY_CUTOFF_WEEK:
            status_load = "MASUK SELEPAS MINGGU 10"
        elif total_ks < int(lrow["min_ks"]):
            status_load = "UNDERLOAD"
        elif total_ks > int(lrow["max_ks"]):
            status_load = "OVERLOAD"
        else:
            status_load = "ADIL"

        detail_list = []

        if not tmp.empty:
            for subj, g in tmp.groupby("kod_kursus"):
                cls = ", ".join(g["kelas_baru"].astype(str).tolist())
                cr = int(g["KS"].sum())
                detail_list.append(f"{subj}: {cr} KS ({cls})")

        summary_rows.append({
            "pensyarah": lname,
            "peranan": lrow["peranan"],
            "status_pensyarah": lrow["status"],
            "aktif": bool(lrow["active"]),
            "minggu_mula_available": int(lrow["minggu_mula_available"]),
            "minimum_KS": int(lrow["min_ks"]),
            "maksimum_KS": int(lrow["max_ks"]),
            "jumlah_KS": total_ks,
            "jumlah_kelas": total_class,
            "bil_subjek": len(subjects),
            "senarai_subjek": ", ".join(subjects),
            "perincian_mengajar": " | ".join(detail_list),
            "beza_dari_target_16": total_ks - TARGET_KS,
            "status_load": status_load
        })

    df_summary = pd.DataFrame(summary_rows)

    assigned_ids = set(df_assign["kelas_id"]) if not df_assign.empty else set()

    df_unassigned = dfc_active[
        ~dfc_active["kelas_id"].isin(assigned_ids)
    ].copy()

    df_temp_cover = (
        df_assign[df_assign["perlu_cover_sementara"] == "YA"].copy()
        if not df_assign.empty
        else pd.DataFrame()
    )

    df_status = pd.DataFrame([{
        "jumlah_kelas_aktif": len(dfc_active),
        "jumlah_kelas_tutup": len(df_closed),
        "kelas_diagih": len(assigned_ids),
        "kelas_tidak_diagih": len(df_unassigned),
        "jumlah_KS_aktif": int(dfc_active["ks"].sum()),
        "KS_diagih": int(df_assign["KS"].sum()) if not df_assign.empty else 0,
        "jumlah_pensyarah": len(dfl),
        "pensyarah_aktif": int(dfl["active"].sum()),
        "pensyarah_adil": int((df_summary["status_load"] == "ADIL").sum()),
        "pensyarah_underload": int((df_summary["status_load"] == "UNDERLOAD").sum()),
        "pensyarah_emergency_overload": int((df_summary["status_load"] == "OVERLOAD").sum()),
        "kes_cover_sementara": len(df_temp_cover)
    }])

    return (
        df_assign,
        df_summary,
        df_temp_cover,
        df_unassigned,
        df_status
    )
    df_summary = pd.DataFrame(summary_rows)

    assigned_ids = set(
        df_assign["kelas_id"]
    ) if not df_assign.empty else set()

    df_unassigned = dfc_active[
        ~dfc_active["kelas_id"].isin(assigned_ids)
    ].copy()

    df_temp_cover = (
        df_assign[
            df_assign["perlu_cover_sementara"] == "YA"
        ].copy()
        if not df_assign.empty
        else pd.DataFrame()
    )

    df_status = pd.DataFrame([{
        "jumlah_kelas_aktif": len(dfc_active),
        "jumlah_kelas_tutup": len(df_closed),
        "kelas_diagih": len(assigned_ids),
        "kelas_tidak_diagih": len(df_unassigned),
        "jumlah_KS_aktif": int(dfc_active["ks"].sum()),
        "KS_diagih": int(df_assign["KS"].sum()) if not df_assign.empty else 0,
        "jumlah_pensyarah": len(dfl),
        "pensyarah_aktif": int(dfl["active"].sum()),
        "pensyarah_adil": int((df_summary["status_load"] == "ADIL").sum()),
        "pensyarah_underload": int((df_summary["status_load"] == "UNDERLOAD").sum()),
        "pensyarah_emergency_overload": int((df_summary["status_load"] == "EMERGENCY OVERLOAD").sum()),
        "kes_cover_sementara": len(df_temp_cover)
    }])

    return (
        df_assign,
        df_summary,
        df_temp_cover,
        df_unassigned,
        df_status
    )
# ============================================================
# UPLOAD + MAIN APP
# ============================================================

st.markdown(
    '<div class="section-title">1. Upload Main Files</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-note">Gunakan istilah KS. Sasaran agihan ialah 16 KS dengan julat adil 15–17 KS.</div>',
    unsafe_allow_html=True
)

u1, u2 = st.columns(2)

with u1:
    file_classes = st.file_uploader(
        "Upload Jadual Kelas",
        type=["xlsx", "csv"]
    )

with u2:
    file_lect = st.file_uploader(
        "Upload Pensyarah",
        type=["xlsx", "csv"]
    )


if file_classes is None or file_lect is None:

    st.info("Upload dua fail: Jadual Kelas dan Pensyarah.")

    st.markdown(
        """
        <div class="soft-card">
        <b>Format wajib Jadual Kelas</b><br>
        kod_kursus, kelas_baru, ks<br><br>

        <b>Format wajib Pensyarah</b><br>
        Nama Pensyarah, Peranan, Minimum KS, Maksimum KS, Pilihan 1 hingga Pilihan 5<br><br>

        <b>Optional</b><br>
        status_kelas, saiz_kelas, minggu_mula_kelas, minggu_akhir_kelas, 
        status, minggu_mula_available, minggu_akhir_available
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    if "loaded_class_file" not in st.session_state:
        st.session_state.loaded_class_file = ""

    if (
        "class_df" not in st.session_state
        or st.session_state.loaded_class_file != file_classes.name
    ):
        st.session_state.class_df = prepare_class_data(file_classes)
        st.session_state.loaded_class_file = file_classes.name

    dfl = prepare_lecturer_data(file_lect)

    st.markdown(
        '<div class="section-title">2. Class Manager</div>',
        unsafe_allow_html=True
    )

    manager_tabs = st.tabs([
        "📋 Edit Jadual Kelas",
        "➕ Tambah Kelas",
        "🗑️ Tutup Kelas"
    ])

    with manager_tabs[0]:

        edited = st.data_editor(
            st.session_state.class_df,
            use_container_width=True,
            height=430,
            num_rows="dynamic",
            column_config={
                "status_kelas": st.column_config.SelectboxColumn(
                    "status_kelas",
                    options=["BUKA", "BARU", "TUTUP"],
                    required=True
                )
            }
        )

        if st.button(
            "💾 Simpan Perubahan Jadual Kelas",
            use_container_width=True
        ):

            edited = edited.copy()
            edited["kod_kursus"] = edited["kod_kursus"].map(clean_text)
            edited["kelas_baru"] = edited["kelas_baru"].astype(str).str.strip()
            edited["status_kelas"] = edited["status_kelas"].map(standardize_status)
            edited["ks"] = pd.to_numeric(
                edited["ks"],
                errors="coerce"
            ).fillna(0).astype(int)

            edited["kelas_id"] = (
                edited["kod_kursus"]
                + "-"
                + edited["kelas_baru"].astype(str)
            )

            edited = edited.drop_duplicates(
                subset=["kelas_id"],
                keep="last"
            ).copy()

            st.session_state.class_df = edited
            st.success("Perubahan jadual kelas disimpan.")

    with manager_tabs[1]:

        c1, c2, c3 = st.columns(3)

        with c1:
            new_subject = st.text_input(
                "Kod kursus",
                placeholder="Contoh: MAT112"
            )

            new_class = st.text_input(
                "Group / kelas",
                placeholder="Contoh: A1"
            )

        with c2:
            new_ks = st.number_input(
                "KS",
                1,
                10,
                3,
                1
            )

            new_size = st.number_input(
                "Saiz kelas",
                0,
                500,
                0,
                1
            )

        with c3:
            new_start = st.number_input(
                "Minggu mula kelas",
                1,
                SEMESTER_WEEKS,
                1,
                1
            )

            new_end = st.number_input(
                "Minggu akhir kelas",
                1,
                SEMESTER_WEEKS,
                SEMESTER_WEEKS,
                1
            )

        new_note = st.text_input(
            "Catatan",
            placeholder="Contoh: kelas tambahan / kelas baharu"
        )

        if st.button(
            "➕ Tambah Kelas Baru",
            use_container_width=True
        ):

            if clean_text(new_subject) == "" or new_class.strip() == "":
                st.error("Kod kursus dan group/kelas wajib diisi.")

            else:

                new_row = {
                    "kelas_id": clean_text(new_subject) + "-" + new_class.strip(),
                    "kod_kursus": clean_text(new_subject),
                    "kelas_baru": new_class.strip(),
                    "status_kelas": "BARU",
                    "ks": int(new_ks),
                    "saiz_kelas": int(new_size),
                    "campuran_group": "",
                    "perincian": new_note,
                    "pensyarah_asal": "",
                    "lock_agihan": "TIDAK",
                    "share_allowed": "TIDAK",
                    "minggu_mula_kelas": int(new_start),
                    "minggu_akhir_kelas": int(new_end)
                }

                updated = pd.concat(
                    [
                        st.session_state.class_df,
                        pd.DataFrame([new_row])
                    ],
                    ignore_index=True
                )

                updated["kelas_id"] = (
                    updated["kod_kursus"].map(clean_text)
                    + "-"
                    + updated["kelas_baru"].astype(str).str.strip()
                )

                updated = updated.drop_duplicates(
                    subset=["kelas_id"],
                    keep="last"
                ).copy()

                st.session_state.class_df = updated

                st.success(
                    f"Kelas {new_row['kelas_id']} berjaya ditambah."
                )

    with manager_tabs[2]:

        close_mode = st.radio(
            "Pilihan tutup",
            [
                "Tutup satu kelas",
                "Tutup semua kelas bagi satu subjek"
            ],
            horizontal=True
        )

        if close_mode == "Tutup satu kelas":

            class_ids = sorted(
                st.session_state.class_df["kelas_id"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_class = st.selectbox(
                "Pilih kelas",
                class_ids
            )

            if st.button(
                "🗑️ Tutup Kelas Ini",
                use_container_width=True
            ):

                st.session_state.class_df.loc[
                    st.session_state.class_df["kelas_id"] == selected_class,
                    "status_kelas"
                ] = "TUTUP"

                st.success(
                    f"{selected_class} telah ditutup."
                )

        else:

            subjects = sorted(
                st.session_state.class_df["kod_kursus"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_subject = st.selectbox(
                "Pilih subjek",
                subjects
            )

            if st.button(
                "🗑️ Tutup Semua Kelas Subjek Ini",
                use_container_width=True
            ):

                st.session_state.class_df.loc[
                    st.session_state.class_df["kod_kursus"] == selected_subject,
                    "status_kelas"
                ] = "TUTUP"

                st.success(
                    f"Semua kelas bagi {selected_subject} telah ditutup."
                )


    df_all = st.session_state.class_df.copy()
    df_all["status_kelas"] = df_all["status_kelas"].map(standardize_status)

    df_active = df_all[
        df_all["status_kelas"].isin(["BUKA", "BARU"])
    ].copy()

    df_closed = df_all[
        df_all["status_kelas"] == "TUTUP"
    ].copy()

    st.markdown(
        '<div class="section-title">3. Data Overview</div>',
        unsafe_allow_html=True
    )

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        metric_card(
            "Kelas Aktif",
            len(df_active),
            "BUKA + BARU"
        )

    with k2:
        metric_card(
            "Kelas Tutup",
            len(df_closed),
            "Tidak diagih"
        )

    with k3:
        metric_card(
            "Jumlah KS Aktif",
            int(df_active["ks"].sum()),
            "Jumlah KS perlu diagih"
        )

    with k4:
        metric_card(
            "Pensyarah Aktif",
            int(dfl["active"].sum()),
            "Boleh mengajar"
        )

    with k5:
        avg_ks = round(
            int(df_active["ks"].sum()) / max(int(dfl["active"].sum()), 1),
            2
        )

        metric_card(
            "Purata KS",
            avg_ks,
            "Rujukan fairness"
        )

    with st.expander(
        "Lihat Data Aktif / Tutup / Pensyarah",
        expanded=False
    ):

        t1, t2, t3 = st.tabs([
            "Kelas Aktif",
            "Kelas Tutup",
            "Pensyarah"
        ])

        with t1:
            st.dataframe(
                df_active,
                use_container_width=True,
                height=360
            )

        with t2:
            st.dataframe(
                df_closed,
                use_container_width=True,
                height=360
            )

        with t3:
            st.dataframe(
                dfl,
                use_container_width=True,
                height=360
            )

    st.markdown(
        '<div class="section-title">4. Run ILASO Fair Allocation</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🚀 Run Fair KS Allocation",
        use_container_width=True
    ):

        pref = build_preference_score(dfl)

        solver_status, assigned_df = solve_allocation(
            df_active,
            dfl,
            pref
        )

        if solver_status == "Optimal":
            st.success("Optimization Status: Optimal")
        else:
            st.warning(f"Optimization Status: {solver_status}")

        (
            df_assign,
            df_summary,
            df_temp_cover,
            df_unassigned,
            df_status
        ) = build_outputs(
            df_active,
            df_closed,
            dfl,
            pref,
            assigned_df
        )

        s = df_status.iloc[0]

        st.markdown(
            '<div class="section-title">5. Executive Dashboard</div>',
            unsafe_allow_html=True
        )

        d1, d2, d3, d4, d5 = st.columns(5)

        with d1:
            metric_card(
                "Coverage",
                f"{s['kelas_diagih']}/{s['jumlah_kelas_aktif']}",
                "Kelas diagih"
            )

        with d2:
            metric_card(
                "Fair Load",
                int(s["pensyarah_adil"]),
                "Pensyarah 15–17 KS"
            )

        with d3:
            metric_card(
                "Underload",
                int(s["pensyarah_underload"]),
                "Kurang 15 KS"
            )

        with d4:
            metric_card(
                "Emergency",
                int(s["pensyarah_emergency_overload"]),
                "Lebih 17 KS"
            )

        with d5:
            metric_card(
                "Cover Sementara",
                int(s["kes_cover_sementara"]),
                "Masuk lewat"
            )

        result_tabs = st.tabs([
            "📌 Allocation",
            "👤 Lecturer Analysis",
            "⏱️ Temporary Cover",
            "📊 Charts",
            "🔍 Audit",
            "📥 Export"
        ])

        with result_tabs[0]:

            st.markdown("### Agihan Kelas Utama")

            st.dataframe(
                df_assign,
                use_container_width=True,
                height=520
            )

        with result_tabs[1]:

            st.markdown("### Analisis Pensyarah")

            st.dataframe(
                df_summary,
                use_container_width=True,
                height=540
            )

        with result_tabs[2]:

            st.markdown("### Kes Cover Sementara")

            if df_temp_cover.empty:
                st.success("Tiada kes cover sementara.")
            else:
                st.warning(
                    "Ada pensyarah masuk lewat. Minggu awal perlu cover sementara."
                )

                st.dataframe(
                    df_temp_cover,
                    use_container_width=True,
                    height=420
                )

        with result_tabs[3]:

            st.markdown("### Workload Distribution")

            if px is not None and not df_summary.empty:

                fig = px.bar(
                    df_summary.sort_values("jumlah_KS"),
                    x="jumlah_KS",
                    y="pensyarah",
                    orientation="h",
                    text="jumlah_KS",
                    title="Jumlah KS Mengajar Mengikut Pensyarah"
                )

                fig.update_layout(height=680)

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.dataframe(
                    df_summary[
                        ["pensyarah", "jumlah_KS"]
                    ],
                    use_container_width=True
                )

        with result_tabs[4]:

            st.markdown("### Audit Semakan")

            if df_unassigned.empty:
                st.success("Semua kelas aktif berjaya diagih.")
            else:
                st.error("Ada kelas aktif tidak diagih.")
                st.dataframe(
                    df_unassigned,
                    use_container_width=True
                )

            under = df_summary[
                df_summary["status_load"] == "UNDERLOAD"
            ]

            emergency = df_summary[
                df_summary["status_load"] == "EMERGENCY OVERLOAD"
            ]

            if not under.empty:
                st.warning("Pensyarah underload.")
                st.dataframe(
                    under,
                    use_container_width=True
                )

            if not emergency.empty:
                st.error("Pensyarah emergency overload.")
                st.dataframe(
                    emergency,
                    use_container_width=True
                )

            st.markdown("### Kelas Ditutup")

            st.dataframe(
                df_closed,
                use_container_width=True,
                height=300
            )

        with result_tabs[5]:

            output = to_excel_bytes({
                "Status": df_status,
                "Agihan": df_assign,
                "Analisis_Pensyarah": df_summary,
                "Cover_Sementara": df_temp_cover,
                "Kelas_Tidak_Diagih": df_unassigned,
                "Kelas_Tutup": df_closed,
                "Main_File_Updated": df_all
            })

            st.download_button(
                "📥 Download Full Result Excel",
                data=output,
                file_name="ILASO_result_fair_KS.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            updated_main = to_excel_bytes({
                "Jadual_Kelas": df_all
            })

            st.download_button(
                "📥 Download Updated Main File",
                data=updated_main,
                file_name="Jadual_Kelas_Updated_KS.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )


st.markdown(
    """
    <div class="footer">
        ILASO Fair KS Engine • Target 16 KS • Fair range 15–17 KS • Late-entry lecturers supported
    </div>
    """,
    unsafe_allow_html=True
)
