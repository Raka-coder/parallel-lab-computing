# Analisis Praktikum 1–3: Remote Procedure Calls

> Mata kuliah Komputasi Paralel dan Terdistribusi — bagian tugas individu (Praktikum 1–3).
> Semua angka di dokumen ini berasal dari eksekusi kode di folder ini (output mentah ada di `praktikum1/hasil/`, `praktikum2/hasil/`, `praktikum3/hasil/`).
> Lingkungan ukur: Python 3.12, grpcio 1.85, **satu mesin (localhost), 1 core CPU**.

## 0. Ringkasan temuan

| # | Temuan | Bukti |
|---|--------|-------|
| 1 | Pesan XML-RPC `tambah(5,3)` berukuran **190 B** (request) + **121 B** (response) untuk data murni 8 B + 4 B → **±96 % adalah overhead** format | §1.6 |
| 2 | RPC jauh lebih lambat dari panggilan lokal: **0,403 ms vs 0,049 µs** per panggilan (±8.200×) | §1.4 |
| 3 | Protobuf **14,6×** lebih kecil dari XML-RPC untuk data mahasiswa yang sama (24 B vs 350 B) | §2.4 |
| 4 | Menambah field Protobuf baru **tidak merusak** client lama (backward compatible) | §2.3 |
| 5 | Retry tanpa ID tetap → transfer ganda (A turun 280, seharusnya 200). Dengan `request_id` tetap → tepat 200 | §3.1–3.2 |
| 6 | Tanpa lock, race condition **tidak selalu muncul** (GIL + critical section sangat pendek), tetapi terbukti nyata saat jendela diperlebar | §3.3 |
| 7 | Throughput server naik hampir linear terhadap `max_workers` (10 → 39 → 97 → 188 req/s) untuk beban yang menunggu (I/O-bound) | §3.4 |
| 8 | Dedup `request_id` yang hanya di RAM **kehilangan jaminan at-most-once saat server restart**; perbaikan: log di database dalam satu transaksi dengan perubahan saldo | §3.6 |

---

## 1. Praktikum 1 — XML-RPC

### 1.1 Langkah 1–3 (server, client, pengamatan)
Server `SimpleXMLRPCServer` di port 8000 mendaftarkan `tambah`, `kali`, `bagi` (+ fungsi tambahan latihan). Client `ServerProxy(..., verbose=True)` mencetak pesan HTTP dan XML.

Pesan yang ditangkap untuk laporan (`tambah(5, 3)`):

```xml
<!-- methodCall (Content-Length: 190) -->
<?xml version='1.0'?>
<methodCall>
<methodName>tambah</methodName>
<params>
<param>
<value><int>5</int></value>
</param>
<param>
<value><int>3</int></value>
</param>
</params>
</methodCall>

<!-- methodResponse (Content-length: 121) -->
<?xml version='1.0'?>
<methodResponse>
<params>
<param>
<value><int>8</int></value>
</param>
</params>
</methodResponse>
```

Error `bagi(10, 0)` **tidak** menjadi error HTTP; server tetap membalas `HTTP 200` dengan `<fault>` (faultCode 1, faultString `<class 'ValueError'>:Pembagian dengan nol`), lalu client stub mengubahnya menjadi `xmlrpc.client.Fault`. Ini contoh stub menyembunyikan jaringan: error server tampak seperti exception lokal.

### 1.2 L1.1 — `pangkat(a, b)` dan `akar(x)`
`pangkat(2,10)=1024`, `pangkat(2,0.5)=1.4142135623730951`, `akar(144)=12.0`. `akar(-4)` melempar `ValueError` di server → sampai ke client sebagai `Fault`. Catatan: `pangkat(2, 40)` justru **gagal** (lihat L1.3).

### 1.3 L1.2 — `statistik(daftar)`
`statistik([3,1,4,1,5,9,2,6])` → `{'min': 1, 'max': 9, 'rata2': 3.875}`. Marshalling:

- `list` → `<array><data> <value><int>…</int></value> … </data></array>`
- `dict` → `<struct>` berisi `<member><name>…</name><value>…</value></member>`
- `float` → `<double>`; kunci dict **wajib string** (XML-RPC `struct`).
- Request 8 angka = **389 B**; response dict 3 anggota = **331 B**. Setiap elemen kecil dibungkus beberapa tag, sehingga ukuran tumbuh jauh lebih cepat daripada datanya.

