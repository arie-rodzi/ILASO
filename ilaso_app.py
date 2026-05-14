# ============================================================
# ILASO PREMIUM CLEAN VERSION
# Corrected Shared-Class Logic
# ============================================================
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


# ============================================================
# FIXED CONFIG
# ============================================================

SEMESTER_WEEKS = 14
DEFAULT_MIN = 15
DEFAULT_MAX = 18
TARGET_CREDIT = 15

MAX_SUBJECTS = 2
MAX_CLASSES_SAME_SUBJECT = 3

SCORE_PREF = {1: 100, 2: 80, 3: 60, 4: 40, 5: 20}
SCORE_NOT_PREF = -30

W_PREF = 80
W_UNDER = 5000
W_BALANCE = 2500
W_SHARE = 20000


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    st.markdown("""
<style>

.main {
    background-color: #F8FAFC;
}

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
    background: #FFFFFF;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    border: 1px solid #E2E8F0;
}

.metric-label {
    font-size: 13px;
    color: #64748B;
    font-weight: 800;
}

.metric-value {
    font-size: 32px;
    color: #0B3678;
    font-weight: 900;
}

.metric-note {
    color: #64748B;
    font-size: 12px;
}

.section-title {
    color: #0B1F3A;
    font-size: 26px;
    font-weight: 900;
}

.upload-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 22px;
    padding: 24px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.stButton > button {
    background: linear-gradient(135deg, #2563EB, #1D4ED8);
    color: white;
    border-radius: 12px;
    border: none;
    font-weight: 900;
}

</style>
""", unsafe_allow_html=True)
    page_title="ILASO",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<div class="ilaso-hero">

<div class="ilaso-title">
ILASO
</div>

<div class="ilaso-subtitle">
Intelligent Lecturer Allocation System with Correct Shared-Class Detection
</div>

<div class="ilaso-tag">
1 class = 1 lecturer by default • Sharing minimized • Late-entry lecturers supported
</div>

</div>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">ILASO</div>
        <div class="hero-subtitle">
            Intelligent Lecturer Allocation System with Correct Shared-Class Detection
        </div>
        <span class="hero-pill">1 class = 1 lecturer by default • Sharing minimized • Late-entry lecturers supported</span>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

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

    required = ["kod_kursus", "kelas_baru", "jam_kredit"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"Fail Jadual Kelas tiada column wajib: {missing}")
        st.stop()

    df["kod_kursus"] = df["kod_kursus"].map(clean_text)
    df["kelas_baru"] = df["kelas_baru"].astype(str).str.strip()
    df["jam_kredit"] = pd.to_numeric(df["jam_kredit"], errors="coerce").fillna(0).astype(int)

    if "status_kelas" not in df.columns:
        df["status_kelas"] = "BUKA"
    df["status_kelas"] = df["status_kelas"].map(standardize_status)

    if "saiz_kelas" not in df.columns:
        df["saiz_kelas"] = 0
    df["saiz_kelas"] = pd.to_numeric(df["saiz_kelas"], errors="coerce").fillna(0).astype(int)

    for col in ["campuran_group", "perincian", "kredit_info", "pensyarah_asal", "lock_agihan"]:
        if col not in df.columns:
            df[col] = ""

    df["lock_agihan"] = df["lock_agihan"].map(yes_no)

    if "minggu_mula_kelas" not in df.columns:
        df["minggu_mula_kelas"] = 1

    if "minggu_akhir_kelas" not in df.columns:
        df["minggu_akhir_kelas"] = SEMESTER_WEEKS

    df["minggu_mula_kelas"] = pd.to_numeric(df["minggu_mula_kelas"], errors="coerce").fillna(1).astype(int)
    df["minggu_akhir_kelas"] = pd.to_numeric(df["minggu_akhir_kelas"], errors="coerce").fillna(SEMESTER_WEEKS).astype(int)

    df["minggu_mula_kelas"] = df["minggu_mula_kelas"].clip(1, SEMESTER_WEEKS)
    df["minggu_akhir_kelas"] = df["minggu_akhir_kelas"].clip(1, SEMESTER_WEEKS)

    if "share_allowed" not in df.columns:
        df["share_allowed"] = "TIDAK"

    df["share_allowed"] = df["share_allowed"].map(yes_no)

    df = df[
        (df["kod_kursus"] != "") &
        (df["kelas_baru"] != "") &
        (df["jam_kredit"] > 0)
    ].copy()

    df["kelas_id"] = df["kod_kursus"] + "-" + df["kelas_baru"].astype(str)

    df = df.drop_duplicates(subset=["kelas_id"], keep="first").copy()

    cols = [
        "kelas_id",
        "kod_kursus",
        "kelas_baru",
        "status_kelas",
        "jam_kredit",
        "saiz_kelas",
        "campuran_group",
        "perincian",
        "kredit_info",
        "pensyarah_asal",
        "lock_agihan",
        "share_allowed",
        "minggu_mula_kelas",
        "minggu_akhir_kelas"
    ]

    other_cols = [c for c in df.columns if c not in cols]

    return df[cols + other_cols]


