"""
web_simulation.py — UTS Komputasi Paralel & Terdistribusi
Topik : Parallel Web Simulation
Nama  : Raka Restu Saputra
NPM   : 247006111172

Skrip ini menjalankan:
  • Bagian B — Implementasi hybrid pipeline (Threads + ProcessPool)
  • Bagian C — Eksperimen 10 konfigurasi + tabel + grafik

Jalankan di Terminal 2 (setelah mock_server.py):
  py web_simulation.py                # default: B + C
  py web_simulation.py --mode b       # hanya Bagian B
  py web_simulation.py --mode c       # hanya Bagian C
"""

import argparse
import csv
import os
import queue
import random
import statistics
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor

import requests

NAMA = "Raka Restu Saputra"
NPM  = "247006111172"


def get_params(nim=NPM):
    """Hitung parameter pribadi dari NIM."""
    s = str(nim)
    return {
        "threads"  : (int(s[-2:]) % 4) + 2,    # 72 % 4 = 0  → 2
        "processes": (int(s[5:7]) % 3) + 2,    # 61 % 3 = 1  → 3
        "data"     : int(s[-3:]) * 10,         # 172 × 10    → 1720
    }


PARAMS      = get_params()
N_THREADS   = PARAMS["threads"]
N_PROCESSES = PARAMS["processes"]
N_DATA      = PARAMS["data"]

DEFAULT_URL = "http://127.0.0.1:8000/api/data"
HEALTH_URL  = "http://127.0.0.1:8000/health"

random.seed(int(NPM))

OUTPUT_DIR = "output"


# WORKER CPU-BOUND (Stage 2)
def analyze_latency(chunk):
    """Analisis statistik dari sekumpulan latency (ms)."""
    if not chunk:
        return {"count": 0}
    return {
        "count" : len(chunk),
        "mean"  : statistics.mean(chunk),
        "min"   : min(chunk),
        "max"   : max(chunk),
        "stddev": statistics.stdev(chunk) if len(chunk) > 1 else 0.0,
        "p50"   : statistics.median(chunk),
        "p90"   : statistics.quantiles(chunk, n=10)[8] if len(chunk) >= 10 else 0.0,
        "p95"   : statistics.quantiles(chunk, n=20)[18] if len(chunk) >= 20 else 0.0,
        "p99"   : statistics.quantiles(chunk, n=100)[98] if len(chunk) >= 100 else 0.0,
    }


# LOADER THREAD (Stage 1)
def loader_thread(n_requests, q, url):
    """Kirim HTTP request, catat latency ke queue."""
    for _ in range(n_requests):
        t0 = time.perf_counter()
        try:
            r = requests.get(url, timeout=5)
            _ = r.status_code
        except Exception:
            pass
        latency_ms = (time.perf_counter() - t0) * 1000
        q.put(latency_ms)
        
