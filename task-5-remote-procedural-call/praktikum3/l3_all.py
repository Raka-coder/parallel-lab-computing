"""Praktikum 3 — menjalankan L3.1 sampai L3.5 + analisis restart server.

Server dinyalakan/dimatikan otomatis untuk setiap skenario agar state
(SALDO, PROSES) selalu bersih.

Jalankan:
    python l3_all.py                    # semua skenario (±2-3 menit)
    python l3_all.py --bagian 4         # hanya L3.4 (grafik)
    python l3_all.py --putaran 3        # 3 putaran untuk L3.1/L3.2/L3.4
    python l3_all.py --log-server       # tampilkan log server
"""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import grpc

ROOT = Path(__file__).resolve().parent.parent
GRPC_APP = ROOT / "grpc_app"
HASIL = Path(__file__).resolve().parent / "hasil"
if str(GRPC_APP) not in sys.path:
    sys.path.insert(0, str(GRPC_APP))

import akademik_pb2 as pb  # noqa: E402
import akademik_pb2_grpc as pb_grpc  # noqa: E402
from klien import FailoverClient, ambil_saldo, transfer, transfer_id_baru  # noqa: E402

HOST = "127.0.0.1"
PORT = 50051
# Sesuai lembar latihan: dua server di 50051 dan 50052.
# Matikan server manual di 50051 dulu (Ctrl+C), karena skrip ini menyalakannya sendiri.
PORT_FAILOVER_1 = 50051
PORT_FAILOVER_2 = 50052
PORT_PERSISTEN = 50091
TAMPILKAN_LOG_SERVER = False
RINGKASAN: dict[str, object] = {}


# ---------------------------------------------------------------------------
# Utilitas
# ---------------------------------------------------------------------------
def judul(teks: str) -> None:
    print(f"\n{'=' * 74}\n{teks}\n{'=' * 74}", flush=True)


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
def server(port: int = PORT, *argumen: str, skrip: str = "server_grpc.py"):
    keluaran = None if TAMPILKAN_LOG_SERVER else subprocess.DEVNULL
    proses = subprocess.Popen(
        [sys.executable, str(GRPC_APP / skrip), "--port", str(port), *argumen],
        cwd=GRPC_APP,
        stdout=keluaran,
        stderr=keluaran,
    )
    try:
        tunggu_port(HOST, port)
        time.sleep(0.15)
        yield proses
    finally:
        proses.terminate()
        try:
            proses.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proses.kill()
            proses.wait(timeout=5)


@contextmanager
def kanal(port: int = PORT):
    with grpc.insecure_channel(f"{HOST}:{port}") as ch:
        grpc.channel_ready_future(ch).result(timeout=5)
        yield pb_grpc.LayananNilaiStub(ch)


def saldo_semua(stub) -> dict[str, int]:
    return {akun: ambil_saldo(stub, akun) for akun in ("A", "B")}


class ServerPersisten:
    """Server SQLite yang bisa dimatikan dan dinyalakan lagi (uji restart)."""

    def __init__(self, port: int, db: Path, dedup: str) -> None:
        self.port = port
        self.db = db
        self.dedup = dedup
        self.proses: subprocess.Popen | None = None

    def mulai(self) -> None:
        keluaran = None if TAMPILKAN_LOG_SERVER else subprocess.DEVNULL
        self.proses = subprocess.Popen(
            [
                sys.executable,
                str(GRPC_APP / "server_persisten.py"),
                "--port", str(self.port),
                "--db", str(self.db),
                "--dedup", self.dedup,
            ],
            cwd=GRPC_APP,
            stdout=keluaran,
            stderr=keluaran,
        )
        tunggu_port(HOST, self.port)
        time.sleep(0.15)

    def matikan(self) -> None:
        if self.proses is None:
            return
        self.proses.terminate()
        try:
            self.proses.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proses.kill()
            self.proses.wait(timeout=5)
        self.proses = None


