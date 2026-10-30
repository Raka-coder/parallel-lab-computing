# Tugas 5 — Remote Procedure Calls (XML-RPC, gRPC, Toleransi Kegagalan)

Implementasi Praktikum 1–3 mata kuliah **Komputasi Paralel dan Terdistribusi**.

| | |
|---|---|
| Nama | Raka Restu Saputra |
| NPM | 172 |
| Kelas | F |
| Cakupan | Praktikum 1 (XML-RPC), Praktikum 2 (gRPC + Protobuf), Praktikum 3 (concurrency, timeout, kegagalan) |

> **Baru pertama kali membuka proyek ini? Baca [PANDUAN.md](PANDUAN.md).**
> Panduan tersebut menjelaskan konsep client–server, arti port, langkah instalasi, cara menjalankan tiap praktikum (termasuk mode dua terminal), dan cara membaca hasilnya — dari nol.

---

## Mulai cepat

Dari folder `task-5-remote-procedural-call/`:

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt

python praktikum1/l1_all.py
python praktikum2/l2_all.py
python praktikum3/l3_all.py
```

Tiga perintah terakhir adalah inti tugas: XML-RPC, gRPC, lalu skenario kegagalan.

---

## Struktur

```text
task-5-remote-procedural-call/
├── PANDUAN.md              # tutorial dari nol (mulai di sini)
├── README.md               # dokumen ini
├── requirements.txt        # grpcio, grpcio-tools, matplotlib
├── docs/                   # analisis, PRD, arsitektur, aturan, rencana
├── praktikum1/             # XML-RPC: server kalkulator + driver L1.1–L1.5
├── grpc_app/               # kontrak .proto, server, client, server persisten
├── old_stub/               # kontrak lama untuk uji kompatibilitas L2.3
├── praktikum2/             # L2.0–L2.5 (gRPC)
├── praktikum3/             # L3.1–L3.6 (retry, race, failover, restart)
│
├── praktikum1/hasil/       # log L1 (l1_all.txt)
├── praktikum2/hasil/       # log L2 (l2_all.txt)
├── praktikum3/hasil/       # log L3, ringkasan JSON, grafik
└── venv/                   # lingkungan Python (dibuat sendiri, tidak di-commit)
```

Setiap folder praktikum punya README cara menjalankan sendiri:

| Folder | Isi | README |
|---|---|---|
| `praktikum1/` | XML-RPC: marshalling, batas tipe, latensi, server mati | [README](praktikum1/README.md) |
| `grpc_app/` | kontrak, server, client, server persisten | [README](grpc_app/README.md) |
| `old_stub/` | client lama vs server baru | [README](old_stub/README.md) |
| `praktikum2/` | L2.0–L2.5 | [README](praktikum2/README.md) |
| `praktikum3/` | L3.1–L3.6 | [README](praktikum3/README.md) |

---

## Cara menjalankan per praktikum

### Praktikum 1 — XML-RPC

```bash
# Mode dua terminal (paling mudah dipahami)
python praktikum1/server_kalkulator.py --verbose     # terminal 1
python praktikum1/client_kalkulator.py --verbose     # terminal 2

# Latihan otomatis (satu driver; server dinyalakan sendiri)
python praktikum1/l1_all.py                 # semua L1.1-L1.5
python praktikum1/l1_all.py --bagian 2      # hanya L1.2
python praktikum1/l1_all.py --bagian 2 4    # hanya L1.2 dan L1.4
python praktikum1/l1_all.py --bagian 4 --use-podman   # L1.4 via container
powershell -ExecutionPolicy Bypass -File praktikum1/test_l1_4_wsl.ps1  # L1.4 via WSL2
```

### Praktikum 2 — gRPC

```bash
# Mode dua terminal
python grpc_app/server_grpc.py --workers 10          # terminal 1
python grpc_app/client_grpc.py                       # terminal 2

# Semua latihan L2 (server otomatis di port 50071)
python praktikum2/l2_all.py
python praktikum2/l2_all.py --bagian 0 4     # hanya L2.0 dan L2.4
```

### Praktikum 3 — concurrency & kegagalan

```bash
# Semua skenario (±2–3 menit; beberapa sengaja menunggu timeout)
python praktikum3/l3_all.py

