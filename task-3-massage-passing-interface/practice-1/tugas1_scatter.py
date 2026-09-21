# Nama: Raka Restu Saputra
# NPM: 247006111172
# Kelas: F
# Mata Kuliah: Komputasi Paralel dan Terdistribusi
# Tugas 3 - Praktikum 1: Scatter Sederhana (MPI)

from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Pastikan jumlah proses = 4
if size != 4:
    if rank == 0:
        print("Harap jalankan dengan -n 4")
    raise SystemExit

data = [10, 20, 30, 40] if rank == 0 else None
recv = comm.scatter(data, root=0)

print(f"Rank {rank} menerima {recv}")
