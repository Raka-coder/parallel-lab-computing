# Parallel and Distributed Computing (Komputasi Paralel dan Terdistribusi)

Repositori ini berisi kumpulan tugas, praktikum, dan implementasi materi mata kuliah **Komputasi Paralel dan Terdistribusi** menggunakan bahasa pemrograman Python.

---

## Identitas Mahasiswa

- **Nama**: Raka Restu Saputra
- **NPM**: 247006111172
- **Kelas**: F
- **Mata Kuliah**: Komputasi Paralel dan Terdistribusi

---

## Daftar Isi & Struktur Tugas

```text
parallel-computing/
├── .gitignore                          # Konfigurasi Git ignore root
├── README.md                           # Dokumentasi utama repositori
├── requirements.txt                    # Dependensi pustaka Python global
├── task-2-thread-task-parallel/        # Tugas 2: Thread and Task Parallelism
│   ├── README.md                       # Dokumentasi lengkap Tugas 2
│   ├── practice-1/                     # Praktikum 1: Thread Parallelism (I/O-Bound)
│   ├── practice-2/                     # Praktikum 2: Task Parallelism (CPU-Bound)
│   ├── practice-3/                     # Praktikum 3: Perbandingan Threads vs Tasks
│   └── practice-4/                     # Praktikum 4: Hybrid Pipeline Architecture
└── task-3/                             # Tugas 3 (Upcoming / Mendatang)
```

---

## Panduan Instalasi Global

Siapkan lingkungan Python dari root repositori:

```bash
# 1. Membuat dan mengaktifkan virtual environment
python3 -m venv venv
source venv/bin/activate  # Untuk Windows: venv\Scripts\activate

# 2. Menginstall dependensi yang dibutuhkan
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Daftar Tugas

### 1. [Tugas 2 — Thread and Task Parallelism](task-2-thread-task-parallel/README.md)
Pembahasan komprehensif mengenai konkurensi dan komputasi paralel:
- **[Praktikum 1 — Thread Parallelism (I/O-Bound)](task-2-thread-task-parallel/practice-1/README.md)**: Simulasi unduhan file asinkron multithreading dan evaluasi speedup.
- **[Praktikum 2 — Task Parallelism (CPU-Bound)](task-2-thread-task-parallel/practice-2/README.md)**: Komputasi berat dengan `ProcessPoolExecutor`, analisis skalabilitas 2, 4, 8 worker, dan efisiensi paralel.
- **[Praktikum 3 — Perbandingan Threads vs Tasks](task-2-thread-task-parallel/practice-3/README.md)**: Uji silang langsung beban I/O vs CPU pada Serial, Threads, dan Processes serta dampak GIL.
- **[Praktikum 4 — Hybrid Pipeline Architecture](task-2-thread-task-parallel/practice-4/README.md)**: Arsitektur 3-tahap (I/O Loader Threads $\rightarrow$ Queue Buffer $\rightarrow$ Multi-Process CPU Workers) memproses langsung dataset nyata SMS Spam (`dataset/train.csv`).

### Cara Menjalankan Tugas 2:

**Linux / macOS (`python3`):**
```bash
python3 task-2-thread-task-parallel/practice-1/thread-parallelism.py
python3 task-2-thread-task-parallel/practice-2/task-parallelism.py
python3 task-2-thread-task-parallel/practice-3/compare-threads-tasks.py
python3 task-2-thread-task-parallel/practice-4/hybrid-pipeline.py
```

**Windows (`py`):**
```powershell
py task-2-thread-task-parallel/practice-1/thread-parallelism.py
py task-2-thread-task-parallel/practice-2/task-parallelism.py
py task-2-thread-task-parallel/practice-3/compare-threads-tasks.py
py task-2-thread-task-parallel/practice-4/hybrid-pipeline.py
```

---

### 2. Tugas 3 (Upcoming)
Modul untuk praktikum selanjutnya pada folder `task-3/`.
