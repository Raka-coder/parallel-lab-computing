"""Server gRPC dengan deduplikasi PERSISTEN (SQLite) — jawaban analisis P3.

Masalah: `PROSES` (log request_id) yang hanya di RAM hilang saat server
restart, sehingga retry dianggap permintaan baru -> transfer terjadi dua kali.

Perbaikan: saldo DAN log request_id disimpan di SQLite, lalu
"cek duplikat -> ubah saldo -> simpan log" dijalankan dalam SATU transaksi
(`BEGIN IMMEDIATE ... COMMIT`). Bila crash di tengah, semuanya batal; bila
sukses, semuanya tersimpan.

Mode pembanding:
    --dedup sqlite   (BENAR)  log ikut persisten
    --dedup ram      (SALAH)  log hanya di RAM, saldo tetap persisten

Contoh:
    python server_persisten.py --port 50061 --db /tmp/l36.db --dedup sqlite
"""

from __future__ import annotations

import argparse
import errno
import socket
import sqlite3
import sys
import threading
import time
from concurrent import futures
from datetime import datetime

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc

SALDO_AWAL = {"A": 1000, "B": 500}
TTL_PROSES_DETIK = 24 * 60 * 60  # request_id lama dibersihkan setelah 1 hari


def log(pesan: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {pesan}", flush=True)


class LayananPersisten(pb_grpc.LayananNilaiServicer):
    def __init__(self, db_path: str, dedup: str = "sqlite") -> None:
        self.db_path = db_path
        self.dedup = dedup
        self.proses_ram: dict[str, bytes] = {}
        self.ram_lock = threading.Lock()
        self._siapkan_database()

    # -- database --------------------------------------------------------
    def _koneksi(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        return con

    def _siapkan_database(self) -> None:
        con = self._koneksi()
        try:
            con.execute(
                "CREATE TABLE IF NOT EXISTS saldo (akun TEXT PRIMARY KEY, jumlah INTEGER NOT NULL)"
            )
            con.execute(
                "CREATE TABLE IF NOT EXISTS proses ("
                "request_id TEXT PRIMARY KEY, respons BLOB NOT NULL, dibuat REAL NOT NULL)"
            )
            con.execute("BEGIN IMMEDIATE")
            for akun, jumlah in SALDO_AWAL.items():
                con.execute("INSERT OR IGNORE INTO saldo (akun, jumlah) VALUES (?, ?)", (akun, jumlah))
            # Retensi: buang log lama agar tabel tidak tumbuh tanpa batas.
            con.execute("DELETE FROM proses WHERE dibuat < ?", (time.time() - TTL_PROSES_DETIK,))
            con.commit()
        finally:
            con.close()

    def _saldo(self, con: sqlite3.Connection) -> dict[str, int]:
        return dict(con.execute("SELECT akun, jumlah FROM saldo").fetchall())

    # -- transfer --------------------------------------------------------
    def Transfer(self, request, context):  # noqa: N802
        if request.dari not in SALDO_AWAL or request.ke not in SALDO_AWAL:
            context.abort(grpc.StatusCode.NOT_FOUND, "Akun tidak ditemukan")
        if request.jumlah <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Jumlah harus > 0")

        if self.dedup == "ram":
            return self._transfer_ram(request, context)
        return self._transfer_sqlite(request, context)

    def _transfer_ram(self, request, context):
        """Dedup di RAM (SALAH): hilang saat restart, saldo tetap persisten."""
        with self.ram_lock:
            tersimpan = self.proses_ram.get(request.request_id)
            if tersimpan is not None:
                log(f"Transfer({request.request_id}) -> duplikat RAM")
                return pb.StatusResponse.FromString(tersimpan)

            con = self._koneksi()
            try:
                con.execute("BEGIN IMMEDIATE")
                saldo = self._saldo(con)
                if saldo[request.dari] < request.jumlah:
                    con.rollback()
                    context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Saldo tidak cukup")
                con.execute(
                    "UPDATE saldo SET jumlah = jumlah - ? WHERE akun = ?",
                    (request.jumlah, request.dari),
                )
                con.execute(
                    "UPDATE saldo SET jumlah = jumlah + ? WHERE akun = ?",
                    (request.jumlah, request.ke),
                )
                con.commit()
            finally:
                con.close()

            respons = pb.StatusResponse(sukses=True, pesan="Transfer berhasil", jumlah=request.jumlah)
            self.proses_ram[request.request_id] = respons.SerializeToString()
            log(f"Transfer({request.request_id}) dieksekusi (dedup RAM)")
            return respons

    def _transfer_sqlite(self, request, context):
        """Dedup + perubahan saldo dalam SATU transaksi atomik (BENAR)."""
        con = self._koneksi()
        try:
            con.execute("BEGIN IMMEDIATE")  # kunci tulis lintas thread/proses
            baris = con.execute(
                "SELECT respons FROM proses WHERE request_id = ?", (request.request_id,)
            ).fetchone()
            if baris is not None:
                con.rollback()
                log(f"Transfer({request.request_id}) -> duplikat SQLite")
                return pb.StatusResponse.FromString(baris[0])

            saldo = self._saldo(con)
            if saldo[request.dari] < request.jumlah:
                con.rollback()
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Saldo tidak cukup")

            con.execute(
                "UPDATE saldo SET jumlah = jumlah - ? WHERE akun = ?",
                (request.jumlah, request.dari),
            )
            con.execute(
                "UPDATE saldo SET jumlah = jumlah + ? WHERE akun = ?",
                (request.jumlah, request.ke),
            )
            respons = pb.StatusResponse(sukses=True, pesan="Transfer berhasil", jumlah=request.jumlah)
            con.execute(
                "INSERT INTO proses (request_id, respons, dibuat) VALUES (?, ?, ?)",
                (request.request_id, respons.SerializeToString(), time.time()),
            )
            con.commit()
            log(f"Transfer({request.request_id}) dieksekusi + log tersimpan (SQLite)")
            return respons
        except BaseException:
            # Termasuk context.abort (RpcError) -> batalkan transaksi yang terbuka.
            if con.in_transaction:
                con.rollback()
            raise
        finally:
            con.close()

    def GetSaldo(self, request, context):  # noqa: N802
        if request.akun not in SALDO_AWAL:
            context.abort(grpc.StatusCode.NOT_FOUND, "Akun tidak ditemukan")
        con = self._koneksi()
        try:
            saldo = self._saldo(con)
        finally:
            con.close()
        return pb.SaldoResponse(akun=request.akun, saldo=saldo[request.akun])


def port_bebas(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as uji:
        uji.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            uji.bind(("0.0.0.0", port))
        except OSError:
            return False
    return True


def pesan_gagal_bind(port: int) -> None:
    print(
        f"Port {port} sudah dipakai proses lain.\n"
        f"  Lihat proses  : ss -ltnp | grep :{port}   (Linux)  atau  lsof -i :{port}\n"
        f"  Hentikan      : pkill -f server_persisten  (atau Ctrl+C di terminal server lama)\n"
        f"  Ganti port    : python grpc_app/server_persisten.py --port {port + 1}",
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
    parser = argparse.ArgumentParser(description="Server gRPC persisten (SQLite)")
    parser.add_argument("--port", type=int, default=50061)
    parser.add_argument("--db", default="saldo.db", help="berkas database SQLite")
    parser.add_argument("--dedup", choices=["sqlite", "ram"], default="sqlite")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    if not port_bebas(args.port):
        pesan_gagal_bind(args.port)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=args.workers))
    pb_grpc.add_LayananNilaiServicer_to_server(LayananPersisten(args.db, args.dedup), server)
    if not server.add_insecure_port(f"0.0.0.0:{args.port}"):
        pesan_gagal_bind(args.port)
    server.start()
    log(f"Server persisten di 0.0.0.0:{args.port} db={args.db} dedup={args.dedup}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=1)


if __name__ == "__main__":
    main()
