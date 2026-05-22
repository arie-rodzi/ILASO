# ============================================================
# ILASO Premium 6-File System — Main App
# pip install streamlit pandas numpy openpyxl pulp plotly
# streamlit run app.py
# ============================================================
import pandas as pd
import streamlit as st

try:
    import plotly.express as px
except Exception:
    px = None

from config_styles import SEMESTER_WEEKS
from ui_components import apply_page_config, hero, section, metric_card, soft_card_html
from data_utils import prepare_class_data, prepare_lecturer_data, build_preference_score, to_excel_bytes, clean_text, standardize_status
from optimizer import solve_allocation, build_outputs
from emergency_engine import ensure_emergency_log, compute_emergency_reallocation


apply_page_config()
hero()
ensure_emergency_log(st.session_state)

# Sidebar premium navigation note
with st.sidebar:
    st.markdown("### ILASO Premium")
    st.markdown("Fair KS allocation + emergency log.")
    st.markdown("---")
    st.markdown("**Workflow**")
    st.markdown("1. Upload files\n2. Validate data\n3. Manage classes\n4. Run fair allocation\n5. Emergency log\n6. Dashboard & export")

# ============================================================
# 1. Upload Files
# ============================================================
section("1. Upload Files", "Upload fail Jadual Kelas dan Pensyarah. Sistem menggunakan istilah KS sepenuhnya.")
u1, u2 = st.columns(2)
with u1:
    file_classes = st.file_uploader("Upload Jadual Kelas", type=["xlsx", "csv"])
with u2:
    file_lect = st.file_uploader("Upload Pensyarah", type=["xlsx", "csv"])

if file_classes is None or file_lect is None:
    soft_card_html(
        """
        <b>Format wajib Jadual Kelas</b><br>
        kod_kursus, kelas_baru, ks<br><br>
        <b>Format wajib Pensyarah</b><br>
        Nama Pensyarah, Peranan, Minimum KS, Maksimum KS, Pilihan 1 hingga Pilihan 5<br><br>
        <span class="badge">Emergency Log akan aktif selepas Fair Allocation dijalankan.</span>
        """
    )
    st.stop()

# ============================================================
# Load Data
# ============================================================
if "loaded_class_file" not in st.session_state:
    st.session_state.loaded_class_file = ""

if "class_df" not in st.session_state or st.session_state.loaded_class_file != file_classes.name:
    st.session_state.class_df = prepare_class_data(file_classes)
    st.session_state.loaded_class_file = file_classes.name
    # New upload resets derived result, but not mandatory old emergency log
    for key in ["df_assign", "df_summary", "df_temp_cover", "df_unassigned", "df_status", "target_ks"]:
        st.session_state.pop(key, None)
    st.session_state["emergency_log"] = pd.DataFrame()

dfl = prepare_lecturer_data(file_lect)

# ============================================================
# 2. Data Validation
# ============================================================
section("2. Data Validation", "Semak kapasiti KS, kelas aktif, kelas tutup dan pensyarah aktif sebelum run optimizer.")
df_all = st.session_state.class_df.copy()
df_all["status_kelas"] = df_all["status_kelas"].map(standardize_status)
df_active = df_all[df_all["status_kelas"].isin(["BUKA", "BARU"])].copy()
df_closed = df_all[df_all["status_kelas"] == "TUTUP"].copy()

v1, v2, v3, v4, v5 = st.columns(5)
with v1:
    metric_card("Kelas Aktif", len(df_active), "BUKA + BARU")
with v2:
    metric_card("Kelas Tutup", len(df_closed), "Tidak diagih")
with v3:
    metric_card("Jumlah KS", int(df_active["ks"].sum()), "KS aktif")
with v4:
    metric_card("Pensyarah Aktif", int(dfl["active"].sum()), "Boleh mengajar")
with v5:
    avg_ks = round(int(df_active["ks"].sum()) / max(int(dfl["active"].sum()), 1), 2)
    metric_card("Purata KS", avg_ks, "Rujukan fairness")

cap_max = int(dfl.loc[dfl["active"], "max_ks"].sum())
cap_min = int(dfl.loc[dfl["active"], "min_ks"].sum())
if cap_max < int(df_active["ks"].sum()):
    st.error("Kapasiti maksimum pensyarah aktif tidak cukup untuk cover semua KS aktif.")