### 1.4 L1.4 — Latensi 100 panggilan `tambah()`

| Pemanggilan | Total 100 panggilan | Per panggilan |
|---|---|---|
| Fungsi lokal | 0,0049 ms | 0,049 µs |
| XML-RPC (localhost) | 40,32 ms (median 5 putaran) | 0,403 ms |
| XML-RPC (WSL2 Debian → Windows) | 305,2 ms (median 5 putaran) | 3,052 ms |
| **Rasio localhost** | | **±8.246× lebih lambat** |

Analisis: biaya RPC berasal dari serialisasi XML, pembuatan/penguraian HTTP, system call socket, dan context switch antar proses — bukan dari penjumlahan itu sendiri. Pada **dua komputer berbeda** angkanya akan lebih besar lagi karena ditambah latensi jaringan (RTT) per panggilan. Pelajaran desain: hindari pemanggilan RPC kecil berulang (*chatty interface*); gabungkan menjadi satu panggilan batch.

> ⚠️ Baris lokal dan localhost diukur di **satu mesin**. Uji lintas jaringan sudah dilakukan dari **WSL2 Debian** ke server Windows melalui Hyper-V Virtual Switch: **±3,05–3,19 ms/panggilan** vs lokal WSL **±0,05–0,11 µs** (±28.000–67.000×), log `praktikum1/hasil/l1_4_wsl.txt`. Jalankan ulang dengan `powershell -ExecutionPolicy Bypass -File praktikum1/test_l1_4_wsl.ps1` atau `wsl -d Debian -- python3 praktikum1/rpc_l14_wsl.py`.

### 1.5 L1.3 — `datetime` dan bilangan > 2³¹

| Uji | Hasil | Penyebab |
|---|---|---|
| Kirim `datetime` | Sampai sebagai `<dateTime.iso8601>20261029T14:30:00`; di sisi penerima menjadi objek `xmlrpc.client.DateTime`, bukan `datetime` | XML-RPC punya tipe tanggal sendiri; Python mengembalikan wrapper kecuali `use_datetime=True` |
| `echo(2**31 - 1)` | Berhasil | Muat dalam `<int>` 32-bit bertanda |
| `echo(2**31)` dan `echo(2**40)` | **`OverflowError: int exceeds XML-RPC limits`** (terjadi di *client*, sebelum dikirim) | Spesifikasi XML-RPC: `<int>`/`<i4>` hanya 32-bit bertanda (−2³¹ … 2³¹−1) |
| `pangkat(2, 40)` | `Fault: OverflowError` — kali ini terjadi di **server** saat marshalling *hasil* | Argumen kecil, hasil melampaui batas |
| `pangkat(2.0, 40)` | `1099511627776.0` | `<double>` 64-bit sanggup |

Solusi: kirim bilangan besar sebagai **string** (konversi manual di kedua sisi) atau `float` (kehilangan presisi di atas 2⁵³). Pelajaran: **IDL/skema tipe menentukan apa yang bisa dikirim**; kesalahan bisa muncul di sisi yang tidak terduga (server, bukan hanya client).

### 1.6 L1.5 — Server dimatikan saat client berjalan

| Skenario | Exception |
|---|---|
| Server mati **sebelum** panggilan | `ConnectionRefusedError: [Errno 111] Connection refused` |
| Server mati **saat** panggilan berjalan (`lambat(5)`) | `ConnectionResetError: [Errno 104] Connection reset by peer` |

Penanganan (`panggil_aman()` di `server_util.py`): `try/except` terpisah untuk `xmlrpc.client.Fault` (error logika server), `ProtocolError` (HTTP), `ConnectionError`/`RemoteDisconnected` (server tidak terjangkau), dan `socket.timeout`. Dengan retry sederhana (0,5 s × 5 kali), client berhasil mendapat hasil `42` setelah server dihidupkan lagi pada percobaan ke-4.

Poin penting: pada skenario kedua client **tidak tahu** apakah `lambat()` sempat dieksekusi — inilah masalah *semantik pemanggilan* (maybe/at-least-once) yang dibahas di Praktikum 3.

### 1.7 Pertanyaan analisis Praktikum 1 — ukuran pesan `tambah(5, 3)`

