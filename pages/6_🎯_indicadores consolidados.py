import streamlit as st
import pandas as pd
import sys
import os
from PIL import Image
from utils import resource_path

# Configurando Página
st.set_page_config(
    page_icon="Home.jpg",
    layout='wide',
    page_title="Pós Obra - Indicadores"
)

#Logo superior no sidebar, imagem grande e reduzida.
logo_horizontal_path = resource_path("LOGO_VR.png")
logo_reduzida_path   = resource_path("LOGO_VR_REDUZIDA.png")

try:
    logo_horizontal = Image.open(logo_horizontal_path)
    logo_reduzida   = Image.open(logo_reduzida_path)
    st.logo(image=logo_horizontal, size="large", icon_image=logo_reduzida)
except Exception as e:
    st.error(f"Não foi possível carregar as imagens: {e}")


# CEBEÇALHO INÍCIO ===========================================================================================================================
#st.image("LOGO_VR.png", caption="") - pra adicionar imagens
st.markdown('<h1 style="color: orange;">Indicadores Consolidados 🎯</h1>', unsafe_allow_html=True)
#st.image("fluxograma.png", caption="")


st.markdown('''
       Página em Construção. Volte mais tarde! 🚧 ''')