# PANDUAN — Dari Nol Sampai Jalan

Dokumen ini menjelaskan **apa yang dibangun, kenapa begitu, dan urutan menjalankannya dari awal**. Tidak perlu paham RPC sebelumnya. Ikuti dari atas ke bawah.

---

## 1. Apa yang sebenarnya kita bangun?

Bayangkan dua program di dua komputer (atau dua terminal di satu komputer):

```text
PROGRAM A (client)                         PROGRAM B (server)
┌────────────────────┐                    ┌────────────────────┐
│ tambah(5, 3)       │  ── pesan RPC ──▶  │ terima "tambah"    │
│                    │                    │ hitung 5 + 3 = 8   │
│ terima 8           │  ◀── balasan ───   │ kirim 8            │
└────────────────────┘                    └────────────────────┘
```

Ini disebut **RPC (Remote Procedure Call)**: memanggil fungsi yang **tidak ada di program kita**, melainkan di program lain. Yang dikirim bukan panggilan fungsi biasa, tetapi **pesan** lewat jaringan (TCP + port).

Yang berubah saat RPC:

| Hal | Fungsi lokal biasa | RPC |
|---|---|---|
| Lokasi fungsi | di memori program yang sama | di proses/mesin lain |
| Data | langsung jadi objek | harus **diserialisasi** jadi byte, lalu dikirim |
| Waktu | ±0,1 mikrodetik | ±1.000 mikrodetik (serialisasi + socket + jaringan) |
| Gagal | hampir tidak mungkin | bisa timeout, server mati, balasan hilang |

Tiga praktikum mengupas tiga sisi berbeda:

| Praktikum | Pertanyaan yang dijawab |
|---|---|
| **1. XML-RPC** | Bagaimana cara paling sederhana membuat RPC? Berapa biayanya? Apa yang terjadi kalau server mati? |
| **2. gRPC** | Bagaimana RPC yang efisien dan punya kontrak ketat? Bagaimana streaming dan perubahan schema? |
| **3. Kegagalan** | Kalau balasan hilang lalu kita retry, apakah operasi jadi dobel? Bagaimana membuatnya aman? |

---

## 2. Konsep yang wajib dipahami dulu

**Server** = program yang *menunggu* di sebuah port.
**Client** = program yang *menghubungi* port itu.
Karena server harus hidup saat client memanggil, urutannya selalu: **nyalakan server dulu → baru client**.

**Port** = nomor pintu di komputer. Proyek ini memakai:

| Port | Dipakai oleh |
|---|---|
| 8000 | server XML-RPC manual |
| 8010–8012 | server otomatis untuk latihan L1 |
| 50051 | server gRPC manual |
| 50071 | server gRPC untuk `l2_all.py` |
| 50051, 50052 | dua server untuk uji failover (matikan server manual 50051 dulu) |
| 50091 | server persisten (SQLite) untuk uji restart |

**Dua teknologi di proyek ini:**

1. **XML-RPC** — data diubah menjadi teks XML lalu dikirim lewat HTTP. Mudah dibaca manusia, tapi boros (setiap angka dibungkus tag).
2. **gRPC + Protobuf** — data diubah menjadi byte biner sesuai kontrak `.proto`. Jauh lebih kecil dan cepat, tapi butuh stub hasil generate.

**Stub** = kode Python yang dibuat otomatis oleh `protoc` dari file `.proto`. Isinya kelas `LayananNilaiStub` (untuk client) dan `LayananNilaiServicer` (untuk server). Itu sebabnya ada file `*_pb2.py` dan `*_pb2_grpc.py` — **jangan diedit tangan**, generate ulang kalau `.proto` berubah.

**`request_id`** = nomor unik untuk satu operasi logis. Kalau client mengirim ulang dengan `request_id` yang sama, server tahu itu **bukan transfer baru**, melainkan pengulangan permintaan yang sama.

---

## 3. Struktur folder (setelah dirapikan)