| Pesan | Ukuran total | Data sebenarnya | Overhead |
|---|---|---|---|
| Request (`methodCall`) | 190 B | 8 B (dua int32) | 182 B = **95,8 %** |
| Response (`methodResponse`) | 121 B | 4 B (satu int32) | 117 B = **96,7 %** |
| Keduanya | 311 B | 12 B | 299 B = **96,1 %** |

Ini belum termasuk header HTTP (±130–200 B lagi per pesan). Overhead berasal dari tag XML, deklarasi `<?xml?>`, nama metode, dan pembungkus `<params><param><value>`. Format teks mudah dibaca/di-debug tetapi boros — motivasi Praktikum 2 (Protobuf biner).

---

## 2. Praktikum 2 — gRPC dan Protocol Buffers

### 2.1 Langkah 1–4 (kontrak, stub, server, client)
Stub dihasilkan dengan `python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. akademik.proto`. Di `akademik_pb2_grpc.py`:

- **`LayananNilaiStub`** — *client stub*: dibuat dari channel, setiap RPC menjadi atribut yang bisa dipanggil (`stub.GetMahasiswa(...)`).
- **`LayananNilaiServicer`** — kelas dasar *server stub/skeleton*: method default melempar `UNIMPLEMENTED`; kita meng-*override* sesuai kontrak. `add_LayananNilaiServicer_to_server()` mendaftarkannya ke server.
- `akademik_pb2.py` — kelas message (`Mahasiswa`, `NilaiRequest`, …) beserta serialisasi biner.

Hasil eksekusi: `Andi - IPK 3.26`; `Nilai tersimpan`; server streaming mengirim `Basis Data` pada t+0,01 s, `Jaringan` pada t+0,51 s, `Komputasi Paralel` pada t+1,01 s (client menerima **bertahap**, bukan menunggu semuanya). Error ditangani lewat status code: `NOT_FOUND – NIM 9999 tidak ditemukan`, `INVALID_ARGUMENT – Nilai harus 0-100`.

### 2.2 L2.1 — Client streaming `KirimBanyakNilai`
Client mengirim 100 nilai valid + 1 nilai tidak valid (999) lewat satu generator. Server mengonsumsi `request_iterator`, menyimpan yang valid, dan membalas **satu** respons: `sukses=False, jumlah=100, pesan='100 nilai tersimpan, 1 ditolak'`. Field `int32 jumlah = 3` ditambahkan pada `StatusResponse` agar jumlah dapat dibaca sebagai angka, bukan di-parse dari teks.

### 2.3 L2.2 — Bidirectional streaming `Diskusi`
Setiap peserta memiliki antrean (`queue.Queue`); thread pembaca meneruskan tiap pesan masuk ke antrean peserta **lain**, sementara generator respons menyalurkan isi antreannya. Uji dengan dua client: Sari menerima kedua pesan Andi, Andi menerima pesan Sari; pengirim tidak menerima pesannya sendiri. Saat client menutup stream, sentinel `None` dikirim dan peserta dihapus dari `ROOM` (tidak bocor).

Catatan konsekuensi: setiap peserta aktif memegang **satu worker thread** server (+ satu thread pembaca) selama terhubung, sehingga `max_workers` membatasi jumlah peserta simultan.

### 2.4 L2.3 — Backward compatibility Protobuf
Client dengan stub **lama** (tanpa `prodi`) dijalankan terhadap server **baru** (dengan `string prodi = 4`):

```
field Mahasiswa di stub lama: ['nim', 'nama', 'ipk']
client lama menerima: Andi 3.35 | punya atribut prodi? False
unknown fields tersimpan (bytes): …220b496e666f726d6174696b61   <- field 4 "Informatika" tetap ada
```

**Tetap berjalan.** Alasan: Protobuf mengidentifikasi field lewat **nomor** (`= 4`), bukan nama atau posisi. Penerima yang tidak mengenal nomor 4 mengabaikannya (disimpan sebagai *unknown field* dan ikut diserialisasi ulang). Sebaliknya, client baru ke server lama menerima nilai default (`""`). Aturan agar tetap kompatibel: (1) jangan ubah/pakai ulang nomor field; (2) hanya **tambah** field dengan nomor baru; (3) field yang dihapus ditandai `reserved`; (4) jangan ubah tipe field secara sembarang. Ini yang tidak dimiliki XML-RPC yang bergantung pada urutan parameter.

