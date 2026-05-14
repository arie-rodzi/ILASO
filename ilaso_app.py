# ============================================================
# ILASO - Intelligent Lecturer Allocation System
# With Add / Close Subject-Class Manager
# ============================================================
# Run:
# streamlit run ilaso_app.py
#
# Install:
# pip install streamlit pandas numpy openpyxl pulp plotly
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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ILASO",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .block-container {padding-top:1.2rem; padding-bottom:2rem;}
    .hero {
        background: linear-gradient(135deg,#061A40,#0B3D91);
        color:white; padding:26px 32px; border-radius:24px;
        box-shadow:0 12px 35px rgba(0,0,0,0.16); margin-bottom:20px;
    }
    .hero h1 {font-size:38px; margin:0; font-weight:850;}
    .hero p {font-size:16px; color:#EAF0FF; margin-top:5px;}
    .metric-card {
        background:white; border:1px solid #E6EAF2; border-radius:18px;
        padding:18px; box-shadow:0 8px 24px rgba(10,40,90,0.08);
    }
    .metric-label {font-size:12px; color:#667085; font-weight:700; text-transform:uppercase;}
    .metric-value {font-size:30px; font-weight:850; color:#061A40;}
    .section-title {font-size:22px; font-weight:850; color:#061A40; margin-top:16px;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero">
        <h1>ILASO</h1>
        <p>Intelligent Lecturer Allocation with Class Manager, Closed-Class Handling and Lecturer Analytics</p>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# BASIC SETTINGS
# ============================================================

st.sidebar.title("⚙️ ILASO Setting")

semester_weeks = st.sidebar.number_input("Jumlah minggu semester", 1, 30, 14, 1)
target_credit = st.sidebar.number_input("Target kredit pensyarah", 1, 40, 15, 1)
default_min = st.sidebar.number_input("Default minimum kredit", 0, 40, 15, 1)
default_max = st.sidebar.number_input("Default maksimum kredit", 0, 40, 18, 1)
max_subjects = st.sidebar.number_input("Maksimum subjek unik / pensyarah", 1, 5, 2, 1)
max_classes_same_subject = st.sidebar.number_input("Maksimum kelas sama subjek / pensyarah", 1, 10, 3, 1)

advanced = st.sidebar.toggle("Advanced Mode", value=False)

if advanced:
    score_p1 = st.sidebar.number_input("Skor Pilihan 1", -1000, 1000, 100, 5)
    score_p2 = st.sidebar.number_input("Skor Pilihan 2", -1000, 1000, 80, 5)
    score_p3 = st.sidebar.number_input("Skor Pilihan 3", -1000, 1000, 60, 5)
    score_p4 = st.sidebar.number_input("Skor Pilihan 4", -1000, 1000, 40, 5)
    score_p5 = st.sidebar.number_input("Skor Pilihan 5", -1000, 1000, 20, 5)
    score_not_pref = st.sidebar.number_input("Skor bukan pilihan", -1000, 1000, -30, 5)

    w_pref = st.sidebar.number_input("Weight preference", 1, 100000, 80, 10)
    w_under = st.sidebar.number_input("Penalty underload", 1, 100000, 5000, 100)
    w_balance = st.sidebar.number_input("Penalty imbalance", 1, 100000, 2500, 100)
else:
    score_p1, score_p2, score_p3, score_p4, score_p5 = 100, 80, 60, 40, 20
    score_not_pref = -30
    w_pref, w_under, w_balance = 80, 5000, 2500


# ============================================================
# HELPERS
# ============================================================

def metric_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div style="font-size:12px;color:#7A869A;">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


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
    if x in ["", "OPEN", "AKTIF", "ACTIVE", "BUKA"]:
        return "BUKA"
    if x in ["TUTUP", "CLOSE", "CLOSED", "CANCEL", "CANCELLED", "BATAL"]:
        return "TUTUP"
    if x in ["NEW", "BARU", "BAHARU"]:
        return "BARU"
    return x


def read_file(uploaded_file, expected_sheet=None):
    name = uploaded_file.name.lower()

    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file, encoding="utf-8-sig")

    xl = pd.ExcelFile(uploaded_file)

    if expected_sheet and expected_sheet in xl.sheet_names:
        return pd.read_excel(uploaded_file, sheet_name=expected_sheet)

    return pd.read_excel(uploaded_file, sheet_name=xl.sheet_names[0])


def prepare_class_data(file_classes):
    df = read_file(file_classes, expected_sheet="Jadual_Kelas").copy()

    required = ["kod_kursus", "kelas_baru", "jam_kredit"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Fail kelas tiada column wajib: {missing}")
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

    for c in ["campuran_group", "perincian", "kredit_info"]:
        if c not in df.columns:
            df[c] = ""

    if "pensyarah_asal" not in df.columns:
        df["pensyarah_asal"] = ""

    if "lock_agihan" not in df.columns:
        df["lock_agihan"] = "TIDAK"

    if "minggu_mula_kelas" not in df.columns:
        df["minggu_mula_kelas"] = 1

    if "minggu_akhir_kelas" not in df.columns:
        df["minggu_akhir_kelas"] = semester_weeks

    df["minggu_mula_kelas"] = pd.to_numeric(df["minggu_mula_kelas"], errors="coerce").fillna(1).astype(int)
    df["minggu_akhir_kelas"] = pd.to_numeric(df["minggu_akhir_kelas"], errors="coerce").fillna(semester_weeks).astype(int)

    df = df[(df["kod_kursus"] != "") & (df["kelas_baru"] != "") & (df["jam_kredit"] > 0)].copy()
    df["kelas_id"] = df["kod_kursus"] + "-" + df["kelas_baru"].astype(str)

    df = df.drop_duplicates(subset=["kelas_id"], keep="first").copy()

    preferred_cols = [
        "kelas_id", "kod_kursus", "kelas_baru", "status_kelas", "jam_kredit",
        "saiz_kelas", "campuran_group", "perincian", "kredit_info",
        "pensyarah_asal", "lock_agihan", "minggu_mula_kelas", "minggu_akhir_kelas"
    ]

    other_cols = [c for c in df.columns if c not in preferred_cols]
    return df[preferred_cols + other_cols]


def prepare_lecturer_data(file_lect):
    raw = read_file(file_lect, expected_sheet="Pensyarah").copy()

    required = ["Nama Pensyarah", "Peranan", "Minimum Jam Kredit", "Maksimum Jam Kredit"]
    missing = [c for c in required if c not in raw.columns]
    if missing:
        st.error(f"Fail pensyarah tiada column wajib: {missing}")
        st.stop()

    df = raw.rename(columns={
        "Nama Pensyarah": "nama",
        "Peranan": "peranan",
        "Minimum Jam Kredit": "min_kredit",
        "Maksimum Jam Kredit": "max_kredit"
    }).copy()

    df["nama"] = df["nama"].map(clean_name)
    df["peranan"] = df["peranan"].astype(str).str.strip()
    df["min_kredit"] = pd.to_numeric(df["min_kredit"], errors="coerce").fillna(default_min).astype(int)
    df["max_kredit"] = pd.to_numeric(df["max_kredit"], errors="coerce").fillna(default_max).astype(int)

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
        df["minggu_akhir_available"] = semester_weeks

    df["minggu_mula_available"] = pd.to_numeric(df["minggu_mula_available"], errors="coerce").fillna(1).astype(int)
    df["minggu_akhir_available"] = pd.to_numeric(df["minggu_akhir_available"], errors="coerce").fillna(semester_weeks).astype(int)

    df["available_weeks"] = (
        df["minggu_akhir_available"] - df["minggu_mula_available"] + 1
    ).clip(lower=0, upper=semester_weeks)

    df["availability_ratio"] = df["available_weeks"] / semester_weeks

    df["effective_min_kredit"] = np.floor(df["min_kredit"] * df["availability_ratio"]).astype(int)
    df["effective_max_kredit"] = np.floor(df["max_kredit"] * df["availability_ratio"]).astype(int)

    cuti_mask = (
        df["peranan"].str.lower().str.contains("cuti", na=False) |
        df["status"].isin(["CUTI", "TIDAK_AKTIF", "SABBATICAL"])
    )

    df.loc[cuti_mask, ["effective_min_kredit", "effective_max_kredit"]] = 0
    df["active"] = df["effective_max_kredit"] > 0

    df = df[df["nama"] != ""].drop_duplicates(subset=["nama"], keep="first").copy()
    return df


def preference_score_table(dfl):
    score_map = {
        1: score_p1,
        2: score_p2,
        3: score_p3,
        4: score_p4,
        5: score_p5
    }

    pref = {}

    for _, row in dfl.iterrows():
        lname = row["nama"]
        for i in range(1, 6):
            subj = clean_text(row.get(f"Pilihan {i}", ""))
            if subj:
                pref[(lname, subj)] = score_map[i]

    return pref


def get_pref_score(lname, subject, pref):
    return int(pref.get((lname, subject), score_not_pref))


def get_pref_label(lname, subject, dfl):
    row = dfl[dfl["nama"] == lname]
    if row.empty:
        return "Tidak diketahui"

    row = row.iloc[0]

    for i in range(1, 6):
        if clean_text(row.get(f"Pilihan {i}", "")) == subject:
            return f"Pilihan {i}"

    return "Bukan pilihan"


def is_available(lrow, crow):
    return max(
        int(lrow["minggu_mula_available"]),
        int(crow["minggu_mula_kelas"])
    ) <= min(
        int(lrow["minggu_akhir_available"]),
        int(crow["minggu_akhir_kelas"])
    )


# ============================================================
# OPTIMIZER
# ============================================================

def solve_allocation(dfc_active, dfl, pref):
    if pl is None:
        st.error("PuLP belum install. Sila run: pip install pulp")
        st.stop()

    classes = dfc_active["kelas_id"].tolist()
    lecturers = dfl["nama"].tolist()
    subjects = sorted(dfc_active["kod_kursus"].unique())

    credit = dfc_active.set_index("kelas_id")["jam_kredit"].astype(int).to_dict()
    cls_subject = dfc_active.set_index("kelas_id")["kod_kursus"].to_dict()

    min_k = dfl.set_index("nama")["effective_min_kredit"].astype(int).to_dict()
    max_k = dfl.set_index("nama")["effective_max_kredit"].astype(int).to_dict()
    active = dfl.set_index("nama")["active"].to_dict()

    class_rows = dfc_active.set_index("kelas_id")
    lect_rows = dfl.set_index("nama")

    prob = pl.LpProblem("ILASO", pl.LpMinimize)

    x = pl.LpVariable.dicts("x", (classes, lecturers), 0, 1, cat="Binary")
    y = pl.LpVariable.dicts("y", (lecturers, subjects), 0, 1, cat="Binary")
    under_min = pl.LpVariable.dicts("under_min", lecturers, lowBound=0)
    over_target = pl.LpVariable.dicts("over_target", lecturers, lowBound=0)
    under_target = pl.LpVariable.dicts("under_target", lecturers, lowBound=0)

    for c in classes:
        prob += pl.lpSum(x[c][l] for l in lecturers) == 1

    for l in lecturers:
        if not active[l]:
            for c in classes:
                prob += x[c][l] == 0

    for c in classes:
        for l in lecturers:
            if not is_available(lect_rows.loc[l], class_rows.loc[c]):
                prob += x[c][l] == 0

    for l in lecturers:
        load = pl.lpSum(credit[c] * x[c][l] for c in classes)
        prob += load <= max_k[l]

    for c in classes:
        s = cls_subject[c]
        for l in lecturers:
            prob += x[c][l] <= y[l][s]

    for l in lecturers:
        prob += pl.lpSum(y[l][s] for s in subjects) <= int(max_subjects)

    for l in lecturers:
        for s in subjects:
            sc = [c for c in classes if cls_subject[c] == s]
            prob += pl.lpSum(x[c][l] for c in sc) <= int(max_classes_same_subject)

    for l in lecturers:
        load = pl.lpSum(credit[c] * x[c][l] for c in classes)
        if active[l]:
            eff_target = min(int(target_credit), max_k[l])
            prob += load + under_min[l] >= min_k[l]
            prob += load - eff_target <= over_target[l]
            prob += eff_target - load <= under_target[l]
        else:
            prob += under_min[l] == 0
            prob += over_target[l] == 0
            prob += under_target[l] == 0

    preference_reward = pl.lpSum(
        credit[c] * get_pref_score(l, cls_subject[c], pref) * x[c][l]
        for c in classes for l in lecturers
    )

    under_penalty = pl.lpSum(under_min[l] for l in lecturers if active[l])
    balance_penalty = pl.lpSum(
        under_target[l] + over_target[l]
        for l in lecturers if active[l]
    )

    prob += (
        w_under * under_penalty
        + w_balance * balance_penalty
        - w_pref * preference_reward
    )

    solver = pl.PULP_CBC_CMD(msg=False, timeLimit=180)
    prob.solve(solver)

    status = pl.LpStatus[prob.status]

    assigned = {}
    for c in classes:
        for l in lecturers:
            val = float(pl.value(x[c][l]) or 0)
            if val > 0.5:
                assigned[c] = l

    return status, assigned


# ============================================================
# OUTPUT ANALYTICS
# ============================================================

def build_outputs(dfc_active, df_closed, dfl, pref, assigned):
    rows = []
    lect_lookup = dfl.set_index("nama")

    for _, r in dfc_active.iterrows():
        cid = r["kelas_id"]
        lname = assigned.get(cid, "")

        if lname == "":
            continue

        lrow = lect_lookup.loc[lname]
        subj = r["kod_kursus"]
        asal = str(r.get("pensyarah_asal", "")).strip()

        rows.append({
            "kelas_id": cid,
            "kod_kursus": subj,
            "kelas_baru": r["kelas_baru"],
            "status_kelas": r["status_kelas"],
            "jam_kredit": int(r["jam_kredit"]),
            "saiz_kelas": r.get("saiz_kelas", ""),
            "pensyarah": lname,
            "peranan": lrow["peranan"],
            "padanan_pilihan": get_pref_label(lname, subj, dfl),
            "skor_pilihan": get_pref_score(lname, subj, pref),
            "pensyarah_asal": asal,
            "berubah_dari_asal": "YA" if asal and asal != lname else "TIDAK",
            "minggu_mula_kelas": r["minggu_mula_kelas"],
            "minggu_akhir_kelas": r["minggu_akhir_kelas"],
        })

    df_assign = pd.DataFrame(rows)

    if not df_assign.empty:
        df_assign = df_assign.sort_values(["pensyarah", "kod_kursus", "kelas_baru"])

    summary = []

    for _, lrow in dfl.iterrows():
        lname = lrow["nama"]
        tmp = df_assign[df_assign["pensyarah"] == lname] if not df_assign.empty else pd.DataFrame()

        total_credit = int(tmp["jam_kredit"].sum()) if not tmp.empty else 0
        subjects = sorted(tmp["kod_kursus"].unique()) if not tmp.empty else []

        detail_subjek = []
        if not tmp.empty:
            for s, g in tmp.groupby("kod_kursus"):
                detail_subjek.append(
                    f"{s}: {int(g['jam_kredit'].sum())} kredit ({', '.join(g['kelas_baru'].astype(str))})"
                )

        summary.append({
            "pensyarah": lname,
            "peranan": lrow["peranan"],
            "status_pensyarah": lrow["status"],
            "aktif": bool(lrow["active"]),
            "min_efektif": int(lrow["effective_min_kredit"]),
            "max_efektif": int(lrow["effective_max_kredit"]),
            "jumlah_jam_mengajar": total_credit,
            "jumlah_kelas": len(tmp),
            "bil_subjek": len(subjects),
            "senarai_subjek": ", ".join(subjects),
            "perincian_mengajar": " | ".join(detail_subjek),
            "status_load": (
                "CUTI / TIDAK AKTIF" if not bool(lrow["active"]) else
                "UNDERLOAD" if total_credit < int(lrow["effective_min_kredit"]) else
                "OVERLOAD" if total_credit > int(lrow["effective_max_kredit"]) else
                "OK"
            )
        })

    df_summary = pd.DataFrame(summary)

    combined_rows = []

    if not df_assign.empty:
        for subj, g in df_assign.groupby("kod_kursus"):
            lecturers = sorted(g["pensyarah"].unique())
            combined_rows.append({
                "kod_kursus": subj,
                "bil_pensyarah": len(lecturers),
                "pensyarah_terlibat": ", ".join(lecturers),
                "status_combined": "Combined Teaching" if len(lecturers) > 1 else "Single Lecturer"
            })

    df_combined_subject = pd.DataFrame(combined_rows)

    lecturer_combined = []

    if not df_assign.empty and not df_combined_subject.empty:
        for lname in dfl["nama"]:
            related = []

            for _, row in df_combined_subject.iterrows():
                lecturers = [x.strip() for x in row["pensyarah_terlibat"].split(",")]
                if lname in lecturers and len(lecturers) > 1:
                    others = [x for x in lecturers if x != lname]
                    related.append(f"{row['kod_kursus']} dengan {', '.join(others)}")

            lecturer_combined.append({
                "pensyarah": lname,
                "combined_dengan": " | ".join(related) if related else "Tiada"
            })

    df_lecturer_combined = pd.DataFrame(lecturer_combined)

    if not df_summary.empty and not df_lecturer_combined.empty:
        df_summary = df_summary.merge(df_lecturer_combined, on="pensyarah", how="left")

    assigned_ids = set(df_assign["kelas_id"]) if not df_assign.empty else set()
    df_unassigned = dfc_active[~dfc_active["kelas_id"].isin(assigned_ids)].copy()

    status = pd.DataFrame([{
        "jumlah_kelas_aktif": len(dfc_active),
        "jumlah_kelas_tutup": len(df_closed),
        "kelas_diagih": len(df_assign),
        "kelas_tidak_diagih": len(df_unassigned),
        "jumlah_kredit_aktif": int(dfc_active["jam_kredit"].sum()),
        "kredit_diagih": int(df_assign["jam_kredit"].sum()) if not df_assign.empty else 0,
        "pensyarah_aktif": int(dfl["active"].sum()),
        "pensyarah_underload": int((df_summary["status_load"] == "UNDERLOAD").sum()),
        "pensyarah_overload": int((df_summary["status_load"] == "OVERLOAD").sum()),
    }])

    return df_assign, df_summary, df_combined_subject, df_unassigned, status


def to_excel_bytes(dfs):
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for name, df in dfs.items():
                df.to_excel(writer, index=False, sheet_name=name[:31])
        return buffer.getvalue()


# ============================================================
# UPLOAD
# ============================================================

st.markdown('<div class="section-title">1. Upload Main Files</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    file_classes = st.file_uploader(
        "Upload main file Jadual Kelas",
        type=["xlsx", "csv"]
    )

with c2:
    file_lect = st.file_uploader(
        "Upload file Pensyarah",
        type=["xlsx", "csv"]
    )


# ============================================================
# MAIN APP
# ============================================================

if file_classes is not None and file_lect is not None:

    if "class_df_loaded_name" not in st.session_state:
        st.session_state.class_df_loaded_name = ""

    if st.session_state.class_df_loaded_name != file_classes.name:
        st.session_state.class_df = prepare_class_data(file_classes)
        st.session_state.class_df_loaded_name = file_classes.name

    dfl = prepare_lecturer_data(file_lect)

    st.markdown('<div class="section-title">2. Class Manager: Tambah / Tutup Subjek Terus Dalam Sistem</div>', unsafe_allow_html=True)

    tabs_manager = st.tabs([
        "📋 Edit Status Kelas",
        "➕ Tambah Subjek / Kelas Baru",
        "🗑️ Tutup Subjek / Kelas"
    ])

    with tabs_manager[0]:
        st.info("Edit `status_kelas` kepada BUKA / BARU / TUTUP. Kelas TUTUP tidak akan masuk allocation.")

        edited_df = st.data_editor(
            st.session_state.class_df,
            use_container_width=True,
            height=420,
            num_rows="dynamic",
            column_config={
                "status_kelas": st.column_config.SelectboxColumn(
                    "status_kelas",
                    options=["BUKA", "BARU", "TUTUP"],
                    required=True
                )
            },
            key="class_editor"
        )

        if st.button("💾 Simpan Perubahan Class Manager", use_container_width=True):
            edited_df["kod_kursus"] = edited_df["kod_kursus"].map(clean_text)
            edited_df["kelas_baru"] = edited_df["kelas_baru"].astype(str).str.strip()
            edited_df["status_kelas"] = edited_df["status_kelas"].map(standardize_status)
            edited_df["jam_kredit"] = pd.to_numeric(edited_df["jam_kredit"], errors="coerce").fillna(0).astype(int)
            edited_df["kelas_id"] = edited_df["kod_kursus"] + "-" + edited_df["kelas_baru"].astype(str)
            edited_df = edited_df.drop_duplicates(subset=["kelas_id"], keep="last").copy()
            st.session_state.class_df = edited_df
            st.success("Perubahan disimpan.")

    with tabs_manager[1]:
        st.subheader("Tambah Subjek / Kelas Baru")

        a1, a2, a3 = st.columns(3)

        with a1:
            new_subject = st.text_input("Kod kursus", placeholder="Contoh: MAT421")
            new_class = st.text_input("Kelas baru", placeholder="Contoh: CS2404A")

        with a2:
            new_credit = st.number_input("Jam kredit", 1, 10, 3, 1)
            new_size = st.number_input("Saiz kelas", 0, 500, 0, 1)

        with a3:
            new_start = st.number_input("Minggu mula kelas", 1, semester_weeks, 1, 1)
            new_end = st.number_input("Minggu akhir kelas", 1, semester_weeks, semester_weeks, 1)

        new_detail = st.text_input("Catatan / Perincian", placeholder="Contoh: kelas tambahan dibuka minggu ke-4")

        if st.button("➕ Tambah Ke Main File Dalam Sistem", use_container_width=True):
            if clean_text(new_subject) == "" or new_class.strip() == "":
                st.error("Kod kursus dan kelas baru wajib diisi.")
            else:
                new_row = {
                    "kelas_id": clean_text(new_subject) + "-" + new_class.strip(),
                    "kod_kursus": clean_text(new_subject),
                    "kelas_baru": new_class.strip(),
                    "status_kelas": "BARU",
                    "jam_kredit": int(new_credit),
                    "saiz_kelas": int(new_size),
                    "campuran_group": "",
                    "perincian": new_detail,
                    "kredit_info": "",
                    "pensyarah_asal": "",
                    "lock_agihan": "TIDAK",
                    "minggu_mula_kelas": int(new_start),
                    "minggu_akhir_kelas": int(new_end)
                }

                temp = pd.concat(
                    [st.session_state.class_df, pd.DataFrame([new_row])],
                    ignore_index=True
                )

                temp["kelas_id"] = temp["kod_kursus"].map(clean_text) + "-" + temp["kelas_baru"].astype(str).str.strip()
                temp = temp.drop_duplicates(subset=["kelas_id"], keep="last").copy()

                st.session_state.class_df = temp
                st.success(f"Kelas {new_row['kelas_id']} berjaya ditambah sebagai BARU.")

    with tabs_manager[2]:
        st.subheader("Tutup Subjek / Kelas")

        all_subjects = sorted(st.session_state.class_df["kod_kursus"].dropna().unique())
        close_mode = st.radio(
            "Pilih cara tutup",
            ["Tutup satu kelas sahaja", "Tutup semua kelas untuk satu subjek"],
            horizontal=True
        )

        if close_mode == "Tutup satu kelas sahaja":
            all_class_ids = sorted(st.session_state.class_df["kelas_id"].dropna().unique())
            selected_class = st.selectbox("Pilih kelas_id untuk ditutup", all_class_ids)

            if st.button("🗑️ Tutup Kelas Ini", use_container_width=True):
                st.session_state.class_df.loc[
                    st.session_state.class_df["kelas_id"] == selected_class,
                    "status_kelas"
                ] = "TUTUP"
                st.success(f"{selected_class} telah ditutup.")

        else:
            selected_subject = st.selectbox("Pilih kod kursus untuk tutup semua kelas", all_subjects)

            if st.button("🗑️ Tutup Semua Kelas Subjek Ini", use_container_width=True):
                st.session_state.class_df.loc[
                    st.session_state.class_df["kod_kursus"] == selected_subject,
                    "status_kelas"
                ] = "TUTUP"
                st.success(f"Semua kelas bagi {selected_subject} telah ditutup.")

    df_all = st.session_state.class_df.copy()
    df_all["status_kelas"] = df_all["status_kelas"].map(standardize_status)

    df_active = df_all[df_all["status_kelas"].isin(["BUKA", "BARU"])].copy()
    df_closed = df_all[df_all["status_kelas"] == "TUTUP"].copy()

    st.markdown('<div class="section-title">3. Data Readiness</div>', unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        metric_card("Kelas Aktif", len(df_active), "BUKA + BARU")
    with m2:
        metric_card("Kelas Tutup", len(df_closed), "Tidak masuk allocation")
    with m3:
        metric_card("Jumlah Kredit", int(df_active["jam_kredit"].sum()), "Kelas aktif sahaja")
    with m4:
        metric_card("Pensyarah Aktif", int(dfl["active"].sum()), "Boleh mengajar")
    with m5:
        metric_card("Kapasiti", int(dfl["effective_max_kredit"].sum()), "Max kredit efektif")

    if int(dfl["effective_max_kredit"].sum()) < int(df_active["jam_kredit"].sum()):
        st.error("Kapasiti pensyarah tidak cukup untuk cover semua kelas aktif.")

    with st.expander("Lihat kelas aktif dan kelas tutup", expanded=False):
        q1, q2 = st.columns(2)
        with q1:
            st.write("Kelas Aktif")
            st.dataframe(df_active, use_container_width=True, height=300)
        with q2:
            st.write("Kelas Tutup")
            st.dataframe(df_closed, use_container_width=True, height=300)

    st.markdown('<div class="section-title">4. Run Allocation</div>', unsafe_allow_html=True)

    if st.button("🚀 Run ILASO Allocation", use_container_width=True):

        pref = preference_score_table(dfl)

        status_solver, assigned = solve_allocation(df_active, dfl, pref)

        if status_solver == "Optimal":
            st.success("Optimization Status: Optimal")
        else:
            st.warning(f"Optimization Status: {status_solver}")

        df_assign, df_summary, df_combined, df_unassigned, df_status = build_outputs(
            df_active, df_closed, dfl, pref, assigned
        )

        s = df_status.iloc[0]

        st.markdown('<div class="section-title">5. Executive Dashboard</div>', unsafe_allow_html=True)

        k1, k2, k3, k4, k5 = st.columns(5)

        with k1:
            metric_card("Coverage", f"{s['kelas_diagih']}/{s['jumlah_kelas_aktif']}", "Kelas berjaya diagih")
        with k2:
            metric_card("Closed", int(s["jumlah_kelas_tutup"]), "Kelas ditutup")
        with k3:
            metric_card("Underload", int(s["pensyarah_underload"]), "Pensyarah kurang jam")
        with k4:
            metric_card("Overload", int(s["pensyarah_overload"]), "Pensyarah lebih jam")
        with k5:
            metric_card("Kredit", int(s["kredit_diagih"]), "Jumlah kredit diagih")

        result_tabs = st.tabs([
            "📌 Allocation",
            "👤 Lecturer Analysis",
            "🤝 Combined Teaching",
            "📊 Charts",
            "🔍 Audit",
            "📥 Export"
        ])

        with result_tabs[0]:
            st.subheader("Agihan Kelas")
            st.dataframe(df_assign, use_container_width=True, height=500)

        with result_tabs[1]:
            st.subheader("Analisis Pensyarah")
            st.dataframe(df_summary, use_container_width=True, height=520)

        with result_tabs[2]:
            st.subheader("Combined Teaching by Subject")
            st.dataframe(df_combined, use_container_width=True, height=350)

            st.subheader("Combined Teaching by Lecturer")
            if "combined_dengan" in df_summary.columns:
                st.dataframe(
                    df_summary[["pensyarah", "jumlah_jam_mengajar", "senarai_subjek", "combined_dengan"]],
                    use_container_width=True,
                    height=420
                )

        with result_tabs[3]:
            st.subheader("Analytics")

            if px is not None and not df_summary.empty:
                fig = px.bar(
                    df_summary.sort_values("jumlah_jam_mengajar"),
                    x="jumlah_jam_mengajar",
                    y="pensyarah",
                    orientation="h",
                    title="Jumlah Jam Mengajar Mengikut Pensyarah"
                )
                fig.update_layout(height=650)
                st.plotly_chart(fig, use_container_width=True)

            if px is not None and not df_assign.empty:
                pref_count = df_assign["padanan_pilihan"].value_counts().reset_index()
                pref_count.columns = ["padanan_pilihan", "count"]

                fig2 = px.pie(
                    pref_count,
                    names="padanan_pilihan",
                    values="count",
                    title="Preference Satisfaction",
                    hole=0.45
                )
                st.plotly_chart(fig2, use_container_width=True)

        with result_tabs[4]:
            st.subheader("Audit")

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

            st.subheader("Kelas Ditutup")
            st.dataframe(df_closed, use_container_width=True, height=260)

        with result_tabs[5]:
            output = to_excel_bytes({
                "Status": df_status,
                "Agihan": df_assign,
                "Analisis_Pensyarah": df_summary,
                "Combined_Teaching": df_combined,
                "Kelas_Tidak_Diagih": df_unassigned,
                "Kelas_Tutup": df_closed,
                "Main_File_Updated": df_all
            })

            st.download_button(
                "📥 Download Result Excel",
                data=output,
                file_name="ILASO_result_with_class_manager.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            updated_main = to_excel_bytes({
                "Jadual_Kelas": df_all
            })

            st.download_button(
                "📥 Download Updated Main File",
                data=updated_main,
                file_name="Jadual_Kelas_Updated_ILASO.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

else:
    st.info("Upload dua fail: main file Jadual Kelas dan file Pensyarah.")

st.divider()
st.caption("ILASO handles lecturer-class allocation, class closure, added subject/classes, workload analytics and combined teaching analysis.")
