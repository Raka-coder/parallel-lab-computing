# Parallel and Distributed Computing (Komputasi Paralel dan Terdistribusi)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MPI](https://img.shields.io/badge/MPI-mpi4py-1F4257?style=for-the-badge&logo=openmpi&logoColor=white)](https://mpi4py.readthedocs.io/)
[![NumPy](https://img.shields.io/badge/NumPy-Scientific-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualisasi-11557C?style=for-the-badge&logo=plotly&logoColor=white)](https://matplotlib.org/)
[![Tasks](https://img.shields.io/badge/Tasks-3_of_3_Completed-blueviolet?style=for-the-badge&logo=checkmarx&logoColor=white)](#daftar-tugas)

Repositori ini berisi kumpulan tugas, praktikum, dan implementasi materi mata kuliah **Komputasi Paralel dan Terdistribusi** menggunakan bahasa pemrograman Python.

---

## Identitas Mahasiswa

- **Nama**: Raka Restu Saputra
- **NPM**: 172
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
├── task-3-massage-passing-interface/   # Tugas 3: Message Passing Interface (MPI)
│   ├── practice-1/                     # Praktikum 1: Scatter Sederhana
│   ├── practice-2/                     # Praktikum 2: Gather Sederhana
│   ├── practice-3/                     # Praktikum 3: Scatter + Gather (Kombinasi)
│   ├── practice-4/                     # Praktikum 4: Hitung Jumlah (Scatter + Gather)
│   └── practice-5/                     # Praktikum 5: Reduce vs Allreduce
└── task-4-hybrid-computing/            # Tugas 4: Hybrid Computing (A = 2)
    ├── README.md                       # Dokumentasi lengkap Tugas 4
    ├── requirements.txt                # Dependensi Tugas 4 (matplotlib, mpi4py)
    ├── b1_hybrid_pipeline/             # B1: Threads + ProcessPool + Backpressure (120 file Zipf)
    ├── b2_mpi_processpool/             # B2: MPI antar-rank + ProcessPool intra-rank (π Monte Carlo)
    ├── b3_wordcount_mpi/               # B3: MPI Word Count ThreadPool vs ProcessPool (40 e-book Gutenberg)
    ├── tools/                          # Generator gambar pendukung (Amdahl, diagram C)
    └── docs/figs/                      # Gambar pendukung (amdahl_A2.png, diagram_c_fraud_hybrid.png)
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

# 3. Untuk Tugas 3 (MPI), pastikan juga install MPI runtime
Windows: install MS-MPI dari https://docs.microsoft.com/en-us/message-passing-interface/microsoft-mpi
Linux: sudo apt install openmpi-bin libopenmpi-dev
macOS: brew install open-mpi
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

### 2. [Tugas 3 — Message Passing Interface (MPI)](task-3-massage-passing-interface/)
Implementasi komunikasi antar proses menggunakan library `mpi4py`:
- **[Praktikum 1 — Scatter Sederhana](task-3-massage-passing-interface/practice-1/)**: Distribusi data dari rank 0 ke seluruh proses menggunakan `comm.scatter()`.
- **[Praktikum 2 — Gather Sederhana](task-3-massage-passing-interface/practice-2/)**: Pengumpulan data dari semua proses ke root menggunakan `comm.gather()`.
- **[Praktikum 3 — Scatter + Gather (Kombinasi)](task-3-massage-passing-interface/practice-3/)**: Penggabungan distribusi data, komputasi lokal (kuadrat), dan pengumpulan hasil.
- **[Praktikum 4 — Hitung Jumlah](task-3-massage-passing-interface/practice-4/)**: Scatter + Gather dengan komputasi `2*x` dan agregasi total.
- **[Praktikum 5 — Reduce vs Allreduce](task-3-massage-passing-interface/practice-5/)**: Perbandingan `reduce` (hasil ke rank 0) vs `allreduce` (hasil ke semua rank) untuk MAX, SUM, dan rata-rata global.

### Cara Menjalankan Tugas 3:

```bash
# Pastikan mpi4py & MPI runtime sudah terinstall
# pip install mpi4py

# Praktikum 1 - Scatter
mpiexec -n 4 py task-3-massage-passing-interface/practice-1/scatter-simple.py

# Praktikum 2 - Gather
mpiexec -n 4 py task-3-massage-passing-interface/practice-2/gather-simple.py

# Praktikum 3 - Scatter + Gather
mpiexec -n 4 py task-3-massage-passing-interface/practice-3/scatter-gather.py

# Praktikum 4 - Hitung Jumlah
mpiexec -n 4 py task-3-massage-passing-interface/practice-4/calculate-scatter-gather.py

# Praktikum 5 - Reduce vs Allreduce
mpiexec -n 4 py task-3-massage-passing-interface/practice-5/reduce-allreduce.py
```

> ⚠️ Praktikum 1, 3, 4 wajib dengan `-n 4`. Praktikum 2 & 5 fleksibel jumlah proses.

---

### 3. [Tugas 4 — Hybrid Computing](task-4-hybrid-computing/README.md)
Implementasi hybrid dua level (I/O + CPU, antar-proses + dalam-proses), masing-masing dengan README + hasil:
- **[B1 — Hybrid Pipeline (Threads + ProcessPool + Backpressure)](task-4-hybrid-computing/b1_hybrid_pipeline/README.md)**: Pipeline `N_LOADER_THREADS → Queue(maxsize=Q_MAX) → ProcessPool`, 120 file teks sintetis Zipf (`100 + 10*A`, A = 2). Grid `{1,2,4} loader × {1,2,4,cores} worker × {4,32} Q_MAX`, metrik `throughput_fps`, `avg_latency_s`, `loader_blocked_s`.
- **[B2 — Strong Scaling MPI + ProcessPool (π Monte Carlo)](task-4-hybrid-computing/b2_mpi_processpool/README.md)**: MPI antar-rank + `ProcessPoolExecutor(spawn)` intra-rank, kerja total tetap (`TOTAL_TASKS = 64`, `SAMPLES_PER_TASK = 220.000`). Metrik `Speedup S = T1/Tn`, `Efisiensi E = S/n`.
- **[B3 — Global Word Count (MPI + Threads/Proses)](task-4-hybrid-computing/b3_wordcount_mpi/README.md)**: Word count global di atas ≥ 30 teks nyata (40 e-book Project Gutenberg), bandingkan `ThreadPoolExecutor` vs `ProcessPoolExecutor` intra-rank + stopwords ID+EN dibuang + Top-10.

> 📦 Dataset berat (`b1_hybrid_pipeline/data/`, `b3_wordcount_mpi/corpus/`) tidak di-push ke repo (±52 MB) — tetap ada lokal via `.gitignore`. Regenerasi dengan `make_dataset.py` (B1) / `download_corpus.py` (B3). Detail di [README Tugas 4](task-4-hybrid-computing/README.md).

### Cara Menjalankan Tugas 4:

**Linux / macOS (`python3`):**
```bash
# B1 — dataset, satu run, lalu full grid
python3 task-4-hybrid-computing/b1_hybrid_pipeline/make_dataset.py --n 120
python3 task-4-hybrid-computing/b1_hybrid_pipeline/hybrid_pipeline.py --threads 2 --workers 4 --qmax 4
python3 task-4-hybrid-computing/b1_hybrid_pipeline/run_b1_grid.py --repeat 3

# B2 — butuh MPI + mpi4py
python3 task-4-hybrid-computing/b2_mpi_processpool/run_b2_grid.py

# B3 — unduh korpus sekali saja, lalu run MPI
python3 task-4-hybrid-computing/b3_wordcount_mpi/download_corpus.py
mpiexec -n 4 python3 task-4-hybrid-computing/b3_wordcount_mpi/wordcount_mpi.py --workers 4 --repeat 3
```

**Windows (`py`):**
```powershell
# B1
py task-4-hybrid-computing\b1_hybrid_pipeline\make_dataset.py --n 120
py task-4-hybrid-computing\b1_hybrid_pipeline\hybrid_pipeline.py --threads 2 --workers 4 --qmax 4
py task-4-hybrid-computing\b1_hybrid_pipeline\run_b1_grid.py --repeat 3

# B2
py task-4-hybrid-computing\b2_mpi_processpool\run_b2_grid.py

# B3
py task-4-hybrid-computing\b3_wordcount_mpi\download_corpus.py
mpiexec -n 4 py task-4-hybrid-computing\b3_wordcount_mpi\wordcount_mpi.py --workers 4 --repeat 3
```
