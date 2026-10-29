# Praktikum 3 — Concurrency, Timeout, dan Kegagalan

Enam skenario yang membuktikan mengapa "memanggil seperti fungsi lokal" berbahaya: retry bisa menggandakan efek, race condition menghasilkan uang hilang, jumlah worker menentukan throughput, dan dedup di memori tidak selamat dari restart.

| Kode | Topik | Inti |
|---|---|---|
| L3.1 | Retry dengan `request_id` **tetap** | Server menyimpan hasil per `request_id` → efek **at-most-once** |
| L3.2 | Retry dengan `request_id` **baru** | Setiap percobaan dianggap permintaan berbeda → transfer berulang |
| L3.3 | Transfer paralel tanpa lock | *Lost update* merusak total saldo |
| L3.4 | Throughput vs `max_workers` | Throughput ≈ `workers / waktu_layanan` (Hukum Little) |
| L3.5 | Failover dua server | Client berpindah saat `UNAVAILABLE` |
| L3.6 | Restart server: dedup RAM vs SQLite | Dedup di RAM hilang; SQLite memberi *effectively-once* |

## Berkas

| Berkas | Fungsi |
|---|---|
| `klien.py` | Pembungkus pemanggilan: `panggil_dengan_retry`, `transfer`, `transfer_id_baru`, `ambil_saldo`, `FailoverClient` |
| `l3_all.py` | Driver semua skenario, menulis `praktikum3/hasil/l3_ringkasan.json` dan `praktikum3/hasil/l3_4_throughput.png` |

## Cara menjalankan

Dari `task-5-remote-procedural-call/` dengan venv aktif:

```bash
# Semua skenario (sekitar 2–3 menit; L3.2 & L3.6 sengaja menunggu timeout)
python praktikum3/l3_all.py

# Per bagian; --putaran membatasi jumlah run acak (L3.1–L3.3)
python praktikum3/l3_all.py --bagian 1 --putaran 1
python praktikum3/l3_all.py --bagian 2 --putaran 1
python praktikum3/l3_all.py --bagian 3
python praktikum3/l3_all.py --bagian 4 --putaran 3
python praktikum3/l3_all.py --bagian 5
python praktikum3/l3_all.py --bagian 6

# Beberapa bagian sekaligus
python praktikum3/l3_all.py --bagian 4 5
python praktikum3/l3_all.py --bagian 1 6

# Tampilkan log server (default disembunyikan)
python praktikum3/l3_all.py --bagian 1 --log-server
```

Semua server dinyalakan dan dimatikan otomatis. Port yang dipakai: L3.1–L3.3 `50061`, L3.4 `50071`, L3.5 `50051`/`50052` (sesuai lembar latihan — matikan server manual di 50051 dulu), L3.6 `50091`.

## Hasil yang diharapkan (uji di mesin ini)

```text
L3.1  Run 1: RPC=25 (retry 5), gagal=0, A=800, B=700, total=1500
L3.2  Run 1: transfer sampai ke server=30, dilaporkan gagal=1, A=700, B=800, total=1500
L3.3  dengan lock                : A= 500 B=1000 total=1500
      tanpa lock                 : A= 500 B=1000 total=1500   (GIL menyembunyikan bug)
      tanpa lock + jendela 2 ms  : A= 870 B= 630 total=1500   (lost update terbukti)
      dengan lock + jendela 2 ms : A= 500 B=1000 total=1500
L3.4  workers= 1: 20.21s |   9.9 req/s | latensi 1925 ms
      workers= 4:  5.06s |  39.5 req/s | latensi  485 ms
      workers=10:  2.04s |  98.1 req/s | latensi  198 ms
      workers=20:  1.07s | 187.0 req/s | latensi  105 ms
L3.5  sebelum server-1 mati: 50051 ; setelah server-1 mati: 50052
L3.6  dedup=ram   : A=900 -> retry -> A=800 (transfer terjadi 2x)
      dedup=sqlite: A=900 -> retry -> A=900 (transfer terjadi 1x)
```

Angka acak (L3.1–L3.3) bisa berubah tiap run; yang penting polanya: `request_id` tetap → total tetap 1500, `request_id` baru → A < 800.

## Membaca hasil

- **L3.1**: server sengaja menunda balasan 3 s, client timeout 2 s lalu retry. Karena `request_id` sama, server mengembalikan hasil tersimpan tanpa memotong saldo lagi. `retry 4–6` berarti balasan asli baru tiba setelah beberapa percobaan.
- **L3.2**: setiap percobaan memakai UUID baru → server mengeksekusi transfer lagi. Selisih `A` terhadap `800` (mis. 700) adalah uang yang berpindah lebih dari sekali.
- **L3.3**: di CPython, `A -= jumlah; B += jumlah` sangat singkat sehingga GIL sering membuatnya tampak aman. Opsi `--race-window` menambahkan jeda antara baca dan tulis untuk memperbesar peluang *lost update* — inilah yang akan terjadi di server multi-proses/multi-mesin.
- **L3.4**: throughput naik hampir linear sampai jumlah worker; latensi turun karena antrean memendek. `workers=20` melebihi inti fisik (8) sehingga kenaikan mulai melandai.
- **L3.5**: `FailoverClient` mencoba server berikutnya saat `UNAVAILABLE`. Aman untuk operasi idempoten seperti `GetMahasiswa`; untuk `Transfer` tetap perlu state bersama.
- **L3.6**: `server_persisten.py --dedup sqlite` menulis saldo dan `request_id` dalam satu transaksi `BEGIN IMMEDIATE`, sehingga retry setelah restart dikenali. Mode `ram` kehilangan catatan saat proses mati.

## Berkas hasil

| Berkas | Isi |
|---|---|
| `praktikum3/hasil/l3_ringkasan.json` | Angka semua bagian; bagian ditimpa ulang setiap kali dijalankan |
| `praktikum3/hasil/l3_4_throughput.png` | Dua panel: throughput vs worker dan latensi rata-rata vs worker (sumbu-Y log) |
| `praktikum3/hasil/*.txt` | Log eksekusi lengkap (bila disimpan dengan `tee`) |

## Troubleshooting

| Gejala | Solusi |
|---|---|
| Total saldo bukan 1500 di L3.3 | itu justru temuan (race); jalankan `--bagian 3` lagi untuk melihat variasi |
| L3.2 memakan waktu lama | normal: tiap percobaan menunggu timeout 2 s, dan ada 2 putaran |
| `FAILED_PRECONDITION: Saldo tidak cukup` | jumlah transfer melebihi saldo awal; skrip bawaan sudah benar (50 transfer × 10) |
| Port bentrok | hentikan server sisa (`pkill -f server_grpc`), atau ubah konstanta port di `l3_all.py` |
| Grafik tidak terbuka | file hanya disimpan (backend `Agg`); buka `praktikum3/hasil/l3_4_throughput.png` |
