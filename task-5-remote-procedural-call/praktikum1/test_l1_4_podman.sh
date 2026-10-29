#!/usr/bin/env bash
# test_l1_4_podman.sh — benchmark L1.4 lintas jaringan memakai Podman.
#
# Host (Fedora) menjalankan server XML-RPC; container Python/Alpine menjadi
# "komputer kedua" dengan namespace jaringan sendiri. Traffic melewati pasta/
# bridge, bukan loopback, sehingga latensi yang diukur realistis.
#
# Jalankan dari mana saja:
#   ./praktikum1/test_l1_4_podman.sh
#   PORT=8001 N=200 ./praktikum1/test_l1_4_podman.sh
#   IMAGE=docker.io/library/python:3.12-alpine ./praktikum1/test_l1_4_podman.sh
#
# Bila belum ada server yang melayani, skrip menyalakannya sendiri di
# 0.0.0.0:<port> (tanpa --verbose) lalu mematikannya lagi saat selesai.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${IMAGE:-docker.io/library/python:3.12-alpine}"
NETWORK="${NETWORK:-rpc-test-net}"
PORT="${PORT:-8000}"
N="${N:-100}"
PY="${PY:-$ROOT/venv/bin/python}"
LOG="$(mktemp -t l1_4_podman_server.XXXXXX.log)"
SRV=""

bersihkan() {
    if [ -n "$SRV" ] && kill -0 "$SRV" 2>/dev/null; then
        kill "$SRV" 2>/dev/null || true
        wait "$SRV" 2>/dev/null || true
    fi
    rm -f "$LOG"
}
trap bersihkan EXIT

if ! command -v podman >/dev/null 2>&1; then
    echo "GAGAL: podman tidak ditemukan. Instal dulu: sudo dnf install podman" >&2
    exit 1
fi

if [ "${LEWATI_IDENTITAS:-0}" != "1" ]; then
    cat <<'IDENTITAS'
================================================================================
  KOMPUTASI PARALEL & TERDISTRIBUSI
  Praktikum Remote Procedure Calls (RPC)
================================================================================
  MAHASISWA   : Raka Restu Saputra
  NIM         : 247006111172
  KELAS       : F
================================================================================
IDENTITAS
    echo
fi

echo "======================================================================"
echo "  L1.4 — BENCHMARK XML-RPC LINTAS JARINGAN (PODMAN)"
echo "======================================================================"
echo "  Image   : $IMAGE"
echo "  Network : $NETWORK"
echo "  Port    : $PORT"
echo "  Request : $N"
echo

podman network exists "$NETWORK" 2>/dev/null || podman network create "$NETWORK" >/dev/null
GW="$(podman network inspect -f '{{(index .Subnets 0).Gateway}}' "$NETWORK" 2>/dev/null || true)"

KANDIDAT=("host.containers.internal")
[ -n "$GW" ] && KANDIDAT+=("$GW")
for ip in $(hostname -I 2>/dev/null || true); do KANDIDAT+=("$ip"); done
[ -n "${HOST_TAMBAHAN:-}" ] && KANDIDAT+=("$HOST_TAMBAHAN")

# Skrip Python yang berjalan DI DALAM container (hanya stdlib).
baca_stdin() {
    cat <<'PY'
import statistics
import socket
import sys
import time
import xmlrpc.client

port = int(sys.argv[1])
jumlah = int(sys.argv[2])
kandidat = sys.argv[3:]
socket.setdefaulttimeout(3)

dipakai = None
galat = []
for host in kandidat:
    try:
        proxy = xmlrpc.client.ServerProxy(f"http://{host}:{port}/")
        if proxy.tambah(5, 3) == 8:
            dipakai = host
            break
    except Exception as exc:  # noqa: BLE001 - laporkan semua kandidat
        galat.append(f"  - {host}:{port} -> {type(exc).__name__}: {exc}")

if dipakai is None:
    print("Tidak ada kandidat host yang melayani XML-RPC:", file=sys.stderr)
    print("\n".join(galat), file=sys.stderr)
    raise SystemExit(3)

proxy = xmlrpc.client.ServerProxy(f"http://{dipakai}:{port}/")
for _ in range(3):          # pemanasan, tidak dihitung
    proxy.tambah(5, 3)

sampel = []
for _ in range(jumlah):
    mulai = time.perf_counter()
    proxy.tambah(5, 3)
    sampel.append(time.perf_counter() - mulai)

total = sum(sampel)
rata = total / jumlah
print()
print("Hasil benchmark di dalam container")
print(f"  Host tujuan     : {dipakai}:{port}")
print(f"  Requests        : {jumlah}")
print(f"  Total           : {total:.4f} s")
print(f"  Rata-rata       : {rata * 1000:.4f} ms/panggilan")
print(f"  Median          : {statistics.median(sampel) * 1000:.4f} ms")
print(f"  Min / Maks      : {min(sampel) * 1000:.4f} / {max(sampel) * 1000:.4f} ms")
print("  Environment     : PODMAN CONTAINER (Cross-Network)")
print(f"PODMAN_HOST={dipakai}")
print(f"PODMAN_AVG_MS={rata * 1000:.6f}")
PY
}

jalankan_container() {
    podman run --rm -i --name "rpc-client-l14-$$" \
        --network "$NETWORK" \
        -e no_proxy='*' -e NO_PROXY='*' \
        "$IMAGE" python - "$PORT" "$N" "$@" < <(baca_stdin)
}

mulai_server() {
    local i j
    for i in $(seq 1 20); do
        "$PY" "$ROOT/praktikum1/server_kalkulator.py" --host 0.0.0.0 --port "$PORT" >"$LOG" 2>&1 &
        SRV=$!

        for j in $(seq 1 40); do
            if (exec 3<>"/dev/tcp/127.0.0.1/$PORT") 2>/dev/null; then
                return 0
            fi
            kill -0 "$SRV" 2>/dev/null || break
            sleep 0.25
        done

        # Gagal (mis. port dipakai proses lain) -> coba port berikutnya.
        kill "$SRV" 2>/dev/null || true
        wait "$SRV" 2>/dev/null || true
        SRV=""
        PORT=$((PORT + 1))
    done

    echo "GAGAL menyalakan server di 20 port percobaan. Log terakhir:" >&2
    cat "$LOG" >&2
    return 1
}

set +e
KELUARAN="$(jalankan_container "${KANDIDAT[@]}" 2>&1)"
STATUS=$?
set -e

if [ "$STATUS" -eq 3 ]; then
    mulai_server
    set +e
    KELUARAN="$(jalankan_container "${KANDIDAT[@]}" 2>&1)"
    STATUS=$?
    set -e
fi

printf '%s\n' "$KELUARAN"
if [ "$STATUS" -ne 0 ]; then
    echo "Benchmark gagal (exit $STATUS)." >&2
    exit "$STATUS"
fi

echo
echo "======================================================================"
echo "  UJI L1.4 SELESAI — container sebagai perangkat kedua"
echo "======================================================================"
