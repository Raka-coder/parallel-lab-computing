# UTS Hybrid Computing — Parallel Web Simulation

**Nama:** Raka Restu Saputra  
**NPM:** 247006111172  
**Kelas:** F  
**Mata Kuliah:** Komputasi Paralel & Terdistribusi

---

## Parameter Pribadi (dari NIM)

| Parameter | Rumus | Nilai |
|-----------|-------|-------|
| Jumlah Thread | (72 mod 4) + 2 | **2** |
| Jumlah Process | (61 mod 3) + 2 | **3** |
| Jumlah Data | 172 × 10 | **1720** |

---

## Instalasi

```bash
pip install -r requirements.txt
```

---

## Cara Menjalankan

**Terminal 1 — Jalankan mock server (biarkan tetap terbuka):**

```bash
py mock_server.py
# atau dengan opsi kustom:
py mock_server.py --port 8000 --latency-min 0.001 --latency-max 0.010
```

**Terminal 2 — Jalankan simulasi:**

```bash
# Default: Bagian B + Bagian C (eksperimen + grafik)
py web_simulation.py

# Hanya Bagian B (single run, parameter NIM)
py web_simulation.py --mode b

# Hanya Bagian C (10 konfigurasi + grafik)
py web_simulation.py --mode c

# Dengan URL target kustom
py web_simulation.py --url http://127.0.0.1:8000/api/data
```

**Catatan:**
- Mock server harus berjalan di Terminal 1 sebelum menjalankan `web_simulation.py`
- Semua output (log, CSV, grafik) tersimpan di folder `output/`

