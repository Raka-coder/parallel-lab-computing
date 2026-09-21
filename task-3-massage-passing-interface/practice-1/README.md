# Tugas 3 Praktikum 1 — Scatter Sederhana (MPI)

Dokumentasi praktikum modul **Message Passing Interface (MPI)** mengenai distribusi data dari proses root ke seluruh proses menggunakan `comm.scatter()` dengan library `mpi4py`.

---

## Identitas Mahasiswa

- **Nama**: Raka Restu Saputra
- **NPM**: 247006111172
- **Kelas**: F
- **Mata Kuliah**: Komputasi Paralel dan Terdistribusi

---

## Konteks & Tujuan Praktikum

1. **Distribusi Data**: Memahami cara kerja *collective communication* `Scatter` — proses rank 0 membagi data secara rata ke seluruh proses dalam komunikator `MPI.COMM_WORLD`.
2. **Validasi Jumlah Proses**: Memastikan program hanya berjalan dengan tepat **4 proses**, karena list sumber `[10, 20, 30, 40]` memiliki 4 elemen (1 elemen per proses).
3. **Perilaku Output Paralel**: Mengamati *non-determinisme urutan cetak* antar proses — urutan baris output dapat berbeda setiap eksekusi, tetapi **pemetaan rank → data selalu deterministik**.

---

## Spesifikasi Program

1. Proses 0 memiliki list `[10, 20, 30, 40]`.
2. Data dibagi rata ke **4 proses** dengan scatter.
3. Setiap proses mencetak data yang diterimanya.

---

## Struktur File

```text
practice-1/
├── README.md            # Dokumentasi modul Praktikum 1
└── tugas1_scatter.py    # Skrip utama MPI Scatter Sederhana
```

---

## Konsep Alur Eksekusi

```
┌──────────────────────────────────────────────────────────┐
│  TAHAP 1 — INISIALISASI MPI                              │
│  • comm = MPI.COMM_WORLD → komunikator global            │
│  • rank = ID proses (0, 1, 2, 3)                         │
│  • size = jumlah proses (harus 4)                        │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  TAHAP 2 — VALIDASI size == 4                            │
│  • Jika bukan 4 → cetak pesan error (hanya rank 0)       │
│  • raise SystemExit → semua proses berhenti              │
│                                                          │
│  Kenapa harus 4? Karena list [10,20,30,40] punya 4       │
│  elemen → 1 elemen per proses.                           │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  TAHAP 3 — PERSIAPAN DATA                                │
│  • Rank 0  : data = [10, 20, 30, 40]                     │
│  • Rank 1-3: data = None                                 │
│                                                          │
│  Kenapa rank lain None? Karena hanya rank 0 yang boleh   │
│  punya data sumber. Rank lain menerima dari scatter.     │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  TAHAP 4 — SCATTER                                       │
│  • comm.scatter(data, root=0)                            │
│  • Rank 0 membagi 4 elemen ke 4 proses                   │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  TAHAP 5 — CETAK OUTPUT                                  │
│  • Setiap proses mencetak: "Rank X menerima Y"           │
│  • Urutan output bisa berbeda-beda antar eksekusi        │
└──────────────────────────────────────────────────────────┘
```

### Ilustrasi Scatter

```
Rank 0: [10, 20, 30, 40]
              │
              │  comm.scatter(data, root=0)
              ▼
    ┌──────┬──────┬──────┬──────┐
    │Rank 0│Rank 1│Rank 2│Rank 3│
    ├──────┼──────┼──────┼──────┤
    │  10  │  20  │  30  │  40  │
    └──────┴──────┴──────┴──────┘
```

**Poin penting:**
- `comm.scatter()` mengembalikan **satu nilai** (skalar), bukan list.
- Data dibagi **rata** → jumlah elemen harus = jumlah proses.
- Urutan pembagian **selalu sesuai rank** (rank 0 dapat elemen pertama).

---

## Kebutuhan Sistem & Library

