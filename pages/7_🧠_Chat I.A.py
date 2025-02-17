import streamlit as st
import pandas as pd
import openai
import os

# Configurando a página - TEM QUE SER O PRIMEIRO COMANDO DO STREAMLIT
st.set_page_config(
    page_icon="🧠",
    page_title="Assistente A.T",
    layout='wide'
)

# Logo superior no sidebar, imagem grande e reduzida.
logo_horizontal = 'LOGO_VR.png'
logo_reduzida = "LOGO_VR_REDUZIDA.png"
st.logo(image=logo_horizontal, size="large", icon_image=logo_reduzida)

# Cabeçalho
st.markdown('<h1 style="color: orange;">Auto Análise Preliminar ♻️</h1>', unsafe_allow_html=True)

openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("🧠 Assistente A.T")
st.write("Tire suas dúvidas sobre o **Manual do Proprietário** e a **NBR 17.170**!")

# Histórico de mensagens do chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibir mensagens antigas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada do usuário
user_input = st.text_input("Digite sua dúvida:", key="user_input")

if user_input:
    # Adiciona pergunta ao histórico
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Envia a pergunta para a API da OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=st.session_state.messages
    )

    bot_response = response["choices"][0]["message"]["content"]

    # Adiciona resposta ao histórico
    st.session_state.messages.append({"role": "assistant", "content": bot_response})

    # Exibe resposta no Streamlit
    with st.chat_message("assistant"):
        st.markdown(bot_response)
