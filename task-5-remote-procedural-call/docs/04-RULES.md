# Rules — Aturan Pengerjaan Praktikum RPC

Aturan ini mengikat kode, eksperimen, dan laporan. Bila ada konflik, urutan prioritas: **aturan modul/dosen → bagian 1 (integritas) → sisanya**.

## 1. Integritas akademik
1. Penggunaan alat bantu (termasuk AI) **wajib dicantumkan** di laporan (ketentuan modul).
2. Pahami setiap baris kode sebelum dikumpulkan; mampu menjelaskan *mengapa* hasilnya begitu.
3. Tulis analisis dengan kata sendiri; jangan menyalin tabel/kalimat mentah dari dokumen ini.
4. Angka laporan harus berasal dari **eksekusi sendiri**; jangan menyalin angka dari `01-ANALISIS.md` tanpa menjalankan ulang.
5. Screenshot diambil sendiri dari terminal sendiri.
6. Laporkan hasil apa adanya, termasuk saat hasil tidak sesuai harapan (mis. race condition tidak muncul).

## 2. Struktur dan penamaan
1. Python ≥ 3.10, virtualenv `venv/`, dependensi di `requirements.txt` (`grpcio`, `grpcio-tools`, `matplotlib`).
2. Identifier kode dalam bahasa yang konsisten dengan modul (nama RPC/field Indonesia: `GetMahasiswa`, `nim`, `nilai`). Komentar dan pesan dalam Bahasa Indonesia.
3. Satu skrip = satu tujuan; nama berkas berawalan nomor latihan (`l3_4_…`) agar mudah dipetakan ke laporan.
4. Berkas hasil generate (`*_pb2*.py`) **tidak diedit manual**; ubah `.proto` lalu generate ulang:
   `python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. akademik.proto`
5. Output mentah eksperimen disimpan di `results/` (txt/json/png).

## 3. Aturan Protocol Buffers
1. `syntax = "proto3"`; message PascalCase, field snake_case, RPC PascalCase kata kerja (`GetMahasiswa`, `KirimBanyakNilai`).
2. **Jangan mengubah atau memakai ulang nomor field.** Menambah fitur = field baru dengan nomor baru.
3. Field yang dibuang diberi `reserved <nomor>; reserved "<nama>";`.
4. Jangan mengubah tipe field yang sudah dipakai.
5. Pilih tipe RPC sesuai kebutuhan: unary (1 balasan), server streaming (banyak balasan), client streaming (banyak kiriman), bidirectional (percakapan).
6. Operasi yang mengubah state dan tidak idempoten **wajib** punya `request_id` pada request.

## 4. Aturan error dan status
1. Gunakan `context.abort(grpc.StatusCode.X, "pesan jelas")`; jangan membiarkan exception mentah (menjadi `UNKNOWN`).
2. Pemetaan: tidak ada → `NOT_FOUND`; input salah → `INVALID_ARGUMENT`; layanan mati → `UNAVAILABLE`; waktu habis → `DEADLINE_EXCEEDED`.
3. Validasi input di server (nilai 0–100, jumlah > 0, akun dikenal) — jangan percaya client.
4. XML-RPC: tangkap `Fault`, `ProtocolError`, `ConnectionError`, `socket.timeout` secara terpisah; pesan error ke pengguna tidak membocorkan detail internal.

## 5. Aturan timeout, retry, dan idempotensi
1. **Setiap** RPC client memiliki `timeout`. Tanpa timeout, client bisa menggantung selamanya.
2. Retry hanya pada `UNAVAILABLE` dan `DEADLINE_EXCEEDED`; **tidak** pada `INVALID_ARGUMENT`, `NOT_FOUND`, dll.
3. Jeda exponential backoff: `0,5 × 2^(percobaan−1)` detik; batas percobaan 3 (tambahkan jitter bila ada banyak client).
4. `request_id` dibuat **sekali** per operasi logis (di luar loop retry) dan dipakai ulang di setiap percobaan. Membuat ID baru per percobaan **dilarang** kecuali sedang mendemonstrasikan kesalahan (L3.2).
5. Operasi non-idempoten tanpa `request_id` tidak boleh di-retry otomatis.
6. Failover otomatis hanya untuk operasi idempoten, kecuali state/dedup dibagi antar server.

