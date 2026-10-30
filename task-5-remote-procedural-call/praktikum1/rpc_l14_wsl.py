#!/usr/bin/env python3
"""Benchmark L1.4 lintas jaringan: WSL Debian (client) -> Windows (server).

Jalankan dari terminal WSL Debian saat server XML-RPC Windows aktif dengan
bind 0.0.0.0:

    python3 rpc_l14_wsl.py
    python3 rpc_l14_wsl.py --host 192.168.1.41
    WINDOWS_IP=192.168.1.41 python3 rpc_l14_wsl.py --requests 200 --rounds 5

Tanpa --host, skrip memakai WINDOWS_IP bila diisi, lalu alamat gateway WSL
(vEthernet WSL di Windows) yang merupakan host Hyper-V Virtual Switch.
"""

from __future__ import annotations

import argparse
import os
import socket
import statistics
import sys
import time
import xmlrpc.client

JUMLAH_DEFAULT = 100
PUTARAN_DEFAULT = 5
PORT_DEFAULT = 8000
TIMEOUT_DEFAULT = 5.0


def tambah_lokal(a: float, b: float) -> float:
    return a + b


def deteksi_gateway_wsl() -> str | None:
    try:
        with open("/proc/net/route", encoding="ascii") as berkas:
            next(berkas, None)
            for baris in berkas:
                kolom = baris.split()
                if len(kolom) >= 3 and kolom[1] == "00000000":
                    heks = kolom[2]
                    return ".".join(str(int(heks[i : i + 2], 16)) for i in (6, 4, 2, 0))
    except OSError:
        return None
    return None


def pilih_host(argumen: str | None) -> tuple[str, str]:
    if argumen:
        return argumen, "argumen --host"
    dari_env = os.environ.get("WINDOWS_IP", "").strip()
    if dari_env:
        return dari_env, "variabel WINDOWS_IP"
    gateway = deteksi_gateway_wsl()
    if gateway:
        return gateway, "gateway WSL (vEthernet WSL)"
    raise SystemExit(
        "Tidak bisa menentukan alamat Windows. Jalankan dengan --host <IP Windows> "
        "atau set WINDOWS_IP."
    )


def ukur(fungsi, jumlah: int, putaran: int) -> list[float]:
    fungsi(5, 3)
    for _ in range(3):
        fungsi(5, 3)

    total_per_putaran: list[float] = []
    for _ in range(putaran):
        mulai = time.perf_counter()
        for _ in range(jumlah):
            fungsi(5, 3)
        total_per_putaran.append(time.perf_counter() - mulai)
    return total_per_putaran


def ringkas(total_per_putaran: list[float], jumlah: int) -> dict[str, float]:
    per_panggilan = [total / jumlah for total in total_per_putaran]
    return {
        "median_detik": statistics.median(per_panggilan),
        "median_total": statistics.median(total_per_putaran),
        "rata_detik": statistics.fmean(per_panggilan),
        "min_detik": min(per_panggilan),
        "max_detik": max(per_panggilan),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark L1.4 WSL Debian -> Windows")
    parser.add_argument("--host", default=None, help="IP Windows (default: deteksi otomatis)")
    parser.add_argument("--port", type=int, default=PORT_DEFAULT)
    parser.add_argument("--requests", type=int, default=JUMLAH_DEFAULT)
    parser.add_argument("--rounds", type=int, default=PUTARAN_DEFAULT)
    parser.add_argument("--timeout", type=float, default=TIMEOUT_DEFAULT)
    args = parser.parse_args()

    if args.requests < 1 or args.rounds < 1:
        parser.error("--requests dan --rounds harus >= 1")

    host, sumber = pilih_host(args.host)
    socket.setdefaulttimeout(args.timeout)

    print("===============================================")
    print("  UJI L1.4: WSL DEBIAN -> WINDOWS HOST")
    print("===============================================")
    print(f"Target Server : {host}:{args.port}")
    print(f"Sumber alamat : {sumber}")
    print(f"Requests      : {args.requests} x {args.rounds} putaran")

    try:
        proxy = xmlrpc.client.ServerProxy(f"http://{host}:{args.port}/", allow_none=True)
        hasil = proxy.tambah(5, 3)
        print(f"Tes koneksi   : 5 + 3 = {hasil}")
        if hasil != 8:
            raise RuntimeError(f"balasan tidak sesuai: {hasil!r}")
    except Exception as exc:  # noqa: BLE001 - tampilkan semua kegagalan koneksi
        print(f"\nGAGAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "Pastikan: 1. Server Windows berjalan dengan --host 0.0.0.0. "
            "2. Firewall port terbuka. 3. Alamat Windows benar.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print(f"\nMemulai benchmark {args.requests}x pemanggilan tambah()...")

    lokal = ringkas(ukur(tambah_lokal, args.requests, args.rounds), args.requests)
    rpc = ringkas(ukur(proxy.tambah, args.requests, args.rounds), args.requests)

    rasio = rpc["median_detik"] / lokal["median_detik"]

    print("\n--- HASIL BENCHMARK ---")
    print(f"Lokal (WSL)   : {lokal['median_detik'] * 1e6:.3f} us/panggilan")
    print(f"XML-RPC       : {rpc['median_detik'] * 1000:.4f} ms/panggilan")
    print(f"Total Waktu   : {rpc['median_total']:.4f} detik (median {args.rounds} putaran)")
    print(f"Rata-rata     : {rpc['rata_detik'] * 1000:.4f} ms/panggilan")
    print(f"Rentang       : {rpc['min_detik'] * 1000:.4f} - {rpc['max_detik'] * 1000:.4f} ms")
    print(f"Rasio         : XML-RPC {rasio:,.0f}x lebih lambat daripada lokal")
    print("Environment   : WSL DEBIAN (Client) -> WINDOWS (Server)")
    print("Network Path  : Hyper-V Virtual Switch (Cross-Network)")
    print(f"WSL_AVG_MS={rpc['median_detik'] * 1000:.6f}")
    print(f"LOCAL_US={lokal['median_detik'] * 1e6:.6f}")
    print("=======================")


if __name__ == "__main__":
    main()
