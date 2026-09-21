# Nama: Raka Restu Saputra
# NPM: 247006111172
# Kelas: F
# Mata Kuliah: Komputasi Paralel dan Terdistribusi
# Tugas 5 - Praktikum 5: Reduce vs Allreduce (MAX & Rata-Rata Global)

from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# =====================================================================
# HEADER (hanya rank 0)
# =====================================================================
if rank == 0:
    print("=" * 60)
    print("TUGAS 5 - PRAKTIKUM 5: REDUCE VS ALLREDUCE")
    print("Nama  : Raka Restu Saputra")
    print("NPM   : 247006111172")
    print("Kelas : F")
    print("=" * 60)
    print()

comm.Barrier()

# =====================================================================
# BAGIAN A — MAX dengan REDUCE
# =====================================================================
if rank == 0:
    print("--- BAGIAN A: MAX dengan Reduce ---")

my_val = rank * 7 + 3
print(f"[Rank {rank}] my_val = {rank} * 7 + 3 = {my_val}")

max_val = comm.reduce(my_val, op=MPI.MAX, root=0)

if rank == 0:
    print(f"[Rank 0] [REDUCE-MAX] Nilai terbesar = {max_val}")
    print(f"[Rank 0] Proses dengan nilai terbesar biasanya rank terakhir")
    print(f"         (karena fungsi naik terhadap rank).")
    print()

comm.Barrier()

# =====================================================================
# BAGIAN B — Rata-rata global via ALLREDUCE
# =====================================================================
if rank == 0:
    print("--- BAGIAN B: AVG dengan Allreduce ---")

val_for_avg = rank + 1
print(f"[Rank {rank}] val_for_avg = {rank} + 1 = {val_for_avg}")

global_sum = comm.allreduce(val_for_avg, op=MPI.SUM)
global_avg = global_sum / size

print(f"[Rank {rank}] [ALLREDUCE-AVG] sum = {global_sum}, "
      f"avg = {global_avg}")

comm.Barrier()
if rank == 0:
    print()

# =====================================================================
# BAGIAN C — Total 1000 bilangan acak/proses via ALLREDUCE
# =====================================================================
if rank == 0:
    print("--- BAGIAN C: TOTAL 1000 Bilangan Acak/Proses ---")

rng = np.random.default_rng(seed=12345 + rank)
nums = rng.random(1000)
local_sum = float(np.sum(nums))

print(f"[Rank {rank}] local_sum (1000 bilangan) = {local_sum:.6f}")

total_sum = comm.allreduce(local_sum, op=MPI.SUM)

# Semua rank menerima total_sum (karena Allreduce)
print(f"[Rank {rank}] [ALLREDUCE-SUM] Total = {total_sum:.6f}")

comm.Barrier()

# =====================================================================
# RINGKASAN AKHIR (hanya rank 0)
# =====================================================================
if rank == 0:
    print()
    print("=" * 60)
    print("RINGKASAN HASIL")
    print("=" * 60)
    print(f"Bagian A - MAX   : {max_val}")
    print(f"Bagian B - SUM   : {global_sum}")
    print(f"Bagian C - AVG   : {global_avg}")
    print(f"Bagian D - TOTAL : {total_sum:.6f}")
    print(f"Jumlah proses    : {size}")
    print("=" * 60)