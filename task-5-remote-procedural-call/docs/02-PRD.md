# PRD — Paket Pengerjaan Praktikum RPC 1–3 (Individu)

| | |
|---|---|
| Mata kuliah | Komputasi Paralel dan Terdistribusi — Universitas Siliwangi |
| Topik | Remote Procedure Calls (XML-RPC, gRPC, toleransi kegagalan) |
| Cakupan | **Praktikum 1–3 saja** (tugas individu). Tugas Proyek Mini kelompok *di luar cakupan* |
| Pemilik | Raka |
| Versi / tanggal | 1.0 — 29 Oktober 2026 |

## 1. Latar belakang dan tujuan
Modul menilai Praktikum 1–3 secara terpisah: setiap latihan (L1.x, L2.x, L3.x) bernilai sama dan pertanyaan analisis menambah nilai laporan. Tujuan produk ini: **menghasilkan kode yang berjalan, data ukur yang dapat diverifikasi, dan analisis yang kuat** sebagai bahan dua-tiga laporan praktikum, sekaligus sebagai bahan belajar.

### Capaian pembelajaran yang dipenuhi
| CPMK modul | Dipenuhi oleh |
|---|---|
| Cara kerja RPC (stub, marshalling) | P1 (XML terlihat), P2 (stub hasil generate) |
| Bandingkan RPC vs lokal vs socket | L1.4, L2.4 |
| Bangun layanan XML-RPC dan gRPC | P1, P2 |
| Definisi antarmuka dengan IDL | `akademik.proto` |
| Concurrency, timeout, kegagalan | P3 |
| Ukur latensi dan throughput | L1.4, L3.4 |

## 2. Sasaran dan non-sasaran
**Sasaran**
- G1. Seluruh 15 latihan (L1.1–L3.5) + 3 pertanyaan analisis memiliki kode, output, dan analisis.
- G2. Semua angka di laporan bisa direproduksi dengan satu perintah per praktikum.
- G3. Perbedaan perilaku *benar vs salah* terbukti dengan eksperimen (retry ber-ID vs ber-ID baru; dengan vs tanpa lock; dedup RAM vs persisten).

**Non-sasaran**
- Tugas Proyek Mini (5 studi kasus), TLS/autentikasi, deployment produksi, UI.

## 3. Pengguna dan skenario
| Pengguna | Kebutuhan |
|---|---|
| Raka (mahasiswa) | Kode siap jalan, hasil nyata, penjelasan untuk dituliskan ulang ke laporan dengan kata sendiri |
| Dosen/asisten | Laporan sesuai format (identitas, tujuan, langkah+kode, screenshot, analisis, kesimpulan) dan kode bisa dijalankan dengan README |

## 4. Kebutuhan fungsional

### 4.1 Praktikum 1 — XML-RPC
| ID | Kebutuhan | Kriteria penerimaan |
|---|---|---|
| FR-1.0 | Server kalkulator (`tambah`, `kali`, `bagi`) + client verbose | `5+3=8`, `4x7=28`, bagi-nol menghasilkan `Fault`; pesan `<methodCall>`/`<methodResponse>` tercetak |
| FR-1.1 | `pangkat(a,b)`, `akar(x)` | `pangkat(2,10)=1024`; `akar(-4)` → `Fault` |
| FR-1.2 | `statistik(daftar)` → `{min,max,rata2}` | Mengembalikan dict benar; XML `<array>`/`<struct>` didokumentasikan |
| FR-1.3 | Uji `datetime` dan int > 2³¹ | Perilaku + penyebab tercatat (OverflowError; `DateTime`) |
| FR-1.4 | Benchmark 100× `tambah()` vs lokal, dukung host jarak jauh | Skrip menerima argumen IP; tabel hasil |
| FR-1.5 | Penanganan server mati | Exception diamati (Refused/Reset) dan ditangani, ada retry |
| FR-1.A | Analisis ukuran XML `tambah(5,3)` | Byte total, data murni, % overhead |

### 4.2 Praktikum 2 — gRPC
| ID | Kebutuhan | Kriteria penerimaan |
|---|---|---|
| FR-2.0 | `akademik.proto` + stub ter-generate | `LayananNilaiStub` dan `LayananNilaiServicer` teridentifikasi |
| FR-2.1 | Unary `GetMahasiswa`, `TambahNilai`; server streaming `StreamNilai` | Streaming datang bertahap (±0,5 s/item); error `NOT_FOUND`/`INVALID_ARGUMENT` |
| FR-2.2 | L2.1 client streaming `KirimBanyakNilai` | Mengembalikan jumlah tersimpan |
| FR-2.3 | L2.2 bidirectional `Diskusi` | Dua client saling menerima pesan; disconnect bersih |
| FR-2.4 | L2.3 kompatibilitas | Client lama vs server baru (field `prodi=4`) tetap jalan |
| FR-2.5 | L2.4 perbandingan ukuran | `len(SerializeToString())` vs XML-RPC, rasio |
| FR-2.6 | L2.5 asinkron | 10 `.future()` dikumpulkan via `.result()` |