elif cap_min > int(df_active["ks"].sum()):
    st.warning("Jumlah minimum KS pensyarah aktif lebih tinggi daripada KS kelas aktif. Kemungkinan infeasible.")
else:
    st.success("Data capacity check nampak munasabah.")

with st.expander("Lihat data upload", expanded=False):
    t1, t2, t3 = st.tabs(["Kelas Aktif", "Kelas Tutup", "Pensyarah"])
    with t1:
        st.dataframe(df_active, use_container_width=True, height=340)
    with t2:
        st.dataframe(df_closed, use_container_width=True, height=340)
    with t3:
        st.dataframe(dfl, use_container_width=True, height=340)

# ============================================================
# 3. Class Manager
# ============================================================
section("3. Class Manager", "Edit, tambah atau tutup kelas sebelum run Fair KS Allocation.")
manager_tabs = st.tabs(["📋 Edit Jadual Kelas", "➕ Tambah Kelas", "🗑️ Tutup Kelas"])

with manager_tabs[0]:
    edited = st.data_editor(
        st.session_state.class_df,
        use_container_width=True,
        height=420,
        num_rows="dynamic",
        column_config={
            "status_kelas": st.column_config.SelectboxColumn("status_kelas", options=["BUKA", "BARU", "TUTUP"], required=True),
            "share_allowed": st.column_config.SelectboxColumn("share_allowed", options=["TIDAK", "YA"], required=True),
        },
    )
    if st.button("💾 Simpan Perubahan Jadual Kelas", use_container_width=True):
        edited = edited.copy()
        edited["kod_kursus"] = edited["kod_kursus"].map(clean_text)
        edited["kelas_baru"] = edited["kelas_baru"].astype(str).str.strip()
        edited["status_kelas"] = edited["status_kelas"].map(standardize_status)
        edited["ks"] = pd.to_numeric(edited["ks"], errors="coerce").fillna(0).astype(int)
        edited["kelas_id"] = edited["kod_kursus"] + "-" + edited["kelas_baru"].astype(str)
        edited = edited.drop_duplicates(subset=["kelas_id"], keep="last").copy()
        st.session_state.class_df = edited
        for key in ["df_assign", "df_summary", "df_temp_cover", "df_unassigned", "df_status", "target_ks"]:
            st.session_state.pop(key, None)
        st.session_state["emergency_log"] = pd.DataFrame()
        st.success("Perubahan disimpan. Sila run semula Fair KS Allocation.")
        st.rerun()

with manager_tabs[1]:
    c1, c2, c3 = st.columns(3)
    with c1:
        new_subject = st.text_input("Kod kursus", placeholder="Contoh: MAT112")
        new_class = st.text_input("Group / kelas", placeholder="Contoh: A1")
    with c2:
        new_ks = st.number_input("KS", 1, 10, 3, 1)
        new_size = st.number_input("Saiz kelas", 0, 500, 0, 1)
    with c3:
        new_start = st.number_input("Minggu mula kelas", 1, SEMESTER_WEEKS, 1, 1)
        new_end = st.number_input("Minggu akhir kelas", 1, SEMESTER_WEEKS, SEMESTER_WEEKS, 1)
    new_note = st.text_input("Catatan", placeholder="Contoh: kelas tambahan / kelas baharu")
    if st.button("➕ Tambah Kelas Baru", use_container_width=True):
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
                "minggu_akhir_kelas": int(new_end),
            }
            updated = pd.concat([st.session_state.class_df, pd.DataFrame([new_row])], ignore_index=True)
            updated["kelas_id"] = updated["kod_kursus"].map(clean_text) + "-" + updated["kelas_baru"].astype(str).str.strip()
            updated = updated.drop_duplicates(subset=["kelas_id"], keep="last").copy()
            st.session_state.class_df = updated
            for key in ["df_assign", "df_summary", "df_temp_cover", "df_unassigned", "df_status", "target_ks"]:
                st.session_state.pop(key, None)
            st.session_state["emergency_log"] = pd.DataFrame()
            st.success(f"Kelas {new_row['kelas_id']} berjaya ditambah. Sila run semula allocation.")
            st.rerun()

