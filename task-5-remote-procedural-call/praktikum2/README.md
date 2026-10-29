# Praktikum 2 — gRPC: Kontrak, Streaming, Kompatibilitas

Menjalankan lima latihan Praktikum 2 di atas kontrak `grpc_app/akademik.proto`:

| Kode | Topik | Yang dibuktikan |
|---|---|---|
| L2.0 | Stub hasil `protoc` | Struktur kelas `Stub`/`Servicer`, field message, daftar method |
| L2.1 | Client streaming `KirimBanyakNilai` | 100 nilai valid + 1 tidak valid → `jumlah=100`, 1 ditolak |
| L2.2 | Bidirectional streaming `Diskusi` | Dua client bertukar pesan pada satu koneksi |
| L2.3 | Backward compatibility | Client stub lama tetap jalan; `prodi` tersimpan sebagai unknown field |
| L2.4 | Ukuran payload | Protobuf vs XML-RPC (tanpa header HTTP) |
| L2.5 | Async `.future()` | 10 panggilan paralel ke server `--get-delay 0.1` |

## Berkas

| Berkas | Fungsi |
|---|---|
| `harness.py` | Utilitas: path proyek (`DIR_INI`, `GRPC_APP`, `OLD_STUB`, `HASIL`), context manager server, `judul()`, `tunggu_port()` |
| `l2_all.py` | Driver semua latihan; menyalakan/mematikan server otomatis |

## Cara menjalankan

Dari `task-5-remote-procedural-call/` dengan venv aktif:

```bash
# Semua latihan (server otomatis di port 50071)
python praktikum2/l2_all.py

# Satu latihan saja
python praktikum2/l2_all.py --bagian 0   # L2.0
python praktikum2/l2_all.py --bagian 1   # L2.1
python praktikum2/l2_all.py --bagian 2   # L2.2
python praktikum2/l2_all.py --bagian 3   # L2.3
python praktikum2/l2_all.py --bagian 4   # L2.4
python praktikum2/l2_all.py --bagian 5   # L2.5

# Beberapa bagian sekaligus
python praktikum2/l2_all.py --bagian 0 4
python praktikum2/l2_all.py --bagian 1 3 5
```

### Memakai server yang sudah jalan (dua terminal / dua komputer)

Terminal 1:

```bash
python grpc_app/server_grpc.py --port 50071 --slow-prob 0.3 --seed 7
```

Terminal 2:

```bash
python praktikum2/l2_all.py --host 127.0.0.1 --port 50071 --tanpa-server
```

Untuk dua komputer, ganti `--host` dengan IP server dan pastikan port terbuka. L2.5 membutuhkan `--get-delay 0.1`; tanpa server otomatis, tambahkan opsi itu saat menyalakan server.

## Hasil yang diharapkan

```text
L2.0  Client stub : akademik_pb2_grpc.LayananNilaiStub
      Server stub : akademik_pb2_grpc.LayananNilaiServicer
      Message     : nim, nama, ipk, prodi
L2.1  sukses=False jumlah=100 pesan='100 nilai tersimpan, 1 ditolak'
L2.2  Andi menerima: ['Halo Sari, ...']; Sari menerima: [...]
L2.3  Client lama menerima: Andi 3.26 | punya atribut prodi? False
      Field 4 'Informatika' tetap ada di bytes? True
L2.4  Mahasiswa 24 B vs 350 B (14,6x); +prodi 37 B; request NIM 9 B vs 163 B (18,1x)
L2.5  Sinkron 10x ±1.022 ms | Asinkron total ±109 ms
```

Angka dapat berbeda sesuai mesin. L2.2 memakai dua thread client dan server dengan `--slow-prob`; bila pesan tidak muncul, jalankan ulang.

## Catatan desain

- `harness.py` menambahkan `grpc_app/` dan `old_stub/` ke `sys.path`, sehingga skrip bisa dijalankan dari folder mana pun.
- Server dijalankan sebagai subprocess dengan `stdout/stderr` dibuang agar keluaran latihan bersih; bila gagal start, `tunggu_port()` melaporkan port tidak siap.
- Port default 50071 (bukan 50051) agar tidak bentrok dengan server yang mungkin sudah berjalan manual.

## Troubleshooting

| Gejala | Solusi |
|---|---|
| `port 50071 tidak siap` | jalankan server manual untuk melihat error; cek `--port` atau stub belum digenerate |
| L2.2 menggantung | server lambat; naikkan timeout di harness atau kurangi `--slow-prob` |
| Angka L2.5 jauh dari harapan | `--get-delay` tidak aktif (server manual) atau mesin sedang sibuk |
| `ModuleNotFoundError: klien_lama` | jalankan lewat `l2_all.py` (harness mengatur path) |
