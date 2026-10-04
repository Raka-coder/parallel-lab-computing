"""
mock_server.py — Server target untuk Parallel Web Simulation
Jalankan di Terminal 1: py mock_server.py
Biarkan terbuka selama eksperimen berjalan.
"""
import argparse
import random
import time

from flask import Flask, jsonify

app = Flask(__name__)

# Latency default 1-10 ms agar eksperimen cepat
LATENCY_MIN = 0.001
LATENCY_MAX = 0.010


@app.route('/api/data', methods=['GET'])
def get_data():
    """Endpoint utama — simulasi latency server."""
    latency = random.uniform(LATENCY_MIN, LATENCY_MAX)
    time.sleep(latency)
    return jsonify({
        "status": "ok",
        "latency_simulated_ms": round(latency * 1000, 3),
        "data": "sample_response"
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check — dipakai program utama untuk verifikasi server."""
    return jsonify({"status": "healthy"})


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--latency-min", type=float, default=LATENCY_MIN,
                    help="Latency minimum (detik). Default 0.001 (1 ms)")
    ap.add_argument("--latency-max", type=float, default=LATENCY_MAX,
                    help="Latency maksimum (detik). Default 0.010 (10 ms)")
    args = ap.parse_args()

    LATENCY_MIN = args.latency_min
    LATENCY_MAX = args.latency_max

    print("=" * 65)
    print("  MOCK WEB SERVER")
    print("=" * 65)
    print(f"  URL       : http://127.0.0.1:{args.port}/api/data")
    print(f"  Health    : http://127.0.0.1:{args.port}/health")
    print(f"  Latency   : {LATENCY_MIN*1000:.0f}-{LATENCY_MAX*1000:.0f} ms")
    print("=" * 65)
    print("  JANGAN TUTUP TERMINAL INI")
    print("=" * 65)
    app.run(host='0.0.0.0', port=args.port, threaded=True, debug=False)