## 6. Aturan concurrency
1. Semua state bersama yang dimodifikasi lebih dari satu thread dilindungi lock (atau transaksi DB).
2. Lock melingkupi seluruh urutan **cek → ubah → catat** sebagai satu unit.
3. Jangan melakukan `sleep`/I/O lambat **di dalam** lock.
4. Jangan mengiterasi koleksi yang bisa dimodifikasi thread lain; iterasi salinan.
5. Dedup/log permintaan yang harus bertahan terhadap restart disimpan persisten, dan ditulis dalam **transaksi yang sama** dengan perubahan state.
6. Opsi eksperimen yang sengaja menimbulkan bug (`--no-lock`, `--race-window`) hanya untuk demonstrasi dan harus dinyatakan di laporan.
7. Jumlah `max_workers` ≥ jumlah stream panjang yang diharapkan (tiap stream `Diskusi` memegang worker).

## 7. Aturan pengukuran
1. Lakukan **pemanasan** (satu panggilan) sebelum mengukur; gunakan `time.perf_counter()`.
2. Ulangi pengukuran (≥ 3 putaran; L1.4 memakai median) dan sebutkan ukuran sampel.
3. Catat lingkungan: CPU/core, OS, versi Python/grpcio, lokal vs dua mesin.
4. Pisahkan variabel: ubah **satu** faktor per eksperimen (mis. hanya `max_workers`).
5. Hasil acak (peluang 30 %) dijalankan ≥ 2 kali; laporkan rentang, bukan satu angka.
6. Simpan data mentah; grafik dibuat dari data tersebut (bukan angka diketik manual).
7. Ukuran pesan = `len(bytes)` payload; sebutkan bila header/framing tidak dihitung.

## 8. Aturan kualitas kode
1. Tidak ada angka ajaib tersembunyi; konstanta (timeout, port, jeda) di bagian atas atau argumen CLI.
2. Skrip eksperimen membersihkan proses server (`terminate`) agar tidak ada port yang menggantung.
3. Server dapat dijalankan dengan satu perintah dan mencetak port yang dipakai.
4. Tidak ada kredensial atau path absolut milik mesin tertentu di dalam kode.
5. Tidak menyalin kode dari sumber tanpa memahami dan mencantumkannya.

## 9. Aturan laporan
1. Satu PDF per praktikum, nama `NIM_Praktikum-RPC-<nomor>.pdf`; kumpul ≤ 1 minggu setelah pertemuan.
2. Urutan: identitas → tujuan + teori (≤ 1 hlm) → langkah + kode per latihan → screenshot → analisis (tabel/grafik) → kesimpulan + kendala.
3. Tiap latihan (L1.1 … L3.5) punya subjudul sendiri dan bukti (output/screenshot) karena dinilai per latihan.
4. Tiap pertanyaan analisis dijawab dengan angka + penjelasan penyebab (bukan hanya angka).
5. Tabel L3.4 diisi lengkap dan disertai grafik.
6. Tulis keterbatasan (satu mesin, acak, jumlah putaran) dan alat bantu yang dipakai.

## 10. Aturan Git (disarankan)
1. Commit kecil per latihan: `feat(p1): L1.1 pangkat dan akar`, `test(p3): L3.3 race condition`.
2. `.gitignore`: `venv/`, `__pycache__/`, `*.db`. Berkas `*_pb2*.py` boleh dikomit agar repo langsung jalan (atau wajib ada langkah generate di README).
3. README memuat cara instal, generate stub, jalankan server/client, dan jalankan eksperimen.
