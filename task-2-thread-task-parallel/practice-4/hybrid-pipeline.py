import os
import csv
import re
import time
import queue
import threading
from concurrent.futures import ProcessPoolExecutor

DATASET_CSV = "dataset/train.csv"
NUM_BATCHES = 20
QUEUE_MAXSIZE = 5


def clean_and_tokenize(text):
    text = text.lower()
    return re.findall(r'\b[a-z0-9]+\b', text)


def process_batch(records):
    total_tokens = 0
    vocab = {}

    for text in records:
        tokens = clean_and_tokenize(text)
        total_tokens += len(tokens)

        for t in tokens:
            h = 0
            for ch in t:
                for k in range(50):
                    h = (h * 31 + ord(ch) + k) % 1000000007
            vocab[t] = vocab.get(t, 0) + 1

    return {
        "count": len(records),
        "tokens": total_tokens,
        "unique_vocab": len(vocab)
    }


def loader_thread(csv_path, batch_ranges, q):
    for batch_id, start_row, end_row in batch_ranges:
        try:
            load_start = time.perf_counter()
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                next(reader, None)
                batch_records = [
                    row[0] for idx, row in enumerate(reader)
                    if start_row <= idx < end_row and row
                ]
            q.put((batch_id, batch_records, load_start))
        except Exception as e:
            print(f"Error membaca batch {batch_id}: {e}")
    q.put(None)


def aggregator(q, results, num_loaders, cpu_executor):
    futures = []
    done_loaders = 0

    while done_loaders < num_loaders:
        item = q.get()
        if item is None:
            done_loaders += 1
            continue

        batch_id, batch_records, load_time = item
        future = cpu_executor.submit(process_batch, batch_records)
        futures.append((batch_id, len(batch_records), load_time, future))

    for batch_id, count, load_time, future in futures:
        result = future.result()
        latency = time.perf_counter() - load_time
        results.append({
            'batch_id': batch_id,
            'count': count,
            'result': result,
            'latency': latency
        })


def get_dataset_info(csv_path=DATASET_CSV):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File dataset tidak ditemukan di: {csv_path}")

    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        next(reader, None)
        total_rows = sum(1 for row in reader if row)
    return total_rows


def run_baseline(csv_path):
    start = time.perf_counter()
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        next(reader, None)
        all_records = [row[0] for row in reader if row]

    result = process_batch(all_records)
    total_time = time.perf_counter() - start
    return total_time, len(all_records), result


def run_hybrid(csv_path, total_rows, num_batches, num_loaders, num_workers):
    q = queue.Queue(maxsize=QUEUE_MAXSIZE)
    results = []

    batch_size = (total_rows + num_batches - 1) // num_batches
    all_batches = []
    for b in range(num_batches):
        s = b * batch_size
        e = min((b + 1) * batch_size, total_rows)
        all_batches.append((b, s, e))

    loader_chunks = [all_batches[i::num_loaders] for i in range(num_loaders)]

    start = time.perf_counter()

    with ProcessPoolExecutor(max_workers=num_workers) as cpu_executor:
        loaders = []
        for chunk in loader_chunks:
            t = threading.Thread(target=loader_thread, args=(csv_path, chunk, q))
            loaders.append(t)
            t.start()

        aggregator(q, results, num_loaders, cpu_executor)

        for t in loaders:
            t.join()

    total_time = time.perf_counter() - start
    return total_time, results


