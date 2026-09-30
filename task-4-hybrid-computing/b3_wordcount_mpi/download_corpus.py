"""
download_corpus.py -- B3: unduh >= 30 e-book teks nyata dari Project Gutenberg.
Jalankan di laptop Anda (butuh internet):   python download_corpus.py --out corpus
Header/footer lisensi Gutenberg dibuang. Bila ada ID yang gagal, dilewati.
Anda boleh mengganti/menambah ID, atau memakai artikel berita berbahasa Indonesia
(simpan saja sebagai .txt di folder corpus).
"""
import argparse
import re
import time
import urllib.request
from pathlib import Path

BOOK_IDS = [1342, 11, 84, 2701, 1661, 98, 1400, 174, 345, 1952, 76, 74, 1260, 2554,
            2600, 1232, 158, 161, 1080, 5200, 244, 25344, 46, 219, 120, 16, 55, 35,
            36, 43, 1184, 768, 1497, 2814, 205, 145, 4300, 6130, 2591, 1727]
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = BASE_DIR / "corpus"
START = re.compile(r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.S)
END = re.compile(r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG.*", re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--min", type=int, default=30)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    ok = 0
    for bid in BOOK_IDS:
        url = f"https://www.gutenberg.org/cache/epub/{bid}/pg{bid}.txt"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (tugas-kuliah)"})
            text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"lewati {bid}: {e}")
            continue
        m = START.search(text)
        if m:
            text = text[m.end():]
        text = END.sub("", text)
        (out / f"pg{bid}.txt").write_text(text, encoding="utf-8")
        ok += 1
        print(f"[{ok}] pg{bid}.txt  ({len(text)/1e3:.0f} KB)")
        time.sleep(1)                      # sopan terhadap server
    print(f"Selesai: {ok} file. " + ("OK (>= 30)" if ok >= args.min else "KURANG dari 30, tambah ID/sumber lain!"))


if __name__ == "__main__":
    main()