```text
task-5-remote-procedural-call/
├── PANDUAN.md               ← dokumen ini: baca dari awal
├── README.md                ← ringkasan + quick start
├── requirements.txt         ← daftar paket Python
├── venv/                    ← lingkungan Python (dibuat sendiri, tidak di-commit)
│
├── praktikum1/              ← XML-RPC
│   ├── README.md
│   ├── server_kalkulator.py     server yang menyediakan tambah, kali, bagi, ...
│   ├── client_kalkulator.py     client demo
│   ├── server_util.py           alat bantu (tunggu port, retry, matikan server)
│   ├── l1_all.py                driver L1.1-L1.5 (bisa per bagian)
│   └── hasil/                   log hasil eksekusi L1
│
├── grpc_app/                ← inti gRPC (dipakai Praktikum 2 & 3)
│   ├── README.md
│   ├── akademik.proto           KONTRAK: daftar fungsi & bentuk data
│   ├── akademik_pb2.py          hasil generate (message)
│   ├── akademik_pb2_grpc.py     hasil generate (stub client/server)
│   ├── server_grpc.py           implementasi server
│   ├── client_grpc.py           client demo
│   └── server_persisten.py      server + SQLite (untuk uji restart)
│
├── old_stub/                ← versi lama kontrak (untuk L2.3)
│   ├── README.md
│   ├── akademik_lama.proto
│   ├── akademik_lama_pb2.py
│   └── klien_lama.py
│
├── praktikum2/              ← latihan L2.0–L2.5
│   ├── README.md
│   ├── harness.py               alat bantu: nyalakan server, tunggu port, cetak judul
│   ├── l2_all.py                driver semua latihan
│   └── hasil/                   log hasil eksekusi L2
│
├── praktikum3/              ← latihan L3.1–L3.6
│   ├── README.md
│   ├── klien.py                 retry, transfer, failover
│   ├── l3_all.py                driver semua skenario
│   └── hasil/                   log, ringkasan JSON, grafik
│
└── docs/                    ← dokumen perencanaan (analisis, PRD, arsitektur, aturan)
```

Aturan penting: **semua perintah di panduan ini dijalankan dari folder `task-5-remote-procedural-call/`.**

---

## 4. Langkah 0 — cek Python

Buka terminal, lalu:

```bash
cd /path/ke/parallel-lab-computing/task-5-remote-procedural-call
python3 --version
```

Butuh Python **3.10 atau lebih baru** (di proyek ini diuji dengan 3.14.6). Kalau `python3` tidak ada di Windows, pakai `py --version`.

---

## 5. Langkah 1 — buat lingkungan dan pasang paket

Lingkungan virtual (`venv`) = kotak berisi paket Python khusus proyek ini, supaya tidak bentrok dengan proyek lain.

```bash
# masih di folder task-5-remote-procedural-call/
python3 -m venv venv

# aktifkan (Linux/macOS)
source venv/bin/activate

# aktifkan (Windows PowerShell)
# venv\Scripts\Activate.ps1

# pasang paket
pip install --upgrade pip
pip install -r requirements.txt
```

Kalau berhasil, prompt terminal biasanya berawalan `(venv)`. **Setiap kali membuka terminal baru, aktifkan venv lagi.**

Paket yang dipasang:

| Paket | Untuk apa |
|---|---|
| `grpcio` | runtime gRPC (Praktikum 2 & 3) |
| `grpcio-tools` | `protoc` untuk generate stub dari `.proto` |
| `matplotlib` | grafik throughput L3.4 |

XML-RPC tidak butuh paket tambahan — sudah ada di Python.

---

## 6. Langkah 2 — pastikan semuanya siap

```bash
python -c "import grpc, grpc_tools, matplotlib; print('siap:', grpc.__version__)"
```

Keluaran contoh: `siap: 1.85.0`.

Stub protobuf **sudah disertakan**, jadi tidak perlu generate. Hanya kalau mengubah `.proto`:

```bash
cd grpc_app && python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. akademik.proto
cd ..

cd old_stub && python -m grpc_tools.protoc -I. --python_out=. akademik_lama.proto
cd ..
```

---

## 7. Langkah 3 — Praktikum 1 (XML-RPC), mode dua terminal

Ini cara paling mudah memahami alurnya: lihat server dan client sebagai dua program terpisah.

**Terminal 1 — nyalakan server, biarkan terbuka:**

```bash
python praktikum1/server_kalkulator.py --verbose
```

Yang terjadi:

- program membuat server di `0.0.0.0:8000`;
- `--verbose` membuat setiap panggilan dicetak, termasuk XML mentah yang dikirim/diterima;
- server **tidak selesai** — ia menunggu. Ini normal. Hentikan dengan `Ctrl+C`.

