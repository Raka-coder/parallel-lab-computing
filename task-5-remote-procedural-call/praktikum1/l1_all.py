"""Praktikum 1 — semua latihan XML-RPC dalam satu driver.

Jalankan semua:
    python praktikum1/l1_all.py

Jalankan sebagian (satu atau beberapa bagian sekaligus):
    python praktikum1/l1_all.py --bagian 2
    python praktikum1/l1_all.py --bagian 2 4
    python praktikum1/l1_all.py --bagian 1 3 4 5

Uji L1.4 via Podman (tanpa komputer kedua):
    python praktikum1/l1_all.py --bagian 4 --use-podman

Uji dua komputer (L1.1-L1.4):
    # komputer A
    python praktikum1/server_kalkulator.py --host 0.0.0.0
    # komputer B
    python praktikum1/l1_all.py --bagian 1 3 4 --host 192.168.1.10

Pemetaan bagian:
    1 = L1.1 pangkat & akar
    2 = L1.2 marshalling XML + hitung overhead
    3 = L1.3 datetime & bilangan di atas 2^31
    4 = L1.4 benchmark 100 panggilan: lokal vs XML-RPC
    5 = L1.5 server mati di tiga titik + retry (selalu lokal)
"""

from __future__ import annotations

import argparse
import os
import statistics
import subprocess
import sys
import threading
import time
import xmlrpc.client
from datetime import datetime

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from banner import cetak_identitas  # noqa: E402
from server_util import (
    DIR_INI,
    HOST_LOKAL,
    PORT_DEFAULT,
    hentikan,
    panggil_aman,
    pastikan_server,
    port_terbuka,
    proxy,
    tunggu_port,
)

N_PANGGILAN = 100
N_PUTARAN = 5
BAGIAN = (1, 2, 3, 4, 5)
HASIL = DIR_INI / "hasil"


def judul(teks: str) -> None:
    print(f"\n{'=' * 70}\n{teks}\n{'=' * 70}")


# ---------------------------------------------------------------------------
# L1.1 — pangkat & akar
# ---------------------------------------------------------------------------
def l1_1(server: xmlrpc.client.ServerProxy) -> None:
    judul("L1.1 — pangkat & akar")
    print(f"pangkat(2, 10)  = {server.pangkat(2, 10)}")
    print(f"pangkat(2, 0.5) = {server.pangkat(2, 0.5)}")
    print(f"akar(144)       = {server.akar(144)}")
    try:
        server.akar(-4)
    except xmlrpc.client.Fault as fault:
        print(f"akar(-4)        -> Fault: {fault.faultString}")


# ---------------------------------------------------------------------------
# L1.2 — marshalling XML
# ---------------------------------------------------------------------------
def _ukuran(teks: str) -> int:
    return len(teks.encode("utf-8"))


def _tampilkan(judul_pesan: str, teks: str) -> int:
    n = _ukuran(teks)
    print(f"\n--- {judul_pesan} ({n} byte) ---")
    print(teks)
    return n


def l1_2() -> None:
    judul("L1.2 — Marshalling XML-RPC & overhead format")

    request = xmlrpc.client.dumps((5, 3), methodname="tambah")
    response = xmlrpc.client.dumps((8,), methodresponse=True)
    n_req = _tampilkan("methodCall tambah(5, 3)", request)
    n_res = _tampilkan("methodResponse", response)

    data_req = 2 * 4  # dua int32
    data_res = 1 * 4  # satu int32
    overhead_req = n_req - data_req
    overhead_res = n_res - data_res

    print("\n| Pesan | Total | Data murni | Overhead | % overhead |")
    print("|---|---|---|---|---|")
    print(f"| Request  | {n_req} B | {data_req} B | {overhead_req} B | {100 * overhead_req / n_req:.1f} % |")
    print(f"| Response | {n_res} B | {data_res} B | {overhead_res} B | {100 * overhead_res / n_res:.1f} % |")
    total, data = n_req + n_res, data_req + data_res
    print(f"| Total    | {total} B | {data} B | {total - data} B | {100 * (total - data) / total:.1f} % |")
    print("\nCatatan: header HTTP belum dihitung (biasanya 130-200 byte lagi per pesan).")

    data_daftar = [3, 1, 4, 1, 5, 9, 2, 6]
    req_stat = xmlrpc.client.dumps((data_daftar,), methodname="statistik")
    _tampilkan("Request statistik (list -> <array>)", req_stat)

    hasil_stat = {"min": 1, "max": 9, "rata2": 3.875}
    res_stat = xmlrpc.client.dumps((hasil_stat,), methodresponse=True)
    _tampilkan("Response statistik (dict -> <struct>)", res_stat)

    print("\nPoin:")
    print("- list  -> <array><data><value>...</value></data></array>")
    print("- dict  -> <struct><member><name>..</name><value>..</value></member></struct>")
    print("- float -> <double>; kunci dict WAJIB string (spesifikasi XML-RPC)")
    print(f"- 8 angka memakai {_ukuran(req_stat)} byte; tiap elemen dibungkus beberapa tag,")
    print("  sehingga ukuran tumbuh jauh lebih cepat daripada data sebenarnya.")