# ---------------------------------------------------------------------------
# L3.1 — retry dengan request_id TETAP (benar)
# ---------------------------------------------------------------------------
def l3_1(putaran: int = 2) -> list[dict]:
    judul("L3.1 — Retry dengan request_id TETAP (efek: sekali saja / at-most-once)")
    baris: list[dict] = []
    for run in range(1, putaran + 1):
        with server(PORT, "--workers", "10", "--slow-prob", "0.3", "--slow-s", "3.0"):
            with kanal() as stub:
                hitung = {"percobaan": 0, "retry": 0, "gagal": 0}
                for i in range(20):
                    transfer(stub, f"L31-{run}-{i}", jumlah=10, timeout=2.0,
                             maks_percobaan=3, penghitung=hitung)
                saldo = saldo_semua(stub)
        data = {
            "run": run,
            "percobaan": hitung["percobaan"],
            "retry": hitung["retry"],
            "gagal": hitung["gagal"],
            **saldo,
            "total": saldo["A"] + saldo["B"],
        }
        baris.append(data)
        print(f"Run {run}: RPC={data['percobaan']} (retry {data['retry']}), "
              f"gagal={data['gagal']}, A={data['A']}, B={data['B']}, total={data['total']}")

    print("\nHarapan: A=800 (1000-200), B=700, total=1500.")
    print("Retry menemukan request_id di PROSES -> balasan sama, TANPA transfer ulang.")
    RINGKASAN["L3.1"] = baris
    return baris


# ---------------------------------------------------------------------------
# L3.2 — request_id BARU setiap percobaan (salah)
# ---------------------------------------------------------------------------
def l3_2(putaran: int = 2) -> list[dict]:
    judul("L3.2 — request_id BARU setiap percobaan (efek: transfer berulang)")
    baris: list[dict] = []
    for run in range(1, putaran + 1):
        with server(PORT, "--workers", "10", "--slow-prob", "0.3", "--slow-s", "3.0"):
            with kanal() as stub:
                hitung = {"percobaan": 0, "retry": 0, "gagal": 0}
                dilaporkan_gagal = 0
                for i in range(20):
                    try:
                        transfer_id_baru(stub, lambda: uuid.uuid4().hex, jumlah=10,
                                         timeout=2.0, maks_percobaan=3, penghitung=hitung)
                    except grpc.RpcError:
                        dilaporkan_gagal += 1
                saldo = saldo_semua(stub)
        jumlah_transfer = (1000 - saldo["A"]) // 10
        data = {
            "run": run,
            "percobaan": hitung["percobaan"],
            "retry": hitung["retry"],
            "transfer_terjadi": jumlah_transfer,
            "dilaporkan_gagal": dilaporkan_gagal,
            **saldo,
            "total": saldo["A"] + saldo["B"],
        }
        baris.append(data)
        print(f"Run {run}: transfer sampai ke server={jumlah_transfer}, "
              f"dilaporkan gagal={dilaporkan_gagal}, A={data['A']}, B={data['B']}, total={data['total']}")

    print("\nHarapan seharusnya A=800. Setiap timeout memakai ID baru -> server")
    print("menganggap permintaan berbeda dan mengeksekusi transfer lagi.")
    RINGKASAN["L3.2"] = baris
    return baris


# ---------------------------------------------------------------------------
# L3.3 — race condition tanpa lock
# ---------------------------------------------------------------------------
def l3_3() -> list[dict]:
    judul("L3.3 — Tanpa lock: race condition (harapan A=500, B=1000, total=1500)")
    konfigurasi = [
        ("dengan lock", []),
        ("tanpa lock", ["--no-lock"]),
        ("tanpa lock + jendela 2 ms", ["--no-lock", "--race-window", "0.002"]),
        ("dengan lock + jendela 2 ms", ["--race-window", "0.002"]),
    ]
    baris: list[dict] = []
    for nama, opsi in konfigurasi:
        with server(PORT, "--workers", "10", *opsi):
            with kanal() as stub:
                mulai = time.perf_counter()

                def pekerja(indeks_thread: int) -> None:
                    # 10 thread x 5 transfer = 50 transfer, masing-masing 10 unit.
                    for i in range(5):
                        transfer(stub, f"L33-{nama}-{indeks_thread}-{i}", jumlah=10,
                                 timeout=5.0, maks_percobaan=1)

                with ThreadPoolExecutor(max_workers=10) as eksekutor:
                    list(eksekutor.map(pekerja, range(10)))
                saldo = saldo_semua(stub)
                durasi = time.perf_counter() - mulai
        data = {"konfigurasi": nama, "A": saldo["A"], "B": saldo["B"],
                "total": saldo["A"] + saldo["B"], "detik": round(durasi, 2)}
        baris.append(data)
        print(f"{nama:32s}: A={saldo['A']:4d} B={saldo['B']:4d} "
              f"total={data['total']:4d}  ({durasi:.2f}s)")

    print("\nCatatan jujur: menghapus lock saja sering TIDAK memunculkan kerusakan")
    print("pada CPython (GIL + critical section sangat pendek). Jendela baca->tulis")
    print("2 ms memperbesar peluang dan membuktikan bug-nya nyata (lost update).")
    RINGKASAN["L3.3"] = baris
    return baris


