import streamlit as st
import pandas as pd
import numpy as np
import spacy

# Carregar modelo de linguagem natural do spaCy
nlp = spacy.load("pt_core_news_sm")

# Base de conhecimento expandida para melhor enquadramento
dados_norma = [
    {"Grupo": "Estrutura", "Sistema": "Elementos estruturais", "Descrição": "Falhas em lajes, pilares, vigas e paredes estruturais", "Tipos de Falhas": "Trincas, fissuras, deslocamento de concreto", "Prazo de Garantia": 20},
    {"Grupo": "Vedações", "Sistema": "Revestimentos", "Descrição": "Camada de acabamento decorativo – textura", "Tipos de Falhas": "Perda de integridade da película", "Prazo de Garantia": 3},
    {"Grupo": "Esquadrias", "Sistema": "Janelas e Portas", "Descrição": "Vedação da interface da esquadria e requadros", "Tipos de Falhas": "Perda de estanqueidade devido à falta de aderência", "Prazo de Garantia": 0.5},
    {"Grupo": "Sistemas", "Sistema": "Sistemas Elétricos", "Descrição": "Componentes elétricos de baixa tensão", "Tipos de Falhas": "Falha na alimentação de energia, sobrecarga", "Prazo de Garantia": 5}
]

# Dicionário de termos associados a cada grupo
termos_sistema = {
    "Sistemas Elétricos": ["tomada", "disjuntor", "energia", "circuito", "fiação", "voltagem", "curto-circuito", "quadro elétrico"],
    "Estrutura": ["rachadura", "trinca", "fissura", "coluna", "viga", "pilar", "afundamento"],
    "Vedações": ["reboco", "revestimento", "azulejo", "cerâmica", "gesso", "pintura"],
    "Esquadrias": ["janela", "porta", "batente", "vedação", "vidro", "fechadura"]
}

# Função para encontrar o melhor enquadramento
def encontrar_enquadramento_com_regras(problema_relatado):
    doc = nlp(problema_relatado.lower())
    
    # Verificar palavras-chave primeiro e retornar imediatamente
    for grupo, termos in termos_sistema.items():
        if any(token.text in termos for token in doc):
            for item in dados_norma:
                if item["Grupo"] == grupo:
                    return item  # Retorna o primeiro item correto
    
    # Se não encontrou correspondência direta, faz um comparativo semântico
    melhor_pontuacao = 0
    melhor_item = None
    
    for item in dados_norma:
        descricao_doc = nlp(item["Descrição"].lower())
        similaridade = doc.similarity(descricao_doc)
        
        if similaridade > melhor_pontuacao:
            melhor_pontuacao = similaridade
            melhor_item = item
    
    return melhor_item

# Definir função de validação do prazo de garantia
def validar_prazo_garantia(obra_nome, data_solicitacao, prazo_garantia):
    data_cvco = pd.to_datetime("2020-01-01")  # Aqui deve ser ajustado para buscar na base real
    data_solicitacao = pd.to_datetime(data_solicitacao)
    diferenca_anos = (data_solicitacao - data_cvco).days / 365
    return "PROCEDENTE" if diferenca_anos <= prazo_garantia else "IMPROCEDENTE"

# Função para processar a solicitação
def processar_solicitacao(obra_nome, garantia_selecionada, problema_relatado, data_solicitacao, numero_solicitacao):
    enquadramento = encontrar_enquadramento_com_regras(problema_relatado)
    status_garantia = validar_prazo_garantia(obra_nome, data_solicitacao, enquadramento["Prazo de Garantia"])
    return {
        "Número da Solicitação": numero_solicitacao,
        "Obra Nome": obra_nome,
        "Garantia Selecionada": garantia_selecionada,
        "Problema Relatado": problema_relatado,
        "Grupo Identificado": enquadramento["Grupo"],
        "Sistema Identificado": enquadramento["Sistema"],
        "Descrição Identificada": enquadramento["Descrição"],
        "Tipo de Falha Identificado": enquadramento["Tipos de Falhas"],
        "Prazo de Garantia": enquadramento["Prazo de Garantia"],
        "Status da Garantia": status_garantia
    }

# Criar interface no Streamlit
st.title("Análise de Solicitações - Garantia e Enquadramento")

# Criar campos do formulário
obra_nome = st.text_input("Obra Nome")
garantia_selecionada = st.text_input("Garantia Selecionada")
problema_relatado = st.text_area("Problema Relatado")
data_solicitacao = st.date_input("Data da Solicitação")
numero_solicitacao = st.text_input("Número da Solicitação")

# Botão para processar a solicitação
if st.button("Analisar Solicitação"):
    if obra_nome and problema_relatado and data_solicitacao:
        resultado = processar_solicitacao(obra_nome, garantia_selecionada, problema_relatado, data_solicitacao, numero_solicitacao)
        st.write("### Resultado da Análise:")
        st.json(resultado)
    else:
        st.warning("Por favor, preencha todos os campos obrigatórios.")