# ---------------------------------------------------------------------------
# L1.3 — batas tipe data
# ---------------------------------------------------------------------------
def _uji_tipe(judul_uji: str, aksi) -> None:
    print(f"\n--- {judul_uji} ---")
    try:
        hasil = aksi()
        print(f"hasil : {hasil!r}")
        print(f"tipe  : {type(hasil).__name__}")
    except xmlrpc.client.Fault as fault:
        print(f"FAULT (dari server): {fault.faultString}")
    except Exception as exc:  # noqa: BLE001 - sengaja menampilkan semua jenis error
        print(f"ERROR di client  : {type(exc).__name__}: {exc}")


def l1_3(server: xmlrpc.client.ServerProxy) -> None:
    judul("L1.3 — Batas tipe data: datetime & bilangan > 2^31")

    _uji_tipe("Kirim datetime.datetime", lambda: server.echo(datetime(2026, 10, 29, 14, 30, 0)))
    print("Penjelasan: XML-RPC punya tipe <dateTime.iso8601> sendiri.")
    print("            Python mengembalikan wrapper xmlrpc.client.DateTime,")
    print("            bukan datetime, kecuali dibuat dengan use_datetime=True.")

    _uji_tipe("echo(2**31 - 1) = 2147483647 (muat int32)", lambda: server.echo(2**31 - 1))
    _uji_tipe("echo(2**31) = 2147483648", lambda: server.echo(2**31))
    _uji_tipe("echo(2**40) = 1099511627776", lambda: server.echo(2**40))
    print("Penjelasan: <int>/<i4> hanya 32-bit bertanda. OverflowError terjadi")
    print("            di CLIENT saat marshalling, sebelum dikirim.")

    _uji_tipe("pangkat(2, 40) — argumen kecil, hasil kebesaran", lambda: server.pangkat(2, 40))
    print("Penjelasan: kali ini error terjadi di SERVER saat marshalling HASIL.")

    _uji_tipe("pangkat(2.0, 40) — pakai <double>", lambda: server.pangkat(2.0, 40))
    print("Penjelasan: <double> 64-bit sanggup menyimpan hasil ini.")

    print("\nSolusi untuk bilangan besar: kirim sebagai string (konversi manual),")
    print("atau float bila presisi di atas 2^53 tidak dibutuhkan.")


# ---------------------------------------------------------------------------
# L1.4 — benchmark lokal vs RPC
# ---------------------------------------------------------------------------
def _tambah_lokal(a: float, b: float) -> float:
    return a + b


def _ukur(fungsi, putaran: int) -> tuple[float, list[float]]:
    """Kembalikan (median detik, semua sampel). Pemanasan 1 panggilan dulu."""
    fungsi(0, 1)
    sampel: list[float] = []
    for _ in range(putaran):
        mulai = time.perf_counter()
        for i in range(N_PANGGILAN):
            fungsi(i, 1)
        sampel.append(time.perf_counter() - mulai)
    return statistics.median(sampel), sampel


def l1_4(server: xmlrpc.client.ServerProxy, host: str, putaran: int) -> None:
    judul(f"L1.4 — {N_PANGGILAN} panggilan tambah(), median {putaran} putaran")
    asal = "SATU MESIN (localhost)" if host in ("127.0.0.1", "localhost") else f"JARINGAN ({host})"
    print(f"Lingkungan: {asal}")

    median_lokal, _ = _ukur(_tambah_lokal, putaran)
    median_rpc, sampel_rpc = _ukur(server.tambah, putaran)

    per_lokal = median_lokal / N_PANGGILAN
    per_rpc = median_rpc / N_PANGGILAN

    print(f"Lokal     : total {median_lokal * 1000:8.4f} ms | per panggilan {per_lokal * 1e6:8.3f} us")
    print(f"XML-RPC   : total {median_rpc * 1000:8.4f} ms | per panggilan {per_rpc * 1e6:8.3f} us")
    print(f"Rasio     : XML-RPC {per_rpc / per_lokal:,.0f}x lebih lambat")
    print(f"Sampel RPC per putaran (ms): {[round(s * 1000, 3) for s in sampel_rpc]}")
    print("\nBiaya RPC bukan dari penjumlahan, melainkan serialisasi XML,")
    print("HTTP, system call socket, dan context switch antar proses.")


