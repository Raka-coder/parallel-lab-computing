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
└── task-3-massage-passing-interface/   # Tugas 3: Message Passing Interface (MPI)
    ├── practice-1/                     # Praktikum 1: Scatter Sederhana
    ├── practice-2/                     # Praktikum 2: Gather Sederhana
    ├── practice-3/                     # Praktikum 3: Scatter + Gather (Kombinasi)
    ├── practice-4/                     # Praktikum 4: Hitung Jumlah (Scatter + Gather)
    └── practice-5/                     # Praktikum 5: Reduce vs Allreduce
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
# Windows: install MS-MPI dari https://docs.microsoft.com/en-us/message-passing-interface/microsoft-mpi
# Linux: sudo apt install openmpi-bin libopenmpi-dev
# macOS: brew install open-mpi
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
