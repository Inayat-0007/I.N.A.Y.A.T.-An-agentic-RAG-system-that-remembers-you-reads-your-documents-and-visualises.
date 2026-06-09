# -*- coding: utf-8 -*-
"""I.N.A.Y.A.T. — SPA Runner.

Orchestrates running both the FastAPI backend server (port 8000) and the
Vite development frontend server (port 5173) concurrently.
"""

import os
import sys
import subprocess
import threading
import time

def run_backend():
    print("🚀 Starting FastAPI Backend Server on http://localhost:8000...")
    # Run uvicorn on port 8000
    subprocess.run([sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"], shell=True)

def run_frontend():
    print("⚡ Starting Vite React Dev Server on http://localhost:5173...")
    # Change directory to frontend and run npm run dev
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    
    # Check if node_modules exists, if not, alert user to run npm install
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("⚠️ node_modules not found in /frontend. Installing packages first...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)
        
    subprocess.run(["npm", "run", "dev"], cwd=frontend_dir, shell=True)

def main():
    # Verify npm is installed
    try:
        subprocess.run(["npm", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
    except FileNotFoundError:
        print("❌ Error: NPM/Node.js is not installed on your system. Please install Node.js to run the frontend developer tools.")
        sys.exit(1)

    # Launch threads
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    frontend_thread = threading.Thread(target=run_frontend, daemon=True)

    backend_thread.start()
    time.sleep(2.5) # Wait for FastAPI to bind port
    frontend_thread.start()

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down I.N.A.Y.A.T. development servers...")
        sys.exit(0)

if __name__ == "__main__":
    main()
