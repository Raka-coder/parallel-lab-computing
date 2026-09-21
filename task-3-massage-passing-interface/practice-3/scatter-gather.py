# Nama: Raka Restu Saputra
# NPM: 247006111172
# Kelas: F
# Mata Kuliah: Komputasi Paralel dan Terdistribusi
# Tugas 3 - Praktikum 3: Scatter + Gather (Kombinasi)

from mpi4py import MPI
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if size != 4:
    if rank == 0:
        print("Harap jalankan dengan -n 4")
    raise SystemExit

if rank == 0:
    print("=" * 60)
    print("TUGAS 3 - PRAKTIKUM 3: SCATTER + GATHER (KOMBINASI)")
    print("Nama  : Raka Restu Saputra")
    print("NPM   : 247006111172")
    print("Kelas : F")
    print("=" * 60)
    print()

comm.Barrier()

if rank == 0:
    data = [1, 2, 3, 4]
    print(f"[Rank {rank}] [TAHAP 1] Menyiapkan data: {data}")
else:
    data = None
    print(f"[Rank {rank}] [TAHAP 1] Menunggu data dari rank 0...")

comm.Barrier()
if rank == 0:
    print()
comm.Barrier()

x = comm.scatter(data, root=0)
print(f"[Rank {rank}] [TAHAP 2 - SCATTER] Menerima x = {x}")

comm.Barrier()
if rank == 0:
    print()
comm.Barrier()

y = x * x
print(f"[Rank {rank}] [TAHAP 3 - KOMPUTASI] {x} x {x} = {y}")

comm.Barrier()
if rank == 0:
    print()
comm.Barrier()

hasil = comm.gather(y, root=0)

if rank == 0:
    print(f"[Rank 0] [TAHAP 4 - GATHER] Menerima hasil dari semua rank:")
    for i, val in enumerate(hasil):
        print(f"          - Dari rank {i}: {val}")

comm.Barrier()
if rank == 0:
    print()
comm.Barrier()

if rank == 0:
    print("=" * 60)
    print("HASIL AKHIR")
    print("=" * 60)
    print(f"Input  : {data}")
    print(f"Output : {hasil}")
    print("=" * 60)