"""Client gRPC — Praktikum 2 Langkah 4.

Panggilan dasar setiap tipe RPC: unary, server streaming, dan penanganan
error lewat status code.

Jalankan server lebih dulu:
    python server_grpc.py

Lalu:
    python client_grpc.py
    python client_grpc.py --host 192.168.1.10 --port 50051
"""

from __future__ import annotations

import argparse
import time

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc


def judul(teks: str) -> None:
    print(f"\n{'=' * 62}\n{teks}\n{'=' * 62}")


import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
from banner import cetak_identitas  # noqa: E402

def main() -> None:
    cetak_identitas()
    parser = argparse.ArgumentParser(description="Client gRPC LayananNilai")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    with grpc.insecure_channel(f"{args.host}:{args.port}") as channel:
        grpc.channel_ready_future(channel).result(timeout=5)
        stub = pb_grpc.LayananNilaiStub(channel)
        print(f"Terhubung ke {args.host}:{args.port}")
        print(f"Client stub : {type(stub).__name__}")
        print(f"Server stub : {pb_grpc.LayananNilaiServicer.__name__} (kelas dasar)")

        judul("Unary — GetMahasiswa")
        mhs = stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001"), timeout=args.timeout)
        print(f"{mhs.nama} - IPK {mhs.ipk} - {mhs.prodi}")

        judul("Unary — TambahNilai")
        status = stub.TambahNilai(
            pb.NilaiRequest(nim="2023001", mata_kuliah="Basis Data", nilai=88),
            timeout=args.timeout,
        )
        print(f"{status.pesan} (jumlah={status.jumlah})")

        judul("Server streaming — StreamNilai (diterima bertahap)")
        mulai = time.perf_counter()
        for nilai in stub.StreamNilai(pb.MahasiswaRequest(nim="2023001"), timeout=args.timeout):
            print(f"  t+{time.perf_counter() - mulai:5.2f}s  {nilai.mata_kuliah}: {nilai.nilai}")

        judul("Error — NIM tidak dikenal")
        try:
            stub.GetMahasiswa(pb.MahasiswaRequest(nim="9999"), timeout=args.timeout)
        except grpc.RpcError as exc:
            print(f"{exc.code().name} - {exc.details()}")

        judul("Error — nilai di luar 0-100")
        try:
            stub.TambahNilai(
                pb.NilaiRequest(nim="2023001", mata_kuliah="X", nilai=999),
                timeout=args.timeout,
            )
        except grpc.RpcError as exc:
            print(f"{exc.code().name} - {exc.details()}")


if __name__ == "__main__":
    main()
