"""Client kalkulator XML-RPC — Praktikum 1 (Langkah 2, L1.1, L1.2).

Jalankan server lebih dulu (terminal lain):
    python server_kalkulator.py --verbose

Lalu:
    python client_kalkulator.py
    python client_kalkulator.py --verbose          # tampilkan pesan HTTP + XML
    python client_kalkulator.py --host 192.168.1.10
"""

from __future__ import annotations

import argparse
import xmlrpc.client

from server_util import HOST_LOKAL, PORT_DEFAULT, pastikan_server


def cetak_judul(teks: str) -> None:
    print(f"\n{'=' * 62}\n{teks}\n{'=' * 62}")


import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
from banner import cetak_identitas  # noqa: E402

def main() -> None:
    cetak_identitas()
    parser = argparse.ArgumentParser(description="Client kalkulator XML-RPC")
    parser.add_argument("--host", default=HOST_LOKAL)
    parser.add_argument("--port", type=int, default=PORT_DEFAULT)
    parser.add_argument("--verbose", action="store_true", help="tampilkan pesan HTTP/XML")
    args = parser.parse_args()

    server, proses = pastikan_server(args.host, args.port)
    if proses is not None:
        print(f"(Server lokal dinyalakan otomatis di {args.host}:{args.port})")
    else:
        print(f"(Memakai server yang sudah berjalan di {args.host}:{args.port})")

    try:
        cetak_judul("Langkah 2 — panggilan dasar")
        print(f"5 + 3      = {server.tambah(5, 3)}")
        print(f"4 x 7      = {server.kali(4, 7)}")
        print(f"10 / 4     = {server.bagi(10, 4)}")

        cetak_judul("L1.1 — pangkat & akar")
        print(f"pangkat(2, 10)  = {server.pangkat(2, 10)}")
        print(f"pangkat(2, 0.5) = {server.pangkat(2, 0.5)}")
        print(f"akar(144)       = {server.akar(144)}")
        try:
            server.akar(-4)
        except xmlrpc.client.Fault as fault:
            print(f"akar(-4)        -> Fault: {fault.faultString}")

        cetak_judul("L1.2 — statistik(daftar)")
        data = [3, 1, 4, 1, 5, 9, 2, 6]
        print(f"statistik({data}) = {server.statistik(data)}")

        cetak_judul("Error logika: bagi(10, 0)")
        try:
            server.bagi(10, 0)
        except xmlrpc.client.Fault as fault:
            # Fault = error aplikasi dari server, BUKAN error HTTP.
            print(f"Fault code={fault.faultCode}: {fault.faultString}")

        cetak_judul("Daftar method yang tersedia")
        print(server.system.listMethods())
    finally:
        if proses is not None:
            proses.terminate()
            proses.wait(timeout=5)


if __name__ == "__main__":
    main()
