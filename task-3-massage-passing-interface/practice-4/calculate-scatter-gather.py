# Nama: Raka Restu Saputra
# NPM: 247006111172
# Kelas: F
# Mata Kuliah: Komputasi Paralel dan Terdistribusi
# Tugas 4 - Praktikum 4: Hitung Jumlah dengan Scatter + Gather (Bonus)

from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if size != 4:
    if rank == 0:
        print("Harap jalankan dengan -n 4")
    raise SystemExit

if rank == 0:
    print("=" * 60)
    print("TUGAS 4 - PRAKTIKUM 4: HITUNG JUMLAH (SCATTER + GATHER)")
    print("Nama  : Raka Restu Saputra")
    print("NPM   : 247006111172")
    print("Kelas : F")
    print("=" * 60)
    print()

comm.Barrier()

if rank == 0:
    data = [5, 10, 15, 20]
    print(f"[Rank {rank}] [TAHAP 1] Menyiapkan data: {data}")
else:
    data = None
    print(f"[Rank {rank}] [TAHAP 1] Menunggu data dari rank 0...")

comm.Barrier()
if rank == 0:
    print()

x = comm.scatter(data, root=0)
print(f"[Rank {rank}] [TAHAP 2 - SCATTER] Menerima x = {x}")

comm.Barrier()
if rank == 0:
    print()

local = 2 * x
print(f"[Rank {rank}] [TAHAP 3 - KOMPUTASI] 2 x {x} = {local}")

comm.Barrier()
if rank == 0:
    print()

kumpul = comm.gather(local, root=0)

if rank == 0:
    print(f"[Rank 0] [TAHAP 4 - GATHER] Hasil dari semua rank:")
    for i, val in enumerate(kumpul):
        print(f"          - Dari rank {i}: {val}")

comm.Barrier()
if rank == 0:
    print()

if rank == 0:
    total = sum(kumpul)
    print(f"[Rank 0] [TAHAP 5 - AGREGASI] Total = {total}")
    print()
    print("=" * 60)
    print("HASIL AKHIR")
    print("=" * 60)
    print(f"Data awal     : {data}")
    print(f"*2 per-proses : {kumpul}")
    print(f"Total akhir   : {total}")

    # Validasi manual
    expected = sum(2 * d for d in data)
    status = "COCOK" if total == expected else "TIDAK COCOK"
    print(f"Validasi      : {expected} -> {status}")
    print("=" * 60)