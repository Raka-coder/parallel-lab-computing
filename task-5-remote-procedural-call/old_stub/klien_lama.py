"""Klien dengan STUB LAMA (tanpa field `prodi`) — L2.3.

Klien ini memakai skema `akademik_lama.proto` (hanya nim, nama, ipk) tetapi
memanggil method yang sama di server baru:

    /akademik.LayananNilai/GetMahasiswa

Karena nama method (path) ditentukan oleh package+service di server, klien
lama memakai channel.unary_unary() dengan path tersebut secara eksplisit.

Jalankan (server baru harus hidup):
    python klien_lama.py
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import grpc

DIR_INI = Path(__file__).resolve().parent
if str(DIR_INI) not in sys.path:
    sys.path.insert(0, str(DIR_INI))

import akademik_lama_pb2 as lama  # noqa: E402

PATH_METHOD = "/akademik.LayananNilai/GetMahasiswa"


def ambil_mahasiswa_lama(host: str, port: int, nim: str, timeout: float = 5.0) -> lama.Mahasiswa:
    """Panggil server baru memakai pesan versi lama."""
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        panggil = channel.unary_unary(
            PATH_METHOD,
            request_serializer=lama.MahasiswaRequest.SerializeToString,
            response_deserializer=lama.Mahasiswa.FromString,
        )
        return panggil(lama.MahasiswaRequest(nim=nim), timeout=timeout)


import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
from banner import cetak_identitas  # noqa: E402

def main() -> None:
    cetak_identitas()
    parser = argparse.ArgumentParser(description="Klien dengan stub lama (L2.3)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--nim", default="2023001")
    args = parser.parse_args()

    field_lama = [f.name for f in lama.Mahasiswa.DESCRIPTOR.fields]
    print(f"Field Mahasiswa di stub lama : {field_lama}")

    hasil = ambil_mahasiswa_lama(args.host, args.port, args.nim)
    print(f"Client lama menerima         : {hasil.nama} {hasil.ipk}")
    print(f"Punya atribut 'prodi'?       : {hasattr(hasil, 'prodi')}")

    mentah = hasil.SerializeToString()
    print(f"Bytes hasil serialisasi      : {mentah.hex()}")
    print(f"Mengandung 'Informatika'?    : {b'Informatika' in mentah}")
    print("\nKesimpulan: client lama TETAP BERJALAN. Field nomor 4 yang tidak")
    print("dikenal disimpan sebagai unknown field dan ikut diserialisasi ulang.")


if __name__ == "__main__":
    main()
