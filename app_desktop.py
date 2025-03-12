import sys
import os

if getattr(sys, 'frozen', False):
    sys.path.append(sys._MEIPASS)

import threading
import subprocess
import time
import webview
from utils import resource_path  # Agora deverá funcionar

def start_streamlit():
    home_file = resource_path("home.py")
    subprocess.run(["streamlit", "run", home_file])

if __name__ == '__main__':
    t = threading.Thread(target=start_streamlit, daemon=True)
    t.start()
    time.sleep(5)  # Ajuste o tempo se necessário
    webview.create_window("Dashboard de Pós-Obra", "http://localhost:8501")
    webview.start()
