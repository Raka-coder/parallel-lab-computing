# grpc_app — Kontrak, Server, dan Client gRPC

Berisi kontrak Protobuf, server gRPC, client, dan server persisten (SQLite) yang menjadi inti Praktikum 2 dan 3.

## Berkas

| Berkas | Fungsi |
|---|---|
| `akademik.proto` | Kontrak: package `akademik`, service `LayananNilai`, 7 RPC |
| `akademik_pb2.py`, `akademik_pb2_grpc.py` | Hasil generate — **jangan diedit tangan** |
| `server_grpc.py` | Implementasi server (unary, server-streaming, client-streaming, bidirectional) |
| `client_grpc.py` | Client demo semua RPC + penanganan error |
| `server_persisten.py` | Server dengan saldo + log `request_id` di SQLite (analisis restart P3) |

## Kontrak RPC

```proto
service LayananNilai {
  rpc GetMahasiswa (PermintaanNIM)   returns (Mahasiswa);
  rpc TambahNilai  (NilaiBaru)       returns (Ringkasan);
  rpc StreamNilai  (PermintaanNIM)   returns (stream Nilai);
  rpc KirimBanyakNilai (stream NilaiBaru) returns (Ringkasan);
  rpc Diskusi      (stream Pesan)    returns (stream Pesan);
  rpc Transfer     (PermintaanTransfer) returns (HasilTransfer);
  rpc GetSaldo     (PermintaanSaldo) returns (Saldo);
}
```

`Mahasiswa` = `nim` (1), `nama` (2), `ipk` (3), `prodi` (4). Nomor field tidak boleh diubah/dipakai ulang; data baru selalu memakai nomor baru (pelajaran L2.3).

## Generate stub

Wajib setelah mengubah `.proto`:

```bash
cd grpc_app
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. akademik.proto
cd ..        # kembali ke task-5-remote-procedural-call/
```

Hasil: `akademik_pb2.py` dan `akademik_pb2_grpc.py` di folder yang sama. Stub sudah disertakan sehingga langkah ini opsional saat pertama kali.

## Cara menjalankan

Dari `task-5-remote-procedural-call/` dengan venv aktif.

### Server

```bash
python grpc_app/server_grpc.py --workers 10
# Server LayananNilai mendengar di 0.0.0.0:50051 (10 worker)
```

Opsi:

```text
--port 50051          port dengar
--workers 10          ukuran ThreadPoolExecutor
--get-delay 0.0       detik tidur di GetMahasiswa (uji throughput)
--slow-prob 0.3       peluang balasan Transfer ditunda
--slow-s 3.0          lama penundaan (detik)
--stream-delay 0.5    jeda antar item di StreamNilai
--no-lock             DEMO BUG: Transfer tanpa lock
--race-window 0.002   jeda buatan antara baca dan tulis saldo
--seed 42             seed acak agar perilaku reprodusibel
```

### Client

Terminal lain:

```bash
python grpc_app/client_grpc.py
```

Keluaran yang diharapkan (IPK acak, bisa berbeda tiap jalan karena data dibuat di memori):

```text
Terhubung ke 127.0.0.1:50051
Unary — GetMahasiswa
Andi - IPK 3.26 - Informatika
Unary — TambahNilai
Nilai tersimpan (jumlah=1)
Server streaming — StreamNilai (diterima bertahap)
  t+ 0.00s  Basis Data: 80.0
  t+ 0.50s  Jaringan: 85.0
  t+ 1.00s  Komputasi Paralel: 90.0
Error — NIM tidak dikenal
NOT_FOUND - NIM 9999 tidak ditemukan
Error — nilai di luar 0-100
INVALID_ARGUMENT - Nilai harus 0-100
```

Client demo mencakup unary, server streaming, dan dua jalur error. `KirimBanyakNilai`, `Diskusi`, `Transfer`, dan `GetSaldo` diuji lewat `praktikum2/l2_all.py` dan `praktikum3/l3_all.py`.

Opsi client: `--host`, `--port`, `--timeout`.

### Server persisten (analisis P3)

```bash
python grpc_app/server_persisten.py --db saldo.db --dedup sqlite
python grpc_app/server_persisten.py --port 50062 --db saldo.db --dedup ram
```

- `--dedup sqlite`: `request_id` dan saldo ditulis dalam satu transaksi `BEGIN IMMEDIATE` → retry setelah restart tidak mengulang transfer.
- `--dedup ram`: dedup hanya di memori → hilang saat restart (sengaja untuk pembanding).

Port default 50061. Skrip `praktikum3/l3_all.py --bagian 6` menjalankan perbandingan ini otomatis dengan database sementara.

## Catatan

- Server mengikat `0.0.0.0` agar bisa diakses dari komputer lain; client default `127.0.0.1`.
- `--no-lock` dan `--race-window` hanya untuk demonstrasi race condition, jangan dipakai di produksi.
- Data mahasiswa disimpan di memori proses; restart mengosongkannya (kecuali saldo pada `server_persisten.py`).

## Troubleshooting

| Gejala | Solusi |
|---|---|
| `StatusCode.UNAVAILABLE` | server belum siap atau port beda; tunggu pesan "mendengar di" |
| `ModuleNotFoundError: akademik_pb2` | jalankan dari folder `grpc_app/`, atau generate ulang stub |
| `TypeError: Deskriptor...` duplikat | dua modul `.proto` dengan package sama dimuat bersamaan; `old_stub` sengaja memakai package `akademiklama` |
| `Port 50051 sudah dipakai proses lain` | server sesi lama masih hidup: `ss -ltnp \| grep :50051`, lalu `kill <PID>`; atau `--port 50052` pada server **dan** client. Catatan: gRPC memakai SO_REUSEPORT sehingga dua server bisa tampak bind ke port yang sama — pre-check socket di server mencegahnya |
