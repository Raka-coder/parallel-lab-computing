# Tugas Hybrid Computing (A = 2)

Raka Restu Saputra — 247006111172 — Kelas F.
Tiga penugasan hybrid (I/O + CPU, antar-proses + dalam-proses),
masing-masing di direktorinya sendiri dengan README + hasil.

## Struktur

```text
task-4-hybrid-computing/
├── README.md                  ← file ini
├── requirements.txt
├── b1_hybrid_pipeline/        ← B1: Threads + ProcessPool + backpressure
│   ├── README.md
│   ├── make_dataset.py
│   ├── hybrid_pipeline.py
│   ├── run_b1_grid.py
│   ├── data/                  ← 120 file sintetis Zipf
│   └── results/               ← b1_raw.csv, b1_summary.csv/md, b1_throughput.png
├── b2_mpi_processpool/        ← B2: MPI antar-rank + ProcessPool intra-rank (π Monte Carlo)
│   ├── README.md
│   ├── mc_worker.py
│   ├── mpi_pi_processpool.py
│   ├── run_b2_grid.py
│   └── results/               ← b2_summary.csv, b2_scaling.png
├── b3_wordcount_mpi/          ← B3: MPI word count (ThreadPool vs ProcessPool)
│   ├── README.md
│   ├── download_corpus.py
│   ├── wordcount_mpi.py
│   └── corpus/                ← 40 e-book Gutenberg
├── tools/                     ← generator gambar pendukung
│   ├── make_amdahl_fig.py
│   └── make_diagram_c.py
└── docs/figs/                 ← amdahl_A2.png, diagram_c_fraud_hybrid.png
```

Detail tiap penugasan ada di README masing-masing folder:
[B1](b1_hybrid_pipeline/README.md) ·
[B2](b2_mpi_processpool/README.md) ·
[B3](b3_wordcount_mpi/README.md).

## Prasyarat

```bash
pip install -r requirements.txt
# B2/B3 juga butuh: MPI runtime (MS-MPI di Windows / OpenMPI di Linux)
# + modul mpi4py (sudah termasuk di requirements.txt)
```

## Urutan pakai

```bash
# B1 — dataset, satu run, lalu full grid
python b1_hybrid_pipeline/make_dataset.py --n 120
python b1_hybrid_pipeline/hybrid_pipeline.py --threads 2 --workers 4 --qmax 4
python b1_hybrid_pipeline/run_b1_grid.py --repeat 3

# B2 — butuh MPI + mpi4py
python b2_mpi_processpool/run_b2_grid.py
# atau override launcher MPI:
python b2_mpi_processpool/run_b2_grid.py --mpiexec "mpiexec --allow-run-as-root --oversubscribe"

# B3 — unduh korpus sekali saja, lalu run MPI
python b3_wordcount_mpi/download_corpus.py
mpiexec -n 4 python b3_wordcount_mpi/wordcount_mpi.py --workers 4 --repeat 3

# Gambar pendukung (opsional, hasil ke docs/figs/)
python tools/make_amdahl_fig.py
python tools/make_diagram_c.py
```

> Semua skrip memakai path relatif terhadap lokasinya sendiri,
> jadi bisa dijalankan dari root `task-4-hybrid-computing/` maupun
> dari dalam subdirektorinya. Contoh Colab/Windows ada di README B2/B3.

## Catatan refactor

- File dikelompokkan per penugasan (`b1_*`, `b2_*`, `b3_*`); dataset,
  korpus, dan hasil (`results/`) ikut pindah ke folder masing-masing.
- `run_b1_grid.py`: identitas dicetak di awal (sebelumnya di akhir dan
  tidak terlihat), path subprocess/output absolut berbasis `BASE_DIR`.
- `run_b2_grid.py`: path skrip MPI + output hasil berbasis `BASE_DIR`,
  argumen `--out-dir` baru.
- `hybrid_pipeline.py`: sentinel antrean diganti `object()` (sebelumnya
  `None` yang rawan tabrakan), default `--data` menunjuk `data/` sebelah skrip.
- `mpi_pi_processpool.py`: `sys.path` disisipi direktori skrip agar
  `mc_worker` selalu ketemu; `wordcount_mpi.py` / `download_corpus.py` /
  `make_dataset.py`: default output menunjuk ke folder sebelah skrip.
- `tools/`: output gambar diarahkan ke `docs/figs/`.
