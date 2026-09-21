# Nama: Raka Restu Saputra
# NPM: 247006111172
# Kelas: F
# Mata Kuliah: Komputasi Paralel dan Terdistribusi

from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

if rank == 0:
    print("=" * 50)
    print("TUGAS 3 - PRAKTIKUM 2: GATHER SEDERHANA (MPI)")
    print("Nama  : Raka Restu Saputra")
    print("NPM   : 247006111172")
    print("Kelas : F")
    print("=" * 50)
    print()

send_val = rank * 5
gathered = comm.gather(send_val, root=0)

if rank == 0:
    print(f"Hasil gather di rank 0: {gathered}")
