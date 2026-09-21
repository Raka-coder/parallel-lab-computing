# Tugas 3 Praktikum 3 — Scatter + Gather (Kombinasi)

Dokumentasi praktikum **Message Passing Interface (MPI)** tentang penggabungan distribusi data (`scatter`), komputasi lokal, dan pengumpulan hasil (`gather`) dengan `mpi4py`.

---

## Identitas

- **Nama**: Raka Restu Saputra
- **NPM**: 247006111172
- **Kelas**: F
- **Mata Kuliah**: Komputasi Paralel dan Terdistribusi

---

## Penjelasan Program

Proses 0 memiliki list `[1, 2, 3, 4]`. Data di-scatter ke 4 proses, setiap proses menghitung kuadrat (`y = x * x`), lalu hasil di-gather kembali ke proses 0.

```
Rank 0: [1, 2, 3, 4]  →  scatter  →  x = [1, 2, 3, 4]
                                       │
                                  y = x * x  (paralel)
                                       │
                                       ▼
                              y = [1, 4, 9, 16]  →  gather  →  Rank 0: [1, 4, 9, 16]
```

---

## Cara Menjalankan

```bash
mpiexec -n 4 py scatter-gather.py
```

> Jumlah proses **harus tepat 4**.

---

## Output

```
Input  : [1, 2, 3, 4]
Output : [1, 4, 9, 16]
```

---

## File

| File | Keterangan |
|------|------------|
| `scatter-gather.py` | Skrip utama Scatter + Gather |
| `README.md` | Dokumentasi ini |
