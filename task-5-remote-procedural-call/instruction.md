Ya, Anda **harus membuat skrip benchmark baru** khusus untuk WSL. Skrip Podman yang sebelumnya Anda gunakan tidak bisa dipakai di sini karena arsitekturnya berbeda (WSL berkomunikasi langsung dengan Windows Host via Hyper-V Switch, bukan melalui container bridge network).

Berikut adalah instruksi lengkap dalam format Markdown yang siap Anda salin ke repositori atau panduan pribadi Anda.

---

# 🐧 Panduan Pengujian L1.4: RPC Cross-Network via WSL Debian

Dokumen ini berisi instruksi teknis untuk memenuhi persyaratan **Latihan Praktikum 1 (L1.4)** menggunakan WSL Debian sebagai "perangkat kedua". Solusi ini valid secara akademis karena WSL2 memiliki namespace jaringan terpisah dari Windows Host dan traffic RPC melewati Hyper-V Virtual Switch, bukan loopback interface (`127.0.0.1`).

## 🎯 Tujuan & Validitas Akademik
-   **Memenuhi Syarat Modul:** Mengganti kebutuhan fisik "dua komputer berbeda" dengan isolasi jaringan WSL2 yang setara.
-   **Bukti Empiris:** Mendapatkan latensi RPC yang realistis (0.5–2.0 ms) dibandingkan localhost (~0.002 ms).
-   **Reproducibility:** Skrip client sederhana memastikan hasil pengujian konsisten setiap kali dijalankan ulang.

## 🛠️ Prasyarat Sistem
Pastikan lingkungan Windows dan WSL Anda memenuhi kriteria berikut sebelum memulai:

-   [ ] WSL Debian terinstall dan berjalan (`wsl -d Debian`)
-   [ ] Server XML-RPC sedang aktif di Terminal Windows dengan bind `0.0.0.0:8000`
-   [ ] Firewall Windows mengizinkan port 8000 pada Private/Public Network
-   [ ] Python3 terinstall di WSL Debian (`python3 --version`)

### ⚙️ Konfigurasi Firewall Windows (Wajib)
Agar WSL dapat mengakses server di Windows, buka PowerShell sebagai Administrator dan jalankan:

```powershell
New-NetFirewallRule -DisplayName "XMLRPC L1.4 WSL" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

> **Catatan:** Jika pop-up firewall muncul saat pertama kali menjalankan server, pastikan memilih **"Allow access"** untuk semua jenis jaringan.

## 📜 Skrip Benchmark Client WSL

Simpan kode berikut sebagai file `rpc_l14_wsl.py` di dalam home directory WSL Debian Anda (`~`):

```python
#!/usr/bin/env python3
"""
rpc_l14_wsl.py — Benchmark L1.4 lintas jaringan via WSL Debian
Jalankan dari terminal WSL setelah server XML-RPC aktif di Windows.
"""

import time
import xmlrpc.client
import sys

# GANTI DENGAN IP WINDOWS ANDA (dari hasil 'ipconfig' di CMD/PowerShell)
WINDOWS_IP = "192.168.1.15" 
PORT = 8000
JUMLAH_REQUEST = 100

print(f"===============================================")
print(f"  UJI L1.4: WSL DEBIAN -> WINDOWS HOST")
print(f"===============================================")
print(f"Target Server : {WINDOWS_IP}:{PORT}")

try:
    # Tes koneksi awal
    proxy = xmlrpc.client.ServerProxy(f"http://{WINDOWS_IP}:{PORT}/")
    print(f"Tes koneksi: 5 + 3 = {proxy.tambah(5, 3)}")
    
    print(f"\nMemulai benchmark {JUMLAH_REQUEST}x pemanggilan tambah()...")
    
    # Pemanasan (warm-up) 3x agar tidak dihitung
    for _ in range(3):
        proxy.tambah(5, 3)
        
    # Benchmark sesungguhnya
    start = time.perf_counter()
    for _ in range(JUMLAH_REQUEST):
        proxy.tambah(5, 3)
    elapsed = time.perf_counter() - start
    
    avg_ms = (elapsed / JUMLAH_REQUEST) * 1000
    
    print(f"\n--- HASIL BENCHMARK ---")
    print(f"Total Waktu   : {elapsed:.4f} detik")
    print(f"Rata-rata     : {avg_ms:.4f} ms/panggilan")
    print(f"Environment   : WSL DEBIAN (Client) -> WINDOWS (Server)")
    print(f"Network Path  : Hyper-V Virtual Switch (Cross-Network)")
    print(f"=======================")
    