### 4.3 Praktikum 3 — Concurrency dan kegagalan
| ID | Kebutuhan | Kriteria penerimaan |
|---|---|---|
| FR-3.0 | RPC `Transfer` + dedup `request_id`, balasan lambat acak 30 % | Respons duplikat dikembalikan tanpa eksekusi ulang |
| FR-3.1 | Client timeout 2 s + retry exponential backoff (UNAVAILABLE/DEADLINE_EXCEEDED saja) | 20 transfer → A tepat −200, total 1500 |
| FR-3.2 | Variasi uuid baru tiap percobaan | A < 800 terbukti; dijelaskan |
| FR-3.3 | Variasi tanpa lock, 50 transfer / 10 thread | Hasil dilaporkan jujur (termasuk jika race tidak muncul) + demonstrasi jendela diperlebar |
| FR-3.4 | Throughput untuk workers = 1, 4, 10 | Tabel + grafik; analisis penyebab |
| FR-3.5 | Failover 2 server | Client pindah otomatis saat `UNAVAILABLE` |
| FR-3.A | Analisis restart server | Demonstrasi + perbaikan persisten (SQLite, transaksi atomik) |

## 5. Kebutuhan non-fungsional
- **Reprodusibilitas:** Python ≥ 3.10; satu `requirements.txt`; skrip eksperimen otomatis (`l2_all.py`, `l3_all.py`).
- **Keterbacaan:** komentar dan pesan dalam Bahasa Indonesia; satu file = satu tujuan.
- **Kebenaran pengukuran:** pemanasan sebelum ukur, median/rata-rata dari beberapa putaran, hasil mentah disimpan di `praktikumN/hasil/`.
- **Kejujuran akademik:** keterbatasan (satu mesin, acak) dicantumkan; penggunaan alat bantu dicantumkan di laporan sesuai ketentuan modul.
- **Portabilitas:** server mendengarkan `0.0.0.0`/`[::]`; host client dapat diubah untuk uji dua komputer.

## 6. Deliverable
| Berkas | Isi |
|---|---|
| `` (ZIP) | Kode P1–P3, stub, skrip eksperimen, `praktikumN/hasil/` |
| `docs/01-ANALISIS.md` | Hasil + analisis per latihan |
| `docs/02-PRD.md` … `05-IMPLEMENTATION_PLAN.md` | Dokumen perencanaan |
| `NIM_Praktikum-RPC-1.pdf`, `-2.pdf`, `-3.pdf` *(dibuat Raka)* | Laporan sesuai format modul |

## 7. Format laporan (dari modul)
1. Identitas (nama, NIM, kelas, nomor praktikum) · 2. Tujuan + dasar teori (≤ 1 hlm) · 3. Langkah kerja + kode tiap latihan · 4. Screenshot server & client · 5. Jawaban analisis + tabel/grafik · 6. Kesimpulan + kendala. Penamaan: `NIM_Praktikum-RPC-<nomor>.pdf`; kumpul ≤ 1 minggu setelah pertemuan.

## 8. Metrik keberhasilan
- 15/15 latihan + 3/3 pertanyaan analisis terjawab dengan bukti.
- Seluruh skrip berjalan tanpa error pada mesin bersih mengikuti README.
- Setiap klaim analisis punya angka atau kutipan output.

## 9. Risiko dan mitigasi
| Risiko | Dampak | Mitigasi |
|---|---|---|
| Uji dua komputer belum dilakukan | L1.4 tidak memenuhi soal | Jalankan `praktikum1/l1_all.py --bagian 4 --host <IP>` di lab/laptop kedua; catat di laporan |
| Race condition L3.3 tidak muncul | Kesimpulan salah ("tidak ada race") | Laporkan apa adanya + jendela diperlebar + penjelasan GIL |
| Hasil acak berbeda antar run | Angka laporan ≠ angka di sini | Jalankan ulang, pakai angka sendiri; analisis kualitatif tetap |
| Kemiripan antar mahasiswa / kode dari alat bantu | Pemeriksaan kesamaan | Pahami kode, tulis ulang analisis dengan kata sendiri, cantumkan alat bantu |
| Port bentrok / firewall | Server tidak terjangkau | Port dapat diganti; buka port 8000/50051 untuk uji dua komputer |

## 10. Asumsi dan pertanyaan terbuka
- Asumsi: pembagian laporan = satu PDF per praktikum (3 PDF). *Konfirmasi dengan dosen jika diminta satu PDF.*
- Asumsi: Soal teori (Latihan Soal Teori) dikerjakan terpisah dan tidak termasuk paket ini.
