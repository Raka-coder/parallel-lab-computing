"""Praktikum 2 — harness bersama: path, server subprocess, dan cetakan rapi.

Semua skrip di praktikum2/ memakai modul ini agar:
  - stub gRPC (grpc_app/) dan stub lama (old_stub/) bisa diimpor,
  - server bisa dinyalakan/dimatikan otomatis,
  - keluaran mudah dibaca & disalin ke laporan.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

DIR_INI = Path(__file__).resolve().parent
ROOT = DIR_INI.parent
GRPC_APP = ROOT / "grpc_app"
OLD_STUB = ROOT / "old_stub"
HASIL = Path(__file__).resolve().parent / "hasil"


def siapkan_path() -> None:
    """Tambahkan grpc_app/ dan old_stub/ ke sys.path (idempoten)."""
    for direktori in (GRPC_APP, OLD_STUB):
        if str(direktori) not in sys.path:
            sys.path.insert(0, str(direktori))
    HASIL.mkdir(exist_ok=True)


def judul(teks: str) -> None:
    print(f"\n{'=' * 70}\n{teks}\n{'=' * 70}")


def port_terbuka(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def tunggu_port(host: str, port: int, batas: float = 10.0) -> None:
    mulai = time.monotonic()
    while time.monotonic() - mulai < batas:
        if port_terbuka(host, port):
            return
        time.sleep(0.05)
    raise RuntimeError(f"Server tidak siap di {host}:{port} dalam {batas:.0f} detik")


@contextmanager
def server(port: int = 50051, *argumen: str, host: str = "127.0.0.1", tampilkan_log: bool = False):
    """Nyalakan server_grpc.py sebagai subprocess, lalu matikan saat selesai."""
    perintah = [sys.executable, str(GRPC_APP / "server_grpc.py"), "--port", str(port), *argumen]
    proses = subprocess.Popen(
        perintah,
        cwd=GRPC_APP,
        stdout=None if tampilkan_log else subprocess.DEVNULL,
        stderr=None if tampilkan_log else subprocess.DEVNULL,
    )
    try:
        tunggu_port(host, port)
        time.sleep(0.1)  # beri waktu server menyelesaikan start()
        yield proses
    finally:
        proses.terminate()
        try:
            proses.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proses.kill()
            proses.wait(timeout=5)
