# Nama: Raka Restu Saputra
# NPM: 247006111172
# Kelas: F
# Mata Kuliah: Komputasi Paralel dan Terdistribusi

import sys
import time
from concurrent.futures import ProcessPoolExecutor


def heavy(n, iters=10**6):
    s = 0
    for i in range(iters):
        s += (i * n) % 7
    return s


def run_serial(numbers):
    start = time.perf_counter()
    results = [heavy(n) for n in numbers]
    end = time.perf_counter()
    return end - start, results


def run_parallel(numbers, workers):
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(heavy, numbers))
    end = time.perf_counter()
    return end - start, results


def show_plots(results):
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

    labels = [r["label"] for r in results]
    workers = [r["workers"] for r in results]
    times = [r["time"] for r in results]
    speedups = [r["speedup"] for r in results]
    efficiencies = [r["efficiency"] * 100 for r in results]

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))

    colors = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6"]

    bars1 = ax1.bar(labels, times, color=colors, width=0.5, edgecolor="black", linewidth=1.2)
    ax1.set_title("Waktu Eksekusi (detik)", fontsize=12, fontweight="bold", pad=10)
    ax1.set_ylabel("Waktu (detik)", fontsize=10)
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
            fontweight="bold",
        )

    ax2.plot(labels, speedups, marker="o", linewidth=2.5, markersize=8, color="#2980b9", label="Speedup Aktual")
    ideal_speedups = [w for w in workers]
    ax2.plot(labels, ideal_speedups, linestyle="--", color="#e67e22", linewidth=2, label="Speedup Ideal (Linear)")
    ax2.set_title("Analisis Speedup", fontsize=12, fontweight="bold", pad=10)
    ax2.set_ylabel("Speedup (x)", fontsize=10)
    ax2.grid(True, linestyle="--", alpha=0.7)
    ax2.legend()
    for i, s in enumerate(speedups):
        ax2.annotate(
            f"{s:.2f}x",
            xy=(labels[i], s),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            fontweight="bold",
        )

    bars3 = ax3.bar(labels, efficiencies, color=colors, width=0.5, edgecolor="black", linewidth=1.2)
    ax3.set_title("Efisiensi Paralel (%)", fontsize=12, fontweight="bold", pad=10)
    ax3.set_ylabel("Efisiensi (%)", fontsize=10)
    ax3.set_ylim(0, max(max(efficiencies) * 1.15, 115))
    ax3.grid(axis="y", linestyle="--", alpha=0.7)
    for bar in bars3:
        h = bar.get_height()
        ax3.annotate(
            f"{h:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    plt.suptitle("Evaluasi Performa: Task Parallelism (CPU-Bound)", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("TUGAS 2 - TASK PARALLELISM (CPU-BOUND)")
    print("Nama  : Raka Restu Saputra")
    print("NPM   : 247006111172")
    print("Kelas : F")
    print("=" * 60)

    numbers = list(range(1, 9))

    serial_time, _ = run_serial(numbers)

    print(f"\n{'Proses':<10} {'Waktu (s)':<12} {'Speedup':<12} {'Efisiensi':<12}")
    print("-" * 70)
    print(f"{'Serial':<10} {serial_time:<12.4f} {1.0:<12.2f} {'100.00%':<12}")

    benchmark_results = [
        {"label": "Serial (1)", "workers": 1, "time": serial_time, "speedup": 1.0, "efficiency": 1.0}
    ]

    for workers in [2, 4, 8]:
        par_time, _ = run_parallel(numbers, workers)
        speedup = serial_time / par_time
        efficiency = speedup / workers
        benchmark_results.append({
            "label": f"{workers} Workers",
            "workers": workers,
            "time": par_time,
            "speedup": speedup,
            "efficiency": efficiency,
        })
        print(f"{workers:<10} {par_time:<12.4f} {speedup:<12.2f} {efficiency:<12.2%}")

    print("=" * 70)

    print()
    print("=" * 70)
    print("  MENAMPILKAN GRAFIK (matplotlib)")
    print("=" * 70)
    show_plots(benchmark_results)

    print()
    print("=" * 70)
    print("SELESAI")
    print("=" * 70)