### 2.5 L2.4 — Ukuran pesan Protobuf vs XML-RPC
Data sama: `{nim: "2023001", nama: "Andi", ipk: 3.35}`.

| Pesan | Protobuf | XML-RPC | Rasio |
|---|---|---|---|
| Response (`Mahasiswa`) | **24 B** (37 B jika memuat `prodi`) | 350 B | **14,6×** |
| Request (satu NIM) | **9 B** | 164 B | **18,2×** |

Rincian 24 B: `nim` 2+7, `nama` 2+4, `ipk` 1+8 (tag + panjang/nilai). Nama field tidak dikirim (hanya nomor), angka dikodekan biner. Catatan keadilan: ukuran di atas adalah *payload*; gRPC menambah *framing* 5 B per pesan plus header HTTP/2 (terkompresi HPACK), XML-RPC menambah header HTTP/1.x teks — rasio total tetap jauh di sisi Protobuf.

### 2.6 L2.5 — Pemanggilan asinkron `.future()`
10 permintaan `GetMahasiswa.future(...)` dikirim dalam **5,8 ms** (non-blocking), seluruh hasil terkumpul lewat `.result()` pada **6,4 ms**. Client tidak menunggu satu per satu; untuk server yang lambat, total waktu mendekati waktu **satu** panggilan (bukan sepuluh) selama server memproses paralel. Sinkron = *blocking*; `.future()` = client melanjutkan kerja dan mengambil hasil kemudian.

---

## 3. Praktikum 3 — Concurrency, Timeout, Toleransi Kegagalan

### 3.1 L3.1 — Retry dengan `request_id` tetap (benar)
20 transfer × 10 dari A ke B, server membalas lambat (3 s) dengan peluang 30 % *setelah* transfer terjadi, timeout client 2 s.

| Eksekusi | Percobaan RPC | Gagal total | A | B | Total |
|---|---|---|---|---|---|
| Run 1 | 27 (7 retry) | 0 | 800 | 700 | 1500 |
| Run 2 | 25 (5 retry) | 0 | **800** | **700** | **1500** |

A berkurang **tepat 200** walaupun ada 5–7 retry: pada retry, server menemukan `request_id` di `PROSES` dan mengembalikan balasan yang sama tanpa mentransfer lagi → **at-most-once** (digabung retry client = *effectively-once* selama server tidak restart).

### 3.2 L3.2 — `uuid` baru tiap percobaan (salah)

| Eksekusi | Transfer sampai ke server | Client melaporkan gagal | A | B | Total |
|---|---|---|---|---|---|
| Run 1 | 30 | 3 | 700 | 800 | 1500 |
| Run 2 | 28 | 2 | **720** | **780** | **1500** |

Seharusnya A=800. Setiap timeout membuat client menganggap gagal lalu mengirim ulang dengan ID **baru**, sehingga server menganggapnya permintaan berbeda dan mengeksekusinya lagi. Parahnya, 2–3 transfer dilaporkan **gagal** ke pengguna padahal uang sudah pindah (3× untuk transfer yang sama). Total tetap 1500 karena transfer bersifat konservatif; yang rusak adalah *kebenaran jumlah*. Inilah masalah at-least-once pada operasi tidak idempoten.

### 3.3 L3.3 — Tanpa `with LOCK:` (race condition)
50 transfer × 10 dari 10 thread client. Harapan: A=500, B=1000, total=1500.

| Konfigurasi | Hasil (A / B / total) |
|---|---|
| Dengan LOCK | 500 / 1000 / 1500 |
| **Tanpa lock, kode asli** (5 kali) | 500 / 1000 / 1500 pada **semua** percobaan |
| Tanpa lock + jendela race 2 ms (3 kali) | 950/550/1500 · 900/600/1500 · **950/560/1510** |
| Dengan lock + jendela race 2 ms (kontrol) | 500 / 1000 / 1500 |