def prepare_lecturer_data(file_lect):
    raw = read_file(file_lect, expected_sheet="Pensyarah").copy()

    required = [
        "Nama Pensyarah",
        "Peranan",
        "Minimum Jam Kredit",
        "Maksimum Jam Kredit"
    ]

    missing = [c for c in required if c not in raw.columns]

    if missing:
        st.error(f"Fail Pensyarah tiada column wajib: {missing}")
        st.stop()

    df = raw.rename(columns={
        "Nama Pensyarah": "nama",
        "Peranan": "peranan",
        "Minimum Jam Kredit": "min_kredit",
        "Maksimum Jam Kredit": "max_kredit"
    }).copy()

    df["nama"] = df["nama"].map(clean_name)
    df["peranan"] = df["peranan"].astype(str).str.strip()

    df["min_kredit"] = pd.to_numeric(df["min_kredit"], errors="coerce").fillna(DEFAULT_MIN).astype(int)
    df["max_kredit"] = pd.to_numeric(df["max_kredit"], errors="coerce").fillna(DEFAULT_MAX).astype(int)

    df.loc[df["min_kredit"] > df["max_kredit"], "min_kredit"] = df["max_kredit"]

    for i in range(1, 6):
        col = f"Pilihan {i}"
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].map(clean_text)

    if "status" not in df.columns:
        df["status"] = "AKTIF"

    df["status"] = df["status"].map(clean_text).replace({"": "AKTIF"})

    if "minggu_mula_available" not in df.columns:
        df["minggu_mula_available"] = 1

    if "minggu_akhir_available" not in df.columns:
        df["minggu_akhir_available"] = SEMESTER_WEEKS

    df["minggu_mula_available"] = pd.to_numeric(df["minggu_mula_available"], errors="coerce").fillna(1).astype(int)
    df["minggu_akhir_available"] = pd.to_numeric(df["minggu_akhir_available"], errors="coerce").fillna(SEMESTER_WEEKS).astype(int)

    df["minggu_mula_available"] = df["minggu_mula_available"].clip(1, SEMESTER_WEEKS)
    df["minggu_akhir_available"] = df["minggu_akhir_available"].clip(1, SEMESTER_WEEKS)

    df["available_weeks"] = (
        df["minggu_akhir_available"] - df["minggu_mula_available"] + 1
    ).clip(lower=0, upper=SEMESTER_WEEKS)

    df["availability_ratio"] = df["available_weeks"] / SEMESTER_WEEKS

    df["effective_min_kredit"] = np.floor(df["min_kredit"] * df["availability_ratio"]).astype(int)
    df["effective_max_kredit"] = np.floor(df["max_kredit"] * df["availability_ratio"]).astype(int)

    cuti_mask = (
        df["peranan"].str.lower().str.contains("cuti", na=False) |
        df["status"].isin(["CUTI", "TIDAK_AKTIF", "SABBATICAL", "CUTI_BERSALIN"])
    )

    df.loc[cuti_mask, ["effective_min_kredit", "effective_max_kredit"]] = 0

    df["active"] = df["effective_max_kredit"] > 0

    df = df[df["nama"] != ""].drop_duplicates(subset=["nama"], keep="first").copy()

    return df


# ============================================================
# PREFERENCE
# ============================================================

def build_preference_score(dfl):
    pref = {}

    for _, row in dfl.iterrows():
        lname = row["nama"]

        for i in range(1, 6):
            subj = clean_text(row.get(f"Pilihan {i}", ""))

            if subj:
                pref[(lname, subj)] = SCORE_PREF[i]

    return pref


def get_pref_score(lname, subject, pref):
    return int(pref.get((lname, subject), SCORE_NOT_PREF))


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
    return max(
        int(lect_row["minggu_mula_available"]),
        int(class_row["minggu_mula_kelas"])
    ) <= min(
        int(lect_row["minggu_akhir_available"]),
        int(class_row["minggu_akhir_kelas"])
    )


def can_cover_full_class(lect_row, class_row):
    return (
        int(lect_row["minggu_mula_available"]) <= int(class_row["minggu_mula_kelas"])
        and int(lect_row["minggu_akhir_available"]) >= int(class_row["minggu_akhir_kelas"])
    )


