import subprocess
import sys
import os
import signal
import time

def main():
    print("🚀 Starting EcoFinds V2 Full Stack...")
    print("=========================================")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Start Backend
    print("🔥 Booting Backend (Flask) on port 5000...")
    backend_process = subprocess.Popen([sys.executable, "app.py"], cwd=base_dir)

    # Wait a second to allow Flask to initialize DB and seed before opening browser
    time.sleep(2)

    # 2. Start Frontend
    print("🌍 Booting Frontend (http-server) on port 5173...")
    is_windows = sys.platform.startswith('win')
    
    try:
        # -c-1 disables caching
        # -o /index.html automatically opens the browser
        frontend_cmd = ["npx", "-y", "http-server", "./frontend", "-p", "5173", "-c-1", "-o", "/index.html"]
        frontend_process = subprocess.Popen(
            frontend_cmd, 
            cwd=base_dir, 
            shell=is_windows
        )
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        print("Please ensure Node.js and npx are installed.")
        backend_process.terminate()
        sys.exit(1)

    print("\n✅ Both servers are running successfully!")
    print("👉 Frontend: http://localhost:5173/index.html")
    print("👉 Backend API: http://localhost:5000")
    print("Press Ctrl+C in this terminal to stop both servers at once.\n")

    # Graceful shutdown handling
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down EcoFinds servers gracefully...")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Keep script alive securely waiting for subprocesses
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