def l1_4_podman(port: int, putaran: int) -> None:
    """L1.4 dengan container Podman sebagai "komputer kedua"."""
    judul("L1.4 — benchmark lintas jaringan: host vs container Podman")
    print("Lingkungan: HOST (server) <-> PODMAN CONTAINER (client)")
    print("Container punya namespace jaringan sendiri, jadi traffic tidak lewat lo.")

    median_lokal, _ = _ukur(_tambah_lokal, putaran)
    per_lokal = median_lokal / N_PANGGILAN

    skrip = DIR_INI / "test_l1_4_podman.sh"
    if not skrip.exists():
        raise SystemExit(f"skrip tidak ditemukan: {skrip}")

    lingkungan = dict(os.environ, PORT=str(port), N=str(N_PANGGILAN), LEWATI_IDENTITAS="1")
    proses = subprocess.run(
        ["bash", str(skrip)],
        cwd=DIR_INI.parent,
        env=lingkungan,
        capture_output=True,
        text=True,
    )
    keluaran = proses.stdout + proses.stderr
    print()
    print(keluaran.rstrip())

    HASIL.mkdir(exist_ok=True)
    catatan = (
        f"L1.4 PODMAN — lokal {per_lokal * 1e6:.3f} us/panggilan, "
        f"port {port}, {N_PANGGILAN} request\n\n{keluaran}"
    )
    (HASIL / "l1_4_podman.txt").write_text(catatan, encoding="utf-8")

    if proses.returncode != 0:
        raise SystemExit(proses.returncode)

    baris = [b for b in keluaran.splitlines() if b.startswith("PODMAN_AVG_MS=")]
    if not baris:
        print("\nPERINGATAN: skrip tidak mengembalikan PODMAN_AVG_MS; angka tidak dirangkum.")
        return
    per_podman = float(baris[-1].split("=", 1)[1]) / 1000.0

    print()
    print(f"Lokal (host)       : {per_lokal * 1e6:8.3f} us/panggilan")
    print(f"Podman (container) : {per_podman * 1e6:8.3f} us/panggilan")
    print(f"Rasio              : container {per_podman / per_lokal:,.1f}x lebih lambat")
    print("\nKesimpulan: RPC lintas namespace jaringan tetap jauh lebih lambat")
    print("daripada pemanggilan fungsi lokal; biayanya ada pada serialisasi XML,")
    print("HTTP, socket, dan perpindahan paket, bukan pada komputasi tambah().")


# ---------------------------------------------------------------------------
# L1.5 — server mati di tiga titik
# ---------------------------------------------------------------------------
def cari_port_bebas(mulai: int) -> int:
    for port in range(mulai, mulai + 50):
        if not port_terbuka(HOST_LOKAL, port):
            return port
    raise RuntimeError(f"tidak ada port bebas mulai dari {mulai}")


