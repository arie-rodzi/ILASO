# ============================================================
# ILASO 6-File System — Emergency Reallocation Engine
# ============================================================
import pandas as pd


def ensure_emergency_log(session_state):
    if "emergency_log" not in session_state:
        session_state["emergency_log"] = pd.DataFrame(columns=[
            "kes_no", "pensyarah_emergency", "kelas_id", "kod_kursus", "kelas_baru",
            "minggu_asal_sebelum", "minggu_pengganti", "minggu_asal_sambung",
            "pensyarah_pengganti", "KS_subjek", "bil_minggu_ganti", "KS_pengganti", "status"
        ])


def compute_emergency_reallocation(df_assign, df_summary, emergency_log, emergency_lecturer, start_week, end_week):
    if df_assign.empty or df_summary.empty:
        return pd.DataFrame()

    emergency_classes = df_assign[df_assign["pensyarah_utama"] == emergency_lecturer].copy()
    if emergency_classes.empty:
        return pd.DataFrame()

    # Current base KS from fair allocation
    current_load = (
        df_summary[["pensyarah", "jumlah_KS", "maksimum_KS", "aktif", "minggu_mula_available", "minggu_akhir_available", "senarai_subjek"]]
        .rename(columns={"jumlah_KS": "jumlah_KS_asal"})
        .copy()
    )

    # Add previous emergency load so repeated emergency cases are fair
    if emergency_log is not None and not emergency_log.empty:
        previous = (
            emergency_log[emergency_log["status"] == "OK"]
            .groupby("pensyarah_pengganti")["KS_pengganti"]
            .sum()
            .reset_index()
            .rename(columns={"pensyarah_pengganti": "pensyarah", "KS_pengganti": "KS_emergency_sebelum"})
        )
        current_load = current_load.merge(previous, on="pensyarah", how="left")
    else:
        current_load["KS_emergency_sebelum"] = 0.0

    current_load["KS_emergency_sebelum"] = current_load["KS_emergency_sebelum"].fillna(0.0)
    current_load["jumlah_KS_semasa"] = current_load["jumlah_KS_asal"] + current_load["KS_emergency_sebelum"]

    kes_no = 1 if emergency_log is None or emergency_log.empty else int(emergency_log["kes_no"].max()) + 1
    rows = []

    for _, row in emergency_classes.iterrows():
        kelas_start = int(row["minggu_mula_kelas"])
        kelas_end = int(row["minggu_akhir_kelas"])
        overlap_start = max(kelas_start, int(start_week))
        overlap_end = min(kelas_end, int(end_week))

        if overlap_start > overlap_end:
            continue

        bil_minggu_ganti = overlap_end - overlap_start + 1
        jumlah_minggu_kelas = kelas_end - kelas_start + 1
        ks_ganti = round(float(row["KS"]) * bil_minggu_ganti / jumlah_minggu_kelas, 2)

        calon = current_load[
            (current_load["pensyarah"] != emergency_lecturer)
            & (current_load["aktif"] == True)
            & (current_load["minggu_mula_available"] <= overlap_start)
            & (current_load["minggu_akhir_available"] >= overlap_end)
        ].copy()

        calon["ajar_subjek_sama"] = calon["senarai_subjek"].astype(str).apply(lambda x: 1 if row["kod_kursus"] in x else 0)
        calon["anggaran_KS_lepas_ganti"] = calon["jumlah_KS_semasa"] + ks_ganti
        calon = calon[calon["anggaran_KS_lepas_ganti"] <= calon["maksimum_KS"]].copy()

        if calon.empty:
            pengganti = "TIADA CALON SESUAI"
            status = "GAGAL"
        else:
            calon = calon.sort_values(["ajar_subjek_sama", "jumlah_KS_semasa"], ascending=[False, True])
            pengganti = calon.iloc[0]["pensyarah"]
            status = "OK"
            # update current_load immediately so multiple classes in same emergency are balanced
            current_load.loc[current_load["pensyarah"] == pengganti, "jumlah_KS_semasa"] += ks_ganti

        rows.append({
            "kes_no": kes_no,
            "pensyarah_emergency": emergency_lecturer,
            "kelas_id": row["kelas_id"],
            "kod_kursus": row["kod_kursus"],
            "kelas_baru": row["kelas_baru"],
            "minggu_asal_sebelum": f"{kelas_start}-{overlap_start - 1}" if kelas_start < overlap_start else "",
            "minggu_pengganti": f"{overlap_start}-{overlap_end}",
            "minggu_asal_sambung": f"{overlap_end + 1}-{kelas_end}" if overlap_end < kelas_end else "",
            "pensyarah_pengganti": pengganti,
            "KS_subjek": float(row["KS"]),
            "bil_minggu_ganti": bil_minggu_ganti,
            "KS_pengganti": ks_ganti,
            "status": status,
        })

    return pd.DataFrame(rows)
