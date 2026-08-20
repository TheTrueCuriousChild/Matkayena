"""One-command runner to launch all 4 PS-02 FastAPI Microservices concurrently."""

import subprocess
import sys
import time
import os

SERVERS = [
    {"name": "Server 1 (Core / API)", "module": "backend.services.core_server.main:app", "port": 8000},
    {"name": "Server 2 (Event & Intelligence)", "module": "backend.services.event_intelligence_server.main:app", "port": 8001},
    {"name": "Server 3 (Action & Commission)", "module": "backend.services.action_commission_server.main:app", "port": 8002},
    {"name": "Server 4 (Audit & Blockchain)", "module": "backend.services.audit_blockchain_server.main:app", "port": 8003},
]

def main():
    print("=" * 65)
    print("  PS-02: EVENT-DRIVEN SALES INTELLIGENCE & ACTIONABLE CRM")
    print("  Starting all 4 FastAPI Microservices...")
    print("=" * 65)

    processes = []
    try:
        for s in SERVERS:
            cmd = [
                sys.executable, "-m", "uvicorn",
                s["module"],
                "--host", "0.0.0.0",
                "--port", str(s["port"]),
                "--reload"
            ]
            print(f"🚀 Starting {s['name']} on http://127.0.0.1:{s['port']}...")
            p = subprocess.Popen(cmd)
            processes.append((s["name"], p))
            time.sleep(0.5)

        print("\n" + "=" * 65)
        print("✅ All 4 servers are running:")
        print("   - Server 1 (Core API Gateway):    http://127.0.0.1:8000/docs")
        print("   - Server 2 (Event & Intelligence): http://127.0.0.1:8001/docs")
        print("   - Server 3 (Action & Commission): http://127.0.0.1:8002/docs")
        print("   - Server 4 (Audit & Blockchain):  http://127.0.0.1:8003/docs")
        print("=" * 65)
        print("Press Ctrl+C to stop all servers.\n")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all servers...")
        for name, p in processes:
            p.terminate()
        for name, p in processes:
            p.wait()
        print("All servers stopped cleanly.")

if __name__ == "__main__":
    main()