- Python 3.10+
- Library: `mpi4py` (membutuhkan runtime MPI, mis. MS-MPI / MPICH / OpenMPI)
- Install melalui `pip install -r requirements.txt` atau `pip install mpi4py`

---

## Cara Menjalankan Skrip

Pastikan berada di direktori modul atau panggil dari root workspace.

**Windows (`py` — direkomendasikan):**

```powershell
# Opsi 1: Dari dalam folder practice-1
cd task-3-massage-passing-interface/practice-1
mpiexec -n 4 py tugas1_scatter.py

# Opsi 2: Dari root workspace
mpiexec -n 4 py task-3-massage-passing-interface/practice-1/tugas1_scatter.py
```

> ⚠️ Gunakan launcher **`py`**, bukan `python`. Pada banyak instalasi Windows, perintah `python` tertutup oleh *App Execution Alias* Microsoft Store (file stub 0-byte di `%LOCALAPPDATA%\Microsoft\WindowsApps`) sehingga gagal jalan atau membuka Microsoft Store. Launcher `py` selalu resolve ke instalasi Python asli. Jika tetap ingin memakai `python`, nonaktifkan aliasnya di **Settings > Apps > Advanced app settings > App execution aliases**.

**Linux / macOS (`python3`):**

```bash
# Opsi 1: Dari dalam folder practice-1
cd task-3-massage-passing-interface/practice-1
mpirun -n 4 python3 tugas1_scatter.py

# Opsi 2: Dari root workspace
mpirun -n 4 python3 task-3-massage-passing-interface/practice-1/tugas1_scatter.py
```

> ⚠️ Jumlah proses **harus tepat 4**. Jika dijalankan dengan `-n` selain 4, program akan mencetak pesan `"Harap jalankan dengan -n 4"` dan berhenti.

---

## Troubleshooting & Solusi Kendala (Windows)

### 1. `mpiexec: command not found`
- **Penyebab**: terminal/sesi yang dibuka **sebelum** instalasi MS-MPI masih memegang PATH lama.
- **Solusi**: tutup dan buka **terminal baru**, lalu pastikan `C:\Program Files\Microsoft MPI\Bin\` terdaftar di PATH sistem. Verifikasi cepat:
  ```powershell
  mpiexec -help
  ```

### 2. `python` tidak dikenali / membuka Microsoft Store
- **Penyebab**: *App Execution Alias* Windows (stub `python.exe` 0-byte di `WindowsApps`) menutupi instalasi Python asli karena urutan PATH.
- **Solusi**: gunakan launcher `py`:
  ```powershell
  py --version
  mpiexec -n 4 py tugas1_scatter.py
  ```
  atau nonaktifkan alias di **Settings > Apps > Advanced app settings > App execution aliases**.

### 3. `mpirun: command not found` di Windows
- **Penyebab**: MS-MPI **tidak menyediakan** `mpirun` — nama itu hanya ada di OpenMPI/MPICH (Linux).
- **Solusi**: di Windows selalu gunakan `mpiexec`.

### 4. `PyMPI_Init: unable to import mpi4py` / `No module named 'mpi4py'`
- **Penyebab**: paket `mpi4py` terinstall di interpreter yang berbeda dari yang dipanggil `mpiexec`.
- **Solusi**: pastikan install ke interpreter yang sama:
  ```powershell
  py -m pip install mpi4py
  py -c "import mpi4py; print(mpi4py.__version__)"
  ```

---

## Ekspektasi Output

```
Rank 0 menerima 10
Rank 2 menerima 30
Rank 1 menerima 20
Rank 3 menerima 40
```

> ⚠️ **Urutan baris bisa berbeda** setiap eksekusi — ini normal (non-determinisme output paralel).

**Yang pasti (deterministik):**

---

## Tabel Hasil Praktikum

| Rank | Data Diterima |
|------|---------------|
| 0    | 10            |
| 1    | 20            |
| 2    | 30            |
| 3    | 40            |