with manager_tabs[2]:
    close_mode = st.radio("Pilihan tutup", ["Tutup satu kelas", "Tutup semua kelas bagi satu subjek"], horizontal=True)
    if close_mode == "Tutup satu kelas":
        class_ids = sorted(st.session_state.class_df["kelas_id"].dropna().unique().tolist())
        selected_class = st.selectbox("Pilih kelas", class_ids)
        if st.button("🗑️ Tutup Kelas Ini", use_container_width=True):
            st.session_state.class_df.loc[st.session_state.class_df["kelas_id"] == selected_class, "status_kelas"] = "TUTUP"
            for key in ["df_assign", "df_summary", "df_temp_cover", "df_unassigned", "df_status", "target_ks"]:
                st.session_state.pop(key, None)
            st.session_state["emergency_log"] = pd.DataFrame()
            st.success(f"{selected_class} telah ditutup. Sila run semula allocation.")
            st.rerun()
    else:
        subjects = sorted(st.session_state.class_df["kod_kursus"].dropna().unique().tolist())
        selected_subject = st.selectbox("Pilih subjek", subjects)
        if st.button("🗑️ Tutup Semua Kelas Subjek Ini", use_container_width=True):
            st.session_state.class_df.loc[st.session_state.class_df["kod_kursus"] == selected_subject, "status_kelas"] = "TUTUP"
            for key in ["df_assign", "df_summary", "df_temp_cover", "df_unassigned", "df_status", "target_ks"]:
                st.session_state.pop(key, None)
            st.session_state["emergency_log"] = pd.DataFrame()
            st.success(f"Semua kelas {selected_subject} ditutup. Sila run semula allocation.")
            st.rerun()

# Refresh active data after class manager
st.session_state.class_df["status_kelas"] = st.session_state.class_df["status_kelas"].map(standardize_status)
df_all = st.session_state.class_df.copy()
df_active = df_all[df_all["status_kelas"].isin(["BUKA", "BARU"])].copy()
df_closed = df_all[df_all["status_kelas"] == "TUTUP"].copy()

# ============================================================
# 4. Fair Allocation
# ============================================================
section("4. Run ILASO Fair KS Allocation", "Run optimizer utama sekali. Result disimpan dan tidak berubah apabila Emergency Reallocation dijalankan.")
if st.button("🚀 Run Fair KS Allocation", use_container_width=True):
    pref = build_preference_score(dfl)
    solver_status, assigned_df, target_ks = solve_allocation(df_active, dfl, pref)

    if solver_status == "Optimal":
        st.success("Optimization Status: Optimal")
    else:
        st.warning(f"Optimization Status: {solver_status}")

    df_assign, df_summary, df_temp_cover, df_unassigned, df_status = build_outputs(
        df_active, df_closed, dfl, pref, assigned_df, target_ks
    )

    st.session_state["df_assign"] = df_assign
    st.session_state["df_summary"] = df_summary
    st.session_state["df_temp_cover"] = df_temp_cover
    st.session_state["df_unassigned"] = df_unassigned
    st.session_state["df_status"] = df_status
    st.session_state["target_ks"] = target_ks
    st.session_state["emergency_log"] = pd.DataFrame()
    st.success(f"Fair allocation disimpan. Target purata sistem: {target_ks} KS.")

if "df_assign" not in st.session_state:
    st.info("Run Fair KS Allocation dahulu untuk aktifkan Emergency Reallocation dan Dashboard.")
    st.stop()

# Pull saved result
df_assign = st.session_state["df_assign"]
df_summary = st.session_state["df_summary"]
df_temp_cover = st.session_state["df_temp_cover"]
df_unassigned = st.session_state["df_unassigned"]
df_status = st.session_state["df_status"]
target_ks = st.session_state.get("target_ks")

# ============================================================
# 5. Emergency Reallocation
# ============================================================
section("5. Emergency Reallocation", "Masukkan nama pensyarah dan minggu tidak available. Emergency boleh berlaku banyak kali dan akan disimpan dalam Emergency Log.")

em1, em2, em3 = st.columns([2, 1, 1])
with em1:
    emergency_lecturer = st.selectbox("Pilih Pensyarah Emergency", sorted(df_summary["pensyarah"].tolist()))
with em2:
    emergency_start_week = st.number_input("Minggu mula", 1, SEMESTER_WEEKS, 5, 1)
with em3:
    emergency_end_week = st.number_input("Minggu akhir", 1, SEMESTER_WEEKS, 10, 1)

b1, b2 = st.columns([2, 1])
with b1:
    run_emergency = st.button("🚨 Run Emergency Reallocation", use_container_width=True)
with b2:
    clear_emergency = st.button("🧹 Clear Emergency Log", use_container_width=True)

