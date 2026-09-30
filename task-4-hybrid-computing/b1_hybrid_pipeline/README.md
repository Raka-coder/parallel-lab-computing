# B1 — Hybrid Pipeline (Threads + ProcessPool + Backpressure)

Praktikum 1: pipeline hybrid untuk 120 file teks (`100 + 10*A`, A = 2).

## Arsitektur

```text
[N_LOADER_THREADS] --put--> Queue(maxsize=Q_MAX) --get--> [N_WORKERS dispatcher]
   baca file (I/O)          buffer berbatas (backpressure)   ProcessPool (CPU, bebas GIL)
```

- Loader thread *blocking* di `queue.put()` saat antrean penuh → itulah **backpressure**.
- Tiap dispatcher mengirim 1 tugas ke `ProcessPool` dan menunggu hasilnya,
  sehingga tugas *in-flight* ≤ N_WORKERS.
- Metrik: `total_time_s`, `throughput_fps`, `avg_latency_s`,
  `loader_blocked_s` (total waktu loader terblokir antrean penuh).

## Struktur

| File | Fungsi |
|---|---|
| `make_dataset.py` | Buat 120 file Zipf-sintetis di `data/` |
| `hybrid_pipeline.py` | Satu run pipeline (`--threads/--workers/--qmax/--cpu-iters/--csv`) |
| `run_b1_grid.py` | Grid `{1,2,4} loader × {1,2,4,cores} worker × {4,32} Q_MAX`, median dari `--repeat` |
| `data/` | Dataset (120 × ±30.000 kata, ±24 MB) |
| `results/` | `b1_raw.csv`, `b1_summary.csv`, `b1_summary.md`, `b1_throughput.png` |

## Cara run

```bash
# dari root task-4-hybrid-computing ATAU dari dalam folder ini
python b1_hybrid_pipeline/make_dataset.py --n 120
python b1_hybrid_pipeline/hybrid_pipeline.py --threads 2 --workers 4 --qmax 4
python b1_hybrid_pipeline/run_b1_grid.py --repeat 3
```

Semua default path (`--data`, `--raw`, output) sudah relatif terhadap
lokasi skrip, jadi aman dijalankan dari direktori mana pun.

## Hasil (ringkas, median 3 run, 8-core)

- Throughput naik hampir linier terhadap N_WORKERS (11.5 → ±61 file/s),
  nyaris tidak tergantung jumlah loader thread maupun Q_MAX.
- Q_MAX kecil (4) → latensi rata-rata kecil (±0.2 s), `loader_blocked_s` besar.
- Q_MAX besar (32) → latensi naik (±0.5–2.6 s), blokir loader turun.
- Kesimpulan: tahap CPU (ProcessPool) adalah bottleneck; tambah worker,
  bukan loader/buffer, yang menaikkan throughput.

Lihat tabel lengkap di [`results/b1_summary.md`](results/b1_summary.md)
dan grafik [`results/b1_throughput.png`](results/b1_throughput.png).
