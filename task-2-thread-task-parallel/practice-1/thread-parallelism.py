import threading
import time
import random

log_lock = threading.Lock()


def log(message):
    with log_lock:
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        thread_name = threading.current_thread().name
        print(f"[{timestamp}] [{thread_name:<12}] {message}")


def download_file(i, sec):
    log(f"START  unduh File-{i:<2} (durasi {sec:.2f}s)")
    time.sleep(sec)
    log(f"DONE   unduh File-{i:<2} (selesai dalam {sec:.2f}s)")
    return f"File-{i} selesai dalam {sec:.2f}s"


def run_serial(jobs):
    log("=" * 60)
    log("MODE SERIAL — mulai eksekusi")
    log("=" * 60)

    start = time.perf_counter()
    for i, sec in jobs:
        log(f"→ Menjalankan File-{i} secara berurutan")
        download_file(i, sec)
    end = time.perf_counter()

    log("=" * 60)
    log(f"MODE SERIAL — selesai dalam {end - start:.4f}s")
    log("=" * 60)
    return end - start


def run_threads(jobs):
    log("=" * 60)
    log("MODE THREADED — mulai eksekusi")
    log("=" * 60)

    threads = []
    start = time.perf_counter()

    for i, sec in jobs:
        t = threading.Thread(
            target=download_file,
            args=(i, sec),
            name=f"Thread-{i}"
        )
        threads.append(t)
        log(f"→ Membuat & menjalankan {t.name} untuk File-{i}")
        t.start()

    log(f"→ Semua {len(threads)} thread telah dijalankan, menunggu selesai...")

    for t in threads:
        t.join()
        log(f"✓ {t.name} telah selesai (join)")

    end = time.perf_counter()

    log("=" * 60)
    log(f"MODE THREADED — selesai dalam {end - start:.4f}s")
    log("=" * 60)
    return end - start


def show_plots(serial_time, thread_time, jobs, speedup, ideal_speedup):
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

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    modes = ["Serial", "Threaded"]
    times = [serial_time, thread_time]
    colors = ["#e74c3c", "#2ecc71"]

    bars1 = ax1.bar(modes, times, color=colors, width=0.5, edgecolor="black", linewidth=1.2)
    ax1.set_title("Perbandingan Waktu Eksekusi", fontsize=13, fontweight="bold", pad=12)
    ax1.set_ylabel("Waktu (detik)", fontsize=11)
    ax1.grid(axis="y", linestyle="--", alpha=0.7)

    for bar in bars1:
        height = bar.get_height()
        ax1.annotate(
            f"{height:.2f}s",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    categories = ["Baseline (Serial)", "Speedup Aktual", "Speedup Ideal"]
    speedup_values = [1.0, speedup, ideal_speedup]
    speedup_colors = ["#95a5a6", "#3498db", "#9b59b6"]

    bars2 = ax2.bar(categories, speedup_values, color=speedup_colors, width=0.5, edgecolor="black", linewidth=1.2)
    ax2.set_title("Analisis Speedup", fontsize=13, fontweight="bold", pad=12)
    ax2.set_ylabel("Faktor Peningkatan (x)", fontsize=11)
    ax2.grid(axis="y", linestyle="--", alpha=0.7)

    for bar in bars2:
        height = bar.get_height()
        ax2.annotate(
            f"{height:.2f}x",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    plt.suptitle("Evaluasi Performa: Thread Parallelism (I/O-Bound)", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("TUGAS 1 - THREAD PARALLELISM (I/O-BOUND)")
    print("Nama  : Raka Restu Saputra")
    print("NPM   : 247006111172")
    print("Kelas : F")
    print("=" * 60)

    random.seed(42)
    jobs = [(i, random.uniform(0.5, 2.0)) for i in range(10)]

    log(f"Total file yang akan diunduh: {len(jobs)}")
    log("Daftar file & durasi:")
    for i, sec in jobs:
        log(f"   File-{i:<2} → {sec:.2f}s")

    print()
    serial_time = run_serial(jobs)

    print()
    thread_time = run_threads(jobs)

    speedup = serial_time / thread_time
    total_sleep = sum(s for _, s in jobs)
    max_sleep = max(s for _, s in jobs)
    ideal_speedup = total_sleep / max_sleep

    print()
    print("=" * 60)
    print("RINGKASAN HASIL")
    print("=" * 60)
    print(f"{'Mode':<15} {'Jumlah File':<12} {'Waktu (s)':<12} {'Speedup':<10}")
    print("-" * 60)
    print(f"{'Serial':<15} {len(jobs):<12} {serial_time:<12.4f} {1.0:<10.2f}")
    print(f"{'Threaded':<15} {len(jobs):<12} {thread_time:<12.4f} {speedup:<10.2f}")
    print("=" * 60)

    print()
    print("=" * 60)
    print("ANALISIS")
    print("=" * 60)
    print(f"- Total durasi jika dijalankan serial  : {total_sleep:.2f}s")
    print(f"- Durasi file terlama                   : {max_sleep:.2f}s")
    print(f"- Waktu threaded aktual                 : {thread_time:.4f}s")
    print(f"- Speedup aktual                        : {speedup:.2f}x")
    print(f"- Ideal speedup (total/max)             : {ideal_speedup:.2f}x")
    print(f"- Efisiensi speedup                     : {(speedup/ideal_speedup)*100:.2f}%")
    print("=" * 60)

    print()
    print("=" * 70)
    print("  MENAMPILKAN GRAFIK (matplotlib)")
    print("=" * 70)

    show_plots(serial_time, thread_time, jobs, speedup, ideal_speedup)

    print()
    print("=" * 60)
    print("SELESAI")
    print("=" * 60)