# ============================================================
# OPTIMIZER
# ============================================================

def solve_allocation(dfc, dfl, pref):
    """
    Normal rule:
    - Each kelas_id is assigned to exactly 1 lecturer.

    Shared class rule:
    - Sharing is not automatic.
    - Sharing is allowed only if share_allowed == YA OR no full-cover lecturer exists.
    - Sharing is penalized heavily.
    - Share means the same kelas_id has more than one lecturer.
    """

    if pl is None:
        st.error("PuLP belum install. Sila install: pip install pulp")
        st.stop()

    classes = dfc["kelas_id"].tolist()
    lecturers = dfl["nama"].tolist()
    subjects = sorted(dfc["kod_kursus"].unique().tolist())

    credit = dfc.set_index("kelas_id")["jam_kredit"].astype(int).to_dict()
    cls_subject = dfc.set_index("kelas_id")["kod_kursus"].to_dict()
    share_allowed = dfc.set_index("kelas_id")["share_allowed"].to_dict()

    min_k = dfl.set_index("nama")["effective_min_kredit"].astype(int).to_dict()
    max_k = dfl.set_index("nama")["effective_max_kredit"].astype(int).to_dict()
    active = dfl.set_index("nama")["active"].to_dict()

    class_rows = dfc.set_index("kelas_id")
    lect_rows = dfl.set_index("nama")

    full_cover_exists = {}

    for c in classes:
        crow = class_rows.loc[c]
        ok = False

        for l in lecturers:
            if active[l] and can_cover_full_class(lect_rows.loc[l], crow):
                ok = True
                break

        full_cover_exists[c] = ok

    prob = pl.LpProblem("ILASO_Correct_Shared_Class", pl.LpMinimize)

    x = pl.LpVariable.dicts("x", (classes, lecturers), 0, 1, cat="Binary")
    y = pl.LpVariable.dicts("y", (lecturers, subjects), 0, 1, cat="Binary")
    share = pl.LpVariable.dicts("share", classes, 0, 1, cat="Binary")

    under_min = pl.LpVariable.dicts("under_min", lecturers, lowBound=0)
    over_target = pl.LpVariable.dicts("over_target", lecturers, lowBound=0)
    under_target = pl.LpVariable.dicts("under_target", lecturers, lowBound=0)

    # --------------------------------------------------------
    # Assignment rule
    # --------------------------------------------------------
    for c in classes:
        if share_allowed[c] == "YA" or not full_cover_exists[c]:
            # share possible but minimized
            prob += pl.lpSum(x[c][l] for l in lecturers) >= 1
            prob += pl.lpSum(x[c][l] for l in lecturers) <= 2
            prob += pl.lpSum(x[c][l] for l in lecturers) - 1 <= share[c]
        else:
            # normal condition: exactly one lecturer
            prob += pl.lpSum(x[c][l] for l in lecturers) == 1
            prob += share[c] == 0

    # --------------------------------------------------------
    # Inactive lecturers cannot teach
    # --------------------------------------------------------
    for l in lecturers:
        if not active[l]:
            for c in classes:
                prob += x[c][l] == 0

    # --------------------------------------------------------
    # Availability
    # --------------------------------------------------------
    for c in classes:
        for l in lecturers:
            if not is_available_for_class(lect_rows.loc[l], class_rows.loc[c]):
                prob += x[c][l] == 0

            # If sharing is not required/allowed, lecturer must cover full class
            if share_allowed[c] != "YA" and full_cover_exists[c]:
                if not can_cover_full_class(lect_rows.loc[l], class_rows.loc[c]):
                    prob += x[c][l] == 0

    # --------------------------------------------------------
    # Workload max
    # If shared, this simple version gives full credit to each shared lecturer.
    # This is intentionally conservative to discourage sharing.
    # --------------------------------------------------------
    for l in lecturers:
        total_load = pl.lpSum(credit[c] * x[c][l] for c in classes)
        prob += total_load <= max_k[l]

    # --------------------------------------------------------
    # Link lecturer-subject
    # --------------------------------------------------------
    for c in classes:
        s = cls_subject[c]

        for l in lecturers:
            prob += x[c][l] <= y[l][s]

    # --------------------------------------------------------
    # Subject limit
    # --------------------------------------------------------
    for l in lecturers:
        prob += pl.lpSum(y[l][s] for s in subjects) <= MAX_SUBJECTS

    # --------------------------------------------------------
    # Max classes of same subject per lecturer
    # --------------------------------------------------------
    for l in lecturers:
        for s in subjects:
            subject_classes = [c for c in classes if cls_subject[c] == s]
            prob += pl.lpSum(x[c][l] for c in subject_classes) <= MAX_CLASSES_SAME_SUBJECT

    # --------------------------------------------------------
    # Minimum and target balance
    # --------------------------------------------------------
    for l in lecturers:
        total_load = pl.lpSum(credit[c] * x[c][l] for c in classes)

        if active[l]:
            effective_target = min(TARGET_CREDIT, max_k[l])
            prob += total_load + under_min[l] >= min_k[l]
            prob += total_load - effective_target <= over_target[l]
            prob += effective_target - total_load <= under_target[l]
        else:
            prob += under_min[l] == 0
            prob += over_target[l] == 0
            prob += under_target[l] == 0

    preference_reward = pl.lpSum(
        credit[c] * get_pref_score(l, cls_subject[c], pref) * x[c][l]
        for c in classes
        for l in lecturers
    )

    under_penalty = pl.lpSum(
        under_min[l]
        for l in lecturers
        if active[l]
    )

    balance_penalty = pl.lpSum(
        under_target[l] + over_target[l]
        for l in lecturers
        if active[l]
    )

    share_penalty = pl.lpSum(
        share[c]
        for c in classes
    )

    prob += (
        W_UNDER * under_penalty
        + W_BALANCE * balance_penalty
        + W_SHARE * share_penalty
        - W_PREF * preference_reward
    )

    solver = pl.PULP_CBC_CMD(msg=False, timeLimit=240)
    prob.solve(solver)

    status = pl.LpStatus[prob.status]

    assigned_rows = []

    for c in classes:
        for l in lecturers:
            val = float(pl.value(x[c][l]) or 0)

            if val > 0.5:
                assigned_rows.append({
                    "kelas_id": c,
                    "pensyarah": l,
                    "is_shared": int(round(float(pl.value(share[c]) or 0)))
                })

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
            asal = str(r.get("pensyarah_asal", "")).strip()

            rows.append({
                "kelas_id": cid,
                "kod_kursus": subj,
                "kelas_baru": r["kelas_baru"],
                "status_kelas": r["status_kelas"],
                "jam_kredit": int(r["jam_kredit"]),
                "saiz_kelas": int(r.get("saiz_kelas", 0)),
                "pensyarah": lname,
                "peranan": lrow["peranan"],
                "padanan_pilihan": get_pref_label(lname, subj, dfl),
                "skor_pilihan": get_pref_score(lname, subj, pref),
                "pensyarah_asal": asal,
                "berubah_dari_asal": "YA" if asal and asal != lname else "TIDAK",
                "share_allowed": r.get("share_allowed", "TIDAK"),
                "is_shared": "YA" if int(ar["is_shared"]) == 1 else "TIDAK",
                "minggu_mula_kelas": int(r["minggu_mula_kelas"]),
                "minggu_akhir_kelas": int(r["minggu_akhir_kelas"]),
                "minggu_mula_available": int(lrow["minggu_mula_available"]),
                "minggu_akhir_available": int(lrow["minggu_akhir_available"]),
                "perincian": r.get("perincian", "")
            })

        df_assign = pd.DataFrame(rows)

    if not df_assign.empty:
        df_assign = df_assign.sort_values(["kelas_id", "pensyarah"])

    # --------------------------------------------------------
    # Correct shared class analysis
    # Sharing = same kelas_id has more than one lecturer
    # --------------------------------------------------------
    if not df_assign.empty:
        df_shared_class = (
            df_assign
            .groupby(["kelas_id", "kod_kursus", "kelas_baru"])
            .agg(
                bil_pensyarah=("pensyarah", "nunique"),
                pensyarah_terlibat=("pensyarah", lambda x: ", ".join(sorted(set(x)))),
                minggu_kelas=("minggu_mula_kelas", "first")
            )
            .reset_index()
        )

        df_shared_class["status_share"] = np.where(
            df_shared_class["bil_pensyarah"] > 1,
            "SHARED CLASS",
            "SINGLE LECTURER"
        )

        df_shared_only = df_shared_class[df_shared_class["bil_pensyarah"] > 1].copy()
    else:
        df_shared_class = pd.DataFrame()
        df_shared_only = pd.DataFrame()

    # --------------------------------------------------------
    # Lecturer summary
    # --------------------------------------------------------
    summary_rows = []

    for _, lrow in dfl.iterrows():
        lname = lrow["nama"]

        if df_assign.empty:
            tmp = pd.DataFrame()
        else:
            tmp = df_assign[df_assign["pensyarah"] == lname]

        total_credit = int(tmp["jam_kredit"].sum()) if not tmp.empty else 0
        total_class = int(tmp["kelas_id"].nunique()) if not tmp.empty else 0
        subjects = sorted(tmp["kod_kursus"].unique().tolist()) if not tmp.empty else []

        detail_list = []

        if not tmp.empty:
            for subj, g in tmp.groupby("kod_kursus"):
                cls = ", ".join(g["kelas_baru"].astype(str).tolist())
                cr = int(g["jam_kredit"].sum())
                detail_list.append(f"{subj}: {cr} kredit ({cls})")

        shared_detail = []

        if not df_shared_only.empty:
            for _, sr in df_shared_only.iterrows():
                cid = sr["kelas_id"]
                lecturers = [x.strip() for x in sr["pensyarah_terlibat"].split(",")]

                if lname in lecturers:
                    others = [x for x in lecturers if x != lname]
                    shared_detail.append(f"{cid} dengan {', '.join(others)}")

        active = bool(lrow["active"])
        min_eff = int(lrow["effective_min_kredit"])
        max_eff = int(lrow["effective_max_kredit"])

        if not active:
            load_status = "TIDAK AKTIF / CUTI"
        elif total_credit < min_eff:
            load_status = "UNDERLOAD"
        elif total_credit > max_eff:
            load_status = "OVERLOAD"
        else:
            load_status = "OK"

        summary_rows.append({
            "pensyarah": lname,
            "peranan": lrow["peranan"],
            "status_pensyarah": lrow["status"],
            "aktif": active,
            "minimum_kredit": int(lrow["min_kredit"]),
            "maksimum_kredit": int(lrow["max_kredit"]),
            "minimum_efektif": min_eff,
            "maksimum_efektif": max_eff,
            "jumlah_jam_mengajar": total_credit,
            "jumlah_kelas": total_class,
            "bil_subjek": len(subjects),
            "senarai_subjek": ", ".join(subjects),
            "perincian_mengajar": " | ".join(detail_list),
            "shared_class_dengan": " | ".join(shared_detail) if shared_detail else "Tiada",
            "kurang_minimum": max(min_eff - total_credit, 0) if active else 0,
            "lebihan_maksimum": max(total_credit - max_eff, 0) if active else 0,
            "status_load": load_status
        })

    df_summary = pd.DataFrame(summary_rows)

    assigned_ids = set(df_assign["kelas_id"]) if not df_assign.empty else set()
    df_unassigned = dfc_active[~dfc_active["kelas_id"].isin(assigned_ids)].copy()

    preference_rate = 0

    if not df_assign.empty:
        preference_rate = round(
            df_assign["padanan_pilihan"].str.startswith("Pilihan").mean() * 100,
            1
        )

    df_status = pd.DataFrame([{
        "jumlah_kelas_aktif": len(dfc_active),
        "jumlah_kelas_tutup": len(df_closed),
        "kelas_diagih": len(assigned_ids),
        "kelas_tidak_diagih": len(df_unassigned),
        "jumlah_shared_class": len(df_shared_only),
        "jumlah_kredit_aktif": int(dfc_active["jam_kredit"].sum()),
        "kredit_diagih": int(df_assign["jam_kredit"].sum()) if not df_assign.empty else 0,
        "jumlah_pensyarah": len(dfl),
        "pensyarah_aktif": int(dfl["active"].sum()),
        "pensyarah_underload": int((df_summary["status_load"] == "UNDERLOAD").sum()),
        "pensyarah_overload": int((df_summary["status_load"] == "OVERLOAD").sum()),
        "preference_rate_%": preference_rate
    }])

    return df_assign, df_summary, df_shared_class, df_shared_only, df_unassigned, df_status


