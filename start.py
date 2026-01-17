#!/usr/bin/env python3

import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def run_flask():
    """Start Flask API server"""

    print("Starting Flask API server...")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "-m", "api.app"])

def run_react():
    """Start React development server"""
    print("Starting React development server...")
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    os.chdir(frontend_dir)
    
    # Install dependencies if needed
    if not os.path.exists("node_modules"):
        print("Installing React dependencies...")
        subprocess.run(["npm", "install"], shell=True)
    
    print("Starting React app...")
    subprocess.run(["npm", "start"], shell=True)

def open_browser():
    """Open browser after servers start"""

    time.sleep(3)  # Wait for servers to start
    print("\nOpening browser to http://localhost:3000")
    webbrowser.open("http://localhost:3000")

if __name__ == "__main__":
    print("=" * 60)
    print("Brandon's RDBMS Web Interface - Starting Servers")
    print("=" * 60)
    
    # Open browser
    browser_thread = Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("\n1. Starting Flask API server (http://localhost:5000)")
    print("2. To start React, open another terminal and run:")
    print("   cd react-frontend && npm start")
    print("\n3. Then open http://localhost:3000 in your browser")
    print("=" * 60)
    
    run_flask()