def nyalakan_server(port: int) -> subprocess.Popen:
    proses = subprocess.Popen(
        [sys.executable, str(DIR_INI / "server_kalkulator.py"), "--port", str(port)],
        cwd=DIR_INI,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    tunggu_port(HOST_LOKAL, port)
    time.sleep(0.2)
    return proses


def l1_5() -> None:
    judul("L1.5 — Server mati: ConnectionRefused, RemoteDisconnected, dan retry")

    print("\n--- Skenario 1 — server mati SEBELUM panggilan ---")
    port_1 = cari_port_bebas(8010)
    server = nyalakan_server(port_1)
    hentikan(server)
    time.sleep(0.3)
    try:
        proxy(HOST_LOKAL, port_1, timeout=2.0).tambah(1, 2)
    except Exception as exc:  # noqa: BLE001 - sengaja memperlihatkan jenis aslinya
        print(f"Exception: {type(exc).__name__}: {exc}")

    print("\n--- Skenario 2 — server mati SAAT panggilan berjalan (lambat 5 s) ---")
    port_2 = cari_port_bebas(port_1 + 1)
    server = nyalakan_server(port_2)
    hasil: dict[str, object] = {}

    def panggil() -> None:
        try:
            # retry=False: transport tanpa pengulangan otomatis, agar error
            # asli saat koneksi terputus terlihat (bukan Errno 111 akibat
            # percobaan ulang ke port yang sudah tertutup).
            hasil["nilai"] = proxy(HOST_LOKAL, port_2, timeout=10.0, retry=False).lambat(5)
        except Exception as exc:  # noqa: BLE001
            hasil["error"] = f"{type(exc).__name__}: {exc}"

    thread = threading.Thread(target=panggil)
    thread.start()
    time.sleep(0.7)
    hentikan(server)
    thread.join(timeout=10)
    print(f"Hasil: {hasil.get('nilai', hasil.get('error'))}")
    print("Catatan: client TIDAK tahu apakah lambat() sempat dieksekusi di server.")

    print("\n--- Skenario 3 — server dihidupkan lagi, client retry ---")
    port_3 = cari_port_bebas(port_2 + 1)
    server = nyalakan_server(port_3)
    try:
        print("Memanggil tambah(40, 2) dengan retry maksimal 5x ...")
        hasil = panggil_aman(
            "tambah", 40, 2, host=HOST_LOKAL, port=port_3, timeout=2.0, maks_percobaan=5
        )
        print(f"Berhasil: tambah(40, 2) = {hasil}")
    finally:
        hentikan(server)


# ---------------------------------------------------------------------------
def main() -> None:
    cetak_identitas()
    parser = argparse.ArgumentParser(description="Praktikum 1 — semua latihan XML-RPC")
    parser.add_argument(
        "--bagian",
        type=int,
        nargs="+",
        choices=BAGIAN,
        default=None,
        help="bagian yang dijalankan, boleh lebih dari satu (mis. --bagian 2 4); default semua",
    )
    parser.add_argument("--host", default=HOST_LOKAL,
                        help="host server (default 127.0.0.1; isi IP untuk uji dua komputer)")
    parser.add_argument("--port", type=int, default=PORT_DEFAULT)
    parser.add_argument("--putaran", type=int, default=N_PUTARAN,
                        help="jumlah ulangan benchmark L1.4 (default 5)")
    parser.add_argument("--use-podman", action="store_true",
                        help="L1.4: ukur dari container Podman (pengganti komputer kedua)")
    args = parser.parse_args()

    bagian = sorted(set(args.bagian)) if args.bagian else list(BAGIAN)
    terpencil = args.host not in ("127.0.0.1", "localhost")
    butuh_server = bool({1, 3} & set(bagian)) or (4 in bagian and not args.use_podman)

    if 5 in bagian and terpencil:
        parser.error("L1.5 mematikan/menyalakan server lokal, jadi tidak bisa dipakai dengan --host jauh")
    if args.use_podman and terpencil:
        parser.error("--use-podman membandingkan host dan container di mesin yang sama; jangan digabung --host jauh")
    if args.use_podman and 4 not in bagian:
        parser.error("--use-podman hanya berlaku untuk --bagian 4")

    server = proses = None
    if butuh_server:
        if terpencil:
            if not port_terbuka(args.host, args.port, timeout=1.0):
                print(f"Tidak bisa terhubung ke server di {args.host}:{args.port}.", file=sys.stderr)
                print("Periksa: (1) server jalan di komputer lain, (2) dijalankan dengan --host 0.0.0.0,",
                      file=sys.stderr)
                print("         (3) firewall membuka port (Linux: sudo ufw allow 8000/tcp), (4) IP benar.",
                      file=sys.stderr)
                raise SystemExit(2)
            # Mode dua komputer: jangan menyalakan server lokal.
            server = proxy(args.host, args.port, timeout=10.0)
        else:
            server, proses = pastikan_server(args.host, args.port)

    try:
        if 1 in bagian:
            l1_1(server)
        if 2 in bagian:
            l1_2()
        if 3 in bagian:
            l1_3(server)
        if 4 in bagian:
            if args.use_podman:
                l1_4_podman(args.port, args.putaran)
            else:
                l1_4(server, args.host, args.putaran)
    finally:
        hentikan(proses)

    if 5 in bagian:
        l1_5()

    print("\nSelesai. Simpan keluaran ke praktikum1/hasil/ bila perlu:")
    print("  python praktikum1/l1_all.py 2>&1 | tee praktikum1/hasil/l1_all.txt")


if __name__ == "__main__":
    main()
