"""Helper client Praktikum 3: retry, transfer ber-request_id, dan failover.

Aturan yang diterapkan:
  - retry HANYA untuk UNAVAILABLE dan DEADLINE_EXCEEDED
  - exponential backoff 0,5 x 2^(percobaan-1) detik, maksimal 3 percobaan
  - request_id dibuat SEKALI per operasi logis (di luar loop retry)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import grpc

GRPC_APP = Path(__file__).resolve().parent.parent / "grpc_app"
if str(GRPC_APP) not in sys.path:
    sys.path.insert(0, str(GRPC_APP))

import akademik_pb2 as pb  # noqa: E402
import akademik_pb2_grpc as pb_grpc  # noqa: E402

KODE_DAPAT_DI_RETRY = (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED)


def panggil_dengan_retry(
    panggilan,
    *,
    timeout: float = 2.0,
    maks_percobaan: int = 3,
    jeda_awal: float = 0.5,
    penghitung: dict[str, int] | None = None,
):
    """Jalankan `panggilan(timeout)` dengan retry & backoff.

    `panggilan` adalah callable yang menerima `timeout` dan mengembalikan respons.
    Mengembalikan respons; melempar RpcError terakhir bila semua percobaan gagal.
    """
    for percobaan in range(1, maks_percobaan + 1):
        if penghitung is not None:
            penghitung["percobaan"] = penghitung.get("percobaan", 0) + 1
        try:
            return panggilan(timeout)
        except grpc.RpcError as exc:
            kode = exc.code()
            if kode not in KODE_DAPAT_DI_RETRY:
                raise  # INVALID_ARGUMENT, NOT_FOUND, dll: jangan diulang
            if percobaan == maks_percobaan:
                if penghitung is not None:
                    penghitung["gagal"] = penghitung.get("gagal", 0) + 1
                raise
            if penghitung is not None:
                penghitung["retry"] = penghitung.get("retry", 0) + 1
            time.sleep(jeda_awal * 2 ** (percobaan - 1))
    raise AssertionError("tidak mungkin sampai sini")


def transfer(
    stub,
    request_id: str,
    *,
    dari: str = "A",
    ke: str = "B",
    jumlah: int = 10,
    timeout: float = 2.0,
    maks_percobaan: int = 3,
    penghitung: dict[str, int] | None = None,
):
    """Transfer dengan request_id TETAP di setiap retry (cara yang benar)."""
    permintaan = pb.TransferRequest(request_id=request_id, dari=dari, ke=ke, jumlah=jumlah)
    return panggil_dengan_retry(
        lambda t: stub.Transfer(permintaan, timeout=t),
        timeout=timeout,
        maks_percobaan=maks_percobaan,
        penghitung=penghitung,
    )


def transfer_id_baru(
    stub,
    buat_id,
    *,
    dari: str = "A",
    ke: str = "B",
    jumlah: int = 10,
    timeout: float = 2.0,
    maks_percobaan: int = 3,
    penghitung: dict[str, int] | None = None,
):
    """DEMO SALAH (L3.2): request_id BARU pada setiap percobaan.

    Server menganggap setiap percobaan sebagai permintaan berbeda, sehingga
    operasi non-idempoten dieksekusi berkali-kali (at-least-once).
    """
    return panggil_dengan_retry(
        lambda t: stub.Transfer(
            pb.TransferRequest(request_id=buat_id(), dari=dari, ke=ke, jumlah=jumlah),
            timeout=t,
        ),
        timeout=timeout,
        maks_percobaan=maks_percobaan,
        penghitung=penghitung,
    )


def ambil_saldo(stub, akun: str, timeout: float = 5.0) -> int:
    return stub.GetSaldo(pb.SaldoRequest(akun=akun), timeout=timeout).saldo


class FailoverClient:
    """Client yang berpindah server saat target aktif tidak terjangkau.

    Hanya aman untuk operasi IDEMPOTEN (mis. GetMahasiswa). Untuk Transfer,
    server kedua tidak berbagi PROSES/SALDO sehingga dedup tidak berlaku.
    """

    def __init__(self, targets: list[str], timeout: float = 2.0) -> None:
        if not targets:
            raise ValueError("minimal satu target")
        self.targets = list(targets)
        self.timeout = timeout
        self.indeks = 0
        self._kanal = {t: grpc.insecure_channel(t) for t in self.targets}
        self._stub = {t: pb_grpc.LayananNilaiStub(self._kanal[t]) for t in self.targets}

    @property
    def target_aktif(self) -> str:
        return self.targets[self.indeks]

    def panggil(self, nama_method: str, permintaan):
        """Kembalikan (respons, target) atau lempar RuntimeError bila semua gagal."""
        galat: list[str] = []
        for _ in range(len(self.targets)):
            target = self.target_aktif
            try:
                respons = getattr(self._stub[target], nama_method)(permintaan, timeout=self.timeout)
                return respons, target
            except grpc.RpcError as exc:
                if exc.code() not in KODE_DAPAT_DI_RETRY:
                    raise
                galat.append(f"{target} {exc.code().name}")
                self.indeks = (self.indeks + 1) % len(self.targets)
        raise RuntimeError("semua target gagal: " + ", ".join(galat))

    def tutup(self) -> None:
        for kanal in self._kanal.values():
            kanal.close()
