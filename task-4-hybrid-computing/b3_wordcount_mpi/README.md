# B3 — Global Word Count (MPI + Threads/Proses)

Praktikum 3: word count global di atas teks nyata (≥ 30 e-book Project Gutenberg),
membandingkan dua executor intra-rank, dengan stopwords dibuang + Top-10.

## Modifikasi vs kode asli

| ID | Isi |
|---|---|
| MOD-1 | Dataset dummy → teks nyata (`corpus/`, 40 file `pg*.txt`) |
| MOD-2 | Dua versi intra-rank: (a) `ThreadPoolExecutor`, (b) `ProcessPoolExecutor` (spawn) |
| MOD-3 | Stopwords ID+EN dibuang (`dan, yang, di, the, of, and`, …), tampilkan Top-10 |

## Arsitektur

```text
rank 0: list corpus/*.txt -> scatter (round-robin: files[i::size])
setiap rank: warm-up baca file -> timed(ThreadPool) -> timed(ProcessPool)
rank 0: gather Counter + waktu -> makespan = max antar-rank -> Top-10
```

`timed()` memakai `Barrier + MPI.Wtime` dan median dari `--repeat` run.
Assert memastikan hasil thread ≡ hasil proses.

## Struktur

| File | Fungsi |
|---|---|
| `download_corpus.py` | Unduh ±40 e-book Gutenberg ke `corpus/` (buang header/footer lisensi) |
| `wordcount_mpi.py` | Program utama MPI (`--data/--workers/--repeat`) |
| `corpus/` | 40 file teks nyata (sudah terunduh) |

## Cara run

```bash
pip install mpi4py

# (sekali saja, butuh internet)
python b3_wordcount_mpi/download_corpus.py --out b3_wordcount_mpi/corpus

# run utama (hanya rank 0 yang mencetak)
mpiexec -n 4 python b3_wordcount_mpi/wordcount_mpi.py --workers 4 --repeat 3

# Colab
# !pip install mpi4py
# !mpiexec --allow-run-as-root --oversubscribe -n 4 python b3_wordcount_mpi/wordcount_mpi.py
```

Default `--data` menunjuk ke `corpus/` di sebelah skrip, jadi bisa
dijalankan dari root maupun dari dalam folder.

## Hasil yang diharapkan

- Output: identitas (rank 0 saja) → perbandingan waktu
  `ThreadPoolExecutor` vs `ProcessPoolExecutor` + rasio → Top-10 kata.
- `ProcessPool` umumnya menang untuk tokenisasi regex (CPU-bound, GIL-bound);
  `ThreadPool` menang bila workload lebih I/O-bound.
- Konsistensi dijamin `assert c_thr == c_prc`.