**Jawaban jujur:** hanya menghapus `with LOCK:` *tidak* memunculkan kerusakan pada percobaan saya. Penyebabnya GIL CPython (thread tidak benar-benar paralel) dan critical section yang sangat singkat (satu operasi `-=` dan `+=` dalam beberapa mikrodetik); pergantian thread tepat di tengah baca–tulis sangat jarang. **Bug-nya tetap ada** — hanya tersembunyi. Untuk membuktikannya, jendela baca→tulis diperlebar 2 ms (`--race-window`), dan hasilnya rusak parah.

Mekanisme: `SALDO["A"] -= 10` sebenarnya **baca → hitung → tulis**. Thread 1 dan 2 sama-sama membaca A=1000, keduanya menulis 990 → satu transfer **hilang** (*lost update*). Pada uji di atas A=900–950 berarti 5–10 dari 50 transfer yang efektif berlaku di sisi A. Karena A dan B diperbarui secara terpisah, kehilangan pembaruan di keduanya tidak sinkron, sehingga **total bisa menyimpang** (1510 pada run ketiga — uang tercipta dari ketiadaan). Perbaikan: `threading.Lock` (satu proses), atau transaksi database/`BEGIN IMMEDIATE` (lihat §3.6). Lock harus melingkupi *seluruh* urutan cek-saldo → ubah → catat `request_id`, dan **jangan** membungkus `sleep`/operasi lambat di dalamnya.

### 3.4 L3.4 — Throughput vs `max_workers`
200 panggilan `GetMahasiswa` dari 20 thread client; server `sleep(0,1)`.

| max_workers | Waktu total (s) | Throughput (req/s) | Latensi rata-rata (ms) |
|---|---|---|---|
| 1 | 20,25 | 9,9 | 1.928 |
| 4 | 5,09 | 39,3 | 488 |
| 10 | 2,05 | 97,4 | 199 |
| 20 *(tambahan)* | 1,06 | 188,1 | 105 |

Grafik: `praktikum3/hasil/l3_4_throughput.png`.

Analisis:
- Teori: throughput ≈ `max_workers / 0,1 s` → 10, 40, 100, 200 req/s. Hasil ukur (9,9 / 39,3 / 97,4 / 188) sangat dekat; selisih kecil = overhead RPC.
- Latensi rata-rata ≈ 20 thread ÷ throughput (Hukum Little): dengan 1 worker, 19 permintaan antre di belakang satu pekerja → latensi ±2 s, bukan 0,1 s.
- Titik jenuh pada 20 worker: tidak ada gain di atas jumlah thread client (20) — bottleneck pindah ke sisi client.
- **Syarat penting:** beban ini *menunggu* (`sleep` melepas GIL). Jika handler *CPU-bound* di Python, penambahan thread tidak menaikkan throughput karena GIL (dan mesin uji hanya 1 core); gunakan proses terpisah (`ProcessPoolExecutor`/banyak instance server). Tambahan worker juga memakan memori dan bisa memperburuk latensi bila terlalu banyak.

### 3.5 L3.5 (pengayaan) — Failover
Dua server (50051 dan 50052), `FailoverClient` mencoba target aktif dan berpindah pada `UNAVAILABLE`/`DEADLINE_EXCEEDED`.

```
sebelum server-1 mati : 3× OK di 50051
setelah server-1 mati : 50051 UNAVAILABLE → 50052 OK → 50052 OK → 50052 OK  (total 4 ms, hasil=Andi)
```

Failover instan karena koneksi ditolak (`UNAVAILABLE`) langsung terdeteksi. Batasan: (1) hanya aman untuk operasi **idempoten** (`GetMahasiswa`); `Transfer` ke server kedua tidak berbagi `PROSES`/`SALDO` dengan server pertama sehingga dedup tidak berlaku — butuh state bersama/replikasi; (2) tidak ada *failback* dan health-check; (3) pada `DEADLINE_EXCEEDED` server pertama mungkin sudah memproses.

### 3.6 Pertanyaan analisis Praktikum 3 — `PROSES` di memori, server restart
Skenario (`LayananPersisten`): transfer 100 dengan `request_id=X` berhasil (A=900); server crash/restart (balasan dianggap hilang); client mengulang `X`.

| Desain dedup | A setelah retry | Transfer terjadi |
|---|---|---|
| `PROSES` di RAM (saldo di database) | **800** | **2×** ❌ |
| `PROSES` di SQLite, satu transaksi dengan update saldo | **900** | **1×** ✅ |

