# old_stub — Uji Kompatibilitas Client Lama (L2.3)

Stub yang dihasilkan dari **versi lama** kontrak `akademik.proto` — `Mahasiswa` hanya punya tiga field (`nim`, `nama`, `ipk`), tanpa `prodi`. Dipakai untuk membuktikan aturan evolusi Protobuf: menambah field baru tidak merusak client lama.

## Berkas

| Berkas | Fungsi |
|---|---|
| `akademik_lama.proto` | Kontrak lama, `package akademiklama`, `Mahasiswa` tanpa `prodi` |
| `akademik_lama_pb2.py` | Hasil generate (sudah disertakan) |
| `klien_lama.py` | Client memakai stub lama, memanggil method server **baru** lewat jalur `/akademik.LayananNilai/GetMahasiswa` |

Package sengaja dibedakan (`akademiklama`) agar descriptor tidak bentrok ketika modul lama dan baru dimuat dalam satu proses.

## Generate ulang

```bash
cd old_stub
python -m grpc_tools.protoc -I. --python_out=. akademik_lama.proto
cd ..        # kembali ke task-5-remote-procedural-call/
```

## Cara menjalankan

Server baru harus hidup lebih dulu (terminal 1):

```bash
python grpc_app/server_grpc.py
```

Client lama (terminal 2):

```bash
python old_stub/klien_lama.py
python old_stub/klien_lama.py --nim 2023002 --port 50051
```

Keluaran yang diharapkan:

```text
Field Mahasiswa di stub lama : ['nim', 'nama', 'ipk']
Client lama menerima         : Andi 3.26
Punya atribut 'prodi'?       : False
Bytes hasil serialisasi      : 0a0832303233303031...
Mengandung 'Informatika'?    : True

Kesimpulan: client lama TETAP BERJALAN. Field nomor 4 yang tidak
dikenal disimpan sebagai unknown field dan ikut diserialisasi ulang.
```

## Arti hasil

- `hasattr(hasil, "prodi") == False` → kode lama tidak tahu field baru, tetapi tidak error.
- `b"Informatika" in bytes` → field 4 tetap diterima dan **diserialisasi ulang** sebagai *unknown field*, sehingga data tidak hilang saat diteruskan.
- Ini alasan nomor field tidak boleh diubah/dipakai ulang: nomor adalah identitas data di kabel.

## Troubleshooting

| Gejala | Solusi |
|---|---|
| `StatusCode.UNAVAILABLE` | server baru belum jalan atau `--port` berbeda |
| `TypeError: Couldn't build proto file... duplicate` | jangan menggabungkan `akademik_pb2` dan `akademik_lama_pb2` dalam satu file `.proto`; keduanya harus tetap dua package |
| `hasattr prodi` bernilai True | stub lama tidak terpakai (mungkin `akademik_pb2` yang diimpor) — pastikan menjalankan `klien_lama.py` |
