# Tugas 3 Praktikum 4 — Hitung Jumlah (Scatter + Gather)

Dokumentasi praktikum **Message Passing Interface (MPI)** tentang distribusi data, komputasi lokal, pengumpulan hasil, dan agregasi menggunakan `scatter` + `gather` dengan `mpi4py`.

---

## Identitas

- **Nama**: Raka Restu Saputra
- **NPM**: 247006111172
- **Kelas**: F
- **Mata Kuliah**: Komputasi Paralel dan Terdistribusi

---

## Penjelasan Program

Proses 0 memiliki list `[5, 10, 15, 20]`. Data di-scatter ke 4 proses, setiap proses menghitung `2 * x`, hasil di-gather ke rank 0, lalu dijumlahkan.

```
Rank 0: [5, 10, 15, 20]  →  scatter  →  x = [5, 10, 15, 20]
                                          │
                                     local = 2 * x  (paralel)
                                          │
                                          ▼
                                 [10, 20, 30, 40]  →  gather  →  Total = 100
```

---

## Cara Menjalankan

```bash
mpiexec -n 4 py calculate-scatter-gather.py
```

> Jumlah proses **harus tepat 4**.

---

## Output

```
Data awal     : [5, 10, 15, 20]
*2 per-proses : [10, 20, 30, 40]
Total akhir   : 100
Validasi      : 100 -> COCOK
```

---

## File

| File | Keterangan |
|------|------------|
| `calculate-scatter-gather.py` | Skrip utama Hitung Jumlah |
| `README.md` | Dokumentasi ini |
