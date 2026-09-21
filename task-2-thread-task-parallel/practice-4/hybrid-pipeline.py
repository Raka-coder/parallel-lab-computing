# Nama: Raka Restu Saputra
# NPM: 247006111172
# Kelas: F
# Mata Kuliah: Komputasi Paralel dan Terdistribusi

import os
import csv
import time
import queue
import math
import re
import threading
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


SPAM_KEYWORDS = [
    "free", "win", "prize", "cash", "call", "txt", "claim",
    "urgent", "http", "www", "mobile", "phone", "offer"
]


def split_csv_into_files(input_csv, output_dir, n_parts):
    """
    Stage 0: Data Preparation
    Membaca input_csv dan membagi baris secara round-robin ke n_parts file part.
    Setiap part file memiliki header CSV yang sama.
    """
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV '{input_csv}' tidak ditemukan!")

    os.makedirs(output_dir, exist_ok=True)

    with open(input_csv, mode="r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"File CSV '{input_csv}' kosong!")

        rows = [row for row in reader if row]

    part_paths = [os.path.join(output_dir, f"part_{i:03d}.csv") for i in range(n_parts)]
    part_writers = []
    part_handles = []

    for path in part_paths:
        fh = open(path, mode="w", newline="", encoding="utf-8")
        writer = csv.writer(fh)
        writer.writerow(header)
        part_handles.append(fh)
        part_writers.append(writer)

    try:
        for idx, row in enumerate(rows):
            part_writers[idx % n_parts].writerow(row)
    finally:
        for fh in part_handles:
            fh.close()

    return part_paths


def load_file(path):
    """
    Stage 1 Helper: Membaca 1 part file dari disk, mengembalikan (path, rows).
    """
    rows = []
    with open(path, mode="r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        try:
            _ = next(reader)  
        except StopIteration:
            return path, rows

        for row in reader:
            if row:
                rows.append(row)
    return path, rows


def loader_worker(file_paths, q):
    """
    Stage 1: Loader Threads Worker (I/O-Bound).
    """
    for p in file_paths:
        try:
            item = load_file(p)
            q.put(item)
        except Exception as e:
            print(f"Error loading file {p}: {e}")
            q.put((p, []))


def process_chunk(item):
    """
    Stage 2: Process Pool Task (CPU-Bound).
    - Menghitung baris, kata, karakter, label spam/ham, dan spam keyword hits.
    - Checksum berbasis nilai ord().
    - Loop 10.000 iterasi math.sqrt per baris sebagai beban komputasi CPU buatan.
    """
    path, rows = item

    total_rows = len(rows)
    total_words = 0
    total_chars = 0
    spam_count = 0
    ham_count = 0
    keyword_hits = 0
    checksum = 0

    for row in rows:
        text = row[0] if len(row) > 0 else ""
        label_str = row[1].strip() if len(row) > 1 else ""

        if label_str == "1":
            spam_count += 1
        elif label_str == "0":
            ham_count += 1

        total_chars += len(text)
        words = re.findall(r"\b[a-zA-Z0-9_]+\b", text)
        total_words += len(words)

        text_lower = text.lower()
        for kw in SPAM_KEYWORDS:
            keyword_hits += text_lower.count(kw)

        for ch in text:
            checksum = (checksum + ord(ch)) % 1000000007

        val = 1000.0 + len(text)
        for _ in range(10000):
            val = math.sqrt(val * val + 1.0)
        checksum = (checksum + int(val)) % 1000000007

    return {
        "path": path,
        "total_rows": total_rows,
        "total_words": total_words,
        "total_chars": total_chars,
        "spam_count": spam_count,
        "ham_count": ham_count,
        "keyword_hits": keyword_hits,
        "checksum": checksum
    }


def run_serial(part_paths):
    """
    Baseline Comparison: Pemrosesan sekuensial seluruh file secara berurutan.
    """
    t_start = time.perf_counter()
    results = [process_chunk(load_file(p)) for p in part_paths]
    duration = time.perf_counter() - t_start

    num_files = len(part_paths)
    return {
        "total_files": num_files,
        "total_sms": sum(r["total_rows"] for r in results),
        "spam_count": sum(r["spam_count"] for r in results),
        "ham_count": sum(r["ham_count"] for r in results),
        "total_words": sum(r["total_words"] for r in results),
        "total_chars": sum(r["total_chars"] for r in results),
        "keyword_hits": sum(r["keyword_hits"] for r in results),
        "duration": duration,
        "throughput": num_files / duration if duration > 0 else 0,
        "avg_latency": duration / num_files if num_files > 0 else 0
    }


def run_hybrid_pipeline(part_paths, num_loader_threads, num_cpu_workers, queue_size):
    """
    Hybrid Pipeline: Loader Threads + Bounded Queue Buffer + ProcessPoolExecutor.
    """
    t_start = time.perf_counter()
    data_queue = queue.Queue(maxsize=queue_size)
    num_files = len(part_paths)

    thread_assignments = [[] for _ in range(num_loader_threads)]
    for idx, path in enumerate(part_paths):
        thread_assignments[idx % num_loader_threads].append(path)

    loaders = []
    for assignment in thread_assignments:
        t = threading.Thread(target=loader_worker, args=(assignment, data_queue), daemon=True)
        t.start()
        loaders.append(t)

    results = []
    with ProcessPoolExecutor(max_workers=num_cpu_workers) as executor:
        futures = []
        for _ in range(num_files):
            item = data_queue.get()
            fut = executor.submit(process_chunk, item)
            futures.append(fut)
            data_queue.task_done()

        for t in loaders:
            t.join()

        for fut in as_completed(futures):
            results.append(fut.result())

    duration = time.perf_counter() - t_start
    return {
        "total_files": num_files,
        "total_sms": sum(r["total_rows"] for r in results),
        "spam_count": sum(r["spam_count"] for r in results),
        "ham_count": sum(r["ham_count"] for r in results),
        "total_words": sum(r["total_words"] for r in results),
        "total_chars": sum(r["total_chars"] for r in results),
        "keyword_hits": sum(r["keyword_hits"] for r in results),
        "duration": duration,
        "throughput": num_files / duration if duration > 0 else 0,
        "avg_latency": duration / num_files if num_files > 0 else 0
    }


def print_table(records):
    """
    Mencetak tabel metrik terminal format terstandarisasi laporan.
    """
    header = "| Threads Loader | Workers CPU | Jumlah File | Waktu (s) | Throughput (file/s) | Avg Latency (s) |"
    separator = "|" + "-" * 16 + "|" + "-" * 13 + "|" + "-" * 13 + "|" + "-" * 11 + "|" + "-" * 21 + "|" + "-" * 17 + "|"
    print("\n" + "=" * 97)
    print("HASIL EVALUASI METRIK PIPELINE")
    print("=" * 97)
    print(header)
    print(separator)
    for r in records:
        tl_str = str(r["threads_loader"]).center(16)
        wc_str = str(r["workers_cpu"]).center(13)
        jf_str = str(r["jumlah_file"]).center(13)
        w_str = f"{r['waktu']:.4f}".center(11)
        tp_str = f"{r['throughput']:.4f}".center(21)
        lat_str = f"{r['avg_latency']:.4f}".center(17)
        print(f"|{tl_str}|{wc_str}|{jf_str}|{w_str}|{tp_str}|{lat_str}|")
    print(separator + "\n")


def plot_benchmark_results(configs_results, serial_result, output_image="results.png"):
    """
    Membuat grafik komparasi performa (Waktu, Throughput, Speedup) dengan Matplotlib.
    """
    labels = ["Serial\n(1T/1P)"] + [
        f"L={c['threads_loader']}\nW={c['workers_cpu']}" for c in configs_results
    ]
    durations = [serial_result["duration"]] + [c["waktu"] for c in configs_results]
    throughputs = [serial_result["throughput"]] + [c["throughput"] for c in configs_results]
    speedups = [1.0] + [serial_result["duration"] / c["waktu"] for c in configs_results]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Benchmark Evaluasi Hybrid Pipeline (Tugas 4)", fontsize=14, fontweight="bold")
    colors = ["#7f7f7f", "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    bars1 = axes[0].bar(labels, durations, color=colors[:len(labels)], edgecolor="black", alpha=0.85)
    axes[0].set_title("Waktu Eksekusi (detik) - Lower is better")
    axes[0].set_ylabel("Waktu (s)")
    axes[0].grid(axis="y", linestyle="--", alpha=0.7)
    for bar in bars1:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width() / 2.0, yval + 0.05, f"{yval:.2f}s", ha="center", va="bottom", fontsize=9)

    bars2 = axes[1].bar(labels, throughputs, color=colors[:len(labels)], edgecolor="black", alpha=0.85)
    axes[1].set_title("Throughput (file/s) - Higher is better")
    axes[1].set_ylabel("File / detik")
    axes[1].grid(axis="y", linestyle="--", alpha=0.7)
    for bar in bars2:
        yval = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width() / 2.0, yval + 0.1, f"{yval:.2f}", ha="center", va="bottom", fontsize=9)

    bars3 = axes[2].bar(labels, speedups, color=colors[:len(labels)], edgecolor="black", alpha=0.85)
    axes[2].axhline(1.0, color="red", linestyle="--", linewidth=1.2, label="Baseline (1.0x)")
    axes[2].set_title("Speedup vs Baseline - Higher is better")
    axes[2].set_ylabel("Speedup Multiplier (x)")
    axes[2].grid(axis="y", linestyle="--", alpha=0.7)
    axes[2].legend(loc="upper left")
    for bar in bars3:
        yval = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width() / 2.0, yval + 0.03, f"{yval:.2f}x", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    print(f"[Grafik] Visualisasi grafik berhasil disimpan ke: {output_image}")


def main():
    parser = argparse.ArgumentParser(description="Hybrid Pipeline: I/O Loader Threads + Multi-Process CPU Workers")
    parser.add_argument("--input", default="dataset/train.csv", help="Path file CSV input (default: dataset/train.csv)")
    parser.add_argument("--parts", type=int, default=50, help="Jumlah file part (default: 50)")
    parser.add_argument("--loader-threads", type=int, default=4, help="Jumlah thread loader (default: 4)")
    parser.add_argument("--cpu-workers", type=int, default=4, help="Jumlah process CPU worker (default: 4)")
    parser.add_argument("--queue-size", type=int, default=10, help="Maxsize queue untuk backpressure (default: 10)")
    parser.add_argument("--output-dir", default="dataset_parts", help="Folder output part files (default: dataset_parts)")
    parser.add_argument("--run-all-benchmarks", action="store_true", help="Jalankan semua 4 konfigurasi praktikum dan buat grafik")

    args = parser.parse_args()

    input_csv = args.input
    if not os.path.exists(input_csv):
        for candidate in ["dataset/train.csv", "train.csv"]:
            if os.path.exists(candidate):
                input_csv = candidate
                break

    print(f"Input CSV       : {input_csv}")
    print(f"Jumlah Parts    : {args.parts}")
    print(f"Output Directory: {args.output_dir}")

    # Stage 0: Data Preparation
    print("\n[Stage 0] Mempersiapkan data dan membagi ke file parts...")
    part_paths = split_csv_into_files(input_csv, args.output_dir, args.parts)
    print(f"[Stage 0] Berhasil membuat {len(part_paths)} part files di folder '{args.output_dir}'.")

    if args.run_all_benchmarks:
        print("\n" + "=" * 80)
        print("MEMULAI RUN SEMUA 4 KONFIGURASI BENCHMARK + SERIAL BASELINE")
        print("=" * 80)

        print("\n[*] Menjalankan Serial Baseline...")
        ser_res = run_serial(part_paths)
        print(f"    Selesai dalam {ser_res['duration']:.4f}s | Throughput: {ser_res['throughput']:.2f} file/s")

        configs = [
            {"threads_loader": 1, "workers_cpu": 1},
            {"threads_loader": 2, "workers_cpu": 2},
            {"threads_loader": 4, "workers_cpu": 4},
            {"threads_loader": 8, "workers_cpu": 4},
        ]

        table_records = []
        for cfg in configs:
            tl = cfg["threads_loader"]
            cw = cfg["workers_cpu"]
            print(f"\n[*] Menjalankan Konfigurasi: Loader Threads = {tl}, CPU Workers = {cw}, Queue = {args.queue_size}...")
            res = run_hybrid_pipeline(part_paths, tl, cw, args.queue_size)
            print(f"    Selesai dalam {res['duration']:.4f}s | Throughput: {res['throughput']:.2f} file/s")

            rec = {
                "threads_loader": tl,
                "workers_cpu": cw,
                "jumlah_file": args.parts,
                "waktu": res["duration"],
                "throughput": res["throughput"],
                "avg_latency": res["avg_latency"]
            }
            table_records.append(rec)

        print_table(table_records)
        plot_benchmark_results(table_records, ser_res, output_image="results.png")

    else:
        print(f"\n[*] Menjalankan Hybrid Pipeline (Threads: {args.loader_threads}, Workers: {args.cpu_workers}, Queue: {args.queue_size})...")
        res = run_hybrid_pipeline(part_paths, args.loader_threads, args.cpu_workers, args.queue_size)

        rec = {
            "threads_loader": args.loader_threads,
            "workers_cpu": args.cpu_workers,
            "jumlah_file": args.parts,
            "waktu": res["duration"],
            "throughput": res["throughput"],
            "avg_latency": res["avg_latency"]
        }

        print_table([rec])
        print("Detail Agregasi:")
        print(f"- Total Files   : {res['total_files']}")
        print(f"- Total SMS     : {res['total_sms']}")
        print(f"- Spam Count    : {res['spam_count']}")
        print(f"- Ham Count     : {res['ham_count']}")
        print(f"- Total Words   : {res['total_words']}")
        print(f"- Total Chars   : {res['total_chars']}")
        print(f"- Keyword Hits  : {res['keyword_hits']}")


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("TUGAS 4 - HYBRID PIPELINE")
    print("Nama  : Raka Restu Saputra")
    print("NPM   : 247006111172")
    print("Kelas : F")
    print("=" * 60)
    main()