# PIPELINE HYBRID
def run_pipeline(n_requests, n_threads, n_processes, url=DEFAULT_URL):
    """
    Jalankan hybrid pipeline:
      Stage 1 — Threads (I/O-bound): kirim HTTP request
      Stage 2 — ProcessPool (CPU-bound): analisis statistik
    """
    q = queue.Queue(maxsize=200)

    # Bagi request ke thread
    per_thread = n_requests // n_threads
    rem = n_requests % n_threads
    counts = [per_thread + (1 if i < rem else 0) for i in range(n_threads)]

    # ---- Stage 1: Threads ----
    t_start = time.perf_counter()
    threads = []
    for c in counts:
        t = threading.Thread(target=loader_thread, args=(c, q, url))
        threads.append(t)
        t.start()

    latencies = []
    for _ in range(n_requests):
        latencies.append(q.get())

    for t in threads:
        t.join()

    t_stage1 = time.perf_counter() - t_start

    # ---- Stage 2: Processes ----
    t2_start = time.perf_counter()
    chunk_size = max(1, len(latencies) // n_processes)
    chunks = [latencies[i:i+chunk_size] for i in range(0, len(latencies), chunk_size)]

    with ProcessPoolExecutor(max_workers=n_processes) as ex:
        chunk_stats = list(ex.map(analyze_latency, chunks))

    t_stage2 = time.perf_counter() - t2_start
    t_total = time.perf_counter() - t_start

    # Statistik global
    global_stats = {
        "count" : len(latencies),
        "mean"  : statistics.mean(latencies),
        "min"   : min(latencies),
        "max"   : max(latencies),
        "stddev": statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
        "p50"   : statistics.median(latencies),
        "p95"   : statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else 0.0,
        "p99"   : statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else 0.0,
    }

    return {
        "total_time"  : t_total,
        "stage1_time" : t_stage1,
        "stage2_time" : t_stage2,
        "latencies"   : latencies,
        "global_stats": global_stats,
        "chunk_stats" : chunk_stats,
    }


# CEK SERVER
def check_server(url=HEALTH_URL):
    """Pastikan mock server jalan."""
    try:
        r = requests.get(url, timeout=3)
        return r.status_code == 200 and r.json().get("status") == "healthy"
    except Exception:
        return False


# BAGIAN B — Single Run dengan parameter NIM
def run_bagian_b(url):
    print("\n" + "=" * 70)
    print("  BAGIAN B — IMPLEMENTASI HYBRID PIPELINE")
    print("=" * 70)
    print(f"  Nama      : {NAMA}")
    print(f"  NPM       : {NPM}")
    print(f"  Threads   : {N_THREADS}")
    print(f"  Processes : {N_PROCESSES}")
    print(f"  Data      : {N_DATA} request")
    print("=" * 70)

    print(f"\n  [1/2] Stage 1 — {N_DATA} HTTP request via {N_THREADS} thread...")
    print(f"  [2/2] Stage 2 — analisis statistik via {N_PROCESSES} proses...\n")

    result = run_pipeline(N_DATA, N_THREADS, N_PROCESSES, url=url)

    # Hitung speedup & efisiensi (baseline serial = estimasi)
    serial_est = N_DATA * result["global_stats"]["mean"] / 1000
    speedup = serial_est / result["total_time"]
    n_workers = max(N_THREADS, N_PROCESSES)
    efficiency = (speedup / n_workers) * 100

    # Simpan log
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log_path = os.path.join(OUTPUT_DIR, "log_bagian_b.txt")
    with open(log_path, "w") as f:
        f.write(f"Nama: {NAMA}\nNPM: {NPM}\n")
        f.write(f"Threads: {N_THREADS}\nProcesses: {N_PROCESSES}\nData: {N_DATA}\n")
        f.write(f"Total Time: {result['total_time']:.4f} s\n")
        f.write(f"Stage 1: {result['stage1_time']:.4f} s\n")
        f.write(f"Stage 2: {result['stage2_time']:.4f} s\n")
        f.write(f"Throughput: {N_DATA / result['total_time']:.2f} req/s\n")
        f.write(f"Speedup: {speedup:.3f}\n")
        f.write(f"Efficiency: {efficiency:.2f}%\n")
        for k, v in result["global_stats"].items():
            f.write(f"{k}: {v:.4f}\n")

    # Cetak hasil
    print("=" * 70)
    print("  HASIL EKSEKUSI")
    print("=" * 70)
    print(f"  Nama           : {NAMA}")
    print(f"  NPM            : {NPM}")
    print(f"  Threads        : {N_THREADS}")
    print(f"  Processes      : {N_PROCESSES}")
    print(f"  Data           : {N_DATA} request")
    print("-" * 70)
    print(f"  Total Time     : {result['total_time']:.4f} s")
    print(f"    Stage 1 (HTTP)      : {result['stage1_time']:.4f} s")
    print(f"    Stage 2 (analysis)  : {result['stage2_time']:.4f} s")
    print(f"  Throughput     : {N_DATA / result['total_time']:.2f} request/s")
    print(f"  Speedup        : {speedup:.2f}×")
    print(f"  Efisiensi      : {efficiency:.2f}%")
    print("-" * 70)
    print("  Statistik Latency (ms):")
    for k, v in result["global_stats"].items():
        print(f"    {k:<8}: {v:>8.2f}")
    print("-" * 70)
    print("  Breakdown per Proses (Stage 2):")
    for i, cs in enumerate(result["chunk_stats"]):
        print(f"    Proses {i}: count={cs['count']:>4}, "
              f"mean={cs['mean']:>6.2f} ms")
    print("=" * 70)
    print(f"Log disimpan: {log_path}")

    return result


# BAGIAN C — Eksperimen 10 Konfigurasi
CONFIGS_C = [
    # (threads, processes, data)
    (1, 1, 1720),    # 1. Baseline serial
    (1, 3, 1720),    # 2. Thread tunggal, process banyak
    (2, 1, 1720),    # 3. Thread default NIM, process tunggal
    (2, 3, 1720),    # 4. Default parameter NIM
    (2, 6, 1720),    # 5. Process berlebih
    (4, 3, 1720),    # 6. Thread lebih banyak
    (4, 6, 1720),    # 7. Thread + process banyak
    (8, 3, 1720),    # 8. Thread sangat banyak
    (2, 3, 860),     # 9. Data setengah baseline
    (2, 3, 3440),    # 10. Data dua kali baseline
]


def run_bagian_c(url):
    print("\n" + "=" * 70)
    print("  BAGIAN C — EKSPERIMEN 10 KONFIGURASI")
    print("=" * 70)
    print(f"  Total konfigurasi: {len(CONFIGS_C)}")
    print(f"  Nama: {NAMA} | NPM: {NPM}")
    print("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []

    for i, (th, pr, data) in enumerate(CONFIGS_C, 1):
        print(f"\n[{i}/{len(CONFIGS_C)}] Thread={th}, Process={pr}, Data={data}")
        print("  → menjalankan...", end=" ", flush=True)

        try:
            r = run_pipeline(data, th, pr, url=url)
            elapsed = r["total_time"]
            throughput = data / elapsed
            print(f"selesai ({elapsed:.2f}s)")
        except Exception as e:
            print(f"GAGAL: {e}")
            continue

        results.append({
            "no"          : i,
            "threads"     : th,
            "processes"   : pr,
            "data"        : data,
            "time_s"      : round(elapsed, 4),
            "throughput"  : round(throughput, 2),
        })

    # Hitung speedup & efisiensi (baseline = konfigurasi #1)
    if results:
        baseline_time = results[0]["time_s"]
        for r in results:
            n_workers = max(r["threads"], r["processes"])
            r["speedup"]    = round(baseline_time / r["time_s"], 3)
            r["efficiency"] = round((r["speedup"] / n_workers) * 100, 2)

    # Simpan CSV
    csv_path = os.path.join(OUTPUT_DIR, "hasil_eksperimen.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "no", "threads", "processes", "data",
            "time_s", "throughput", "speedup", "efficiency"
        ])
        writer.writeheader()
        writer.writerows(results)

    # Cetak tabel
    print("\n" + "=" * 95)
    print("  TABEL HASIL — BAGIAN C (10 KONFIGURASI)")
    print("=" * 95)
    print(f"  {'No':<4} {'Thr':<6} {'Proc':<6} {'Data':<8} "
          f"{'Waktu(s)':<12} {'Throughput':<14} {'Speedup':<10} {'Eff(%)':<10}")
    print("-" * 95)
    for r in results:
        print(f"  {r['no']:<4} {r['threads']:<6} {r['processes']:<6} {r['data']:<8} "
              f"{r['time_s']:<12.4f} {r['throughput']:<14.2f} "
              f"{r['speedup']:<10.3f} {r['efficiency']:<10.2f}")
    print("=" * 95)
    print(f"CSV disimpan: {csv_path}")

    # Analisis singkat
    best = min(results, key=lambda r: r["time_s"])
    fastest_speedup = max(results, key=lambda r: r["speedup"])
    print(f"\nKonfigurasi tercepat : No {best['no']} "
          f"(T{best['threads']}-P{best['processes']}-D{best['data']}) "
          f"→ {best['time_s']:.2f}s")
    print(f"Speedup tertinggi    : No {fastest_speedup['no']} "
          f"→ {fastest_speedup['speedup']:.3f}×")

    return results


# GRAFIK
def generate_plots(results):
    """Generate 3 grafik: waktu vs thread, waktu vs process, speedup vs config."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Grafik 1: Waktu vs Thread (process=3, data=1720) ---
    td = [r for r in results if r["processes"] == 3 and r["data"] == 1720]
    if td:
        plt.figure(figsize=(8, 5))
        plt.plot([r["threads"] for r in td], [r["time_s"] for r in td],
                 marker="o", color="#1A73E8", linewidth=2, markersize=10)
        plt.xlabel("Jumlah Thread", fontsize=11)
        plt.ylabel("Waktu (s)", fontsize=11)
        plt.title(f"Waktu vs Jumlah Thread", fontsize=12, fontweight="bold")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "grafik_waktu_thread.png"), dpi=150)
        plt.close()

    # --- Grafik 2: Waktu vs Process (thread=2, data=1720) ---
    pd_ = [r for r in results if r["threads"] == 2 and r["data"] == 1720]
    if pd_:
        plt.figure(figsize=(8, 5))
        plt.plot([r["processes"] for r in pd_], [r["time_s"] for r in pd_],
                 marker="s", color="#C2185B", linewidth=2, markersize=10)
        plt.xlabel("Jumlah Process", fontsize=11)
        plt.ylabel("Waktu (s)", fontsize=11)
        plt.title(f"Waktu vs Jumlah Process", fontsize=12, fontweight="bold")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "grafik_waktu_process.png"), dpi=150)
        plt.close()

    # --- Grafik 3: Speedup vs Konfigurasi (semua) ---
    plt.figure(figsize=(12, 6))
    labels = [f"T{r['threads']}·P{r['processes']}\nD{r['data']}" for r in results]
    bars = plt.bar(range(len(results)), [r["speedup"] for r in results],
                   color="#2E7D32", alpha=0.8)
    plt.xticks(range(len(results)), labels, fontsize=8)
    plt.xlabel("Konfigurasi", fontsize=11)
    plt.ylabel("Speedup", fontsize=11)
    plt.title(f"Speedup vs Konfigurasi (10 Percobaan)", fontsize=12, fontweight="bold")
    plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.5,
                label='Baseline (speedup=1)')
    plt.legend()
    plt.grid(alpha=0.3, axis="y")
    for i, bar in enumerate(bars):
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, h + 0.05,
                 f"{h:.2f}", ha="center", fontsize=7)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "grafik_speedup.png"), dpi=150)
    plt.close()

    print(f"\nGrafik disimpan di: {OUTPUT_DIR}/")


# MAIN
def main():
    ap = argparse.ArgumentParser(
        description="UTS Hybrid Computing — Parallel Web Simulation"
    )
    ap.add_argument("--mode", choices=["b", "c", "all"], default="all",
                    help="b=Bagian B saja, c=Bagian C saja, all=keduanya")
    ap.add_argument("--url", default=DEFAULT_URL,
                    help="URL target")
    args = ap.parse_args()

    url = args.url

    print("=" * 70)
    print("  MEMERIKSA MOCK SERVER...")
    if not check_server():
        print("Mock server TIDAK berjalan!")
        print("Jalankan di Terminal lain:")
        print("      py mock_server.py")
        sys.exit(1)
    print("Mock server berjalan\n")

    results = None

    if args.mode in ("b", "all"):
        run_bagian_b(url)

    if args.mode in ("c", "all"):
        results = run_bagian_c(url)
        if results:
            generate_plots(results)

    print("\n" + "=" * 70)
    print("  SELESAI — Semua output tersimpan di folder 'output/'")
    print("=" * 70)


if __name__ == "__main__":
    main()