# ---------------------------------------------------------------------------
# L3.4 — throughput vs max_workers
# ---------------------------------------------------------------------------
def l3_4(putaran: int = 2, daftar_worker: tuple[int, ...] = (1, 4, 10, 20),
         n_thread: int = 20, n_per_thread: int = 10) -> list[dict]:
    judul("L3.4 — Throughput vs max_workers (200 GetMahasiswa, server tidur 0,1 s)")
    baris: list[dict] = []
    total_panggilan = n_thread * n_per_thread
    for worker in daftar_worker:
        ulangan: list[dict] = []
        for _ in range(putaran):
            with server(PORT, "--workers", str(worker), "--get-delay", "0.1"):
                with kanal() as stub:
                    permintaan = pb.MahasiswaRequest(nim="2023001")

                    def pekerja() -> list[float]:
                        latensi = []
                        for _ in range(n_per_thread):
                            mulai = time.perf_counter()
                            stub.GetMahasiswa(permintaan, timeout=30)
                            latensi.append(time.perf_counter() - mulai)
                        return latensi

                    awal = time.perf_counter()
                    with ThreadPoolExecutor(max_workers=n_thread) as eksekutor:
                        semua = [lat for sub in eksekutor.map(lambda _: pekerja(), range(n_thread))
                                 for lat in sub]
                    durasi = time.perf_counter() - awal
            ulangan.append({
                "detik": durasi,
                "throughput": total_panggilan / durasi,
                "latensi_ms": statistics.fmean(semua) * 1000,
            })
        data = {
            "workers": worker,
            "detik": statistics.fmean(r["detik"] for r in ulangan),
            "throughput": statistics.fmean(r["throughput"] for r in ulangan),
            "latensi_ms": statistics.fmean(r["latensi_ms"] for r in ulangan),
        }
        baris.append(data)
        print(f"workers={worker:2d}: {data['detik']:6.2f}s | "
              f"{data['throughput']:7.1f} req/s | latensi {data['latensi_ms']:7.0f} ms")

    print("\nTeori throughput ~ max_workers / 0,1 s (10/40/100/200 req/s).")
    print("Latensi naik saat worker sedikit karena permintaan mengantre (Hukum Little).")
    _grafik_l3_4(baris)
    RINGKASAN["L3.4"] = baris
    return baris


def _grafik_l3_4(baris: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    workers = [b["workers"] for b in baris]
    throughput = [b["throughput"] for b in baris]
    latensi = [b["latensi_ms"] for b in baris]

    gambar, (kiri, kanan) = plt.subplots(1, 2, figsize=(12, 4.5))

    kiri.plot(workers, throughput, marker="o", linewidth=2, color="#1f77b4")
    for x, y in zip(workers, throughput):
        kiri.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center")
    kiri.set_xlabel("max_workers")
    kiri.set_ylabel("Throughput (req/s)")
    kiri.set_title("Throughput naik, lalu jenuh")
    kiri.grid(True, alpha=0.3)
    kiri.set_xticks(workers)

    # Sumbu-Y log: latensi turun dari ribuan ms ke ratusan ms (Hukum Little).
    kanan.plot(workers, latensi, marker="s", linewidth=2, color="#d62728")
    kanan.set_yscale("log")
    for x, y in zip(workers, latensi):
        kanan.annotate(f"{y:.0f} ms", (x, y), textcoords="offset points", xytext=(0, 8), ha="center")
    kanan.set_xlabel("max_workers")
    kanan.set_ylabel("Latensi rata-rata (ms, skala log)")
    kanan.set_title("Latensi turun saat worker bertambah")
    kanan.grid(True, alpha=0.3, which="both")
    kanan.set_xticks(workers)

    gambar.suptitle("L3.4 — Throughput & latensi vs max_workers (200 panggilan, 20 thread)")
    gambar.tight_layout()

    HASIL.mkdir(exist_ok=True)
    tujuan = HASIL / "l3_4_throughput.png"
    gambar.savefig(tujuan, dpi=150)
    plt.close(gambar)
    print(f"Grafik disimpan: {tujuan.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# L3.5 — failover dua server
# ---------------------------------------------------------------------------
def l3_5() -> list[dict]:
    judul("L3.5 — Failover: client berpindah server saat UNAVAILABLE")
    baris: list[dict] = []
    with server(PORT_FAILOVER_1) as server_1, server(PORT_FAILOVER_2):
        klien = FailoverClient([f"{HOST}:{PORT_FAILOVER_1}", f"{HOST}:{PORT_FAILOVER_2}"])
        try:
            for i in range(3):
                respons, target = klien.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="2023001"))
                print(f"  sebelum server-1 mati #{i + 1}: {target} -> {respons.nama}")
                baris.append({"fase": "sebelum", "target": target, "hasil": respons.nama})

            server_1.terminate()
            server_1.wait(timeout=5)
            time.sleep(0.3)
            print("  (server-1 dimatikan)")

            for i in range(3):
                respons, target = klien.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="2023001"))
                print(f"  setelah server-1 mati #{i + 1}: {target} -> {respons.nama}")
                baris.append({"fase": "sesudah", "target": target, "hasil": respons.nama})
        finally:
            klien.tutup()

    print("\nFailover aman untuk GetMahasiswa (idempoten). Untuk Transfer, server")
    print("kedua tidak berbagi PROSES/SALDO -> butuh state bersama/replikasi.")
    RINGKASAN["L3.5"] = baris
    return baris