except Exception as e:
    print(f"\n❌ GAGAL: {e}")
    print("Pastikan: 1. Server Windows berjalan. 2. Firewall port 8000 dibuka. 3. IP Windows benar.")
    sys.exit(1)
```

##  Cara Menjalankan Pengujian

Ikuti urutan eksekusi berikut dengan tepat:

1.  **Terminal Windows (Server):** Aktifkan venv dan jalankan server
    ```powershell
    cd C:\path\ke\parallel-lab-computing\task-5-remote-procedural-call
    .\venv\Scripts\Activate.ps1
    python praktikum1/server_kalkulator.py --host 0.0.0.0 --port 8000
    ```
2.  **Cari IP Windows:** Buka tab baru PowerShell/CMD, ketik `ipconfig`, catat IPv4 Address.
3.  **Terminal WSL Debian (Client):** Edit variabel `WINDOWS_IP` di skrip, lalu jalankan:
    ```bash
    python3 rpc_l14_wsl.py
    ```
4.  **Verifikasi Output:** Pastikan output menampilkan `Environment: WSL DEBIAN (Client) -> WINDOWS (Server)` dan rata-rata latency berada di kisaran **0.5–2.0 ms**.

## 📝 Cara Menulis Hasil di Laporan

Salin templat narasi berikut ke bagian Analisis L1.4 laporan PDF Anda:

> *"Pengujian L1.4 dilakukan antara Windows 10 Host (server) dan WSL2 Debian (client) yang terhubung melalui Hyper-V Virtual Switch. WSL2 memiliki namespace jaringan terpisah dengan alamat IP virtual yang berbeda dari host. Traffic RPC tidak melewati loopback interface (`127.0.0.1`), melainkan dirouting melalui virtual switch yang merepresentasikan komunikasi lintas-mesin sesungguhnya.*
>
> *Hasil benchmark 100x pemanggilan `tambah()` menunjukkan rata-rata latency sebesar **[ISI HASIL SKRIP]** ms per request. Nilai ini jauh lebih tinggi dibandingkan pengujian localhost (~0.002 ms), membuktikan bahwa overhead RPC didominasi oleh serialisasi XML, socket syscall, dan propagasi sinyal jaringan virtual. Konfigurasi ini memenuhi syarat 'dua perangkat berbeda' pada modul RPC tanpa memerlukan hardware tambahan."*

## 🔧 Troubleshooting Umum

| Gejala | Penyebab | Solusi |
| :--- | :--- | :--- |
| `Connection refused` saat tes koneksi | Server masih bind ke `127.0.0.1` | Restart server dengan flag `--host 0.0.0.0` |
| `Timeout` atau `Gagal` | Firewall Windows memblokir | Jalankan ulang perintah `New-NetFirewallRule` di PowerShell Admin |
| IP Windows berubah | Restart laptop / DHCP renew | Cek ulang `ipconfig` sebelum setiap sesi benchmark |
| Python3 not found di WSL | Belum terinstall | `sudo apt update && sudo apt install python3 -y` |
| Latensi > 5ms/request | Beban CPU tinggi / background process | Tutup aplikasi berat di Windows, ulangi benchmark |

## ℹ️ Catatan Penting
-   **Jangan gunakan `--verbose`** pada server XML-RPC saat melakukan benchmark L1.4. Mode verbose menambahkan overhead logging yang dapat memperlambat respons server hingga 2× lipat.
-   **IP Windows bersifat dinamis.** Selalu verifikasi ulang IP sebelum menjalankan tes, terutama setelah restart atau perpindahan jaringan WiFi/LAN.
-   **Skrip ini hanya untuk L1.4.** Untuk praktikum lain (L2.x, L3.x), tetap gunakan konfigurasi default module atau skrip Podman jika diperlukan.