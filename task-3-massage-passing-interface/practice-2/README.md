# Tugas 3 Praktikum 2 — Gather Sederhana (MPI)

Dokumentasi praktikum **Message Passing Interface (MPI)** tentang pengumpulan data dari semua proses ke proses root menggunakan `comm.gather()` dengan `mpi4py`.

---

## Identitas

- **Nama**: Raka Restu Saputra
- **NPM**: 247006111172
- **Kelas**: F
- **Mata Kuliah**: Komputasi Paralel dan Terdistribusi

---

## Penjelasan Program

Setiap proses menghitung `send_val = rank * 5`, lalu data dikumpulkan ke proses 0 melalui `comm.gather()`. Hasilnya berupa list yang disusun sesuai urutan rank.

```
Rank 0: 0    ─┐
Rank 1: 5     │  gather  →  Rank 0: [0, 5, 10, 15]
Rank 2: 10    │
Rank 3: 15   ─┘
```

---

## Cara Menjalankan

```bash
# Dengan 4 proses
mpiexec -n 4 py gather-simple.py

# Dengan 6 proses (untuk uji perubahan)
mpiexec -n 6 py gather-simple.py
```

> Tidak ada validasi jumlah proses — bisa dijalankan dengan `-n` berapa pun.

---

## Output

### `-n 4`
```
Hasil gather di rank 0: [0, 5, 10, 15]
```

### `-n 6`
```
Hasil gather di rank 0: [0, 5, 10, 15, 20, 25]
```

---

## File

| File | Keterangan |
|------|------------|
| `tugas2_gather.py` | Skrip utama MPI Gather |
| `README.md` | Dokumentasi ini |
