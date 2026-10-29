"""Utilitas bersama Praktikum 1: menjalankan & menunggu server XML-RPC lokal.

Dipakai agar setiap skrip latihan bisa dijalankan dengan SATU perintah:
skrip akan memakai server yang sudah hidup, atau menyalakan server sendiri
lalu mematikannya saat selesai.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import xmlrpc.client
from pathlib import Path

HOST_LOKAL = "127.0.0.1"
PORT_DEFAULT = 8000
DIR_INI = Path(__file__).resolve().parent


def port_terbuka(host: str, port: int, timeout: float = 0.3) -> bool:
    """True bila ada sesuatu yang menerima koneksi TCP di host:port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def tunggu_port(host: str, port: int, batas: float = 10.0) -> None:
    """Blokir sampai port siap dipakai, atau lempar RuntimeError."""
    mulai = time.monotonic()
    while time.monotonic() - mulai < batas:
        if port_terbuka(host, port):
            return
        time.sleep(0.05)
    raise RuntimeError(f"Server tidak siap di {host}:{port} dalam {batas:.0f} detik")


class TransportTimeout(xmlrpc.client.Transport):
    """Transport HTTP dengan timeout, supaya panggilan RPC tidak menggantung selamanya."""

    def __init__(self, timeout: float = 5.0) -> None:
        super().__init__()
        self.timeout = timeout

    def make_connection(self, host):  # noqa: ANN001 - tanda tangan dari library
        koneksi = super().make_connection(host)
        koneksi.timeout = self.timeout
        return koneksi


class TransportTanpaRetry(TransportTimeout):
    """Transport yang TIDAK mengulang otomatis saat koneksi terputus.

    Transport bawaan xmlrpc.client mencoba ulang sekali bila mendapat
    RemoteDisconnected/ECONNRESET. Untuk demonstrasi L1.5 kita ingin
    melihat error asli saat server mati di tengah panggilan.
    """

    def request(self, host, handler, request_body, verbose=False):  # noqa: ANN001
        return self.single_request(host, handler, request_body, verbose)


def proxy(
    host: str = HOST_LOKAL,
    port: int = PORT_DEFAULT,
    verbose: bool = False,
    timeout: float = 5.0,
    retry: bool = True,
) -> xmlrpc.client.ServerProxy:
    """Buat ServerProxy dengan timeout agar client tidak menggantung selamanya."""
    transport = TransportTimeout(timeout) if retry else TransportTanpaRetry(timeout)
    return xmlrpc.client.ServerProxy(
        f"http://{host}:{port}",
        transport=transport,
        verbose=verbose,
        allow_none=True,
        use_builtin_types=True,
    )


def pastikan_server(
    host: str = HOST_LOKAL,
    port: int = PORT_DEFAULT,
    verbose_server: bool = False,
    timeout: float = 5.0,
) -> tuple[xmlrpc.client.ServerProxy, subprocess.Popen | None]:
    """Kembalikan (proxy, proses_server).

    Bila port sudah melayani (server dijalankan manual di terminal lain),
    proses yang dikembalikan adalah None dan skrip TIDAK mematikan server itu.
    """
    if not port_terbuka(host, port):
        perintah = [sys.executable, str(DIR_INI / "server_kalkulator.py"), "--port", str(port)]
        if verbose_server:
            perintah.append("--verbose")
        keluaran = None if verbose_server else subprocess.DEVNULL
        proses = subprocess.Popen(
            perintah,
            cwd=DIR_INI,
            stdout=keluaran,
            stderr=keluaran,
        )
        tunggu_port(host, port)
        return proxy(host, port, timeout=timeout), proses
    return proxy(host, port, timeout=timeout), None


def hentikan(proses: subprocess.Popen | None) -> None:
    """Matikan server yang kita nyalakan sendiri (None = abaikan)."""
    if proses is None:
        return
    proses.terminate()
    try:
        proses.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proses.kill()
        proses.wait(timeout=5)


def panggil_aman(
    nama_method: str,
    *args,
    host: str = HOST_LOKAL,
    port: int = PORT_DEFAULT,
    timeout: float = 5.0,
    maks_percobaan: int = 5,
    jeda: float = 0.5,
    verbose: bool = True,
):
    """Panggil method XML-RPC dengan penanganan error dan retry sederhana.

    Error dibedakan:
      - xmlrpc.client.Fault          : error logika di server (JANGAN di-retry)
      - xmlrpc.client.ProtocolError  : balasan HTTP tidak sesuai
      - ConnectionError / RemoteDisconnected : server tidak terjangkau
      - socket.timeout               : server terlalu lama menjawab
    """
    for percobaan in range(1, maks_percobaan + 1):
        try:
            # Proxy baru tiap percobaan: koneksi lama mungkin sudah rusak.
            server = proxy(host, port, timeout=timeout)
            return getattr(server, nama_method)(*args)
        except xmlrpc.client.Fault as fault:
            if verbose:
                print(f"  [percobaan {percobaan}] Fault (error server): {fault.faultString}")
            raise  # error logika, bukan masalah jaringan -> tidak di-retry
        except xmlrpc.client.ProtocolError as exc:
            if verbose:
                print(f"  [percobaan {percobaan}] ProtocolError: HTTP {exc.errcode} {exc.errmsg}")
        except (ConnectionError, xmlrpc.client.RemoteDisconnected) as exc:
            if verbose:
                print(f"  [percobaan {percobaan}] Server tidak terjangkau: {type(exc).__name__}: {exc}")
        except socket.timeout:
            if verbose:
                print(f"  [percobaan {percobaan}] Timeout: server tidak menjawab dalam {timeout} s")

        if percobaan < maks_percobaan:
            if verbose:
                print(f"  menunggu {jeda} s lalu mencoba lagi ...")
            time.sleep(jeda)
    raise RuntimeError(f"Gagal memanggil {nama_method} setelah {maks_percobaan} percobaan")
