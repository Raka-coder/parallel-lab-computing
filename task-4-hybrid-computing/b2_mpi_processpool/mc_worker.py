"""
mc_worker.py -- fungsi worker untuk B2, sengaja dipisah dari skrip MPI.

Alasan (bagian dari perbaikan bug): proses anak ProcessPool (metode 'spawn')
meng-impor ulang modul utama. Jika modul utama meng-import mpi4py di tingkat
atas, SETIAP proses anak ikut menjalankan MPI_Init -> error/hang. Dengan
memisahkan fungsi worker ke modul ini (tanpa mpi4py), anak proses tetap bersih.
"""
import random


def mc_pi_task(args):
    """Monte Carlo: hitung titik yang jatuh di dalam seperempat lingkaran.
    args = (seed, n_samples). CPU-bound murni (Python loop, menahan GIL)."""
    seed, n = args
    rnd = random.Random(seed)
    inside = 0
    for _ in range(n):
        x = rnd.random()
        y = rnd.random()
        if x * x + y * y <= 1.0:
            inside += 1
    return inside
