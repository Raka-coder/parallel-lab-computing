# Tugas 3 Praktikum 5 — Reduce vs Allreduce

Dokumentasi praktikum **Message Passing Interface (MPI)** tentang perbandingan `reduce` dan `allreduce` untuk operasi akumulasi global dengan `mpi4py` dan `numpy`.

---

## Identitas

- **Nama**: Raka Restu Saputra
- **NPM**: 247006111172
- **Kelas**: F
- **Mata Kuliah**: Komputasi Paralel dan Terdistribusi

---

## Penjelasan Program

Program memiliki 3 bagian utama:

**Bagian A — MAX dengan Reduce**
- Setiap proses menghitung `my_val = rank * 7 + 3`
- `comm.reduce()` dengan `MPI.MAX` mengirim hasil terbesar ke rank 0 saja

**Bagian B — Rata-rata dengan Allreduce**
- Setiap proses menghitung `val_for_avg = rank + 1`
- `comm.allreduce()` dengan `MPI.SUM` menjumlahkan ke semua proses
- Rata-rata = `global_sum / size`

**Bagian C — Total 1000 Bilangan Acak**
- Setiap proses menghasilkan 1000 bilangan acak (seed berbeda)
- `comm.allreduce()` menjumlahkan total dari semua proses

---

## Cara Menjalankan

```bash
mpiexec -n 4 py reduce-allreduce.py
```

> Jumlah proses fleksibel (default 4).

---

## Output

```
--- BAGIAN A: MAX dengan Reduce ---
[Rank 0] [REDUCE-MAX] Nilai terbesar = 24

--- BAGIAN B: AVG dengan Allreduce ---
[Rank 0] [ALLREDUCE-AVG] sum = 10, avg = 2.5

--- BAGIAN C: TOTAL 1000 Bilangan Acak/Proses ---
[Rank 0] [ALLREDUCE-SUM] Total = xxx.xxx
```

---

## Perbedaan Reduce vs Allreduce

| Aspek | `reduce` | `allreduce` |
|-------|----------|-------------|
| **Hasil diterima** | Hanya rank 0 | Semua rank |
| **Kebutuhan** | Agregasi di satu titik | Semua proses perlu hasil |

---

## File

| File | Keterangan |
|------|------------|
| `reduce-allreduce.py` | Skrip utama Reduce vs Allreduce |
| `README.md` | Dokumentasi ini |
