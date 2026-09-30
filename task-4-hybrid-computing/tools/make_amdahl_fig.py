"""Grafik Hukum Amdahl untuk A = 2 (bagian serial s = 7%).

Hasil disimpan di ../docs/figs/amdahl_A2.png relatif terhadap file ini.
Jalankan dari mana saja:  python tools/make_amdahl_fig.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
OUT = BASE_DIR.parent / "docs" / "figs" / "amdahl_A2.png"

s = 0.07
S = lambda n: 1 / (s + (1 - s) / n)
ns = list(range(1, 257))
fig, ax = plt.subplots(figsize=(7.5, 4))
ax.plot(ns, [S(n) for n in ns], label="Speedup Amdahl (s = 7%)")
ax.plot(ns, ns, "k--", lw=1, label="Speedup linear (ideal)")
ax.axhline(1 / s, color="r", ls=":", label=f"Batas maksimum 1/s = {1/s:.2f}")
for n in (32, 128):
    ax.scatter([n], [S(n)], zorder=5)
    ax.annotate(f"n={n}: S={S(n):.2f}", (n, S(n)), textcoords="offset points", xytext=(6, -14))
ax.set(xlabel="Jumlah worker (n)", ylabel="Speedup", ylim=(0, 40), xlim=(0, 256),
       title="Hukum Amdahl untuk A = 2 (bagian serial 7%)")
ax.grid(alpha=.3); ax.legend()
fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=170)
print(f"ok -> {OUT}")
