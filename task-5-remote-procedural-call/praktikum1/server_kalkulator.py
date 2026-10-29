"""Server kalkulator XML-RPC — Praktikum 1.

Menjalankan SimpleXMLRPCServer (multithread) di port 8000 dan mendaftarkan
fungsi tambah, kali, bagi, pangkat, akar, statistik, echo, dan lambat.

Contoh:
    python server_kalkulator.py
    python server_kalkulator.py --port 8001 --host 0.0.0.0
"""

from __future__ import annotations

import argparse
import errno
import math
import statistics
import sys
from datetime import datetime
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer


# ---------------------------------------------------------------------------
# Fungsi yang dipanggil jarak jauh
# ---------------------------------------------------------------------------
def tambah(a: float, b: float) -> float:
    return a + b


def kali(a: float, b: float) -> float:
    return a * b


def bagi(a: float, b: float) -> float:
    if b == 0:
        # Melempar ValueError di server -> dikirim sebagai <fault> ke client.
        raise ValueError("Pembagian dengan nol tidak diperbolehkan")
    return a / b


def pangkat(a: float, b: float) -> float:
    """a ** b. Hasil yang melebihi batas <int> XML-RPC akan gagal saat marshalling."""
    return a**b


def akar(x: float) -> float:
    if x < 0:
        raise ValueError("Akar kuadrat bilangan negatif tidak terdefinisi")
    return math.sqrt(x)


def statistik(daftar: list) -> dict:
    """Kembalikan {'min', 'max', 'rata2'} dari daftar angka.

    Kunci dict wajib string agar bisa diubah menjadi XML-RPC <struct>.
    """
    if not daftar:
        raise ValueError("Daftar tidak boleh kosong")
    return {
        "min": min(daftar),
        "max": max(daftar),
        "rata2": statistics.fmean(daftar),
    }


def echo(x):
    """Mengembalikan argumen apa adanya (untuk uji tipe data L1.3)."""
    return x


def lambat(detik: float = 5.0) -> int:
    """Fungsi yang menahan proses selama `detik` untuk uji L1.5 (server mati)."""
    import time

    time.sleep(float(detik))
    return 42


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
class ServerLog(SimpleXMLRPCServer):
    """SimpleXMLRPCServer yang mencetak setiap panggilan (bukti untuk laporan)."""

    verbose = False

    def _dispatch(self, method, params):  # noqa: N802 (nama dari library)
        if self.verbose:
            waktu = datetime.now().strftime("%H:%M:%S")
            print(f"[{waktu}] panggil {method}({', '.join(repr(p) for p in params)})", flush=True)
        return super()._dispatch(method, params)


class ServerMultithread(ThreadingMixIn, ServerLog):
    """Setiap request dilayani thread sendiri, agar satu panggilan lambat
    tidak memblokir panggilan lain."""

    daemon_threads = True
    allow_reuse_address = True


def bangun_server(host: str, port: int, verbose: bool = False) -> ServerMultithread:
    server = ServerMultithread((host, port), allow_none=True, logRequests=False)
    server.verbose = verbose
    for fungsi in (tambah, kali, bagi, pangkat, akar, statistik, echo, lambat):
        server.register_function(fungsi, fungsi.__name__)
    # Introspeksi opsional (system.listMethods) agar mudah dijelajahi.
    server.register_introspection_functions()
    return server


def pesan_gagal_bind(port: int) -> None:
    print(
        f"Port {port} sudah dipakai proses lain.\n"
        f"  Lihat proses  : ss -ltnp | grep :{port}   (Linux)  atau  lsof -i :{port}\n"
        f"  Hentikan      : pkill -f server_kalkulator  (atau Ctrl+C di terminal server lama)\n"
        f"  Ganti port    : python praktikum1/server_kalkulator.py --port {port + 1}",
        file=sys.stderr,
        flush=True,
    )
    raise SystemExit(2)


import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
from banner import cetak_identitas  # noqa: E402

def main() -> None:
    cetak_identitas()
    parser = argparse.ArgumentParser(description="Server kalkulator XML-RPC")
    parser.add_argument("--host", default="0.0.0.0", help="alamat dengar (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="port (default 8000)")
    parser.add_argument("--verbose", action="store_true", help="cetak setiap panggilan")
    args = parser.parse_args()

    try:
        server = bangun_server(args.host, args.port, verbose=args.verbose)
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE:
            raise
        pesan_gagal_bind(args.port)
    print(f"Server XML-RPC berjalan di http://{args.host}:{args.port}", flush=True)
    print(f"Fungsi: {', '.join(server.system_listMethods())}", flush=True)
    print("Tekan Ctrl+C untuk berhenti.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
