"""Praktikum 2 — menjalankan L2.1 sampai L2.5 sekaligus.

Server dinyalakan otomatis (port 50071, workers 16, get-delay 0.1 s),
lalu seluruh latihan dijalankan dan server dimatikan lagi.

Jalankan:
    python l2_all.py            # semua latihan
    python l2_all.py --bagian 4 # hanya L2.4
"""

from __future__ import annotations

import argparse
import threading
import time
import xmlrpc.client

from harness import judul, server, siapkan_path

siapkan_path()

import grpc  # noqa: E402

import akademik_pb2 as pb  # noqa: E402
import akademik_pb2_grpc as pb_grpc  # noqa: E402
from klien_lama import ambil_mahasiswa_lama  # noqa: E402

HOST = "127.0.0.1"
PORT = 50071
NIM = "2023001"


# ---------------------------------------------------------------------------
# L2.0 — identifikasi stub hasil generate
# ---------------------------------------------------------------------------
def l2_0_identifikasi() -> None:
    judul("L2.0 — Stub hasil generate protoc")
    print(f"Client stub  : {pb_grpc.LayananNilaiStub.__module__}.{pb_grpc.LayananNilaiStub.__name__}")
    print(f"Server stub  : {pb_grpc.LayananNilaiServicer.__module__}.{pb_grpc.LayananNilaiServicer.__name__}")
    print(f"Message      : {', '.join(pb.Mahasiswa.DESCRIPTOR.fields_by_name)}")
    print(f"Method RPC   : {', '.join(m.name for m in pb.DESCRIPTOR.services_by_name['LayananNilai'].methods)}")
    print("\n- LayananNilaiStub  : dipakai client; tiap RPC menjadi atribut yang bisa dipanggil.")
    print("- LayananNilaiServicer: kelas dasar server; method default melempar UNIMPLEMENTED.")


# ---------------------------------------------------------------------------
# L2.1 — client streaming
# ---------------------------------------------------------------------------
def l2_1_client_streaming(stub) -> None:
    judul("L2.1 — Client streaming KirimBanyakNilai (100 valid + 1 tidak valid)")

    def generator():
        for i in range(100):
            yield pb.NilaiRequest(nim=NIM, mata_kuliah=f"MK-{i % 10}", nilai=80 + (i % 20))
        yield pb.NilaiRequest(nim=NIM, mata_kuliah="MK-INVALID", nilai=999)

    hasil = stub.KirimBanyakNilai(generator(), timeout=30)
    print(f"sukses={hasil.sukses} jumlah={hasil.jumlah} pesan='{hasil.pesan}'")
    print("Satu generator, satu respons: server menghitung yang valid dan menolak 999.")


# ---------------------------------------------------------------------------
# L2.2 — bidirectional streaming
# ---------------------------------------------------------------------------
def l2_2_diskusi() -> None:
    judul("L2.2 — Bidirectional streaming Diskusi (dua client)")
    hasil: dict[str, list[tuple[str, str]]] = {"Andi": [], "Sari": []}
    penghalang = threading.Barrier(2)

    def peserta(nama: str, isi: str) -> None:
        with grpc.insecure_channel(f"{HOST}:{PORT}") as channel:
            stub = pb_grpc.LayananNilaiStub(channel)

            def generator():
                yield pb.Pesan(pengirim=nama, isi="__join__")
                penghalang.wait(timeout=5)  # pastikan kedua peserta sudah bergabung
                time.sleep(0.3)
                yield pb.Pesan(pengirim=nama, isi=isi)
                time.sleep(2.0)  # tetap terhubung agar sempat menerima pesan balasan

            try:
                for pesan in stub.Diskusi(generator(), timeout=10):
                    hasil[nama].append((pesan.pengirim, pesan.isi))
            except grpc.RpcError as exc:
                print(f"  {nama}: stream berakhir ({exc.code().name})")

    thread_andi = threading.Thread(target=peserta, args=("Andi", "Halo Sari, nilai tugasmu berapa?"))
    thread_sari = threading.Thread(target=peserta, args=("Sari", "Halo Andi, 90. Kamu?"))
    thread_andi.start()
    thread_sari.start()
    thread_andi.join(timeout=15)
    thread_sari.join(timeout=15)

    for nama, daftar in hasil.items():
        print(f"  {nama} menerima: {daftar}")
    print("\nPengirim tidak menerima pesannya sendiri; setiap peserta punya antrean.")


# ---------------------------------------------------------------------------
# L2.3 — kompatibilitas Protobuf
# ---------------------------------------------------------------------------
def l2_3_kompatibilitas() -> None:
    judul("L2.3 — Backward compatibility: client LAMA vs server BARU")
    field_lama = ["nim", "nama", "ipk"]
    print(f"Field di stub lama : {field_lama}")
    hasil = ambil_mahasiswa_lama(HOST, PORT, NIM)
    mentah = hasil.SerializeToString()
    print(f"Client lama menerima: {hasil.nama} {hasil.ipk} | punya atribut prodi? {hasattr(hasil, 'prodi')}")
    print(f"Unknown field tersimpan (hex): {mentah.hex()}")
    print(f"Field 4 'Informatika' tetap ada di bytes? {b'Informatika' in mentah}")
    print("\nAlasan: Protobuf mengenali field lewat NOMOR, bukan nama/urutan.")
    print("Penerima yang tidak mengenal nomor 4 mengabaikannya (unknown field).")
    print("Aturan: jangan ubah/pakai ulang nomor field; hanya tambah nomor baru.")


