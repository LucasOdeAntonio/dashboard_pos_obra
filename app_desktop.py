import sys
import os
import threading
import subprocess
import time
import webview

def resource_path(relative_path):
    """
    Obtém o caminho absoluto para um recurso.
    Funciona tanto em desenvolvimento quanto quando empacotado com PyInstaller (modo onefile).
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def start_streamlit():
    # Usa resource_path para localizar o arquivo home.py
    home_file = resource_path("home.py")
    subprocess.run(["streamlit", "run", home_file])

if __name__ == '__main__':
    # Inicia o servidor Streamlit em uma thread separada
    t = threading.Thread(target=start_streamlit, daemon=True)
    t.start()
    
    # Aguarda alguns segundos para o servidor Streamlit subir (ajuste se necessário)
    time.sleep(5)
    
    # Cria a janela do aplicativo apontando para o endereço local do Streamlit
    webview.create_window("Dashboard de Pós-Obra", "http://localhost:8501")
    webview.start()