# ---------------------------------------------------------------------------
# Analisis P3 — PROSES di RAM vs SQLite saat server restart
# ---------------------------------------------------------------------------
def l3_6() -> list[dict]:
    judul("Analisis P3 — Server restart: dedup RAM vs dedup SQLite")
    baris: list[dict] = []
    direktori = Path(tempfile.mkdtemp(prefix="rpc_l36_"))
    try:
        for mode in ("ram", "sqlite"):
            db = direktori / f"saldo_{mode}.db"
            srv = ServerPersisten(PORT_PERSISTEN, db, mode)
            srv.mulai()
            try:
                with kanal(PORT_PERSISTEN) as stub:
                    transfer(stub, "X", jumlah=100, timeout=5.0, maks_percobaan=1)
                    a_sebelum_restart = ambil_saldo(stub, "A")
            finally:
                srv.matikan()

            # Server "crash": balasan hilang, state di RAM lenyap (mode ram).
            srv.mulai()
            try:
                with kanal(PORT_PERSISTEN) as stub:
                    transfer(stub, "X", jumlah=100, timeout=5.0, maks_percobaan=1)
                    a_setelah_restart = ambil_saldo(stub, "A")
            finally:
                srv.matikan()

            data = {
                "dedup": mode,
                "A_setelah_transfer": a_sebelum_restart,
                "A_setelah_retry": a_setelah_restart,
                "transfer_terjadi": 2 if a_setelah_restart == 800 else 1,
            }
            baris.append(data)
            print(f"dedup={mode:6s}: A={a_sebelum_restart} -> retry -> A={a_setelah_restart} "
                  f"(transfer terjadi {data['transfer_terjadi']}x)")
    finally:
        shutil.rmtree(direktori, ignore_errors=True)

    print("\nKesimpulan: dedup di RAM kehilangan jaminan at-most-once setelah restart.")
    print("Perbaikan: saldo + log request_id di SQLite, ditulis dalam SATU transaksi")
    print("atomik (BEGIN IMMEDIATE). Yang dicapai: at-least-once + dedup = effectively-once.")
    RINGKASAN["L3.6"] = baris
    return baris


# ---------------------------------------------------------------------------
def main() -> None:
    global TAMPILKAN_LOG_SERVER
    parser = argparse.ArgumentParser(description="Praktikum 3 — semua skenario")
    parser.add_argument(
        "--bagian",
        type=int,
        nargs="+",
        choices=[1, 2, 3, 4, 5, 6],
        default=None,
        help="bagian yang dijalankan, boleh lebih dari satu (mis. --bagian 4 5); default semua",
    )
    parser.add_argument("--putaran", type=int, default=2,
                        help="jumlah ulangan untuk L3.1/L3.2/L3.4 (default 2)")
    parser.add_argument("--log-server", action="store_true", help="tampilkan log server")
    args = parser.parse_args()
    TAMPILKAN_LOG_SERVER = args.log_server

    HASIL.mkdir(exist_ok=True)
    bagian = set(args.bagian) if args.bagian else {1, 2, 3, 4, 5, 6}
    if 1 in bagian:
        l3_1(args.putaran)
    if 2 in bagian:
        l3_2(args.putaran)
    if 3 in bagian:
        l3_3()
    if 4 in bagian:
        l3_4(args.putaran)
    if 5 in bagian:
        l3_5()
    if 6 in bagian:
        l3_6()

    if RINGKASAN:
        tujuan = HASIL / "l3_ringkasan.json"
        tujuan.write_text(json.dumps(RINGKASAN, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nRingkasan angka disimpan: {tujuan.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
