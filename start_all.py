import subprocess
import time
import os
import signal
import sys

def start_bot():
    print("🚀 Avvio NitroBot POLYMARKET (Headless CLOB)...")
    return subprocess.Popen([sys.executable, "bot_poly.py"])

def start_server():
    print("🌐 Avvio Dashboard Service (Port 5000)...")
    return subprocess.Popen([sys.executable, "web_server_v2.py"])

if __name__ == "__main__":
    bot_proc = None
    server_proc = None
    
    try:
        server_proc = start_server()
        time.sleep(2) # Attesa per il server
        bot_proc = start_bot()
        
        print("\n✅ SISTEMA ATTIVO!")
        print("Dashboard: http://localhost:5000")
        print("Premi CTRL+C per fermare tutto.\n")
        
        while True:
            time.sleep(1)
            if bot_proc.poll() is not None:
                print("⚠️ Il bot si è fermato inaspettatamente.")
                break
            if server_proc.poll() is not None:
                print("⚠️ Il server si è fermato inaspettatamente.")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Spegnimento in corso...")
    finally:
        if bot_proc: bot_proc.terminate()
        if server_proc: server_proc.terminate()
        print("👋 Arrivederci!")
