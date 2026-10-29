# Implementation Plan — Praktikum RPC 1–3

Estimasi total: **±10–12 jam** kerja (kode sudah tersedia; sisa pekerjaan terutama verifikasi ulang di mesin sendiri, uji dua komputer, screenshot, dan penulisan laporan).

## Status saat ini
| Tahap | Status |
|---|---|
| Kode P1–P3, skrip eksperimen, stub | ✅ Selesai dan dijalankan (lingkungan 1 core, localhost) |
| Output mentah + grafik L3.4 | ✅ `results/` |
| Analisis + PRD/Arsitektur/Rules/Plan | ✅ `docs/` |
| Verifikasi ulang di mesin Raka, uji dua komputer | ⏳ Raka |
| Screenshot, penulisan laporan PDF (3 berkas) | ⏳ Raka |

## Fase 0 — Persiapan (±20 menit)
- [ ] Ekstrak ZIP, `python3 -m venv venv && source venv/bin/activate`
- [ ] `pip install -r requirements.txt`
- [ ] Generate ulang stub: `cd grpc_app && python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. akademik.proto`
- [ ] Catat spesifikasi mesin (CPU/core, OS) untuk bagian keterbatasan laporan
- **Selesai bila:** `python -c "import grpc"` berhasil.

## Fase 1 — Praktikum 1: XML-RPC (±2 jam)
| Langkah | Perintah | Hasil yang disimpan |
|---|---|---|
| Server | `cd praktikum1 && python server_kalkulator.py` | Screenshot server (log request) |
| Client verbose | `python client_kalkulator.py --verbose` | Salin satu `<methodCall>` + `<methodResponse>` |
| L1.1, L1.2 | (di client yang sama) | Output pangkat/akar/statistik |
| Marshalling + ukuran | `python praktikum1/l1_all.py --bagian 2` | Tabel overhead (jawaban analisis P1) |
| L1.3 | `python praktikum1/l1_all.py --bagian 3` | Output + penjelasan |
| **L1.4 (dua komputer)** | Server di laptop A; `python praktikum1/l1_all.py --bagian 4 --host <IP_A>` di laptop B | Tabel latensi lokal vs RPC jarak jauh |
| L1.5 | `python praktikum1/l1_all.py --bagian 5` | Exception + penanganan |
- **Selesai bila:** semua L1.x punya output, L1.4 memakai dua komputer.

## Fase 2 — Praktikum 2: gRPC (±2,5 jam)
- [ ] Buka `akademik_pb2_grpc.py`, tunjuk `LayananNilaiStub` dan `LayananNilaiServicer` (screenshot)
- [ ] `cd grpc_app && python server_grpc.py` (terminal 1), `python client_grpc.py` (terminal 2)
- [ ] `cd praktikum2 && python l2_all.py` → L2.1–L2.5 sekaligus (atau jalankan per bagian untuk screenshot)
- [ ] L2.3: pastikan paham mengapa client lama tetap jalan (aturan nomor field)
- [ ] L2.4: isi tabel Protobuf vs XML-RPC
- **Selesai bila:** semua L2.x punya output; jawaban L2.3 tertulis dengan kata sendiri.

## Fase 3 — Praktikum 3: toleransi kegagalan (±3 jam)
- [ ] `cd praktikum3 && python l3_all.py` (±2 menit; menjalankan dan menghentikan server sendiri)
- [ ] L3.1 — pastikan A=800 dan total=1500; jalankan ≥ 2 kali
- [ ] L3.2 — catat saldo A < 800 dan jelaskan
- [ ] L3.3 — laporkan hasil apa adanya; tunjukkan juga uji jendela diperlebar
- [ ] L3.4 — `python` ulang ≥ 3 putaran bila perlu; buat grafik (`praktikum3/hasil/l3_4_throughput.png` sebagai contoh format)
- [ ] L3.5 — screenshot log failover
- [ ] Analisis restart server: jalankan bagian akhir `l3_all.py`; jelaskan perbaikan SQLite
- **Selesai bila:** tabel L3.4 terisi dan semua pertanyaan analisis punya angka pendukung.

## Fase 4 — Laporan (±3 jam)
- [ ] Buat 3 PDF: `NIM_Praktikum-RPC-1.pdf`, `-2.pdf`, `-3.pdf`
- [ ] Isi tiap PDF: identitas → tujuan/teori → langkah + kode → screenshot → analisis → kesimpulan/kendala
- [ ] Tulis ulang analisis dengan kata sendiri (gunakan `01-ANALISIS.md` sebagai referensi, bukan bahan salin)
- [ ] Cantumkan alat bantu yang dipakai (AI) dan keterbatasan pengukuran
- [ ] Cek: setiap L-x ada bukti, setiap pertanyaan analisis dijawab
- [ ] Kumpulkan ≤ 1 minggu setelah pertemuan

## Fase 5 — Penutup (±30 menit)
- [ ] Jalankan seluruh skrip sekali lagi dari awal pada venv bersih
- [ ] (Opsional) Repositori Git dengan commit per latihan
- [ ] Tutup semua proses server (`pkill -f server_`)

## Peta latihan → berkas → bukti
| Latihan | Berkas | Bukti |
|---|---|---|
| L1.1 | `server_kalkulator.py`, `client_kalkulator.py` | output client |
| L1.2 | `server_kalkulator.py`, `l1_all.py` | XML list/dict |
| L1.3 | `l1_all.py` | OverflowError, DateTime |
| L1.4 | `l1_all.py` | tabel (dua komputer) |
| L1.5 | `l1_all.py`, `server_util.py` | exception + penanganan |
| L2.1–L2.5 | `server_grpc.py`, `praktikum2/l2_all.py` | output per bagian |
| L3.1–L3.3 | `klien.py`, `l3_all.py` | saldo akhir tiap skenario |
| L3.4 | `l3_all.py` | tabel + `l3_4_throughput.png` |
| L3.5 | `klien.FailoverClient` | log failover |
| Analisis P1/P3 | `l1_all.py`, `server_persisten.py` | tabel overhead; demo restart |

## Troubleshooting
| Masalah | Penyebab/solusi |
|---|---|
| `Address already in use` | Proses lama masih jalan: `pkill -f server_` atau ganti port |
| `ModuleNotFoundError: akademik_pb2` | Belum generate stub / jalankan dari folder yang benar |
| Client dua komputer `UNAVAILABLE` | Firewall menutup port, atau masih `localhost`; pakai IP server |
| Hasil L3.1 lama (±15–20 s) | Normal: timeout 2 s × retry |
| Race L3.3 tidak muncul | Normal pada CPython (GIL); gunakan `--race-window 0.002` untuk demonstrasi |