# ---------------------------------------------------------------------------
# L2.4 — perbandingan ukuran
# ---------------------------------------------------------------------------
def l2_4_ukuran() -> None:
    judul("L2.4 — Ukuran Protobuf vs XML-RPC (payload, tanpa header)")

    mhs = pb.Mahasiswa(nim="2023001", nama="Andi", ipk=3.35)
    mhs_prodi = pb.Mahasiswa(nim="2023001", nama="Andi", ipk=3.35, prodi="Informatika")
    req = pb.MahasiswaRequest(nim="2023001")

    xml_req = xmlrpc.client.dumps(("2023001",), methodname="GetMahasiswa")
    xml_res = xmlrpc.client.dumps(
        ({"nim": "2023001", "nama": "Andi", "ipk": 3.35},), methodresponse=True
    )

    pb_res = len(mhs.SerializeToString())
    pb_res_prodi = len(mhs_prodi.SerializeToString())
    pb_req = len(req.SerializeToString())
    n_xml_req, n_xml_res = len(xml_req.encode()), len(xml_res.encode())

    print("| Pesan | Protobuf | XML-RPC | Rasio |")
    print("|---|---|---|---|")
    print(f"| Response Mahasiswa | {pb_res} B | {n_xml_res} B | {n_xml_res / pb_res:.1f}x |")
    print(f"| Response + prodi   | {pb_res_prodi} B | {n_xml_res} B | {n_xml_res / pb_res_prodi:.1f}x |")
    print(f"| Request satu NIM   | {pb_req} B | {n_xml_req} B | {n_xml_req / pb_req:.1f}x |")
    print("\nRincian Protobuf: nama field tidak dikirim (hanya nomor), angka biner.")
    print("gRPC menambah framing 5 B/pesan + HTTP/2 (HPACK); XML-RPC menambah")
    print("header HTTP/1.x teks. Rasio total tetap jauh lebih kecil di Protobuf.")


# ---------------------------------------------------------------------------
# L2.5 — asinkron
# ---------------------------------------------------------------------------
def l2_5_asinkron(stub) -> None:
    judul("L2.5 — Pemanggilan asinkron .future() (server get-delay 0,1 s)")
    permintaan = [pb.MahasiswaRequest(nim=NIM) for _ in range(10)]

    # Sinkron: 10 panggilan berurutan.
    mulai = time.perf_counter()
    for req in permintaan:
        stub.GetMahasiswa(req, timeout=5)
    t_sinkron = time.perf_counter() - mulai

    # Asinkron: kirim semua, ambil hasil kemudian.
    mulai = time.perf_counter()
    futures = [stub.GetMahasiswa.future(req, timeout=5) for req in permintaan]
    t_kirim = time.perf_counter() - mulai
    nama = {f.result(timeout=5).nama for f in futures}
    t_total = time.perf_counter() - mulai

    print(f"Sinkron 10x          : {t_sinkron * 1000:7.1f} ms")
    print(f"Asinkron kirim 10x   : {t_kirim * 1000:7.1f} ms (non-blocking)")
    print(f"Asinkron total+result: {t_total * 1000:7.1f} ms | nama={nama}")
    print("Client tidak menunggu satu per satu; server memproses paralel.")


# ---------------------------------------------------------------------------
def main() -> None:
    global HOST, PORT
    parser = argparse.ArgumentParser(description="Praktikum 2 — semua latihan")
    parser.add_argument(
        "--bagian",
        type=int,
        nargs="+",
        choices=[0, 1, 2, 3, 4, 5],
        default=None,
        help="bagian yang dijalankan, boleh lebih dari satu (mis. --bagian 1 3); default semua",
    )
    parser.add_argument("--host", default=HOST, help="host server (untuk dua komputer)")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--tanpa-server", action="store_true",
                        help="jangan nyalakan server sendiri (pakai server manual)")
    args = parser.parse_args()

    HOST, PORT = args.host, args.port

    from contextlib import nullcontext

    konteks = (
        nullcontext(None)
        if args.tanpa_server
        else server(PORT, "--workers", "16", "--get-delay", "0.1")
    )
    with konteks:
        with grpc.insecure_channel(f"{HOST}:{PORT}") as channel:
            grpc.channel_ready_future(channel).result(timeout=5)
            stub = pb_grpc.LayananNilaiStub(channel)

            bagian = set(args.bagian) if args.bagian else {0, 1, 2, 3, 4, 5}
            if 0 in bagian:
                l2_0_identifikasi()
            if 1 in bagian:
                l2_1_client_streaming(stub)
            if 2 in bagian:
                l2_2_diskusi()
            if 3 in bagian:
                l2_3_kompatibilitas()
            if 4 in bagian:
                l2_4_ukuran()
            if 5 in bagian:
                l2_5_asinkron(stub)

    print("\nSelesai. Salin keluaran ini (atau jalankan dengan | tee) untuk laporan.")


if __name__ == "__main__":
    main()
