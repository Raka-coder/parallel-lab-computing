import time
import random
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


def io_task(i, sec):
    time.sleep(sec)
    return i


def io_task_unpack(job):
    return io_task(*job)


def cpu_task(n, iters=10**6):
    s = 0
    for i in range(iters):
        s += (i * n) % 7
    return s


def run_serial_io(jobs):
    start = time.perf_counter()
    for i, sec in jobs:
        io_task(i, sec)
    return time.perf_counter() - start


def run_threads_io(jobs, workers):
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(io_task_unpack, jobs))
    return time.perf_counter() - start


def run_processes_io(jobs, workers):
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        list(ex.map(io_task_unpack, jobs))
    return time.perf_counter() - start


def run_serial_cpu(numbers):
    start = time.perf_counter()
    for n in numbers:
        cpu_task(n)
    return time.perf_counter() - start


def run_threads_cpu(numbers, workers):
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(cpu_task, numbers))
    return time.perf_counter() - start


def run_processes_cpu(numbers, workers):
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        list(ex.map(cpu_task, numbers))
    return time.perf_counter() - start


def show_plots(data):
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

    categories = ["I/O-bound", "CPU-bound"]
    x = [0, 1]
    width = 0.25

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    serial_times = [data["io"]["serial"], data["cpu"]["serial"]]
    thread_times = [data["io"]["threads"], data["cpu"]["threads"]]
    process_times = [data["io"]["processes"], data["cpu"]["processes"]]

    x_serial = [i - width for i in x]
    x_threads = [i for i in x]
    x_proc = [i + width for i in x]

    b1 = ax1.bar(x_serial, serial_times, width, label="Serial", color="#e74c3c", edgecolor="black", linewidth=1.0)
    b2 = ax1.bar(x_threads, thread_times, width, label="Threads (4 Workers)", color="#3498db", edgecolor="black", linewidth=1.0)
    b3 = ax1.bar(x_proc, process_times, width, label="Processes (4 Workers)", color="#2ecc71", edgecolor="black", linewidth=1.0)

    ax1.set_title("Perbandingan Waktu Eksekusi (detik)", fontsize=12, fontweight="bold", pad=10)
    ax1.set_ylabel("Waktu (detik)", fontsize=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, fontsize=11, fontweight="bold")
    ax1.legend(frameon=True)
    ax1.grid(axis="y", linestyle="--", alpha=0.7)

    for bars in [b1, b2, b3]:
        for bar in bars:
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

    speedup_threads = [data["io"]["speedup_threads"], data["cpu"]["speedup_threads"]]
    speedup_proc = [data["io"]["speedup_processes"], data["cpu"]["speedup_processes"]]

    w2 = 0.35
    x_s_threads = [i - w2 / 2 for i in x]
    x_s_proc = [i + w2 / 2 for i in x]

    sb1 = ax2.bar(x_s_threads, speedup_threads, w2, label="Threads Speedup", color="#3498db", edgecolor="black", linewidth=1.0)
    sb2 = ax2.bar(x_s_proc, speedup_proc, w2, label="Processes Speedup", color="#2ecc71", edgecolor="black", linewidth=1.0)

    ax2.axhline(1.0, color="#7f8c8d", linestyle="--", linewidth=1.5, label="Baseline Serial (1.0x)")

    ax2.set_title("Perbandingan Speedup (x lipat terhadap Serial)", fontsize=12, fontweight="bold", pad=10)
    ax2.set_ylabel("Speedup (x)", fontsize=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories, fontsize=11, fontweight="bold")
    ax2.legend(frameon=True)
    ax2.grid(axis="y", linestyle="--", alpha=0.7)

    for bars in [sb1, sb2]:
        for bar in bars:
            h = bar.get_height()
            ax2.annotate(
                f"{h:.2f}x",
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold"
            )

    plt.suptitle("Tugas 3: Evaluasi Perbandingan Threads vs Processes (4 Workers)", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("TUGAS 3 - PERBANDINGAN THREADS VS TASKS")
    print("Nama  : Raka Restu Saputra")
    print("NPM   : 247006111172")
    print("Kelas : F")
    print("=" * 60)

    WORKERS = 4

    random.seed(42)
    jobs = [(i, random.uniform(0.5, 2.0)) for i in range(10)]

    print("\n[1/2] Menjalankan benchmark I/O-bound...")
    io_serial = run_serial_io(jobs)
    io_threads = run_threads_io(jobs, WORKERS)
    io_processes = run_processes_io(jobs, WORKERS)

    numbers = list(range(1, 9))

    print("[2/2] Menjalankan benchmark CPU-bound...")
    cpu_serial = run_serial_cpu(numbers)
    cpu_threads = run_threads_cpu(numbers, WORKERS)
    cpu_processes = run_processes_cpu(numbers, WORKERS)

    summary_data = {
        "io": {
            "serial": io_serial,
            "threads": io_threads,
            "processes": io_processes,
            "speedup_threads": io_serial / io_threads,
            "speedup_processes": io_serial / io_processes,
        },
        "cpu": {
            "serial": cpu_serial,
            "threads": cpu_threads,
            "processes": cpu_processes,
            "speedup_threads": cpu_serial / cpu_threads,
            "speedup_processes": cpu_serial / cpu_processes,
        }
    }

    print()
    print("=" * 100)
    print("TABEL HASIL PERBANDINGAN")
    print("=" * 100)
    print(f"{'Jenis Aplikasi':<18} {'Serial (s)':<12} {'Threads (s)':<12} "
          f"{'Processes (s)':<15} {'Speedup Threads':<17} {'Speedup Processes':<17}")
    print("-" * 100)
    print(f"{'I/O-bound':<18} {io_serial:<12.4f} {io_threads:<12.4f} "
          f"{io_processes:<15.4f} {summary_data['io']['speedup_threads']:<17.2f} {summary_data['io']['speedup_processes']:<17.2f}")
    print(f"{'CPU-bound':<18} {cpu_serial:<12.4f} {cpu_threads:<12.4f} "
          f"{cpu_processes:<15.4f} {summary_data['cpu']['speedup_threads']:<17.2f} {summary_data['cpu']['speedup_processes']:<17.2f}")
    print("=" * 100)

    print()
    print("=" * 70)
    print("  MENAMPILKAN GRAFIK (matplotlib)")
    print("=" * 70)
    show_plots(summary_data)

    print()
    print("=" * 100)
    print("SELESAI")
    print("=" * 100)