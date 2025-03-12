import sys
import os

def resource_path(relative_path):
    """
    Retorna o caminho absoluto de 'relative_path', seja no modo de desenvolvimento
    ou quando empacotado pelo PyInstaller (onedir ou onefile).
    """
    # Quando empacotado pelo PyInstaller, a flag 'frozen' estará presente.
    if getattr(sys, 'frozen', False):
        # Em modo onefile, PyInstaller extrai tudo em _MEIPASS (pasta temporária).
        # Em modo onedir, _MEIPASS geralmente aponta para a pasta onde está o .exe.
        base_path = sys._MEIPASS
    else:
        # Modo desenvolvimento (sem PyInstaller).
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, relative_path)
