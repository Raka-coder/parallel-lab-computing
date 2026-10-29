"""Server gRPC layanan akademik — Praktikum 2 & 3.

Menjalankan semua RPC dari akademik.proto pada satu server:
GetMahasiswa, TambahNilai, StreamNilai, KirimBanyakNilai, Diskusi,
Transfer (dengan deduplikasi request_id), dan GetSaldo.

Contoh:
    python server_grpc.py
    python server_grpc.py --workers 20 --get-delay 0.1
    python server_grpc.py --slow-prob 0.3 --slow-s 3.0      # L3.1 / L3.2
    python server_grpc.py --no-lock --race-window 0.002      # L3.3 (demonstrasi bug)
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import queue
import random
import socket
import sys
import threading
import time
from concurrent import futures
from datetime import datetime

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc

# ---------------------------------------------------------------------------
# State bersama (di RAM; hilang saat server restart — dibahas di L3.6)
# ---------------------------------------------------------------------------
DATA: dict[str, pb.Mahasiswa] = {
    "2023001": pb.Mahasiswa(nim="2023001", nama="Andi", ipk=3.26, prodi="Informatika"),
    "2023002": pb.Mahasiswa(nim="2023002", nama="Sari", ipk=3.75, prodi="Informatika"),
    "2023003": pb.Mahasiswa(nim="2023003", nama="Budi", ipk=3.10, prodi="Sistem Informasi"),
}
DATA_LOCK = threading.Lock()

NILAI: dict[str, list[pb.Nilai]] = {}

ROOM: dict[str, "queue.Queue[pb.Pesan]"] = {}
ROOM_LOCK = threading.Lock()

# Saldo awal: total selalu 1500 (A=1000, B=500).
SALDO = {"A": 1000, "B": 500}
PROSES: dict[str, pb.StatusResponse] = {}  # request_id -> respons tersimpan
LOCK = threading.Lock()


def log(pesan: str) -> None:
    waktu = datetime.now().strftime("%H:%M:%S")
    print(f"[{waktu}] {pesan}", flush=True)


# ---------------------------------------------------------------------------
# Implementasi layanan
# ---------------------------------------------------------------------------
class LayananNilai(pb_grpc.LayananNilaiServicer):
    def __init__(
        self,
        *,
        get_delay: float = 0.0,
        slow_prob: float = 0.0,
        slow_s: float = 3.0,
        stream_delay: float = 0.5,
        no_lock: bool = False,
        race_window: float = 0.0,
        seed: int | None = None,
    ) -> None:
        self.get_delay = get_delay
        self.slow_prob = slow_prob
        self.slow_s = slow_s
        self.stream_delay = stream_delay
        self.no_lock = no_lock
        self.race_window = race_window
        self.rng = random.Random(seed)

    # -- unary ------------------------------------------------------------
    def GetMahasiswa(self, request, context):  # noqa: N802
        if self.get_delay > 0:
            time.sleep(self.get_delay)
        mhs = DATA.get(request.nim)
        if mhs is None:
            log(f"GetMahasiswa({request.nim}) -> NOT_FOUND")
            context.abort(grpc.StatusCode.NOT_FOUND, f"NIM {request.nim} tidak ditemukan")
        log(f"GetMahasiswa({request.nim}) -> {mhs.nama}")
        return mhs

    def TambahNilai(self, request, context):  # noqa: N802
        if request.nim not in DATA:
            context.abort(grpc.StatusCode.NOT_FOUND, f"NIM {request.nim} tidak ditemukan")
        if not 0 <= request.nilai <= 100:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Nilai harus 0-100")
        with DATA_LOCK:
            daftar = NILAI.setdefault(request.nim, [])
            # Timpa nilai mata kuliah yang sama (operasi idempoten).
            for item in daftar:
                if item.mata_kuliah == request.mata_kuliah:
                    item.nilai = request.nilai
                    break
            else:
                daftar.append(pb.Nilai(mata_kuliah=request.mata_kuliah, nilai=request.nilai))
            jumlah = len(daftar)
        log(f"TambahNilai({request.nim}, {request.mata_kuliah}={request.nilai})")
        return pb.StatusResponse(sukses=True, pesan="Nilai tersimpan", jumlah=jumlah)

    # -- server streaming ------------------------------------------------
    def StreamNilai(self, request, context):  # noqa: N802
        if request.nim not in DATA:
            context.abort(grpc.StatusCode.NOT_FOUND, f"NIM {request.nim} tidak ditemukan")
        log(f"StreamNilai({request.nim}) mulai")
        mata_kuliah = ["Basis Data", "Jaringan", "Komputasi Paralel"]
        for i, mk in enumerate(mata_kuliah):
            if not context.is_active():
                return
            # Kirim bertahap: client menerima item satu per satu.
            if i > 0:
                time.sleep(self.stream_delay)
            yield pb.Nilai(mata_kuliah=mk, nilai=80.0 + i * 5)
        log(f"StreamNilai({request.nim}) selesai")

    # -- client streaming ------------------------------------------------
    def KirimBanyakNilai(self, request_iterator, context):  # noqa: N802
        valid, ditolak = 0, 0
        with DATA_LOCK:
            for req in request_iterator:
                if req.nim not in DATA or not 0 <= req.nilai <= 100:
                    ditolak += 1
                    continue
                NILAI.setdefault(req.nim, []).append(
                    pb.Nilai(mata_kuliah=req.mata_kuliah, nilai=req.nilai)
                )
                valid += 1
        log(f"KirimBanyakNilai: {valid} valid, {ditolak} ditolak")
        return pb.StatusResponse(
            sukses=ditolak == 0,
            pesan=f"{valid} nilai tersimpan, {ditolak} ditolak",
            jumlah=valid,
        )

    # -- bidirectional streaming ----------------------------------------
    def Diskusi(self, request_iterator, context):  # noqa: N802
        try:
            pertama = next(request_iterator)
        except StopIteration:
            return
        nama = pertama.pengirim
        if not nama:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Nama pengirim wajib diisi")

        antrean: queue.Queue[pb.Pesan | None] = queue.Queue()
        with ROOM_LOCK:
            ROOM[nama] = antrean
        log(f"Diskusi: {nama} bergabung (peserta: {list(ROOM)})")

        def sebarkan(pesan: pb.Pesan) -> None:
            with ROOM_LOCK:
                tujuan = [(n, q) for n, q in ROOM.items() if n != nama]
            for _, q in tujuan:
                q.put(pesan)

        def baca_masuk() -> None:
            try:
                for pesan in request_iterator:
                    sebarkan(pesan)
            except grpc.RpcError:
                pass
            finally:
                antrean.put(None)  # sentinel: stream kiriman selesai

        threading.Thread(target=baca_masuk, daemon=True).start()
        try:
            while context.is_active():
                try:
                    item = antrean.get(timeout=0.5)
                except queue.Empty:
                    continue
                if item is None:
                    break
                yield item
        finally:
            with ROOM_LOCK:
                ROOM.pop(nama, None)
            antrean.put(None)
            log(f"Diskusi: {nama} keluar (peserta: {list(ROOM)})")

    # -- transfer (tidak idempoten) -------------------------------------
    def Transfer(self, request, context):  # noqa: N802
        # Lock melingkupi seluruh urutan cek-duplikat -> ubah saldo -> catat.
        # Dengan --no-lock, urutan ini sengaja dibiarkan tanpa proteksi (L3.3).
        kunci = contextlib.nullcontext() if self.no_lock else LOCK
        with kunci:
            if request.request_id in PROSES:
                log(f"Transfer({request.request_id}) -> duplikat, balasan tersimpan")
                return PROSES[request.request_id]

            if request.dari not in SALDO or request.ke not in SALDO:
                context.abort(grpc.StatusCode.NOT_FOUND, "Akun tidak ditemukan")
            if request.jumlah <= 0:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Jumlah harus > 0")
            if SALDO[request.dari] < request.jumlah:
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Saldo tidak cukup")

            saldo_asal = SALDO[request.dari]  # baca
            saldo_tujuan = SALDO[request.ke]
            if self.race_window > 0:
                # Jendela buatan: memperbesar peluang thread lain menyisip
                # di antara baca dan tulis (memperlihatkan lost update).
                time.sleep(self.race_window)

            SALDO[request.dari] = saldo_asal - request.jumlah  # tulis
            SALDO[request.ke] = saldo_tujuan + request.jumlah

            respons = pb.StatusResponse(
                sukses=True,
                pesan=f"{request.dari}->{request.ke} {request.jumlah} berhasil",
                jumlah=request.jumlah,
            )
            PROSES[request.request_id] = respons

        # Balasan lambat DILUAR lock: client bisa timeout padahal transfer
        # sudah terjadi. Retry dengan request_id sama akan mendapat balasan
        # tersimpan tanpa mengeksekusi transfer dua kali.
        if self.slow_prob > 0 and self.rng.random() < self.slow_prob:
            log(f"Transfer({request.request_id}) lambat {self.slow_s}s (balasan tertunda)")
            time.sleep(self.slow_s)

        log(f"Transfer({request.request_id}) {request.dari}->{request.ke} {request.jumlah}")
        return respons

    def GetSaldo(self, request, context):  # noqa: N802
        if request.akun not in SALDO:
            context.abort(grpc.StatusCode.NOT_FOUND, "Akun tidak ditemukan")
        return pb.SaldoResponse(akun=request.akun, saldo=SALDO[request.akun])


# ---------------------------------------------------------------------------
def bangun_server(port: int, workers: int, layanan: LayananNilai) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=workers))
    pb_grpc.add_LayananNilaiServicer_to_server(layanan, server)
    if not server.add_insecure_port(f"0.0.0.0:{port}"):
        raise OSError(errno.EADDRINUSE, f"port {port} sudah dipakai")
    return server


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
        f"  Hentikan      : pkill -f server_grpc  (atau Ctrl+C di terminal server lama)\n"
        f"  Ganti port    : python grpc_app/server_grpc.py --port {port + 1}",
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
    parser = argparse.ArgumentParser(description="Server gRPC LayananNilai")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--workers", type=int, default=10, help="ukuran ThreadPool server")
    parser.add_argument("--get-delay", type=float, default=0.0, help="detik tidur di GetMahasiswa")
    parser.add_argument("--slow-prob", type=float, default=0.0,
                        help="peluang balasan Transfer ditunda (0-1)")
    parser.add_argument("--slow-s", type=float, default=3.0, help="lama penundaan balasan (detik)")
    parser.add_argument("--stream-delay", type=float, default=0.5,
                        help="jeda antar item StreamNilai (detik)")
    parser.add_argument("--no-lock", action="store_true", help="DEMO BUG: Transfer tanpa lock")
    parser.add_argument("--race-window", type=float, default=0.0,
                        help="DEMO BUG: jeda baca->tulis di Transfer (detik)")
    parser.add_argument("--seed", type=int, default=None, help="seed acak (reprodusibel)")
    args = parser.parse_args()

    if not port_bebas(args.port):
        pesan_gagal_bind(args.port)

    layanan = LayananNilai(
        get_delay=args.get_delay,
        slow_prob=args.slow_prob,
        slow_s=args.slow_s,
        stream_delay=args.stream_delay,
        no_lock=args.no_lock,
        race_window=args.race_window,
        seed=args.seed,
    )
    try:
        server = bangun_server(args.port, args.workers, layanan)
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE:
            raise
        pesan_gagal_bind(args.port)
    server.start()
    log(f"Server gRPC berjalan di 0.0.0.0:{args.port} (workers={args.workers})")
    log(f"Opsi: get_delay={args.get_delay}s slow_prob={args.slow_prob} "
        f"slow_s={args.slow_s}s no_lock={args.no_lock} race_window={args.race_window}s")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        log("Server dihentikan.")
        server.stop(grace=1)


if __name__ == "__main__":
    main()
