# Komputasi Paralel dan Terdistribusi — Thread and Task Parallelism

Dokumentasi lengkap proyek praktikum komputasi paralel menggunakan Python untuk pemrosesan berbasis **Thread Parallelism (I/O-Bound)**, **Task Parallelism (CPU-Bound)**, **Perbandingan Threads vs Tasks**, dan **Hybrid Pipeline Architecture (Threads + Processes)** dengan dataset nyata.

---

## Informasi Mahasiswa & Mata Kuliah

- **Mata Kuliah**: Komputasi Paralel dan Terdistribusi
- **Topik**: Thread and Task Parallelism
- **Nama Mahasiswa**: Raka Restu Saputra
- **NPM**: 247006111172
- **Kelas**: F

---

## Daftar Isi

1. [Gambaran Umum Proyek](#gambaran-umum-proyek)
2. [Tech Stack & Kebutuhan Sistem](#tech-stack--kebutuhan-sistem)
3. [Panduan Instalasi Library (requirements.txt)](#panduan-instalasi-library-requirementstxt)
4. [Struktur Direktori Proyek](#struktur-direktori-proyek)
5. [Konsep & Arsitektur Komputasi Paralel](#konsep--arsitektur-komputasi-paralel)
6. [Daftar Modul Praktikum](#daftar-modul-praktikum)
   - [Praktikum 1 — Thread Parallelism (I/O-Bound)](#praktikum-1--thread-parallelism-io-bound)
   - [Praktikum 2 — Task Parallelism (CPU-Bound)](#praktikum-2--task-parallelism-cpu-bound)
   - [Praktikum 3 — Perbandingan Threads vs Tasks](#praktikum-3--perbandingan-threads-vs-tasks)
   - [Praktikum 4 — Hybrid Pipeline (Threads + Processes)](#praktikum-4--hybrid-pipeline-threads--processes)
7. [Ringkasan Perintah Menjalankan Skrip](#ringkasan-perintah-menjalankan-skrip)
8. [Troubleshooting & Solusi Kendala](#troubleshooting--solusi-kendala)

---

## Gambaran Umum Proyek

Repositori ini memuat implementasi 4 modul praktikum komputasi paralel dan terdistribusi:

1. **Praktikum 1 (`practice-1/`)**: Simulasi unduhan file asinkron (I/O-bound) menggunakan modul `threading` bawaan Python, mengukur percepatan (*speedup*) terhadap eksekusi serial.
2. **Praktikum 2 (`practice-2/`)**: Pemrosesan komputasi berat (CPU-bound) menggunakan modul `concurrent.futures.ProcessPoolExecutor` dengan variasi jumlah worker (2, 4, 8 proses) untuk mengukur *speedup* dan efisiensi paralel (*parallel efficiency*).
3. **Praktikum 3 (`practice-3/`)**: Analisis komparatif antara `ThreadPoolExecutor` dan `ProcessPoolExecutor` pada beban I/O-bound vs CPU-bound, mendemonstrasikan dampak *Global Interpreter Lock* (GIL) pada Python.
4. **Praktikum 4 (`practice-4/`)**: Arsitektur *Hybrid Pipeline* 3-tahap (Stage-1: I/O Loader Threads $\rightarrow$ Stage-2: Bounded Queue Buffer $\rightarrow$ Stage-3: Multi-Process CPU Workers) yang mengolah langsung dataset teks SMS Spam (`dataset/train.csv`).

---

## Tech Stack & Kebutuhan Sistem

- **Bahasa Pemrograman**: Python 3.10+ (direkomendasikan Python 3.11 atau 3.12/3.14)
- **Library Standar**:
  - `threading`, `multiprocessing`, `concurrent.futures`
  - `time`, `queue`, `random`, `csv`, `re`, `os`
- **Library Pihak Ketiga**:
  - `matplotlib` (untuk visualisasi grafik perbandingan performa)
- **Sistem Operasi**: Linux / macOS / Windows

---

## Panduan Instalasi Library (requirements.txt)

File kebutuhan pustaka telah disediakan pada [requirements.txt](file:///home/rakarestu/Documents/parallel-computing/task-2-thread-task-parallel/requirements.txt).

### 1. Buat dan Aktifkan Virtual Environment

```bash
# Membuat virtual environment
python3 -m venv venv

# Mengaktifkan di Linux / macOS:
source venv/bin/activate

# Mengaktifkan di Windows (Command Prompt / PowerShell):
# venv\Scripts\activate
```

### 2. Install Dependensi dari requirements.txt

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Struktur Direktori Proyek

```text
task-2-thread-task-parallel/
├── .gitignore                          # Konfigurasi file yang diabaikan Git
├── README.md                           # Dokumentasi utama proyek
├── requirements.txt                    # File dependensi pustaka Python
├── practice-1/
│   ├── README.md                       # Dokumentasi modul Praktikum 1
│   ├── results.png                     # Visualisasi grafik hasil Praktikum 1
│   └── thread-parallelism.py           # Skrip Praktikum 1 (I/O-Bound Threading)
├── practice-2/
│   ├── README.md                       # Dokumentasi modul Praktikum 2
│   ├── results.png                     # Visualisasi grafik hasil Praktikum 2
│   └── task-parallelism.py             # Skrip Praktikum 2 (CPU-Bound Multiprocessing)
├── practice-3/
│   ├── README.md                       # Dokumentasi modul Praktikum 3
│   ├── results.png                     # Visualisasi grafik hasil Praktikum 3
│   └── compare-threads-tasks.py        # Skrip Praktikum 3 (Perbandingan Threads vs Tasks)
└── practice-4/
    ├── README.md                       # Dokumentasi modul Praktikum 4
    ├── dataset/
    │   └── train.csv                   # Dataset SMS Spam (~5.574 baris data teks)
    ├── results.png                     # Visualisasi grafik hasil Praktikum 4
    └── hybrid-pipeline.py              # Skrip Praktikum 4 (Hybrid Pipeline Threads + Processes)
```

---

## Konsep & Arsitektur Komputasi Paralel

### 1. Thread Parallelism vs Task Parallelism

| Aspek | Thread Parallelism (I/O-Bound) | Task Parallelism (CPU-Bound) |
| :--- | :--- | :--- |
| **Modul Utama** | `threading`, `ThreadPoolExecutor` | `multiprocessing`, `ProcessPoolExecutor` |
| **Ruang Memori** | *Shared Memory* (memori bersama dalam 1 proses) | *Isolated Memory* (tiap proses memiliki ruang memori sendiri) |
| **Overhead** | Sangat ringan (pembuatan thread cepat) | Lebih berat (fork/spawn proses dan duplikasi memori) |
| **Karakteristik GIL** | Thread melepaskan GIL saat menunggu I/O (*sleep/disk/network*) | Setiap proses memiliki interpreter & GIL sendiri |
| **Kesesuaian Beban** | Download, API request, pembacaan disk | Matriks, hashing, enkripsi, NLP, komputasi numerik |

### 2. Rumus Metrik Evaluasi

- **Speedup ($S$)**:
  $$S = \frac{T_{\text{serial}}}{T_{\text{paralel}}}$$
- **Parallel Efficiency ($E$)**:
  $$E = \frac{S}{P} \times 100\%$$
  *(di mana $P$ adalah jumlah worker / core prosesor)*
- **Throughput**:
  $$\text{Throughput} = \frac{\text{Jumlah Item/Data yang Diproses}}{\text{Total Waktu Eksekusi (detik)}}$$

---

## Daftar Modul Praktikum

Detail konteks per modul praktikum tersedia pada dokumentasi di masing-masing folder:

### [Praktikum 1 — Thread Parallelism (I/O-Bound)](practice-1/README.md)
- **Fokus**: Simulasi pengunduhan 10 file dengan durasi acak (0.5s – 2.0s).
- **Mekanisme**: Thread concurrency dengan proteksi `threading.Lock()` untuk log sinkronisasi.
- **Visualisasi**: Matplotlib bar chart perbandingan waktu eksekusi Serial vs Threaded dan analisis Speedup Aktual vs Ideal.
- **Perintah Menjalankan**:
  ```bash
  python3 practice-1/thread-parallelism.py
  ```

---

### [Praktikum 2 — Task Parallelism (CPU-Bound)](practice-2/README.md)
- **Fokus**: Komputasi berat perulangan matematika ($10^6$ iterasi) pada 8 task numerik.
- **Mekanisme**: Task distribution pada multi-core CPU dengan variasi 2, 4, dan 8 worker proses (`ProcessPoolExecutor`).
- **Visualisasi**: Matplotlib 3 subplot (Waktu Eksekusi, Kurva Speedup vs Linear Ideal, dan Persentase Efisiensi Paralel).
- **Perintah Menjalankan**:
  ```bash
  python3 practice-2/task-parallelism.py
  ```

---

### [Praktikum 3 — Perbandingan Threads vs Tasks](practice-3/README.md)
- **Fokus**: Uji silang karakteristik konkurensi (Serial vs Threads 4 Workers vs Processes 4 Workers) pada beban I/O-bound dan CPU-bound.
- **Analisis GIL**: Menjelaskan mengapa threads melambat pada CPU-bound akibat perebutan lock di CPython, sedangkan multiprocessing menghasilkan speedup optimal.
- **Visualisasi**: Matplotlib 2 subplot (Perbandingan Waktu Eksekusi Berkelompok dan Perbandingan Speedup terhadap Baseline 1.0x).
- **Perintah Menjalankan**:
  ```bash
  python3 practice-3/compare-threads-tasks.py
  ```

---

### [Praktikum 4 — Hybrid Pipeline (Threads + Processes)](practice-4/README.md)
- **Fokus**: Arsitektur hybrid pipeline 3-tahap (Stage-1: I/O Loader Threads $\rightarrow$ Stage-2: Queue Buffer $\rightarrow$ Stage-3: Process Pool Workers) yang mengolah langsung dataset nyata SMS Spam (`dataset/train.csv` berisi 5.574 data pesan).
- **Metrik**: Evaluasi Throughput (data/s), Average Latency (s), dan Speedup lintas 4 konfigurasi worker.
- **Visualisasi**: Matplotlib 3 subplot (Waktu Eksekusi, Throughput data/detik, dan Speedup vs Baseline).
- **Perintah Menjalankan**:
  ```bash
  python3 practice-4/hybrid-pipeline.py
  ```

---

## Ringkasan Perintah Menjalankan Skrip

Jalankan seluruh modul praktikum dari root workspace:

**Linux / macOS (`python3`):**
```bash
# Praktikum 1: Thread Parallelism (I/O-Bound)
python3 practice-1/thread-parallelism.py

# Praktikum 2: Task Parallelism (CPU-Bound)
python3 practice-2/task-parallelism.py

# Praktikum 3: Perbandingan Threads vs Tasks
python3 practice-3/compare-threads-tasks.py

# Praktikum 4: Hybrid Pipeline dengan dataset/train.csv
python3 practice-4/hybrid-pipeline.py
```

**Windows (`py`):**
```powershell
# Praktikum 1: Thread Parallelism (I/O-Bound)
py practice-1/thread-parallelism.py

# Praktikum 2: Task Parallelism (CPU-Bound)
py practice-2/task-parallelism.py

# Praktikum 3: Perbandingan Threads vs Tasks
py practice-3/compare-threads-tasks.py

# Praktikum 4: Hybrid Pipeline dengan dataset/train.csv
py practice-4/hybrid-pipeline.py
```

---

## Troubleshooting & Solusi Kendala

### 1. `ModuleNotFoundError: No module named 'matplotlib'`
- **Solusi**: Pasang seluruh dependensi menggunakan file requirements:
  ```bash
  pip install -r requirements.txt
  ```

### 2. `_pickle.PicklingError: Can't pickle local object <lambda>`
- **Solusi**: Gunakan fungsi tingkat atas (*top-level function*) yang memiliki nama eksplisit saat mentransmisikan argumen data ke `ProcessPoolExecutor`.

### 3. Matplotlib Figure Error pada Terminal Headless / SSH Tanpa GUI
- **Solusi**: Atur backend Matplotlib non-interaktif sebelum import pyplot:
  ```python
  import matplotlib
  matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  ```

### 4. File dataset `train.csv` Tidak Ditemukan
- **Solusi**: Pastikan Anda berada di direktori `practice-4/` saat mengeksekusi skrip, atau jalankan dari root workspace menggunakan perintah `python3 practice-4/hybrid-pipeline.py`.