def show_plots(baseline_time, baseline_count, benchmark_records):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print()
        print("=" * 70)
        print("  [!] matplotlib belum terinstall.")
        print("  Jalankan perintah berikut untuk menginstall:")
        print("      pip install matplotlib")
        print("=" * 70)
        return

    labels = ["Serial"] + [f"{r[0]}L / {r[1]}W" for r in benchmark_records]
    times = [baseline_time] + [r[2] for r in benchmark_records]
    throughputs = [baseline_count / baseline_time] + [r[3] for r in benchmark_records]
    speedups = [1.0] + [r[5] for r in benchmark_records]

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))

    colors = ["#e74c3c", "#3498db", "#f39c12", "#2ecc71", "#9b59b6"]

    bars1 = ax1.bar(labels, times, color=colors, width=0.55, edgecolor="black", linewidth=1.0)
    ax1.set_title("Waktu Eksekusi (detik)", fontsize=11, fontweight="bold", pad=10)
    ax1.set_ylabel("Waktu (detik)", fontsize=10)
    ax1.tick_params(axis="x", rotation=15)
    ax1.grid(axis="y", linestyle="--", alpha=0.7)
    for bar in bars1:
        h = bar.get_height()
        ax1.annotate(
            f"{h:.2f}s",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

    bars2 = ax2.bar(labels, throughputs, color=colors, width=0.55, edgecolor="black", linewidth=1.0)
    ax2.set_title("Throughput (data/detik)", fontsize=11, fontweight="bold", pad=10)
    ax2.set_ylabel("Data per detik", fontsize=10)
    ax2.tick_params(axis="x", rotation=15)
    ax2.grid(axis="y", linestyle="--", alpha=0.7)
    for bar in bars2:
        h = bar.get_height()
        ax2.annotate(
            f"{h:.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

    bars3 = ax3.bar(labels, speedups, color=colors, width=0.55, edgecolor="black", linewidth=1.0)
    ax3.axhline(1.0, color="#7f8c8d", linestyle="--", linewidth=1.2, label="Baseline (1.0x)")
    ax3.set_title("Speedup vs Baseline (x)", fontsize=11, fontweight="bold", pad=10)
    ax3.set_ylabel("Speedup (x)", fontsize=10)
    ax3.tick_params(axis="x", rotation=15)
    ax3.legend(frameon=True)
    ax3.grid(axis="y", linestyle="--", alpha=0.7)
    for bar in bars3:
        h = bar.get_height()
        ax3.annotate(
            f"{h:.2f}x",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

    plt.suptitle("Tugas 4: Evaluasi Performa Hybrid Pipeline (Threads + Processes)", fontsize=13, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    print("=" * 100)
    print("TUGAS 4 - HYBRID PIPELINE (THREADS + PROCESSES)")
    print("Nama  : Raka Restu Saputra")
    print("NPM   : 247006111172")
    print("Kelas : F")
    print(f"Dataset : {DATASET_CSV}")
    print("=" * 100)

    total_rows = get_dataset_info(DATASET_CSV)
    print(f"\nTotal data SMS dalam dataset: {total_rows} baris.")

    print("\nMenjalankan baseline (single-process serial)...")
    baseline_time, baseline_count, baseline_res = run_baseline(DATASET_CSV)
    print(f"Baseline selesai dalam {baseline_time:.4f}s ({baseline_count} data SMS diproses)\n")

    configs = [
        (4, 4),
        (4, 2),
        (2, 4),
        (8, 4),
    ]

    print("Menjalankan evaluasi konfigurasi Hybrid Pipeline...")
    print(f"\n{'Threads Loader':<16} {'CPU Workers':<13} {'Jumlah Data':<13} "
          f"{'Waktu (s)':<12} {'Throughput (data/s)':<22} {'Avg Latency (s)':<18} {'Speedup':<10}")
    print("-" * 110)

    benchmark_records = []
    for num_loaders, num_workers in configs:
        hybrid_time, hybrid_results = run_hybrid(DATASET_CSV, total_rows, NUM_BATCHES, num_loaders, num_workers)
        total_processed = sum(r['count'] for r in hybrid_results)
        throughput = total_processed / hybrid_time
        avg_latency = sum(r['latency'] for r in hybrid_results) / len(hybrid_results)
        speedup = baseline_time / hybrid_time
        benchmark_records.append((num_loaders, num_workers, hybrid_time, throughput, avg_latency, speedup))

        print(f"{num_loaders:<16} {num_workers:<13} {total_processed:<13} "
              f"{hybrid_time:<12.4f} {throughput:<22.2f} {avg_latency:<18.4f} {speedup:<10.2f}x")

    print("=" * 110)
    best_record = max(benchmark_records, key=lambda x: x[5])
    print(f"\nRingkasan:")
    print(f"- Waktu Baseline (Serial)   : {baseline_time:.4f}s")
    print(f"- Konfigurasi Terbaik       : {best_record[0]} Loader Threads, {best_record[1]} CPU Workers")
    print(f"- Waktu Hybrid Tercepat     : {best_record[2]:.4f}s")
    print(f"- Speedup Terbaik           : {best_record[5]:.2f}x")
    print("=" * 110)

    print()
    print("=" * 70)
    print("  MENAMPILKAN GRAFIK (matplotlib)")
    print("=" * 70)
    show_plots(baseline_time, baseline_count, benchmark_records)

    print()
    print("=" * 100)
    print("SELESAI")
    print("=" * 100)