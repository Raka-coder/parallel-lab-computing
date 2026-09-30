"""
make_dataset.py  -- Pembuat dataset untuk B1 (Praktikum 1).

CATATAN: skrip "Cara RUN" asli di slide 19 tidak tersedia di soal, jadi ini
adalah pengganti setara: membuat 100 + 10*A file .txt berisi teks acak
(distribusi kata mirip bahasa alami / Zipf) agar tokenisasi + hitung frekuensi
menjadi pekerjaan CPU yang nyata.

A = 2  (NIM berakhiran ...172)  ->  100 + 10*2 = 120 file
Pakai:  python make_dataset.py --n 120 --out data
"""
import argparse
import random
from pathlib import Path

A = 2                      # <-- DIUBAH: digit terakhir NIM
DEFAULT_N = 100 + 10 * A   # 120 file
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = BASE_DIR / "data"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--words", type=int, default=30000, help="kata per file")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rnd = random.Random(args.seed)
    vocab = ["".join(rnd.choices("abcdefghijklmnopqrstuvwxyz", k=rnd.randint(2, 9)))
             for _ in range(3000)]
    weights = [1.0 / (i + 1) for i in range(len(vocab))]   # Zipf sederhana

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for i in range(args.n):
        words = rnd.choices(vocab, weights=weights, k=args.words)
        # sisipkan baris baru tiap 12 kata supaya mirip teks nyata
        lines = [" ".join(words[j:j + 12]) for j in range(0, len(words), 12)]
        (out / f"doc_{i:04d}.txt").write_text("\n".join(lines), encoding="utf-8")
    total = sum(f.stat().st_size for f in out.glob("*.txt"))
    print(f"{args.n} file dibuat di '{out}' ({total/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