Jawaban: **jaminan at-most-once hilang** — `PROSES` kosong setelah restart, sehingga retry dianggap permintaan baru. (Pada kode modul, `SALDO` juga ikut hilang karena di RAM, sehingga yang terjadi lebih buruk: semua state kembali ke awal.) Perbaikan yang diimplementasikan di `grpc_app/server_persisten.py`:

1. Simpan saldo **dan** log `request_id → respons` di penyimpanan persisten (SQLite).
2. Lakukan cek-duplikat + update saldo + insert log dalam **satu transaksi atomik** (`BEGIN IMMEDIATE … COMMIT`). Bila crash di tengah, keduanya batal; bila sukses, keduanya tersimpan — tidak ada celah "uang pindah tapi log belum tercatat".
3. Beri masa retensi (TTL) untuk `request_id` lama agar tabel tidak tumbuh tanpa batas; TTL harus lebih lama dari total waktu retry client.
4. Untuk multi-server: gunakan database bersama atau protokol replikasi/konsensus. *Exactly-once* murni tetap tidak dapat dijamin hanya dengan retry; yang dicapai adalah **at-least-once + deduplikasi idempoten = effectively-once**.

---

## 4. Catatan teknis pada kode modul (temuan saat mengerjakan)

1. `Transfer` dengan akun tidak dikenal → `KeyError` → client menerima `UNKNOWN`. Ditambah validasi `NOT_FOUND` dan `jumlah > 0`.
2. `TambahNilai` memakai `DATA.setdefault(...)` tanpa lock, sedangkan `StreamNilai` mengiterasi `dict` yang sama — modifikasi saat iterasi bisa memicu `RuntimeError`. Ditambah `DATA_LOCK` dan iterasi atas salinan (`list(items())`).
3. `time.sleep(3)` pada handler menahan satu worker thread selama 3 s; dengan 30 % lambat dan `max_workers=10`, beban tinggi bisa menghabiskan worker (lihat L3.4).
4. Konversi IPK `rata-rata / 25` hanyalah simulasi, bukan skala nilai akademik sebenarnya.
5. `grpc.insecure_channel` tanpa TLS — cukup untuk praktikum, tidak untuk produksi.
6. Soal L1.3 tertulis "lebih dari 231"; maksud sebenarnya **2³¹** (superscript hilang saat ekstraksi PDF).
7. Tambahan di luar modul (untuk verifikasi, tidak mengubah soal): RPC `GetSaldo`, field `StatusResponse.jumlah`, `Pesan` untuk `Diskusi`.

## 5. Keterbatasan pengukuran (tulis jujur di laporan)

- Sebagian besar uji dijalankan pada **satu mesin, localhost**; L1.4 sudah diuji lintas network namespace via Podman dan **WSL2 Debian** (gateway Hyper-V). Latensi WSL lebih tinggi daripada Podman karena lapisan virtualisasi Windows, dan IP LAN Windows melewati NAT (±12,8 ms vs gateway ±3,05 ms).
- Hasil L3.1/L3.2/L3.3 bersifat acak (peluang 30 % balasan lambat); jumlah retry berbeda tiap run, **kesimpulan tidak berubah**. Sertakan minimal dua run.
- L3.4 memakai 2 putaran per konfigurasi (rata-rata); gunakan ≥ 3 putaran untuk laporan.
- Angka ukuran Protobuf vs XML adalah payload, bukan total byte di kabel.

## 6. Draft kesimpulan (siap diedit)

RPC membuat pemanggilan jarak jauh tampak seperti pemanggilan lokal berkat stub dan marshalling, namun biayanya nyata: latensi ±4 order of magnitude lebih besar dan kegagalan parsial yang tidak ada pada panggilan lokal. XML-RPC mudah dipakai tetapi boros (±96 % overhead pada pesan kecil) dan terbatas tipe datanya (int 32-bit), sedangkan gRPC/Protobuf lebih ringkas (14,6×), bertipe kuat, kompatibel ke belakang, dan mendukung streaming. Keandalan tidak datang gratis: retry harus disertai `request_id` tetap dan deduplikasi persisten agar operasi non-idempoten tidak berjalan ganda, akses data bersama harus dilindungi lock/transaksi, dan kapasitas server (jumlah worker) menentukan throughput dan latensi.
