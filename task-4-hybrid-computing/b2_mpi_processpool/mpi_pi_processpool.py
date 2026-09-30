"""
mpi_pi_processpool.py -- Praktikum 2 (B2): Strong scaling MPI + ProcessPool
VERSI YANG SUDAH DIPERBAIKI.

Model hybrid:
  inter-node / antar-rank : MPI (mpi4py)  -> tugas dibagi statis (rank r ambil r, r+size, ...)
  intra-node / dalam rank : ProcessPoolExecutor(max_workers=W) -> CPU-bound bebas GIL

Strong scaling = TOTAL_TASKS (total kerja) tetap; yang diubah hanya jumlah
rank dan worker.

Perubahan dibanding kode slide 20 (lihat laporan, bagian B2.1):
  [FIX-1] mpi4py di-import DI DALAM main(), bukan di tingkat modul.
  [FIX-2] worker function dipindah ke modul terpisah (mc_worker.py) -> picklable & bersih.
  [FIX-3] mp_context = 'spawn' (bukan fork) -> fork setelah MPI_Init tidak aman.
  [FIX-4] entry point dilindungi  if __name__ == "__main__".
  [FIX-5] makespan diukur dengan Barrier + MPI.Wtime, diambil MAX antar-rank.
"""
import argparse
import json
import multiprocessing as mp
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # agar mc_worker ketemu dari CWD mana pun
from mc_worker import mc_pi_task

A = 2                                        # <-- DIUBAH: digit terakhir NIM
SAMPLES_PER_TASK = 200_000 + 10_000 * A      # <-- DIUBAH: 220.000
TOTAL_TASKS = 64                             # total kerja tetap (strong scaling)


def main():
    from mpi4py import MPI                   # [FIX-1] import lazy
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=1, help="max_workers per rank")
    ap.add_argument("--tasks", type=int, default=TOTAL_TASKS)
    ap.add_argument("--samples", type=int, default=SAMPLES_PER_TASK)
    args = ap.parse_args()

    comm = MPI.COMM_WORLD
    rank, size = comm.Get_rank(), comm.Get_size()

    my_tasks = [(seed, args.samples) for seed in range(args.tasks)][rank::size]

    comm.Barrier()
    t0 = MPI.Wtime()
    ctx = mp.get_context("spawn")            # [FIX-3]
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=ctx) as ex:
        local_inside = sum(ex.map(mc_pi_task, my_tasks))
    total_inside = comm.reduce(local_inside, op=MPI.SUM, root=0)
    comm.Barrier()
    makespan = comm.reduce(MPI.Wtime() - t0, op=MPI.MAX, root=0)   # [FIX-5]

    if rank == 0:
        pi_est = 4.0 * total_inside / (args.tasks * args.samples)
        print(json.dumps({"ranks": size, "workers": args.workers,
                          "total_procs": size * args.workers,
                          "makespan_s": round(makespan, 4),
                          "pi_estimate": round(pi_est, 6)}))


if __name__ == "__main__":                   # [FIX-4]
    main()
