# Tugas 3 Praktikum 1 — Scatter Sederhana (MPI)

Dokumentasi praktikum **Message Passing Interface (MPI)** tentang distribusi data dari proses root ke seluruh proses menggunakan `comm.scatter()` dengan `mpi4py`.

---

## Identitas

- **Nama**: Raka Restu Saputra
- **NPM**: 247006111172
- **Kelas**: F
- **Mata Kuliah**: Komputasi Paralel dan Terdistribusi

---

## Penjelasan Program

Proses 0 memiliki list `[10, 20, 30, 40]`. Melalui `comm.scatter()`, data dibagi rata ke 4 proses — masing-masing proses menerima satu elemen.

```
Rank 0: [10, 20, 30, 40]  →  scatter  →  Rank 0: 10
                                          Rank 1: 20
                                          Rank 2: 30
                                          Rank 3: 40
```

---

## Cara Menjalankan

```bash
# Windows
mpiexec -n 4 py scatter-simple.py

# Linux / macOS
mpirun -n 4 python3 scatter-simple.py
```

> Jumlah proses **harus tepat 4**.

---

## Output

```
Rank 0 menerima 10
Rank 1 menerima 20
Rank 2 menerima 30
Rank 3 menerima 40
```

> Urutan baris bisa berbeda setiap eksekusi (non-determinisme output paralel), tetapi pemetaan rank → data selalu sama.

---

## File

| File | Keterangan |
|------|------------|
| `scatter-simple.py` | Skrip utama MPI Scatter |
| `README.md` | Dokumentasi ini |
