# Praktikum 4 — Hybrid Pipeline (Threads + Processes)

Dokumentasi praktikum modul 4 mengenai arsitektur **Hybrid Pipeline** yang memadukan **I/O Loader Threads** dan **Multi-Process CPU Workers** melalui **Bounded Queue Buffer** untuk memproses dataset nyata SMS Spam (`dataset/train.csv`).

---

## Identitas Mahasiswa

- **Nama**: Raka Restu Saputra
- **NPM**: 247006111172
- **Kelas**: F
- **Mata Kuliah**: Komputasi Paralel dan Terdistribusi
- **Tugas**: 2 - Thread & Task Parallelism (Tugas 4: Hybrid Pipeline)

---

## Konteks & Spesifikasi Arsitektur

Pipeline hybrid ini dirancang dalam 4 tahapan utama:

1. **Stage 0: Data Preparation (`split_csv_into_files`)**
   - Membaca dataset CSV SMS Spam (`dataset/train.csv` berisi 5.574 baris teks).
   - Membagi data secara *round-robin* ke $N$ file partisi kecil (default: 50 file part di `dataset_parts/`).
   - Setiap file part tetap menyertakan header CSV (`sms,label`).
2. **Stage 1: Loader Threads — I/O-Bound (`load_file`)**
   - Sekumpulan `threading.Thread` membaca file-file part dari disk secara konkuren.
   - Hasil pembacaan dimasukkan ke dalam antrean thread-safe berbatas `queue.Queue(maxsize)`.
   - Mengimplementasikan **Backpressure** agar thread loader otomatis terblokir ketika antrean penuh.
3. **Stage 2: Process Pool — CPU-Bound (`process_chunk`)**
   - Mengambil data dari queue buffer dan mendistribusikannya ke `concurrent.futures.ProcessPoolExecutor`.
   - Setiap worker proses CPU melakukan komputasi intensif:
     - Hitung jumlah baris teks (exclude header).
     - Hitung total kata (regex tokenization) & total karakter.
     - Hitung klasifikasi spam (`label==1`) dan ham (`label==0`).
     - Hitung kemunculan 13 kata kunci spam (*free, win, prize, cash, call, txt, claim, urgent, http, www, mobile, phone, offer*).
     - Checksum integer berbasis nilai `ord()`.
     - Beban komputasi buatan (*artificial CPU load*) berupa loop `math.sqrt` sebanyak 10.000 iterasi per baris teks.
4. **Stage 3: Aggregation & Baseline Comparison**
   - Mengumpulkan seluruh `Future` dari ProcessPool dan menjumlahkan metrik global.
   - Membandingkan performa terhadap baseline sekuensial (`run_serial`).

---

## Struktur Direktori

```text
practice-4/
├── README.md                 # Panduan lengkap, instruksi command, dan dokumentasi modul
├── hybrid-pipeline.py        # Skrip utama hybrid pipeline & generator grafik Matplotlib
├── results.png               # Visualisasi grafik performa (Waktu, Throughput, Speedup)
├── dataset/
│   └── train.csv             # Dataset SMS Spam (~5.574 baris data teks)
└── dataset_parts/            # File partisi (part_000.csv s/d part_049.csv)
```

---

## Kebutuhan Sistem & Dependensi

- **Python**: Python 3.10+ (disarankan Python 3.12)
- **Standard Libraries**: `os`, `csv`, `time`, `queue`, `math`, `re`, `threading`, `argparse`, `concurrent.futures`
- **Visualisasi**: `matplotlib`

Instalasi matplotlib jika belum terpasang:
```bash
pip install matplotlib
```

---

## Panduan Menjalankan Perintah (Commands)

### 1. Menjalankan Konfigurasi Mandiri (Single Run)

Jalankan konfigurasi tertentu sesuai kebutuhan praktikum:

```bash
# Konfigurasi 1 (1 Loader Thread, 1 CPU Worker)
python hybrid-pipeline.py --parts 50 --loader-threads 1 --cpu-workers 1

# Konfigurasi 2 (2 Loader Threads, 2 CPU Workers)
python hybrid-pipeline.py --parts 50 --loader-threads 2 --cpu-workers 2

# Konfigurasi 3 (4 Loader Threads, 4 CPU Workers)
python hybrid-pipeline.py --parts 50 --loader-threads 4 --cpu-workers 4

# Konfigurasi 4 (8 Loader Threads, 4 CPU Workers)
python hybrid-pipeline.py --parts 50 --loader-threads 8 --cpu-workers 4
```

> **Catatan Windows**: Jika sistem Anda menggunakan Python Launcher, ganti `python` dengan `py` (misal: `py hybrid-pipeline.py --parts 50 --loader-threads 1 --cpu-workers 1`).

---

### 2. Menjalankan Semua Konfigurasi & Membuat Grafik Sekaligus

Untuk menjalankan seluruh 4 konfigurasi beserta baseline serial dan menghasilkan grafik komparasi [results.png](results.png):

```bash
python hybrid-pipeline.py --parts 50 --run-all-benchmarks
```

---

## Parameter CLI Lengkap

| Flag | Default | Keterangan |
| :--- | :---: | :--- |
| `--input` | `dataset/train.csv` | Lokasi file input dataset CSV |
| `--parts` | `50` | Jumlah partisi file kecil yang dihasilkan |
| `--loader-threads` | `4` | Jumlah thread pembaca file I/O |
| `--cpu-workers` | `4` | Jumlah proses komputasi worker CPU |
| `--queue-size` | `10` | Kapasitas buffer queue (backpressure) |
| `--output-dir` | `dataset_parts` | Folder tempat part files disimpan |
| `--run-all-benchmarks` | `False` | Jalankan semua 4 konfigurasi + baseline secara serentak dan buat grafik `results.png` |

---

## Metrik Evaluasi & Rumus

- **Speedup**:
  $$\text{Speedup} = \frac{T_{\text{serial}}}{T_{\text{hybrid}}}$$
- **Throughput**:
  $$\text{Throughput} = \frac{\text{Jumlah File}}{T_{\text{hybrid}}} \quad (\text{file/s})$$
- **Average Latency**:
  $$\text{Average Latency} = \frac{T_{\text{hybrid}}}{\text{Jumlah File}} \quad (\text{s/file})$$

---

## Visualisasi Grafik & Analisis Diskusi

Grafik hasil perbandingan performa disimpan ke [results.png](results.png):

![Grafik Benchmark Praktikum 4](results.png)

Analisis lengkap mengenai letak bottleneck, peran backpressure, serta penyesuaian rasio thread vs proses dapat dibaca pada berkas [jawaban_diskusi.md](jawaban_diskusi.md).
