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

# Criando o cliente OpenAI corretamente com a API atualizada
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    try:
        # Envia a pergunta para a API da OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages
        )

        bot_response = response.choices[0].message.content

        # Adiciona resposta ao histórico
        st.session_state.messages.append({"role": "assistant", "content": bot_response})

        # Exibe resposta no Streamlit
        with st.chat_message("assistant"):
            st.markdown(bot_response)

    except openai.OpenAIError as e:
        st.error(f"Erro ao acessar a API OpenAI: {str(e)}")
