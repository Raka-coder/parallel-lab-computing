# B2 — Strong Scaling MPI + ProcessPool (Estimasi π Monte Carlo)

Praktikum 2: model hybrid dua level dengan kerja total **tetap**
(strong scaling, `TOTAL_TASKS = 64`, `SAMPLES_PER_TASK = 220.000` untuk A = 2).

## Arsitektur

- **Inter-rank (antar-proses):** MPI via `mpi4py` — tugas dibagi statis
  (`rank r` mengerjakan task `r, r+size, …`).
- **Intra-rank (dalam proses):** `ProcessPoolExecutor(max_workers=W)`
  dengan `mp_context="spawn"` (aman setelah `MPI_Init`, bebas GIL).
- **Makespan** diukur dengan `Barrier + MPI.Wtime`, diambil `MAX` antar-rank;
  hasil direduksi dengan `MPI.SUM`.
- Metrik turunan: `Speedup S = T1/Tn`, `Efisiensi E = S/n` dengan `n = rank × worker`.

## Perbaikan vs kode slide 20

| ID | Perbaikan |
|---|---|
| FIX-1 | `mpi4py` di-import lazy di dalam `main()` |
| FIX-2 | Fungsi worker dipisah ke `mc_worker.py` (picklable, tanpa mpi4py) |
| FIX-3 | `mp_context="spawn"`, bukan `fork` |
| FIX-4 | Entry point `if __name__ == "__main__"` |
| FIX-5 | Makespan = `Barrier + Wtime + MAX-reduce` |

## Struktur

| File | Fungsi |
|---|---|
| `mc_worker.py` | `mc_pi_task((seed, n))` — Monte Carlo murni CPU-bound |
| `mpi_pi_processpool.py` | Satu run MPI (`--workers/--tasks/--samples`, output JSON) |
| `run_b2_grid.py` | Grid rank `{1,2,4}` × worker `{1,2,4}`, median `--repeat`, tabel + grafik |
| `results/` | `b2_summary.csv`, `b2_scaling.png` |

## Cara run

```bash
# butuh MPI + mpi4py  (Windows: MS-MPI; Colab/WSL: OpenMPI)
pip install mpi4py matplotlib

# satu konfigurasi
mpiexec -n 2 python b2_mpi_processpool/mpi_pi_processpool.py --workers 2 --tasks 64

# seluruh grid (default mpiexec bisa dioverride)
python b2_mpi_processpool/run_b2_grid.py
python b2_mpi_processpool/run_b2_grid.py --mpiexec "mpiexec --allow-run-as-root --oversubscribe"
```

## Hasil (ringkas, median 3 run)

| ranks | workers | n | makespan_s | speedup | efisiensi |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 8.655 | 1.00 | 1.000 |
| 1 | 2 | 2 | 4.777 | 1.81 | 0.906 |
| 1 | 4 | 4 | 2.926 | 2.96 | 0.739 |
| 2 | 1 | 2 | 4.646 | 1.86 | 0.931 |
| 2 | 2 | 4 | 3.073 | 2.82 | 0.704 |
| 2 | 4 | 8 | 2.205 | 3.92 | 0.491 |
| 4 | 1 | 4 | 3.166 | 2.73 | 0.683 |
| 4 | 2 | 8 | 2.653 | 3.26 | 0.408 |
| 4 | 4 | 16 | 3.189 | 2.71 | 0.170 |

- Scaling bagus sampai n ≈ 8 (speedup 3.9, efisiensi ±0.5).
- Pada `4 rank × 4 worker` (n = 16) makespan naik lagi → overhead
  spawn + komunikasi MPI mendominasi (efisiensi 0.17).
- Grafik: [`results/b2_scaling.png`](results/b2_scaling.png).
