"""
hybrid_pipeline.py -- Praktikum 1 (B1): Hybrid Pipeline

Arsitektur (threads untuk I/O, proses untuk CPU, dengan backpressure):

  [N_LOADER_THREADS]  --put-->  Queue(maxsize=Q_MAX)  --get-->  [N_WORKERS dispatcher]
     baca file (I/O-bound)      buffer berbatas (backpressure)     kirim ke ProcessPool
                                                                   (CPU-bound, bebas GIL)

- Loader thread berhenti (blocking) di queue.put() saat antrean penuh
  -> itulah backpressure; loader tidak boleh jauh mendahului konsumen.
- Tiap dispatcher thread mengirim 1 tugas ke ProcessPool dan menunggu hasilnya,
  sehingga jumlah tugas "in-flight" <= N_WORKERS.

Metrik: total time, throughput (file/detik), avg latency (detik/file,
dari mulai dibaca loader sampai selesai diproses), serta total waktu
loader terblokir oleh antrean penuh (indikator backpressure).
"""
import argparse
import csv
import os
import queue
import re
import statistics
import threading
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

WORD_RE = re.compile(r"[a-zA-Z]+")
_SENTINEL = object()  # unik; data antrean selalu tuple sehingga aman dibedakan

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = BASE_DIR / "data"


# ---------- pekerjaan CPU-bound (dijalankan di proses terpisah) ----------
def cpu_task(text: str, cpu_iters: int):
    """Tokenisasi + frekuensi kata + loop Python murni (menahan GIL)."""
    words = WORD_RE.findall(text.lower())
    freq = Counter(words)
    acc = 0
    for i in range(cpu_iters):          # beban CPU tambahan yang deterministik
        acc += (i * i) % 7
    return len(words), len(freq), acc


def _warm(_):
    time.sleep(0.05)                    # memaksa pool memunculkan semua worker
    return 0


# ---------- thread loader (I/O-bound) ----------
def loader(path_q, data_q, stats, lock):
    while True:
        try:
            p = path_q.get_nowait()
        except queue.Empty:
            return
        t_start = time.perf_counter()
        text = Path(p).read_text(encoding="utf-8", errors="ignore")   # I/O
        t_put = time.perf_counter()
        data_q.put((p, text, t_start))            # BLOCKING bila antrean penuh
        blocked = time.perf_counter() - t_put
        with lock:
            stats["put_block"] += blocked


# ---------- thread dispatcher: queue -> ProcessPool ----------
def dispatcher(data_q, pool, cpu_iters, latencies, lock):
    while True:
        item = data_q.get()
        if item is _SENTINEL:
            return
        _, text, t_start = item
        pool.submit(cpu_task, text, cpu_iters).result()
        lat = time.perf_counter() - t_start
        with lock:
            latencies.append(lat)


def run_pipeline(data_dir, n_loader, n_workers, q_max, cpu_iters):
    data_path = Path(data_dir)
    if not data_path.is_absolute() and not data_path.exists():
        alt = BASE_DIR / data_dir  # dukung run dari root repo maupun dari subdir
        if alt.exists():
            data_path = alt
    files = sorted(str(p) for p in data_path.glob("*.txt"))
    if not files:
        raise SystemExit(f"Tidak ada .txt di {data_path}. Jalankan make_dataset.py dulu.")

    path_q = queue.Queue()
    for f in files:
        path_q.put(f)
    data_q = queue.Queue(maxsize=q_max)
    latencies, stats, lock = [], {"put_block": 0.0}, threading.Lock()

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        list(pool.map(_warm, range(n_workers * 2)))       # start-up pool tidak dihitung

        t0 = time.perf_counter()
        loaders = [threading.Thread(target=loader, args=(path_q, data_q, stats, lock))
                   for _ in range(n_loader)]
        disp = [threading.Thread(target=dispatcher, args=(data_q, pool, cpu_iters, latencies, lock))
                for _ in range(n_workers)]
        for t in loaders + disp:
            t.start()
        for t in loaders:
            t.join()
        for _ in disp:
            data_q.put(_SENTINEL)
        for t in disp:
            t.join()
        total = time.perf_counter() - t0

    n = len(files)
    return {
        "loader_threads": n_loader, "workers": n_workers, "q_max": q_max,
        "files": n, "total_time_s": round(total, 4),
        "throughput_fps": round(n / total, 3),
        "avg_latency_s": round(statistics.mean(latencies), 4),
        "loader_blocked_s": round(stats["put_block"], 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DEFAULT_DATA))
    ap.add_argument("--threads", type=int, default=2, help="N_LOADER_THREADS")
    ap.add_argument("--workers", type=int, default=2, help="N_WORKERS")
    ap.add_argument("--qmax", type=int, default=4, help="Q_MAX")
    ap.add_argument("--cpu-iters", type=int, default=300_000)
    ap.add_argument("--csv", default=None, help="append hasil ke file CSV ini")
    args = ap.parse_args()

    r = run_pipeline(args.data, args.threads, args.workers, args.qmax, args.cpu_iters)
    print(f"[threads={r['loader_threads']} workers={r['workers']} Q_MAX={r['q_max']}] "
          f"total={r['total_time_s']}s  throughput={r['throughput_fps']} file/s  "
          f"avg_latency={r['avg_latency_s']}s  loader_blocked={r['loader_blocked_s']}s")
    if args.csv:
        new = not os.path.exists(args.csv)
        with open(args.csv, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(r.keys()))
            if new:
                w.writeheader()
            w.writerow(r)


if __name__ == "__main__":      # WAJIB untuk multiprocessing di Windows/macOS (spawn)
    main()
