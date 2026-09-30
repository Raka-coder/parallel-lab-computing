"""make_diagram_c.py -- diagram arsitektur Bagian C (kasus 1: fraud detection e-wallet real-time).

Hasil disimpan di ../docs/figs/diagram_c_fraud_hybrid.png.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(16, 9.6))
ax.set_xlim(0, 160); ax.set_ylim(0, 96); ax.axis("off")

def box(x, y, w, h, text, fc, ec="#333", fs=9, bold=False, lw=1.3, ls="-", tc="#111", va="center"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
                       fc=fc, ec=ec, lw=lw, ls=ls)
    ax.add_patch(p)
    ax.text(x + w / 2, y + (h / 2 if va == "center" else h - 1.6), text, ha="center", va=va if va == "center" else "top",
            fontsize=fs, fontweight="bold" if bold else "normal", color=tc, linespacing=1.25)

def arrow(x1, y1, x2, y2, text=None, c="#333", rad=0.0, ty=1.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
                                 lw=1.5, color=c, connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + ty, text, ha="center", fontsize=8, color=c, style="italic")

ax.text(80, 93.5, "Arsitektur Hybrid Computing: Deteksi Fraud Transaksi E-Wallet Real-Time",
        ha="center", fontsize=15, fontweight="bold")

# ---------- LEVEL 3: inter-node ----------
box(29, 26, 96, 62, "", "#EAF1FB", ec="#2F5FA8", lw=2, ls="--")
ax.text(31, 86, "LEVEL 3 - INTER-NODE (cluster, distributed memory, message passing: Kafka + Ray/Kubernetes)",
        fontsize=10, fontweight="bold", color="#2F5FA8", va="top")

# sumber & ingest (network-bound)
box(2, 62, 22, 12, "Aplikasi e-wallet\n(ribuan TPS)\n[network-bound]", "#F4F4F4", fs=9)
box(2, 44, 22, 12, "API Gateway\n(gRPC / REST)\n[network-bound]", "#F4F4F4", fs=9)
box(2, 28, 22, 10, "Kafka topic\n(partisi per user_id)\n[network-bound]", "#FFE9C7", fs=9)
arrow(13, 62, 13, 56); arrow(13, 44, 13, 38)
arrow(24, 33, 32, 33)
ax.text(25.3, 35.3, "partisi", fontsize=7.5, style="italic")

# tiga node
for i, (nx, name) in enumerate([(33, "Node 1"), (33 + 30, "Node 2"), (33 + 60, "Node N")]):
    pass

# Node 1 diperinci
box(32, 30, 32, 50, "", "#F3FBF3", ec="#3A8A3A", lw=1.8)
ax.text(33, 78.6, "Node 1 - LEVEL 2: INTRA-NODE\n(shared memory, ProcessPool)", fontsize=8, fontweight="bold",
        color="#2D6E2D", va="top")
for j, y in enumerate([57, 44]):
    box(34, y, 28, 11, "", "#FFFFFF", ec="#3A8A3A", lw=1.2)
    ax.text(48, y + 9.7, f"Proses worker P{j+1}\n(feature + inferensi) [CPU-bound]", fontsize=7.6, ha="center", va="top")
    box(35.2, y + 0.9, 12.3, 4.2, "Thread I/O:\nRedis feature", "#FDECEC", ec="#B33", fs=6.6)
    box(48.8, y + 0.9, 12.3, 4.2, "Thread I/O:\ntulis log", "#FDECEC", ec="#B33", fs=6.6)
ax.text(48, 40.4, "... P_k (k = jumlah core)", ha="center", fontsize=7.6)
box(34, 31.5, 28, 5.5, "LEVEL 1: THREAD (I/O, GIL dilepas)", "#FDECEC", ec="#B33", fs=7, bold=True)

# Node 2 dan N (diringkas)
box(67, 50, 26, 30, "Node 2\nProcessPool + thread I/O\n(struktur sama)", "#F3FBF3", ec="#3A8A3A", fs=9)
box(96, 50, 26, 30, "Node N\nProcessPool + thread I/O\n(struktur sama)", "#F3FBF3", ec="#3A8A3A", fs=9)
ax.text(94.5, 66, "...", fontsize=16, ha="center")

# feature store + model registry di dalam cluster
box(67, 30, 55, 14, "Feature store & cache terdistribusi (Redis Cluster)\nprofil user, velocity 1 mnt/1 jam, blacklist device\n[I/O-bound, in-memory]", "#FDECEC", ec="#B33", fs=8.4)
arrow(78, 50, 78, 44); arrow(108, 50, 108, 44)
arrow(64, 63, 67, 63); arrow(64, 37, 67, 37)
ax.text(66, 27.3, "Sinkronisasi antar-node: MPI/gRPC (allreduce metrik, broadcast model)", fontsize=8, style="italic", color="#2F5FA8")

# keluaran
box(132, 62, 26, 12, "Decision service\nAPPROVE / REVIEW / BLOCK\n(latensi < 100 ms)", "#E6F4E6", fs=9)
box(132, 44, 26, 12, "Cassandra / PostgreSQL\n(audit log)\n[I/O-bound]", "#F4F4F4", fs=9)
box(132, 28, 26, 10, "Alert analis fraud\n(Kafka -> dashboard)\n[network-bound]", "#F4F4F4", fs=9)
arrow(122, 70, 132, 68); arrow(145, 62, 145, 56); arrow(145, 44, 145, 38)

# ---------- jalur batch ----------
box(2, 2, 26, 18, "Data lake (Parquet)\nhistori transaksi +\nlabel chargeback\n[I/O-bound]", "#F4F4F4", fs=8.6)
box(38, 2, 50, 18, "Pelatihan ulang terjadwal (batch): Spark / Ray + GPU\nfeature engineering (CPU-bound, shuffle = network-bound)\ntraining XGBoost/GNN multi-node (allreduce)", "#EFE6FA", ec="#6A3FA0", fs=8.6)
box(98, 2, 26, 18, "Model registry\n(MLflow)\nversi model + rollout", "#F4F4F4", fs=8.6)
box(132, 2, 26, 18, "Monitoring\nPrometheus + Grafana\n(latensi p99, drift)", "#F4F4F4", fs=8.6)
arrow(28, 11, 38, 11); arrow(88, 11, 98, 11)
arrow(111, 20, 111, 26.4, "deploy model baru", c="#6A3FA0", ty=-0.3)
arrow(124, 11, 132, 11)
ax.text(80, 22.3, "JALUR BATCH (offline)", fontsize=9, fontweight="bold", color="#6A3FA0", ha="center")

OUT = Path(__file__).resolve().parent.parent / "docs" / "figs" / "diagram_c_fraud_hybrid.png"
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="white")
print(f"ok -> {OUT}")
