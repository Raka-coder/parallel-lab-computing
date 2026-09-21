Baik, maaf saya sebelumnya langsung lompat ke Tugas 3. Mari kita **mulai dari awal dan tersusun**: **Tugas 1 dulu, lalu Tugas 2**. Keduanya dari modul **MPI (Massage Passing Interface)**.

---

# TUGAS PRAKTIKUM 1 — Scatter Sederhana

## Tujuan
- Memahami distribusi data dari rank 0 ke seluruh proses menggunakan **Scatter**.
- Mengamati perilaku urutan output pada eksekusi paralel.

## Spesifikasi
1. Proses 0 memiliki list `[10, 20, 30, 40]`.
2. Data dibagi rata ke **4 proses** dengan scatter.
3. Setiap proses mencetak data yang diterimanya.

## Starter Code
```python
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Pastikan jumlah proses = 4
if size != 4:
    if rank == 0:
        print("Harap jalankan dengan -n 4")
    raise SystemExit

data = [10, 20, 30, 40] if rank == 0 else None
recv = comm.scatter(data, root=0)

print(f"Rank {rank} menerima {recv}")
```

---

## Konsep Pengerjaan Tugas 1

### Alur Eksekusi

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
│  • Rank 0 : data = [10, 20, 30, 40]                      │
│  • Rank 1-3 : data = None                                │
│                                                          │
│  Kenapa rank lain None? Karena hanya rank 0 yang boleh   │
│  punya data sumber. Rank lain akan menerima dari scatter.│
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  TAHAP 4 — SCATTER                                       │
│  • comm.scatter(data, root=0)                            │
│  • Rank 0 membagi 4 elemen ke 4 proses                   │
│                                                          │
│  Hasil:                                                  │
│    Rank 0 → 10                                           │
│    Rank 1 → 20                                           │
│    Rank 2 → 30                                           │
│    Rank 3 → 40                                           │
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

## Cara Menjalankan Tugas 1

```bash
# Pastikan mpi4py & MPI sudah terinstall
mpiexec -n 4 python tugas1_scatter.py
```

**Alternatif jika `mpiexec` tidak tersedia:**
```bash
mpirun -n 4 python tugas1_scatter.py
```

---

## Ekspektasi Output Tugas 1

```
Rank 0 menerima 10
Rank 2 menerima 30
Rank 1 menerima 20
Rank 3 menerima 40
```

> ⚠️ **Urutan bisa berbeda** setiap eksekusi — ini normal (non-determinisme output paralel).

**Yang pasti (deterministik):**

| Rank | Data Diterima |
|------|---------------|
| 0 | 10 |
| 1 | 20 |
| 2 | 30 |
| 3 | 40 |

---

## Tabel Hasil Tugas 1

| Rank | Data Diterima |
|------|---------------|
| 0 | 10 |
| 1 | 20 |
| 2 | 30 |
| 3 | 40 |

---

# TUGAS PRAKTIKUM 2 — Gather Sederhana

## Tujuan
- Memahami pengumpulan data dari semua proses ke root menggunakan **Gather**.
- Mengamati perubahan hasil saat jumlah proses berubah.

## Spesifikasi
1. Tiap proses mengirim data `rank * 5`.
2. Data dikumpulkan di proses 0 dan dicetak sebagai list.

## Starter Code
```python
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

send_val = rank * 5
gathered = comm.gather(send_val, root=0)

if rank == 0:
    print(f"Hasil gather di rank 0: {gathered}")
```

---

## Konsep Pengerjaan Tugas 2

### Alur Eksekusi

```
┌──────────────────────────────────────────────────────────┐
│  TAHAP 1 — INISIALISASI MPI                              │
│  • comm, rank, size                                      │
│  • TIDAK ada validasi size (beda dengan Tugas 1)         │
│  • Bisa dijalankan dengan -n 4, -n 6, dst.               │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  TAHAP 2 — PERSIAPAN DATA                                │
│  • Setiap proses menghitung: send_val = rank * 5         │
│                                                          │
│  Contoh untuk -n 4:                                      │
│    Rank 0 → 0 × 5 = 0                                    │
│    Rank 1 → 1 × 5 = 5                                    │
│    Rank 2 → 2 × 5 = 10                                   │
│    Rank 3 → 3 × 5 = 15                                   │
│                                                          │
│  Contoh untuk -n 6:                                      │
│    Rank 0 → 0                                            │
│    Rank 1 → 5                                            │
│    Rank 2 → 10                                           │
│    Rank 3 → 15                                           │
│    Rank 4 → 20                                           │
│    Rank 5 → 25                                           │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  TAHAP 3 — GATHER                                        │
│  • comm.gather(send_val, root=0)                         │
│  • Semua proses mengirim send_val ke rank 0              │
│  • Rank 0 menyusun hasil sesuai URUTAN RANK              │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  TAHAP 4 — CETAK OUTPUT (hanya rank 0)                   │
│  • if rank == 0: print(gathered)                         │
│  • Rank lain tidak mencetak apa pun                      │
└──────────────────────────────────────────────────────────┘
```

