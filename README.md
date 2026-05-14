# ILASO
## Intelligent Lecturer Allocation with Stability-Aware Optimization

ILASO is a standalone academic workload allocation system designed for lecturer-subject distribution with fairness, stability, and intelligent optimization.

---

# Main Features

- Fair lecturer workload distribution
- Preference-based subject allocation
- Stability-aware reallocation
- Lock previous allocation
- Mid-semester rebalancing
- Lecturer availability handling
- Maternity leave / late-entry support
- Maximum subject and class constraints
- Automatic Excel export
- Executive analytics dashboard

---

# Core Optimization Concepts

ILASO uses:

- Mixed Integer Linear Programming (MILP)
- Multi-objective optimization
- Fairness optimization
- Stability-aware optimization
- Minimum perturbation re-optimization

---

# Installation

## 1. Install Python packages

```bash
pip install -r requirements.txt
```

---

# Run ILASO

```bash
streamlit run ilaso_app.py
```

---

# Required Input Files

## A. Jadual_Kelas

Minimum required columns:

| Column |
|---|
| kod_kursus |
| kelas_baru |
| jam_kredit |

Optional columns:

| Column |
|---|
| saiz_kelas |
| campuran_group |
| perincian |
| status_kelas |
| pensyarah_asal |
| lock_agihan |
| minggu_mula_kelas |
| minggu_akhir_kelas |

---

## B. Pensyarah

Minimum required columns:

| Column |
|---|
| Nama Pensyarah |
| Peranan |
| Minimum Jam Kredit |
| Maksimum Jam Kredit |
| Pilihan 1 |
| Pilihan 2 |
| Pilihan 3 |
| Pilihan 4 |
| Pilihan 5 |

Optional columns:

| Column |
|---|
| minggu_mula_available |
| minggu_akhir_available |
| status |
| allow_partial_loading |
| catatan |

---

# Allocation Philosophy

ILASO prioritizes:

1. Fairness
2. Full class coverage
3. Stability of allocation
4. Lecturer preferences
5. Minimum disruption

---

# Stability-Aware Rebalancing

When classes are:
- closed
- newly opened
- reassigned
- affected by lecturer leave

ILASO attempts to:
- preserve existing allocation
- minimize lecturer disruption
- rebalance only necessary classes

---

# Suggested Workflow

## Initial Allocation

1. Upload lecturer file
2. Upload class file
3. Run allocation
4. Download result
5. Lock stable allocation

---

## Mid-Semester Changes

1. Update class status
2. Add/remove classes
3. Update lecturer availability
4. Run Stability-Aware Rebalance
5. Download updated allocation

---

# Output Files

ILASO exports:

- Allocation result
- Lecturer summary
- Subject coverage
- Closed classes
- Audit checks
- Locked next-input template

---

# Recommended Environment

- Python 3.10+
- Streamlit
- Windows / Linux

---

# System Branding

## ILASO
### Intelligent Lecturer Allocation with Stability-Aware Optimization

Tagline:

> Fair. Stable. Intelligent Academic Allocation.
