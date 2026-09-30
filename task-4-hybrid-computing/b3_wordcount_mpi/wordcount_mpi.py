"""
wordcount_mpi.py -- Praktikum 3 (B3): Global Word Count (MPI + threads/proses)

Modifikasi dari kode asli:
  [MOD-1] dataset dummy diganti teks nyata (folder corpus/, >= 30 file .txt)
  [MOD-2] dua versi pemrosesan di dalam setiap rank:
          (a) ThreadPoolExecutor  (seperti kode asli)
          (b) ProcessPoolExecutor
  [MOD-3] stopwords dibuang (min: dan, yang, di, the, of, and) lalu tampilkan Top-10

Jalankan:  mpiexec -n 4 python wordcount_mpi.py --data corpus --workers 4 --repeat 3
"""
import argparse
import multiprocessing as mp
import re
import statistics
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

WORD_RE = re.compile(r"[a-zA-Z']+")           # tokenisasi (bagian CPU-bound)

# [MOD-3] stopwords: wajib (dan, yang, di, the, of, and) + tambahan umum ID/EN
STOPWORDS = set("""
dan yang di ke dari ini itu untuk dengan pada adalah atau juga tidak akan
the of and to a in that is was he she it his her i you with as for on be at by
had not but this which they are from or have were his my me we so all an
""".split())

NAMA  = "Raka Restu Saputra"
NPM   = "247006111172"
KELAS = "F"


def print_identity():
    """Cetak identitas — hanya dipanggil di rank 0."""
    print("=" * 65)
    print("  B3 - Modifikasi Global Word Count")
    print("=" * 65)
    print(f"  Nama       : {NAMA}")
    print(f"  NPM        : {NPM}")
    print(f"  Kelas      : {KELAS}")
    print("-" * 65)


def count_file(path):
    """Baca file (I/O) + tokenisasi regex (CPU) -> Counter kata, tanpa stopwords."""
    text = Path(path).read_text(encoding="utf-8", errors="ignore").lower()
    text = text.replace("’", "'").replace("‘", "'")
    words = (w.strip("'") for w in WORD_RE.findall(text))
    return Counter(w for w in words if w and len(w) > 1 and w not in STOPWORDS)


def count_threads(files, workers):                     # versi (a)
    total = Counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for c in ex.map(count_file, files):
            total.update(c)
    return total


def count_processes(files, workers):                   # versi (b)
    total = Counter()
    ctx = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as ex:
        for c in ex.map(count_file, files, chunksize=1):
            total.update(c)
    return total


def timed(fn, files, workers, repeat, MPI):
    times = []
    result = None
    for _ in range(repeat):
        MPI.COMM_WORLD.Barrier()
        t0 = MPI.Wtime()
        result = fn(files, workers)
        MPI.COMM_WORLD.Barrier()
        times.append(MPI.Wtime() - t0)
    return statistics.median(times), result


def main():
    try:
        from mpi4py import MPI
    except ImportError:
        print(
            "ERROR: modul 'mpi4py' tidak ditemukan.\n"
            "Di Windows, install dulu Microsoft MPI lalu jalankan:\n"
            '  pip install mpi4py\n'
            "Lalu ulangi:  mpiexec -n 4 python wordcount_mpi.py --data corpus",
            file=sys.stderr,
        )
        sys.exit(1)

    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).resolve().parent / "corpus"))
    ap.add_argument("--workers", type=int, default=4, help="thread/proses per rank")
    ap.add_argument("--repeat", type=int, default=3)
    args = ap.parse_args()

    comm = MPI.COMM_WORLD
    rank, size = comm.Get_rank(), comm.Get_size()

    # ===== Identitas — HANYA rank 0 yang cetak =====
    if rank == 0:
        print_identity()
        print(f"  Jumlah rank MPI : {size}")
        print(f"  Workers/rank    : {args.workers}")
        print(f"  Repeat          : {args.repeat}")
        print("=" * 65)

    chunks = None
    files = []
    if rank == 0:
        data_dir = Path(args.data)
        if not data_dir.is_absolute() and not data_dir.exists():
            data_dir = Path(__file__).resolve().parent / args.data
        files = sorted(str(p) for p in data_dir.glob("*.txt"))
        if not files:
            print(f"ERROR: tidak ada file *.txt di '{data_dir.resolve()}'.", file=sys.stderr)
            print("Pastikan folder corpus/ berisi >= 30 file .txt.", file=sys.stderr)
        elif len(files) < 30:
            print(f"PERINGATAN: hanya {len(files)} file (minimal 30).")
        chunks = [files[i::size] for i in range(size)]

    my_files = comm.scatter(chunks, root=0)

    # Pemanasan: baca semua file sekali agar cache disk adil bagi kedua versi
    for f in my_files:
        Path(f).read_bytes()

    t_thr, c_thr = timed(count_threads, my_files, args.workers, args.repeat, MPI)
    t_prc, c_prc = timed(count_processes, my_files, args.workers, args.repeat, MPI)

    assert c_thr == c_prc, "hasil thread dan proses harus identik"

    all_counts = comm.gather(c_prc, root=0)
    all_times = comm.gather((t_thr, t_prc), root=0)

    # ===== Output — HANYA rank 0 =====
    if rank == 0:
        total = Counter()
        for c in all_counts:
            total.update(c)
        thr = max(t[0] for t in all_times)     # makespan = rank paling lambat
        prc = max(t[1] for t in all_times)

        print()
        print("=" * 65)
        print("  HASIL EKSPERIMEN")
        print("=" * 65)
        print(f"  Rank MPI        : {size}")
        print(f"  Workers/rank    : {args.workers}")
        print(f"  Jumlah file     : {len(files)}")
        print("-" * 65)
        print(f"  ThreadPoolExecutor   : {thr:.3f} s")
        print(f"  ProcessPoolExecutor  : {prc:.3f} s")
        faster = "ProcessPool" if prc < thr else "ThreadPool"
        print(f"  Lebih cepat          : {faster} "
              f"(rasio Thread/Proses = {thr/prc:.2f}x)")
        print("=" * 65)
        print()
        print("  Top 10 kata (stopwords dibuang):")
        print("=" * 65)
        for i, (w, n) in enumerate(total.most_common(10), 1):
            print(f"  {i:2d}. {w:<15} {n}")
        print("=" * 65)


if __name__ == "__main__":
    mp.freeze_support()
    main()