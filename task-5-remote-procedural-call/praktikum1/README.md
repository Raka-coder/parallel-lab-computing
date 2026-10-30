# Praktikum 1 — XML-RPC

Membangun **server kalkulator** dengan `xmlrpc.server`, lalu memakainya untuk mengukur marshalling, batas tipe data, latensi, dan perilaku saat server mati.

## Isi folder

| Berkas | Fungsi |
|---|---|
| `server_util.py` | Utilitas bersama: cek port, tunggu server siap, `Transport` tanpa retry, proxy dengan timeout/retry, nyalakan/hentikan server otomatis |
| `server_kalkulator.py` | `SimpleXMLRPCServer` + `ThreadingMixIn`, metode `tambah`, `kali`, `bagi`, `pangkat`, `akar`, `statistik`, `echo`, `lambat` |
| `client_kalkulator.py` | Client interaktif/CLI untuk memanggil semua metode |
| `l1_all.py` | Driver L1.1–L1.5; bisa dijalankan semua atau per bagian (`--bagian`), termasuk `--use-podman` |
| `test_l1_4_podman.sh` | L1.4 lintas jaringan: server di host, client di container Podman |
| `rpc_l14_wsl.py` | L1.4 lintas jaringan: client Python di WSL Debian, server di Windows |
| `test_l1_4_wsl.ps1` | Runner Windows: menyalakan server bila perlu, menyalin skrip ke `~` WSL, lalu menjalankan benchmark |
| `hasil/` | Log hasil eksekusi (`l1_all.txt`, `l1_4_podman.txt`, `l1_4_wsl.txt`) |

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

### C. Benchmark lintas jaringan via Podman (tanpa komputer kedua)

```bash
python praktikum1/l1_all.py --bagian 4 --use-podman
# atau langsung:
./praktikum1/test_l1_4_podman.sh
```

Skrip membuat network `rpc-test-net`, menjalankan image `python:3.12-alpine`
sebagai client, dan memakai `host.containers.internal` sebagai alamat host.
Container punya namespace jaringan sendiri, jadi traffic tidak lewat `lo` host.
Bila belum ada server, skrip menyalakannya sendiri di `0.0.0.0` (port bebas)
lalu mematikannya lagi. Hasil: **±1,7–1,9 ms/panggilan** vs lokal **±0,06–0,19 µs**
(±24.000–31.000×); log di `praktikum1/hasil/l1_4_podman.txt`.

Prasyarat: Podman terpasang. Image diambil otomatis pada run pertama (±50 MB).
Jika muncul `Connection refused`, pastikan container dapat menjangkau
`host.containers.internal`; pada Podman rootless Fedora biasanya sudah jalan.

### D. Benchmark lintas jaringan via WSL2 Debian

WSL2 punya network namespace sendiri, jadi client di WSL tidak memakai
loopback Windows. Jalankan dari PowerShell di Windows:

```powershell
powershell -ExecutionPolicy Bypass -File praktikum1/test_l1_4_wsl.ps1
```

Runner otomatis menyalakan server `0.0.0.0:8000` bila belum ada, menyalin
`rpc_l14_wsl.py` ke home WSL, memakai gateway WSL (`vEthernet (WSL)`) sebagai
alamat Windows, lalu menyimpan log ke `praktikum1/hasil/l1_4_wsl.txt`.
Alternatif manual dari terminal WSL Debian:

```bash
python3 rpc_l14_wsl.py
python3 rpc_l14_wsl.py --host 192.168.1.41 --requests 100 --rounds 5
```

Hasil di mesin ini: **±3,05–3,19 ms/panggilan** dari WSL vs lokal WSL
**±0,05–0,11 µs** (±28.000–67.000×). IP LAN Windows (`192.168.1.41`) terukur
±12,8 ms karena melewati NAT; gateway WSL lebih stabil dan tetap bukan
loopback. Bila koneksi gagal, buka port 8000 di firewall Windows:

```powershell
New-NetFirewallRule -DisplayName "XMLRPC L1.4 WSL" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

### E. Benchmark dua komputer

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
| L1.4 | XML-RPC ±**1,9–2,1 ms** vs lokal ±**0,06–0,19 µs** per panggilan (**±11.000–32.000×**); via Podman ±**1,7–1,9 ms** (**±24.000–31.000×**); via WSL2 Debian ±**3,05–3,19 ms** (**±28.000–67.000×**); `--verbose` ±2× lebih lambat |
| L1.5 | (1) server mati → `ConnectionRefusedError`; (2) server mati setelah koneksi → `RemoteDisconnected`; (3) retry → hasil benar (**42**) |

## Menyimpan log

```bash
python praktikum1/l1_all.py 2>&1 | tee praktikum1/hasil/l1_all.txt
```

## Opsi penting

```text
server_kalkulator.py  --host 0.0.0.0  --port 8000  --verbose
client_kalkulator.py  --host 127.0.0.1 --port 8000 --verbose
l1_all.py             [--bagian 1 2 3 4 5] [--host 127.0.0.1] [--port 8000] [--putaran 5] [--use-podman]
rpc_l14_wsl.py        [--host IP_WINDOWS] [--port 8000] [--requests 100] [--rounds 5]
test_l1_4_wsl.ps1     [-HostIP IP_WINDOWS] [-Port 8000] [-Requests 100] [-Rounds 5] [-Distro Debian]
```

`--verbose` menampilkan HTTP/XML mentah sehingga terlihat langsung isi marshalling.

## Troubleshooting

| Gejala | Sebab / solusi |
|---|---|
| `Port 8000 sudah dipakai proses lain` | server lama masih hidup: `ss -ltnp \| grep :8000`, lalu `kill <PID>`; atau ganti `--port 8001` |
| Client menggantung | host/port salah, atau firewall memblokir; uji `curl http://IP:8000` |
| L1.5 skenario 2 kadang lolos | balapan waktu; jalankan ulang, server sengaja dimatikan tepat setelah request dikirim |
| WSL `Connection refused` / timeout | server belum bind `0.0.0.0`, firewall memblokir, atau alamat Windows salah; coba `--host` gateway WSL atau buka port 8000 |
| Angka latensi jauh berbeda | wajar: hasil bergantung CPU, beban, dan jaringan. Catat lingkungan pengukuran |