# ============================================================
# UPLOAD
# ============================================================

st.markdown('<div class="section-title">1. Upload Main Files</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-note">Minimum dan maksimum kredit diambil terus daripada fail pensyarah. Semester fixed 14 minggu.</div>',
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


# ============================================================
# MAIN APP
# ============================================================

if file_classes is None or file_lect is None:
    st.info("Upload dua fail: Jadual Kelas dan Pensyarah.")

    st.markdown(
        """
        <div class="soft-card">
        <b>Format wajib Jadual Kelas</b><br>
        kod_kursus, kelas_baru, jam_kredit<br><br>

        <b>Column optional untuk sharing</b><br>
        share_allowed = YA / TIDAK<br>
        Jika kosong, sistem anggap TIDAK.<br><br>

        <b>Format wajib Pensyarah</b><br>
        Nama Pensyarah, Peranan, Minimum Jam Kredit, Maksimum Jam Kredit, Pilihan 1 hingga Pilihan 5
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    if "loaded_class_file" not in st.session_state:
        st.session_state.loaded_class_file = ""

    if "class_df" not in st.session_state or st.session_state.loaded_class_file != file_classes.name:
        st.session_state.class_df = prepare_class_data(file_classes)
        st.session_state.loaded_class_file = file_classes.name

    dfl = prepare_lecturer_data(file_lect)

    st.markdown('<div class="section-title">2. Class Manager</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Tambah kelas baru, tutup kelas, atau benarkan sharing hanya untuk class tertentu.</div>',
        unsafe_allow_html=True
    )

    manager_tabs = st.tabs([
        "📋 Edit Jadual Kelas",
        "➕ Tambah Kelas Baru",
        "🗑️ Tutup Kelas / Subjek",
        "🤝 Share Permission"
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
                ),
                "share_allowed": st.column_config.SelectboxColumn(
                    "share_allowed",
                    options=["TIDAK", "YA"],
                    required=True
                )
            }
        )

        if st.button("💾 Simpan Perubahan Jadual Kelas", use_container_width=True):
            edited = edited.copy()
            edited["kod_kursus"] = edited["kod_kursus"].map(clean_text)
            edited["kelas_baru"] = edited["kelas_baru"].astype(str).str.strip()
            edited["status_kelas"] = edited["status_kelas"].map(standardize_status)
            edited["share_allowed"] = edited["share_allowed"].map(yes_no)
            edited["jam_kredit"] = pd.to_numeric(edited["jam_kredit"], errors="coerce").fillna(0).astype(int)
            edited["kelas_id"] = edited["kod_kursus"] + "-" + edited["kelas_baru"].astype(str)
            edited = edited.drop_duplicates(subset=["kelas_id"], keep="last").copy()
            st.session_state.class_df = edited
            st.success("Perubahan jadual kelas disimpan.")

    with manager_tabs[1]:
        c1, c2, c3 = st.columns(3)

        with c1:
            new_subject = st.text_input("Kod kursus", placeholder="Contoh: MAT112")
            new_class = st.text_input("Group / kelas", placeholder="Contoh: A1")

        with c2:
            new_credit = st.number_input("Jam kredit", 1, 10, 3, 1)
            new_size = st.number_input("Saiz kelas", 0, 500, 0, 1)

        with c3:
            new_start = st.number_input("Minggu mula", 1, SEMESTER_WEEKS, 1, 1)
            new_end = st.number_input("Minggu akhir", 1, SEMESTER_WEEKS, SEMESTER_WEEKS, 1)

        new_share = st.selectbox("Benarkan sharing untuk kelas ini?", ["TIDAK", "YA"])
        new_note = st.text_input("Catatan", placeholder="Contoh: kelas tambahan / pensyarah masuk lambat")

        if st.button("➕ Tambah Kelas Baru", use_container_width=True):
            if clean_text(new_subject) == "" or new_class.strip() == "":
                st.error("Kod kursus dan group/kelas wajib diisi.")
            else:
                new_row = {
                    "kelas_id": clean_text(new_subject) + "-" + new_class.strip(),
                    "kod_kursus": clean_text(new_subject),
                    "kelas_baru": new_class.strip(),
                    "status_kelas": "BARU",
                    "jam_kredit": int(new_credit),
                    "saiz_kelas": int(new_size),
                    "campuran_group": "",
                    "perincian": new_note,
                    "kredit_info": "",
                    "pensyarah_asal": "",
                    "lock_agihan": "TIDAK",
                    "share_allowed": new_share,
                    "minggu_mula_kelas": int(new_start),
                    "minggu_akhir_kelas": int(new_end)
                }

                updated = pd.concat(
                    [st.session_state.class_df, pd.DataFrame([new_row])],
                    ignore_index=True
                )

                updated["kelas_id"] = updated["kod_kursus"].map(clean_text) + "-" + updated["kelas_baru"].astype(str).str.strip()
                updated = updated.drop_duplicates(subset=["kelas_id"], keep="last").copy()

                st.session_state.class_df = updated
                st.success(f"Kelas {new_row['kelas_id']} berjaya ditambah.")

    with manager_tabs[2]:
        close_mode = st.radio(
            "Pilihan tutup",
            ["Tutup satu kelas", "Tutup semua kelas bagi satu subjek"],
            horizontal=True
        )

        if close_mode == "Tutup satu kelas":
            class_ids = sorted(st.session_state.class_df["kelas_id"].dropna().unique().tolist())
            selected_class = st.selectbox("Pilih kelas", class_ids)

            if st.button("🗑️ Tutup Kelas Ini", use_container_width=True):
                st.session_state.class_df.loc[
                    st.session_state.class_df["kelas_id"] == selected_class,
                    "status_kelas"
                ] = "TUTUP"
                st.success(f"{selected_class} telah ditutup.")

        else:
            subjects = sorted(st.session_state.class_df["kod_kursus"].dropna().unique().tolist())
            selected_subject = st.selectbox("Pilih subjek", subjects)

            if st.button("🗑️ Tutup Semua Kelas Subjek Ini", use_container_width=True):
                st.session_state.class_df.loc[
                    st.session_state.class_df["kod_kursus"] == selected_subject,
                    "status_kelas"
                ] = "TUTUP"
                st.success(f"Semua kelas bagi {selected_subject} telah ditutup.")

    with manager_tabs[3]:
        st.info("Sharing bermaksud subjek sama dan group sama. Contoh MAT112-A1 diajar oleh dua pensyarah. Sistem akan minimize sharing.")

        share_df = st.session_state.class_df[
            ["kelas_id", "kod_kursus", "kelas_baru", "status_kelas", "share_allowed", "minggu_mula_kelas", "minggu_akhir_kelas", "perincian"]
        ].copy()

        share_edit = st.data_editor(
            share_df,
            use_container_width=True,
            height=400,
            column_config={
                "share_allowed": st.column_config.SelectboxColumn(
                    "share_allowed",
                    options=["TIDAK", "YA"],
                    required=True
                )
            }
        )

        if st.button("💾 Simpan Share Permission", use_container_width=True):
            mapping = share_edit.set_index("kelas_id")["share_allowed"].map(yes_no).to_dict()
            st.session_state.class_df["share_allowed"] = st.session_state.class_df["kelas_id"].map(mapping).fillna("TIDAK")
            st.success("Share permission disimpan.")

    df_all = st.session_state.class_df.copy()
    df_all["status_kelas"] = df_all["status_kelas"].map(standardize_status)
    df_all["share_allowed"] = df_all["share_allowed"].map(yes_no)

    df_active = df_all[df_all["status_kelas"].isin(["BUKA", "BARU"])].copy()
    df_closed = df_all[df_all["status_kelas"] == "TUTUP"].copy()

    st.markdown('<div class="section-title">3. Data Overview</div>', unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        metric_card("Kelas Aktif", len(df_active), "BUKA + BARU")

    with k2:
        metric_card("Kelas Tutup", len(df_closed), "Tidak diagih")

    with k3:
        metric_card("Kredit Aktif", int(df_active["jam_kredit"].sum()), "Jumlah perlu cover")

    with k4:
        metric_card("Pensyarah Aktif", int(dfl["active"].sum()), "Boleh mengajar")

    with k5:
        metric_card("Share Allowed", int((df_active["share_allowed"] == "YA").sum()), "Class yang boleh share")

    if int(dfl["effective_max_kredit"].sum()) < int(df_active["jam_kredit"].sum()):
        st.error("Kapasiti maksimum pensyarah tidak cukup untuk cover semua kelas aktif.")

    with st.expander("Lihat Data Aktif / Tutup / Pensyarah", expanded=False):
        t1, t2, t3 = st.tabs(["Kelas Aktif", "Kelas Tutup", "Pensyarah"])

        with t1:
            st.dataframe(df_active, use_container_width=True, height=360)

        with t2:
            st.dataframe(df_closed, use_container_width=True, height=360)

        with t3:
            st.dataframe(dfl, use_container_width=True, height=360)

    st.markdown('<div class="section-title">4. Run ILASO Allocation</div>', unsafe_allow_html=True)

    if st.button("🚀 Run Allocation", use_container_width=True):
        pref = build_preference_score(dfl)
        solver_status, assigned_df = solve_allocation(df_active, dfl, pref)

        if solver_status == "Optimal":
            st.success("Optimization Status: Optimal")
        else:
            st.warning(f"Optimization Status: {solver_status}")

        df_assign, df_summary, df_shared_class, df_shared_only, df_unassigned, df_status = build_outputs(
            df_active,
            df_closed,
            dfl,
            pref,
            assigned_df
        )

        s = df_status.iloc[0]

        st.markdown('<div class="section-title">5. Executive Dashboard</div>', unsafe_allow_html=True)

        d1, d2, d3, d4, d5 = st.columns(5)

        with d1:
            metric_card("Coverage", f"{s['kelas_diagih']}/{s['jumlah_kelas_aktif']}", "Kelas diagih")

        with d2:
            metric_card("Preference", f"{s['preference_rate_%']}%", "Ikut pilihan")

        with d3:
            metric_card("Shared Class", int(s["jumlah_shared_class"]), "Same subject + same group")

        with d4:
            metric_card("Underload", int(s["pensyarah_underload"]), "Kurang minimum")

        with d5:
            metric_card("Overload", int(s["pensyarah_overload"]), "Lebih maksimum")

        result_tabs = st.tabs([
            "📌 Allocation",
            "👤 Lecturer Analysis",
            "🤝 Shared Class",
            "📊 Charts",
            "🔍 Audit",
            "📥 Export"
        ])

        with result_tabs[0]:
            st.markdown("### Agihan Kelas")
            st.dataframe(df_assign, use_container_width=True, height=520)

        with result_tabs[1]:
            st.markdown("### Analisis Pensyarah")
            st.dataframe(df_summary, use_container_width=True, height=540)

        with result_tabs[2]:
            st.markdown("### Shared Class Analysis")
            st.caption("Sharing hanya dikira apabila kelas_id yang sama mempunyai lebih daripada seorang pensyarah.")

            st.dataframe(df_shared_class, use_container_width=True, height=340)

            st.markdown("### Shared Class Sahaja")
            if df_shared_only.empty:
                st.success("Tiada shared class. Semua kelas diajar oleh seorang pensyarah sahaja.")
            else:
                st.warning("Ada shared class.")
                st.dataframe(df_shared_only, use_container_width=True, height=320)

            st.markdown("### Shared Class by Lecturer")
            st.dataframe(
                df_summary[
                    [
                        "pensyarah",
                        "jumlah_jam_mengajar",
                        "senarai_subjek",
                        "shared_class_dengan",
                        "status_load"
                    ]
                ],
                use_container_width=True,
                height=420
            )

        with result_tabs[3]:
            st.markdown("### Workload Distribution")

            if px is not None and not df_summary.empty:
                fig = px.bar(
                    df_summary.sort_values("jumlah_jam_mengajar"),
                    x="jumlah_jam_mengajar",
                    y="pensyarah",
                    orientation="h",
                    text="jumlah_jam_mengajar",
                    title="Jumlah Jam Mengajar Mengikut Pensyarah"
                )
                fig.update_layout(height=680)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.dataframe(
                    df_summary[["pensyarah", "jumlah_jam_mengajar"]],
                    use_container_width=True
                )

            if px is not None and not df_assign.empty:
                pref_count = df_assign["padanan_pilihan"].value_counts().reset_index()
                pref_count.columns = ["padanan_pilihan", "count"]

                fig2 = px.pie(
                    pref_count,
                    names="padanan_pilihan",
                    values="count",
                    hole=0.45,
                    title="Preference Satisfaction"
                )
                st.plotly_chart(fig2, use_container_width=True)

        with result_tabs[4]:
            st.markdown("### Audit Semakan")

            if df_unassigned.empty:
                st.success("Semua kelas aktif berjaya diagih.")
            else:
                st.error("Ada kelas aktif tidak diagih.")
                st.dataframe(df_unassigned, use_container_width=True)

            under = df_summary[df_summary["status_load"] == "UNDERLOAD"]
            over = df_summary[df_summary["status_load"] == "OVERLOAD"]

            if not under.empty:
                st.warning("Pensyarah underload.")
                st.dataframe(under, use_container_width=True)

            if not over.empty:
                st.error("Pensyarah overload.")
                st.dataframe(over, use_container_width=True)

            if not df_shared_only.empty:
                st.warning("Shared class wujud. Semak sebab: pensyarah masuk lambat / partial availability / share_allowed.")
                st.dataframe(df_shared_only, use_container_width=True)

            st.markdown("### Kelas Ditutup")
            st.dataframe(df_closed, use_container_width=True, height=300)

        with result_tabs[5]:
            output = to_excel_bytes({
                "Status": df_status,
                "Agihan": df_assign,
                "Analisis_Pensyarah": df_summary,
                "Shared_Class_All": df_shared_class,
                "Shared_Class_Only": df_shared_only,
                "Kelas_Tidak_Diagih": df_unassigned,
                "Kelas_Tutup": df_closed,
                "Main_File_Updated": df_all
            })

            st.download_button(
                "📥 Download Full Result Excel",
                data=output,
                file_name="ILASO_result_correct_shared_class.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            updated_main = to_excel_bytes({
                "Jadual_Kelas": df_all
            })

            st.download_button(
                "📥 Download Updated Main File",
                data=updated_main,
                file_name="Jadual_Kelas_Updated.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

st.markdown(
    """
    <div class="footer">
        ILASO fixed semester = 14 weeks. Sharing means the same subject and same group/class is taught by more than one lecturer.
    </div>
    """,
    unsafe_allow_html=True
)
