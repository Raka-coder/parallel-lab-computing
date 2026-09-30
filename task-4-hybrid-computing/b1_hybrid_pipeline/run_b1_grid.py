"""
run_b1_grid.py -- menjalankan seluruh kombinasi B1 secara otomatis, lalu membuat
tabel (CSV + Markdown) dan grafik throughput vs N_WORKERS.

Kombinasi: N_LOADER_THREADS {1,2,4} x N_WORKERS {1,2,4,<core laptop>} x Q_MAX {4,32}
Tiap kombinasi diulang --repeat kali; yang dilaporkan adalah MEDIAN.

Semua path default relatif terhadap direktori skrip ini (BASE_DIR),
sehingga bisa dijalankan dari mana saja:
    python b1_hybrid_pipeline/run_b1_grid.py
    cd b1_hybrid_pipeline && python run_b1_grid.py
"""
import argparse
import csv
import os
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NAMA = "Raka Restu Saputra"
NPM = "247006111172"
KELAS = "F"
A = 2  # digit terakhir NPM

BASE_DIR = Path(__file__).resolve().parent
PIPELINE_SCRIPT = BASE_DIR / "hybrid_pipeline.py"
DEFAULT_DATA = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"


def print_identity():
    """Cetak identitas + spesifikasi perangkat ke terminal."""
    print("=" * 65)
    print("  B1 — HYBRID PIPELINE EXPERIMENT")
    print("=" * 65)
    print(f"  Nama       : {NAMA}")
    print(f"  NPM        : {NPM}")
    print(f"  Kelas      : {KELAS}")
    print(f"  A (NIM)    : {A}")
    print(f"  N_FILES    : {100 + 10 * A} file")
    print("-" * 65)


def resolve(path_str: str) -> str:
    """Kembalikan path absolut; path relatif dicoba thd CWD lalu BASE_DIR."""
    p = Path(path_str)
    if p.is_absolute() or p.exists():
        return str(p)
    cand = BASE_DIR / path_str
    return str(cand if cand.exists() else p)


def main():
    print_identity()
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DEFAULT_DATA))
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--raw", default=str(RESULTS_DIR / "b1_raw.csv"))
    ap.add_argument("--out-dir", default=str(RESULTS_DIR))
    args = ap.parse_args()

    data_dir = resolve(args.data)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = Path(args.raw)
    summary_csv = out_dir / "b1_summary.csv"
    summary_md = out_dir / "b1_summary.md"
    fig_path = out_dir / "b1_throughput.png"

    cores = os.cpu_count() or 4
    workers_list = sorted({1, 2, 4, cores})
    if raw_path.exists():
        raw_path.unlink()

    for qmax in (4, 32):
        for th in (1, 2, 4):
            for w in workers_list:
                for _ in range(args.repeat):
                    subprocess.run([sys.executable, str(PIPELINE_SCRIPT), "--data", data_dir,
                                    "--threads", str(th), "--workers", str(w),
                                    "--qmax", str(qmax), "--csv", str(raw_path)], check=True)

    groups = defaultdict(list)
    with open(raw_path) as f:
        for r in csv.DictReader(f):
            groups[(int(r["q_max"]), int(r["loader_threads"]), int(r["workers"]))].append(r)

    rows = []
    for (q, th, w), rs in sorted(groups.items()):
        med = lambda k: statistics.median(float(x[k]) for x in rs)
        rows.append({"Q_MAX": q, "N_LOADER_THREADS": th, "N_WORKERS": w,
                     "total_time_s": round(med("total_time_s"), 3),
                     "throughput_fps": round(med("throughput_fps"), 2),
                     "avg_latency_s": round(med("avg_latency_s"), 3),
                     "loader_blocked_s": round(med("loader_blocked_s"), 2)})

    with open(summary_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(summary_md, "w") as f:
        hdr = list(rows[0].keys())
        f.write("| " + " | ".join(hdr) + " |\n|" + "---|" * len(hdr) + "\n")
        for r in rows:
            f.write("| " + " | ".join(str(r[h]) for h in hdr) + " |\n")

    # grafik throughput vs N_WORKERS
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, q in zip(axes, (4, 32)):
        for th in (1, 2, 4):
            pts = [(r["N_WORKERS"], r["throughput_fps"]) for r in rows
                   if r["Q_MAX"] == q and r["N_LOADER_THREADS"] == th]
            ax.plot(*zip(*pts), marker="o", label=f"{th} loader thread")
        ax.set_title(f"Q_MAX = {q}")
        ax.set_xlabel("N_WORKERS")
        ax.set_xticks(workers_list)
        ax.grid(alpha=.3)
    axes[0].set_ylabel("Throughput (file/detik)")
    axes[0].legend()
    fig.suptitle(f"B1: Throughput vs N_WORKERS (core laptop = {cores})")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=160)
    print(f"Selesai: {summary_csv}, {summary_md}, {fig_path}")


if __name__ == "__main__":
    main()