Keluaran awal:

```text
Server kalkulator XML-RPC siap di http://0.0.0.0:8000
```

**Terminal 2 — jalankan client (venv juga harus aktif):**

```bash
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
python praktikum1/client_kalkulator.py --verbose
```

Yang terjadi:

1. client membuat proxy ke `http://127.0.0.1:8000`;
2. `proxy.tambah(5, 3)` diubah menjadi request XML;
3. server menjalankan fungsi `tambah` dan mengirim balasan XML;
4. client mengubah balasan menjadi angka `8`.

Di Terminal 1 akan terlihat request masuk; di Terminal 2 terlihat hasil tiap metode (`tambah`, `kali`, `bagi`, `pangkat`, `akar`, `statistik`, `echo`).

### Latihan L1 tanpa dua terminal

Satu driver menjalankan semuanya, atau pilih bagian tertentu (boleh beberapa sekaligus).
Server dinyalakan otomatis, lalu dimatikan lagi:

```bash
python praktikum1/l1_all.py                    # L1.1 sampai L1.5
python praktikum1/l1_all.py --bagian 2         # hanya L1.2 (tidak butuh server)
python praktikum1/l1_all.py --bagian 1 3 4     # tiga bagian sekaligus
python praktikum1/l1_all.py --bagian 5         # hanya L1.5 (server dimatikan/hidupkan sendiri)
```

Pemetaan bagian: `1`=L1.1, `2`=L1.2, `3`=L1.3, `4`=L1.4, `5`=L1.5.

Yang dibuktikan tiap skrip:

| Bagian | Yang dilakukan | Hasil yang Anda lihat |
|---|---|---|
| `--bagian 1` | Memanggil `pangkat` dan `akar` | `pangkat(2,10)=1024`; `akar(-4)` → `Fault` |
| `--bagian 2` | Mengukur panjang XML untuk `tambah(5,3)` | request **190 B**, response **121 B**, padahal datanya hanya 12 B → overhead **96,1 %** |
| `--bagian 3` | `datetime`, `2**31`, `2**40`, `pangkat(2,40)`, `pangkat(2.0,40)` | `DateTime` wrapper; `OverflowError` di client (int XML-RPC 32-bit); `Fault` di server saat marshalling hasil; `double` berhasil |
| `--bagian 4` | 100× panggilan lokal vs 100× panggilan RPC | lokal **±0,1–0,19 µs**, RPC **±1,9–2,1 ms** → **±11.000–19.000×** lebih lambat; `--verbose` ±2× lebih lambat |
| `--bagian 5` | Mematikan server di tiga titik berbeda | `ConnectionRefusedError`, `RemoteDisconnected`, lalu retry berhasil menghasilkan `42` |

### 7d. L1.4 versi dua komputer (sesuai lembar latihan)

Benchmark di atas berjalan di satu mesin. Untuk memenuhi "dua komputer berbeda", lakukan di **dua mesin yang terhubung jaringan yang sama** (WiFi/router yang sama, atau VM + host).

**Komputer A (server):**

```bash
hostname -I                 # catat IP, misal 192.168.1.10   (Windows: ipconfig)
python praktikum1/server_kalkulator.py --host 0.0.0.0
```

`--verbose` boleh ditambahkan saat mendemokan isi XML, tetapi **untuk benchmark jangan dipakai**: mencatat setiap request membuat latensi ±2× lebih tinggi.

Jika ada firewall, buka port 8000:

```bash
sudo ufw allow 8000/tcp     # Ubuntu/Debian
# Windows: New-NetFirewallRule -DisplayName "XMLRPC 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**Komputer B (client)** — venv aktif, lalu:

```bash
python praktikum1/l1_all.py --bagian 4 --host 192.168.1.10
python praktikum1/client_kalkulator.py --host 192.168.1.10
```

Skrip akan **menguji koneksi dulu**; kalau gagal ia mencetak penyebab yang harus diperiksa (server belum jalan, bind ke `127.0.0.1`, firewall, atau IP salah) dan berhenti dengan kode 2. Pada mode ini skrip **tidak** menyalakan server lokal — yang diukur benar-benar lalu lintas jaringan.

Cara membaca hasil: baris `Lingkungan: JARINGAN (...)` menandakan mode dua komputer. Rasio RPC/lokal akan jauh lebih besar daripada localhost karena bertambahnya latency jaringan (biasanya 0,3–2 ms per panggilan di WiFi).

**Kesimpulan Praktikum 1:** RPC itu mudah dipakai, tetapi mahal dan bisa gagal. Program yang memakai RPC wajib menangani timeout, retry, dan server yang mati.

---

## 8. Langkah 4 — Praktikum 2 (gRPC), mode dua terminal

### 8a. Lihat kontraknya dulu

Buka `grpc_app/akademik.proto`. Isinya "daftar menu" server:

```proto
service LayananNilai {
  rpc GetMahasiswa (PermintaanNIM) returns (Mahasiswa);
  rpc TambahNilai  (NilaiBaru)     returns (Ringkasan);
  rpc StreamNilai  (PermintaanNIM) returns (stream Nilai);
  ...
}
message Mahasiswa {
  int64  nim   = 1;
  string nama  = 2;
  double ipk   = 3;
  string prodi = 4;
}
```

Angka `= 1`, `= 2`, ... adalah **nomor field**, bukan urutan tampilan. Nomor inilah yang dikirim di jaringan. Karena itu nomor tidak boleh diubah atau dipakai ulang.

### 8b. Nyalakan server (Terminal 1)

```bash
python grpc_app/server_grpc.py --workers 10
```

Keluaran:

```text
Server gRPC berjalan di 0.0.0.0:50051 (workers=10)
```

### 8c. Jalankan client (Terminal 2)

```bash
python grpc_app/client_grpc.py
```

Yang Anda lihat, berurutan:

1. `GetMahasiswa` → data Andi (IPK acak);
2. `TambahNilai` → nilai tersimpan;
3. `StreamNilai` → tiga nilai datang **bertahap** (t+0,00 s, t+0,50 s, t+1,00 s);
4. NIM tidak dikenal → `NOT_FOUND`;
5. nilai 150 → `INVALID_ARGUMENT`.

### 8d. Latihan L2 sekaligus

Hentikan server manual (`Ctrl+C`), lalu:

```bash
python praktikum2/l2_all.py
```

Server dinyalakan otomatis di port 50071. Yang dibuktikan:

| Kode | Hasil |
|---|---|
| L2.0 | stub client/server dan daftar method hasil generate |
| L2.1 | 100 nilai valid + 1 tidak valid dikirim sebagai **satu stream** → `jumlah=100`, 1 ditolak |
| L2.2 | dua client `Diskusi` saling bertukar pesan (bidirectional) |
| L2.3 | client dari kontrak **lama** tetap jalan; `prodi` tidak dikenali tapi tidak hilang |
| L2.4 | Protobuf **24 B** vs XML-RPC **350 B** (14,6× lebih kecil); request NIM **9 B** vs **163 B** (18,1×) |
| L2.5 | 10 panggilan ke server yang tidur 0,1 s: sinkron **1.021 ms**, async **109 ms** |

**Kesimpulan Praktikum 2:** kontrak biner membuat pesan jauh lebih kecil, streaming mengirim data bertahap, dan menambah field baru tidak merusak client lama.

---

## 9. Langkah 5 — Praktikum 3 (kegagalan)

Semua server dinyalakan otomatis. Jalankan:

```bash
python praktikum3/l3_all.py
```

Durasi ±2–3 menit karena beberapa skenario **sengaja menunggu timeout**.

| Kode | Skenario | Hasil yang harus terlihat |
|---|---|---|
| L3.1 | Balasan ditunda 3 s, client timeout 2 s, retry dengan `request_id` **sama** | A=800, B=700, total **1500** → transfer hanya sekali |
| L3.2 | Sama, tapi `request_id` **baru** setiap retry | transfer 26–32×, A turun ke **680–740** → uang pindah berkali-kali |
| L3.3 | 50 transfer paralel dari 10 thread | dengan lock: A=500/B=1000; tanpa lock + jeda 2 ms: **A≈870–880** (lost update) |
| L3.4 | 1/4/10/20 worker, 200 request | **9,9 / 39,4 / 97,7–98,1 / 185,5–187,3 req/s**; latensi **1930 / 486–487 / 198 / 104–105 ms** + grafik 2 panel (throughput & latensi log) |
| L3.5 | Server pertama dimatikan | client pindah ke server kedua (50052) |
| L3.6 | Server restart, lalu retry | dedup RAM → saldo terpotong 2×; dedup SQLite → tetap 1× |

Bisa dijalankan per bagian:

```bash
python praktikum3/l3_all.py --bagian 1 --putaran 1   # L3.1 saja
python praktikum3/l3_all.py --bagian 3               # L3.3 saja
python praktikum3/l3_all.py --bagian 4               # L3.4 + grafik
```

Hasil tersimpan di:

```text
praktikum3/hasil/l3_ringkasan.json      angka semua bagian
praktikum3/hasil/l3_4_throughput.png    grafik 2 panel: throughput & latensi (log)
```

**Kesimpulan Praktikum 3:** RPC tidak otomatis aman. Retry tanpa `request_id` yang stabil menggandakan efek. Lock dan penyimpanan dedup yang persisten (SQLite) adalah syarat agar operasi aman diulang.

---

## 10. Menyimpan semua log untuk laporan

Dari folder `task-5-remote-procedural-call/`, venv aktif:

```bash
python praktikum1/l1_all.py 2>&1 | tee praktikum1/hasil/l1_all.txt
python praktikum2/l2_all.py 2>&1 | tee praktikum2/hasil/l2_all.txt
python praktikum3/l3_all.py 2>&1 | tee praktikum3/hasil/l3_all.txt
```

Di Windows PowerShell:

```powershell
python praktikum1\l1_all.py | Tee-Object praktikum1\hasil\l1_all.txt
python praktikum2\l2_all.py | Tee-Object praktikum2\hasil\l2_all.txt
python praktikum3\l3_all.py | Tee-Object praktikum3\hasil\l3_all.txt
```

---

## 11. Kalau ada masalah

| Gejala | Penyebab paling umum | Solusi |
|---|---|---|
| `ModuleNotFoundError: grpc` | venv belum aktif | `source venv/bin/activate` lalu ulangi |
| `ModuleNotFoundError: akademik_pb2` | dijalankan dari folder yang salah atau stub belum ada | jalankan dari `task-5-remote-procedural-call/`, atau generate ulang (§6) |
| `Address already in use` / `Port 8000 sudah dipakai proses lain` | server dari sesi sebelumnya masih hidup | cek dengan `ss -ltnp \| grep :8000` (Linux) atau `lsof -i :8000`, lalu `kill <PID>`; atau jalankan `--port 8001`. Server sekarang menampilkan pesan ini otomatis dan berhenti dengan kode 2 |
| `UNAVAILABLE` | server belum siap / port beda / firewall | pastikan server hidup dan port sama; untuk dua komputer pakai IP server |
| Client menggantung | menunggu balasan yang tak pernah datang | `Ctrl+C`, cek log server, naikkan `--timeout` |
| L3.3 tampak "tidak ada bug" | GIL CPython menyembunyikan race singkat | itu normal; jalankan `--bagian 3` dan lihat baris "jendela 2 ms" |
| Angka berbeda dari panduan | CPU, beban, dan mesin berbeda | wajar; catat lingkungan pengukuran di laporan |

Menghentikan semua sisa server:

```bash
pkill -f "server_kalkulator|server_grpc|server_persisten"
```

---

## 12. Urutan belajar yang disarankan

1. Baca §1–§2 (konsep), lalu buka `praktikum1/server_kalkulator.py` — hanya ±120 baris.
2. Jalankan P1 mode dua terminal; lihat XML mentah dengan `--verbose`.
3. Jalankan `l1_2` dan `l1_4`; pahami kenapa RPC mahal.
4. Baca `grpc_app/akademik.proto`; bandingkan dengan `praktikum1` — di sini kontraknya eksplisit.
5. Jalankan P2 mode dua terminal, lalu `l2_all.py`.
6. Baru masuk P3: `praktikum3/klien.py` (retry + `request_id`), lalu `l3_all.py`.
7. Setelah paham, baca `docs/01-ANALISIS.md` — semua pertanyaan "kenapa" ada di sana.

Kalau baru ingin menjalankan tanpa membaca teori: ikuti §5 → §6 → §7 → §8d → §9.
