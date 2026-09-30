"""
run_b2_grid.py -- ukur makespan untuk rank {1,2,4} x max_workers {1,2,4},
hitung Speedup S = T1/Tn dan Efisiensi E = S/n (n = rank x worker),
lalu buat tabel + grafik.

Semua path default relatif terhadap direktori skrip ini (BASE_DIR).

Opsi --mpiexec untuk MS-MPI / OpenMPI. Contoh OpenMPI (Colab / WSL):
    python run_b2_grid.py --mpiexec "mpiexec --allow-run-as-root --oversubscribe"
"""
import argparse
import csv
import json
import shlex
import statistics
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RANKS = (1, 2, 4)
WORKERS = (1, 2, 4)

NAMA = "Raka Restu Saputra"
NPM = "247006111172"
KELAS = "F"

BASE_DIR = Path(__file__).resolve().parent
MPI_SCRIPT = BASE_DIR / "mpi_pi_processpool.py"
RESULTS_DIR = BASE_DIR / "results"

def print_identity():
    print("=" * 65)
    print("  B2 — Strong Scaling MPI + ProcessPool")
    print("=" * 65)
    print(f"  Nama       : {NAMA}")
    print(f"  NPM        : {NPM}")
    print(f"  Kelas      : {KELAS}")
    print("-" * 65)

def main():
    print_identity()
    ap = argparse.ArgumentParser()
    ap.add_argument("--mpiexec", default="mpiexec")
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--tasks", type=int, default=64)
    ap.add_argument("--out-dir", default=str(RESULTS_DIR))
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = out_dir / "b2_summary.csv"
    fig_path = out_dir / "b2_scaling.png"

    res = {}
    for r in RANKS:
        for w in WORKERS:
            times = []
            for _ in range(args.repeat):
                cmd = shlex.split(args.mpiexec) + ["-n", str(r), sys.executable,
                                                   str(MPI_SCRIPT),
                                                   "--workers", str(w), "--tasks", str(args.tasks)]
                out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
                line = [l for l in out.splitlines() if l.startswith("{")][-1]
                times.append(json.loads(line)["makespan_s"])
            res[(r, w)] = statistics.median(times)
            print(f"rank={r} workers={w} makespan={res[(r, w)]:.3f}s  (runs: {times})")

    t1 = res[(1, 1)]
    rows = []
    for (r, w), t in sorted(res.items()):
        n = r * w
        s = t1 / t
        rows.append({"ranks": r, "max_workers": w, "total_workers_n": n,
                     "makespan_s": round(t, 3), "speedup": round(s, 2),
                     "efficiency": round(s / n, 3)})
    with open(summary_csv, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ns = sorted({r["total_workers_n"] for r in rows})
    ax[0].plot(ns, ns, "k--", label="Ideal")
    ax[0].scatter([r["total_workers_n"] for r in rows], [r["speedup"] for r in rows])
    for r in rows:
        ax[0].annotate(f"{r['ranks']}x{r['max_workers']}", (r["total_workers_n"], r["speedup"]),
                       textcoords="offset points", xytext=(4, 4), fontsize=8)
    ax[0].set(xlabel="n = rank x worker", ylabel="Speedup", title="Speedup (label = rank x worker)")
    ax[0].legend()
    ax[0].grid(alpha=.3)
    ax[1].scatter([r["total_workers_n"] for r in rows], [r["efficiency"] for r in rows])
    ax[1].axhline(1, color="k", ls="--")
    ax[1].set(xlabel="n = rank x worker", ylabel="Efisiensi", title="Efisiensi")
    ax[1].grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=160)
    print(f"Selesai: {summary_csv}, {fig_path}")


if __name__ == "__main__":
    main()
