import pandas as pd
import streamlit as st
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Função para calcular a melhor correspondência com TF-IDF
def encontrar_melhor_correspondencia_tfidf(texto, coluna_textos):
    textos = coluna_textos.tolist() + [texto]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(textos)
    cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    melhor_indice = cosine_similarities.argmax()
    melhor_texto = textos[melhor_indice]
    melhor_score = cosine_similarities[melhor_indice]
    return melhor_texto, melhor_score

# Função para garantir que as datas sejam convertidas para o formato correto (DD/MM/YYYY)
def formatar_data(data):
    return datetime.strptime(str(data), '%Y-%m-%d').strftime('%d/%m/%Y')

# Carregar a planilha base2025.xlsx
planilha_path = "base2025.xlsx"
planilha = pd.ExcelFile(planilha_path)

autoanalise_df = planilha.parse("autoanalise")
engenharia_df = planilha.parse("engenharia")

engenharia_df.columns = engenharia_df.columns.str.strip()
autoanalise_df.columns = autoanalise_df.columns.str.strip().str.lower()
engenharia_df.columns = engenharia_df.columns.str.strip().str.lower()

# Inputs do usuário
obra_nome = st.text_input("Obra Nome:")
local_nome = st.text_input("Local Nome:")
data_cvco = st.date_input("Data CVCO:")
numero_solicitacao = st.text_input("Número da Solicitação:")
data_abertura = st.date_input("Data de Abertura:")
garantia_selecionada = st.text_input("Garantia Selecionada:")
problema_relatado = st.text_area("Problema Relatado:")

# Verificar se os campos obrigatórios estão preenchidos
if obra_nome and local_nome and data_cvco and data_abertura and garantia_selecionada and problema_relatado:
    
    # Botão para rodar a análise
    if st.button('Analisar'):
        
        # Formatando as datas
        data_cvco_formatada = formatar_data(data_cvco)
        data_abertura_formatada = formatar_data(data_abertura)
        
        # Filtrar pela Obra Nome e Local Nome na aba engenharia
        if "obra nome" in engenharia_df.columns and "local nome" in engenharia_df.columns:
            engenharia_filtrada = engenharia_df[
                (engenharia_df["obra nome"].str.contains(obra_nome, na=False, case=False)) &
                (engenharia_df["local nome"].str.contains(local_nome, na=False, case=False))
            ]
        else:
            st.error("As colunas 'Obra Nome' ou 'Local Nome' não foram encontradas na aba engenharia.")
            engenharia_filtrada = pd.DataFrame()  # DataFrame vazio para evitar erros subsequentes

        # Análise de textos similares
        if not engenharia_filtrada.empty:
            if "problema relatado" in engenharia_filtrada.columns:
                problema_similar, score_problema = encontrar_melhor_correspondencia_tfidf(
                    problema_relatado, engenharia_filtrada["problema relatado"]
                )
                problema_similar = problema_similar.replace("_x000D_", "\n").strip()

                # Exibir resultados
                st.subheader("Resultados da Análise")
                st.write(f"**Texto Similar no Problema Relatado:**\n{problema_similar}\n(Score: {score_problema:.2f})")
            else:
                st.error("A coluna 'problema relatado' não foi encontrada na aba engenharia.")
        else:
            st.error("Nenhum registro encontrado para a Obra Nome e Local Nome informados.")

        # Exibir o Histórico Similar com Número da Solicitação
        st.subheader("Histórico Similar")
        st.write(f"**Histórico Similar:** {problema_similar}")
        
        # Obter o número da solicitação a partir das colunas "Solicitação Número" ou "VR-Chamado"
        numero_solicitacao_1 = engenharia_filtrada.get("solicitacao numero", pd.Series([None]))
        numero_solicitacao_2 = engenharia_filtrada.get("vr-chamado", pd.Series([None]))

        # Verificar se há valor válido nas duas colunas
        if pd.notna(numero_solicitacao_1.iloc[0]) and pd.notna(numero_solicitacao_2.iloc[0]):  # Verifica se ambos têm valores
            st.write(f"**Número da Solicitação (1):** {numero_solicitacao_1.iloc[0]}")
            st.write(f"**Número da Solicitação (2):** {numero_solicitacao_2.iloc[0]}")
        elif pd.notna(numero_solicitacao_1.iloc[0]):  # Verifica se a primeira coluna tem valor
            st.write(f"**Número da Solicitação:** {numero_solicitacao_1.iloc[0]}")
        elif pd.notna(numero_solicitacao_2.iloc[0]):  # Verifica se a segunda coluna tem valor
            st.write(f"**Número da Solicitação:** {numero_solicitacao_2.iloc[0]}")

        # Cálculo do prazo de garantia (em anos)
        prazo_garantia_coluna = "prazo de garantia"
        
        if prazo_garantia_coluna in autoanalise_df.columns:
            # Buscar o prazo de garantia com base na garantia selecionada
            prazo_garantia_match = autoanalise_df[
                autoanalise_df["grupo sistema construtivo"].str.contains(garantia_selecionada, na=False, case=False)
            ]
            if not prazo_garantia_match.empty:
                prazo_garantia = prazo_garantia_match[prazo_garantia_coluna].iloc[0]  # Selecionar o primeiro resultado
            else:
                st.error(f"Nenhum prazo de garantia encontrado para a Garantia Selecionada: '{garantia_selecionada}' na aba autoanalise.")
                prazo_garantia = None
        else:
            prazo_garantia = None
            st.error("A coluna 'prazo de garantia' não foi encontrada na aba autoanalise.")

        # Determinar o status (PROCEDENTE ou IMPROCEDENTE)
        if prazo_garantia is not None:
            anos_diferenca = (datetime.strptime(data_abertura_formatada, '%d/%m/%Y') - datetime.strptime(data_cvco_formatada, '%d/%m/%Y')).days / 365.25
            if anos_diferenca > prazo_garantia:
                status = "IMPROCEDENTE"
            else:
                status = "PROCEDENTE"

            # Exibir o status final
            st.write(f"**Prazo de Garantia (anos):** {prazo_garantia}")
            st.write(f"**Status Final:** {status}")
        else:
            st.write("Não foi possível determinar o status devido à ausência de informações de prazo de garantia.")
else:
    st.warning("Por favor, preencha todos os campos antes de clicar em 'Analisar'.")
