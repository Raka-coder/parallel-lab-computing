# Praktikum 1 — XML-RPC

Membangun **server kalkulator** dengan `xmlrpc.server`, lalu memakainya untuk mengukur marshalling, batas tipe data, latensi, dan perilaku saat server mati.

## Isi folder

| Berkas | Fungsi |
|---|---|
| `server_util.py` | Utilitas bersama: cek port, tunggu server siap, `Transport` tanpa retry, proxy dengan timeout/retry, nyalakan/hentikan server otomatis |
| `server_kalkulator.py` | `SimpleXMLRPCServer` + `ThreadingMixIn`, metode `tambah`, `kali`, `bagi`, `pangkat`, `akar`, `statistik`, `echo`, `lambat` |
| `client_kalkulator.py` | Client interaktif/CLI untuk memanggil semua metode |
| `l1_all.py` | Driver L1.1–L1.5; bisa dijalankan semua atau per bagian (`--bagian`) |
| `hasil/` | Log hasil eksekusi (`l1_all.txt`) |

## Cara menjalankan

Dari `task-5-remote-procedural-call/` dengan venv aktif.

### A. Mode dua terminal (sesuai modul)

Terminal 1 — server:

```bash
python praktikum1/server_kalkulator.py --verbose
```

Keluaran: `Server kalkulator XML-RPC siap di http://0.0.0.0:8000` (lihat `--help` untuk `--host`, `--port`).

Terminal 2 — client:

```bash
python praktikum1/client_kalkulator.py --verbose
```

Client memanggil `tambah`, `kali`, `bagi`, `pangkat`, `akar`, `statistik`, `echo`, lalu menampilkan hasil. Hentikan server dengan `Ctrl+C`.

### B. Mode satu perintah (server dinyalakan otomatis)

```bash
python praktikum1/l1_all.py                  # semua L1.1-L1.5
python praktikum1/l1_all.py --bagian 2       # hanya L1.2
python praktikum1/l1_all.py --bagian 2 4     # L1.2 dan L1.4 sekaligus
python praktikum1/l1_all.py --bagian 1 3 4 5 # semua kecuali L1.2
```

Pemetaan: `1`=L1.1 pangkat/akar, `2`=L1.2 marshalling, `3`=L1.3 batas tipe, `4`=L1.4 benchmark, `5`=L1.5 server mati.

Driver menyalakan satu server bersama untuk bagian 1/3/4, lalu mematikannya. L1.5 mengelola servernya sendiri (port bebas mulai 8010) karena skenario memang mematikan server.

### C. Benchmark dua komputer

Di komputer server:

```bash
python praktikum1/server_kalkulator.py
```

Di komputer client (ganti dengan IP server):

```bash
python praktikum1/l1_all.py --bagian 4 --host 192.168.1.10
python praktikum1/l1_all.py --bagian 1 3 4 --host 192.168.1.10
python praktikum1/client_kalkulator.py --host 192.168.1.10
```

Pastikan port 8000 terbuka di firewall dan server dijalankan dengan `--host 0.0.0.0` (default). Bagian 5 tidak bisa dipakai dengan `--host` jauh karena ia mematikan/menyalakan server lokal.

Pada mode dua komputer, skrip **tidak** menyalakan server lokal: ia menguji koneksi ke IP tersebut lebih dulu, lalu mengukur 100 panggilan lewat jaringan. Jika gagal, pesannya menyebut hal yang harus diperiksa (server, bind address, firewall, IP).

## Yang diamati

| Latihan | Hasil yang diharapkan |
|---|---|
| L1.2 | `tambah(5,3)` ≈ **190 B** request, **121 B** response; data murni 12 B → overhead **±96 %** (XML tag + HTTP header) |
| L1.3 | `datetime` → `xmlrpc.client.DateTime`; `2**31` → `OverflowError` di client (batas `int` XML-RPC 32-bit); `pangkat(2,40)` → `Fault` di server; `pangkat(2.0,40)` → `1099511627776.0` |
| L1.4 | XML-RPC ±**1,9–2,1 ms** vs lokal ±**0,1–0,19 µs** per panggilan (**±11.000–19.000×** di localhost; `--verbose` ±2× lebih lambat) |
| L1.5 | (1) server mati → `ConnectionRefusedError`; (2) server mati setelah koneksi → `RemoteDisconnected`; (3) retry → hasil benar (**42**) |

## Menyimpan log

```bash
python praktikum1/l1_all.py 2>&1 | tee praktikum1/hasil/l1_all.txt
```

## Opsi penting

```text
server_kalkulator.py  --host 0.0.0.0  --port 8000  --verbose
client_kalkulator.py  --host 127.0.0.1 --port 8000 --verbose
l1_all.py             [--bagian 1 2 3 4 5] [--host 127.0.0.1] [--port 8000] [--putaran 5]
```

`--verbose` menampilkan HTTP/XML mentah sehingga terlihat langsung isi marshalling.

## Troubleshooting

| Gejala | Sebab / solusi |
|---|---|
| `Port 8000 sudah dipakai proses lain` | server lama masih hidup: `ss -ltnp \| grep :8000`, lalu `kill <PID>`; atau ganti `--port 8001` |
| Client menggantung | host/port salah, atau firewall memblokir; uji `curl http://IP:8000` |
| L1.5 skenario 2 kadang lolos | balapan waktu; jalankan ulang, server sengaja dimatikan tepat setelah request dikirim |
| Angka latensi jauh berbeda | wajar: hasil bergantung CPU, beban, dan jaringan. Catat lingkungan pengukuran |
