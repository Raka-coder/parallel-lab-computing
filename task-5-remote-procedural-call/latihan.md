Latihan Praktikum 1: RPC Dasar dengan XML-RPC

    ☑ L1.1 Tambahkan fungsi pangkat(a, b) dan akar(x) di server; uji dari client.
    ☑ L1.2 Buat fungsi statistik(daftar) yang menerima list angka dan mengembalikan dictionary berisi min, max, rata2. Amati bagaimana list dan dictionary dimarshalling menjadi XML.
    ☑ L1.3 Kirim parameter berupa objek datetime dan bilangan sangat besar (lebih dari 2^31). Catat apa yang terjadi dan jelaskan penyebabnya.
         Hasil: datetime -> xmlrpc.client.DateTime; 2^31 -> OverflowError di client; pangkat(2,40) -> Fault di server; pangkat(2.0,40) -> 1099511627776.0.
    ◐ L1.4 Jalankan server dan client di dua komputer berbeda. Ukur waktu 100 kali pemanggilan tambah() menggunakan time.perf_counter() dan bandingkan dengan 100 kali pemanggilan fungsi lokal.
    ☑ L1.5 Matikan server ketika client sedang berjalan. Exception apa yang muncul? Tambahkan penanganan error yang sesuai.

Pertanyaan analisis: berapa ukuran (byte) pesan XML untuk tambah(5, 3)? Berapa persen yang merupakan data sebenarnya dan berapa persen overhead format?


Latihan Praktikum 2: gRPC dan Protocol Buffers

    ☑ L2.1 Tambahkan RPC client streaming KirimBanyakNilai(stream NilaiRequest) returns (StatusResponse) yang menerima banyak nilai sekaligus dan mengembalikan jumlah nilai yang tersimpan.
    ☑ L2.2 Tambahkan RPC bidirectional streaming Diskusi(stream Pesan) returns (stream Pesan) untuk ruang diskusi sederhana antar-client.
    ☑ L2.3 Tambahkan field baru string prodi = 4; pada message Mahasiswa. Jalankan client lama (stub belum digenerate ulang) terhadap server baru. Apakah tetap berjalan? Jelaskan konsep backward compatibility pada Protobuf.
    ☑ L2.4 Bandingkan ukuran pesan: hitung len(mhs.SerializeToString()) dan bandingkan dengan pesan XML-RPC berisi data yang sama dari Praktikum 1.
    ☑ L2.5 Ubah pemanggilan GetMahasiswa menjadi asinkron dengan stub.GetMahasiswa.future(...). Kirim 10 permintaan sekaligus, lalu kumpulkan hasilnya dengan .result().


Latihan Praktikum 3: Concurrency, Timeout, dan Toleransi Kegagalan

    ☑ L3.1 Jalankan 20 kali transfer 10 dari A ke B. Periksa saldo akhir: totalnya harus tetap 1500 dan A berkurang tepat 200.
    ☑ L3.2 Ubah client agar membuat uuid baru di setiap percobaan. Ulangi L3.1, catat saldo akhir, dan jelaskan mengapa terjadi transfer ganda.
    ☑ L3.3 Hapus with LOCK: lalu jalankan 50 transfer dari 10 thread client secara bersamaan (concurrent.futures.ThreadPoolExecutor). Apakah total saldo tetap 1500? Jelaskan race condition yang terjadi.
    ☑ L3.4 Ukur throughput (permintaan per detik) untuk 200 pemanggilan GetMahasiswa dari 20 thread client, dengan time.sleep(0.1) ditambahkan di server, untuk max_workers = 1, 4, dan 10. Isi tabel di bawah dan buat grafiknya di laporan.
   
    ☑ L3.5 (Pengayaan) Jalankan dua server di port 50051 dan 50052. Buat client yang otomatis berpindah ke server kedua jika server pertama UNAVAILABLE (failover).

| max worker | Waktu total (s) | Throughput (req/s) | Latensi rata-rata (ms) |
|------------|-----------------|--------------------|------------------------|
| 1          | 20,3            | 9,9                | 1930                   |
| 4          | 5,1             | 39,4               | 486                    |
| 10         | 2,0             | 97,7               | 198                    |

Grafik throughput + latensi (sumbu-Y log): `praktikum3/hasil/l3_4_throughput.png`.
    
Pertanyaan analisis: server menyimpan PROSES di memori. Apa yang terjadi pada jaminan at-most-once jika server restart? Usulkan perbaikannya.

---
Keterangan status: ☑ sudah dijalankan dan diverifikasi lewat skrip di repo · ◐ sebagian (yang tersisa dijelaskan di bawah).

Catatan status:
- **L1.4** — benchmark 100x sudah jalan dan tercatat (lokal ~0,105 us vs XML-RPC ~2,0 ms = ~19.000x di localhost; rentang 9.500-19.000x tergantung beban, `--verbose` ~2x lebih lambat, `praktikum1/hasil/l1_all.txt`). Eksekusi di **dua komputer** belum dilakukan karena butuh mesin kedua; prosedur lengkap ada di `PANDUAN.md` bagian 7d dan `praktikum1/README.md`, skrip `l1_all.py --bagian 4 --host <IP-server>` sudah mendukung mode jaringan (uji koneksi dulu, tidak menyalakan server lokal).
- **L1.3** — skrip menguji `datetime`, `2**31`, `2**40`, `pangkat(2, 40)`, dan `pangkat(2.0, 40)`; klaim "2^100" pada lembar diwakili oleh `2**40` yang sudah melewati batas int32.

Jawaban pertanyaan analisis:
- **P1 (ukuran XML `tambah(5, 3)`)** — request 190 B, response 121 B; data murni 12 B (6,3%), overhead format 96,1% (XML tag + header HTTP). Rincian di `praktikum1/hasil/l1_all.txt`.
- **P3 (at-most-once saat server restart)** — PROSES/saldo di RAM hilang saat restart, sehingga `request_id` yang sudah diproses tidak dikenal dan retry dieksekusi ulang (transfer ganda). Terbukti di L3.6: dedup RAM A=900 -> 800, dedup SQLite A=900 -> 900. Perbaikan: simpan saldo + log `request_id` di SQLite dalam satu transaksi atomik (`BEGIN IMMEDIATE`), sehingga yang dijamin adalah at-least-once + dedup = effectively-once.
