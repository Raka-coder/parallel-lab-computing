"""Identitas mahasiswa untuk header keluaran semua skrip praktikum.

Dicetak sekali di awal `main()` agar setiap log yang disalin ke laporan
langsung memuat identitas penyusun.
"""

from __future__ import annotations

GARIS = "=" * 80


def cetak_identitas(judul: str = "Praktikum Remote Procedure Calls (RPC)") -> None:
    print(GARIS)
    print("  KOMPUTASI PARALEL & TERDISTRIBUSI")
    print(f"  {judul}")
    print(GARIS)
    print("  MAHASISWA   : Raka Restu Saputra")
    print("  NIM         : 247006111172")
    print("  KELAS       : F")
    print(GARIS)
    print()
