import streamlit as st
import pandas as pd
import sys
import os
from PIL import Image

# Configurando Página
st.set_page_config(
    page_icon="Home.jpg",
    layout='wide',
    page_title="Pós Obra - Indicadores"
)

#Logo superior no sidebar, imagem grande e reduzida.
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

logo_path = resource_path("LOGO_VR.png")
try:
    logo_image = Image.open(logo_path)
    st.logo(image=logo_image, size="large")
except Exception as e:
    st.error(f"Não foi possível carregar a imagem: {e}")


# CEBEÇALHO INÍCIO ===========================================================================================================================
#st.image("LOGO_VR.png", caption="") - pra adicionar imagens
st.markdown('<h1 style="color: orange;">Indicadores Consolidados 🎯</h1>', unsafe_allow_html=True)
#st.image("fluxograma.png", caption="")


st.markdown('''
       Página em Construção. Volte mais tarde! 🚧 ''')