### Ilustrasi Gather

```
    ┌──────┬──────┬──────┬──────┐
    │Rank 0│Rank 1│Rank 2│Rank 3│
    ├──────┼──────┼──────┼──────┤
    │  0   │  5   │  10  │  15  │
    └──────┴──────┴──────┴──────┘
              │
              │  comm.gather(send_val, root=0)
              ▼
Rank 0: [0, 5, 10, 15]
```

**Poin penting:**
- `comm.gather()` mengembalikan **list** (hanya di root).
- Di rank selain 0, hasilnya `None`.
- Urutan list **selalu sesuai rank** — rank 0 di indeks 0, rank 1 di indeks 1, dst.

---

## Cara Menjalankan Tugas 2

```bash
# Dengan 4 proses
mpiexec -n 4 python tugas2_gather.py

# Dengan 6 proses (untuk uji perubahan)
mpiexec -n 6 python tugas2_gather.py
```

---

## Ekspektasi Output Tugas 2

### Kasus 1 — `-n 4`

```
Hasil gather di rank 0: [0, 5, 10, 15]
```

**Penjelasan:**

| Rank | `rank * 5` |
|------|------------|
| 0 | 0 |
| 1 | 5 |
| 2 | 10 |
| 3 | 15 |

List hasil: `[0, 5, 10, 15]`

### Kasus 2 — `-n 6`

```
Hasil gather di rank 0: [0, 5, 10, 15, 20, 25]
```

**Penjelasan:**

| Rank | `rank * 5` |
|------|------------|
| 0 | 0 |
| 1 | 5 |
| 2 | 10 |
| 3 | 15 |
| 4 | 20 |
| 5 | 25 |

List hasil: `[0, 5, 10, 15, 20, 25]`

---

## Tabel Hasil Tugas 2

| Proses | Hasil List di Rank 0 |
|--------|----------------------|
| 4 | `[0, 5, 10, 15]` |
| 6 | `[0, 5, 10, 15, 20, 25]` |

---

# Ringkasan Tugas 1 vs Tugas 2

| Aspek | Tugas 1 (Scatter) | Tugas 2 (Gather) |
|-------|-------------------|-------------------|
| **Arah data** | Rank 0 → semua proses | Semua proses → rank 0 |
| **Fungsi MPI** | `comm.scatter(data, root=0)` | `comm.gather(send_val, root=0)` |
| **Input** | List `[10, 20, 30, 40]` | Skalar `rank * 5` |
| **Output** | Skalar per proses | List di rank 0 |
| **Validasi size** | Harus 4 | Bebas (4, 6, dst.) |
| **Jumlah proses** | Tetap 4 | Fleksibel |
| **Deterministik?** | Ya (urutan data per rank) | Ya (urutan list sesuai rank) |
| **Non-determinisme** | Urutan cetak output | — |

---

# Diagram Gabungan (Tugas 1 & 2)

```
TUGAS 1 — SCATTER                    TUGAS 2 — GATHER

Rank 0: [10, 20, 30, 40]             Rank 0 → send_val = 0
        │                            Rank 1 → send_val = 5
        │ scatter                    Rank 2 → send_val = 10
        ▼                            Rank 3 → send_val = 15
┌────┬────┬────┬────┐                        │
│ R0 │ R1 │ R2 │ R3 │                        │ gather
│ 10 │ 20 │ 30 │ 40 │                        ▼
└────┴────┴────┴────┘                Rank 0: [0, 5, 10, 15]
        │
        │ print
        ▼
"Rank X menerima Y"
```

---

# Langkah Praktik Anda

## Untuk Tugas 1
1. Simpan starter code ke `tugas1_scatter.py`.
2. Jalankan: `mpiexec -n 4 python tugas1_scatter.py`.
3. Screenshot output.
4. Isi tabel:

| Rank | Data Diterima |
|------|---------------|
| 0 | 10 |
| 1 | 20 |
| 2 | 30 |
| 3 | 40 |

## Untuk Tugas 2
1. Simpan starter code ke `tugas2_gather.py`.
2. Jalankan: `mpiexec -n 4 python tugas2_gather.py`.
3. Jalankan lagi: `mpiexec -n 6 python tugas2_gather.py`.
4. Screenshot kedua output.
5. Isi tabel:

| Proses | Hasil List di Rank 0 |
|--------|----------------------|
| 4 | `[0, 5, 10, 15]` |
| 6 | `[0, 5, 10, 15, 20, 25]` |

---