if clear_emergency:
    st.session_state["emergency_log"] = pd.DataFrame()
    st.success("Emergency Log dikosongkan.")
    st.rerun()

if run_emergency:
    if emergency_end_week < emergency_start_week:
        st.error("Minggu akhir tidak boleh kurang daripada minggu mula.")
    else:
        new_emergency = compute_emergency_reallocation(
            df_assign=df_assign,
            df_summary=df_summary,
            emergency_log=st.session_state.get("emergency_log", pd.DataFrame()),
            emergency_lecturer=emergency_lecturer,
            start_week=emergency_start_week,
            end_week=emergency_end_week,
        )
        if new_emergency.empty:
            st.info("Tiada kelas yang bertindih dengan minggu emergency atau pensyarah tiada kelas.")
        else:
            st.session_state["emergency_log"] = pd.concat(
                [st.session_state.get("emergency_log", pd.DataFrame()), new_emergency],
                ignore_index=True,
            )
            st.success("Emergency case ditambah ke Emergency Log.")
            st.dataframe(new_emergency, use_container_width=True, height=260)

emergency_log = st.session_state.get("emergency_log", pd.DataFrame())
if emergency_log is not None and not emergency_log.empty:
    st.markdown("### Emergency Log")
    st.dataframe(emergency_log, use_container_width=True, height=360)
else:
    st.info("Belum ada emergency case direkodkan.")

# ============================================================
# 6. Executive Dashboard + Export
# ============================================================
section("6. Executive Dashboard", "Dashboard premium untuk allocation utama, workload, audit dan export.")
s = df_status.iloc[0]

d1, d2, d3, d4, d5, d6 = st.columns(6)
with d1:
    metric_card("Coverage", f"{s['kelas_diagih']}/{s['jumlah_kelas_aktif']}", "Kelas diagih")
with d2:
    metric_card("Fair Load", int(s["pensyarah_adil"]), "Dalam min/max")
with d3:
    metric_card("Underload", int(s["pensyarah_underload"]), "Bawah minimum")
with d4:
    metric_card("Overload", int(s["pensyarah_overload"]), "Lebih maksimum")
with d5:
    metric_card("Target KS", target_ks, "Purata sistem")
with d6:
    metric_card("Emergency", len(emergency_log) if emergency_log is not None else 0, "Log kes")

tabs = st.tabs(["📌 Allocation", "👤 Lecturer Analysis", "⏱️ Temporary Cover", "📊 Charts", "🔍 Audit", "📥 Export"])

with tabs[0]:
    st.markdown("### Agihan Kelas Utama")
    st.dataframe(df_assign, use_container_width=True, height=520)

with tabs[1]:
    st.markdown("### Analisis Pensyarah")
    st.dataframe(df_summary, use_container_width=True, height=540)

with tabs[2]:
    st.markdown("### Kes Cover Sementara")
    if df_temp_cover.empty:
        st.success("Tiada kes cover sementara.")
    else:
        st.warning("Ada pensyarah masuk lewat. Minggu awal perlu cover sementara.")
        st.dataframe(df_temp_cover, use_container_width=True, height=420)

with tabs[3]:
    st.markdown("### Workload Distribution")
    if px is not None and not df_summary.empty:
        fig = px.bar(
            df_summary.sort_values("jumlah_KS"),
            x="jumlah_KS",
            y="pensyarah",
            orientation="h",
            text="jumlah_KS",
            title="Jumlah KS Mengajar Mengikut Pensyarah",
        )
        fig.update_layout(height=680, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.dataframe(df_summary[["pensyarah", "jumlah_KS"]], use_container_width=True)

with tabs[4]:
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

    st.markdown("### Kelas Ditutup")
    st.dataframe(df_closed, use_container_width=True, height=300)

with tabs[5]:
    output = to_excel_bytes({
        "Status": df_status,
        "Agihan_Utama": df_assign,
        "Analisis_Pensyarah": df_summary,
        "Cover_Sementara": df_temp_cover,
        "Emergency_Log": emergency_log,
        "Kelas_Tidak_Diagih": df_unassigned,
        "Kelas_Tutup": df_closed,
        "Updated_Main_File": df_all,
    })
    st.download_button(
        "📥 Download Full Result Excel",
        data=output,
        file_name="ILASO_premium_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.markdown(
    """
    <div class="footer">
        ILASO Premium • Fair KS Engine • Emergency Log • Minimal-Disturbance Reallocation
    </div>
    """,
    unsafe_allow_html=True,
)
