import streamlit as st
import pandas as pd

# Configurando Página
st.set_page_config(
    page_icon="Home.jpg",
    layout='wide',
    page_title="Pós Obra - Indicadores"
)

#Logo superior no sidebar, imagem grande e reduzida.
logo_horizontal='LOGO_VR.png'
logo_reduzida="LOGO_VR_REDUZIDA.png"
st.logo(image=logo_horizontal, size="large",icon_image=logo_reduzida)


# CEBEÇALHO INÍCIO ===========================================================================================================================
#st.image("LOGO_VR.png", caption="") - pra adicionar imagens
st.markdown('<h1 style="color: orange;">Indicadores Consolidados 🎯</h1>', unsafe_allow_html=True)
#st.image("fluxograma.png", caption="")


st.markdown('''
       Página em Construção. Volte mais tarde! 🚧 ''')