# Per bagian (boleh lebih dari satu)
python praktikum3/l3_all.py --bagian 4   # throughput + grafik
python praktikum3/l3_all.py --bagian 4 5 # throughput + failover
python praktikum3/l3_all.py --bagian 6   # restart: dedup RAM vs SQLite
```

---

## Hasil pengukuran

Lingkungan: AMD Ryzen 5 3500U (8 logical core), Linux, Python 3.14.6, grpcio 1.85.0, **satu mesin (localhost)**; L1.4 juga diuji dari **WSL2 Debian** di Windows (Python 3.13.5) ke server Windows.

| Latihan | Hasil |
|---|---|
| P1 — ukuran `tambah(5,3)` | request **190 B**, response **121 B** dari data 12 B → overhead **96,1 %** |
| P1 — latensi 100× `tambah` | lokal ±0,06–0,19 µs vs XML-RPC ±1,9–2,1 ms → **±11.000–32.000×**; via Podman **±1,7–1,9 ms** (**±24.000–31.000×**, isolasi network namespace); via WSL2 **±3,05–3,19 ms** (**±28.000–67.000×**, Hyper-V Virtual Switch) |
| P2 — ukuran `Mahasiswa` | Protobuf **24 B** (37 B dengan `prodi`) vs XML-RPC **350 B** → **14,6×** |
| P2 — request satu NIM | Protobuf **9 B** vs XML-RPC **163 B** → **18,1×** |
| P2 — async 10× (server 0,1 s) | sinkron 1.021 ms vs future 109 ms |
| L3.1 — `request_id` tetap | A=800, B=700, total **1500** (at-most-once) |
| L3.2 — `request_id` baru | transfer 26–32×, A turun ke 680–740 → uang pindah berkali-kali |
| L3.3 — tanpa lock + jeda 2 ms | A≈870–880 (seharusnya 500) → lost update |
| L3.4 — throughput | 9,9 / 39,4 / 97,7–98,1 / 185,5–187,3 req/s (workers 1/4/10/20); latensi 1930/486–487/198/104–105 ms |
| L3.5 — failover | server-1 (50051) mati → pindah ke 50052 |
| L3.6 — restart | dedup RAM: A 900→800; dedup SQLite: A 900→900 |

Log lengkap: [`praktikum1/hasil/`](praktikum1/hasil/), [`praktikum2/hasil/`](praktikum2/hasil/), [`praktikum3/hasil/`](praktikum3/hasil/). Jalankan ulang sendiri sebelum menyalin ke laporan — angka bisa berbeda karena hasil acak dan mesin berbeda.

---

## Uji dua komputer

Di komputer server:

```bash
python praktikum1/server_kalkulator.py        # 0.0.0.0:8000
python grpc_app/server_grpc.py                # 0.0.0.0:50051
```

Di komputer client (ganti `<IP_SERVER>`, buka port di firewall):

```bash
python praktikum1/l1_all.py --bagian 1 3 4 --host <IP_SERVER>
python praktikum1/client_kalkulator.py --host <IP_SERVER>
python grpc_app/client_grpc.py --host <IP_SERVER>
python praktikum2/l2_all.py --host <IP_SERVER> --port 50071 --tanpa-server
```

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError: grpc` | venv belum aktif / `pip install -r requirements.txt` |
| `ModuleNotFoundError: akademik_pb2` | jalankan dari folder `task-5-remote-procedural-call/`, atau generate ulang stub |
| `Address already in use` / `Port ... sudah dipakai` | server sesi lama masih hidup: `ss -ltnp \| grep :8000`, `kill <PID>`, atau pakai `--port` lain |
| Client dua komputer `UNAVAILABLE` | firewall, atau masih memakai `localhost` |
| L3.3 tidak menunjukkan bug | normal di CPython; bandingkan dengan `--bagian 3` (jendela 2 ms) |

Penjelasan lengkap tiap gejala ada di [PANDUAN.md §11](PANDUAN.md#11-kalau-ada-masalah).

---

## Catatan akademik

- Seluruh angka harus berasal dari eksekusi sendiri (`docs/04-RULES.md`).
- Alat bantu AI dipakai untuk menyusun kode dan dokumentasi; tulis ulang analisis dengan kata sendiri dan cantumkan penggunaannya sesuai ketentuan modul.
- Keterbatasan: pengukuran satu mesin (localhost), beban acak pada L3.1–L3.3, jumlah putaran terbatas.
