import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Configurando Página
st.set_page_config(
    page_icon="Home.jpg",
    layout='wide',
    page_title="Pós Obra - Sistemas Construtivos"
)

#Logo superior no sidebar, imagem grande e reduzida.
logo_horizontal='LOGO_VR.png'
logo_reduzida="LOGO_VR_REDUZIDA.png"
st.logo(image=logo_horizontal, size="large",icon_image=logo_reduzida)


# CEBEÇALHO INÍCIO ===========================================================================================================================
#st.image("LOGO_VR.png", caption="") - pra adicionar imagens
st.markdown('<h1 style="color: orange;">Sistemas Construtivos 🏗️</h1>', unsafe_allow_html=True)
#st.image("fluxograma.png", caption="")


st.markdown('''
       Página em Construção. Volte mais tarde! 🚧 ''')

# =========================================
# Carregamento das planilhas
# =========================================
@st.cache_data
def load_data():
    xls = pd.ExcelFile("base2025.xlsx")
    # Aba Engenharia
    df_eng = pd.read_excel(xls, sheet_name="engenharia")
    # Aba Departamento (para pegar Empreendimento x Data CVCO)
    df_dep = pd.read_excel(xls, sheet_name="departamento")
    
    # Limpa e normaliza as colunas, se necessário
    for df_ in [df_eng, df_dep]:
        df_.columns = df_.columns.str.strip()
    
    return df_eng, df_dep

df_eng, df_dep = load_data()

# =========================================
# Junta "Data CVCO" no dataframe de engenharia
# =========================================
# Precisamos do Empreendimento e Data CVCO para cada linha de engenharia
if "Empreendimento" not in df_eng.columns or "Empreendimento" not in df_dep.columns:
    st.error("Não foi possível relacionar 'Empreendimento' entre as abas engenharia e departamento.")
    st.stop()

# Vamos renomear para padronizar
df_dep = df_dep.rename(columns={"Data CVCO": "Data_CVCO"})
# Reduz df_dep só ao que precisamos
df_dep_min = df_dep[["Empreendimento", "Data_CVCO"]].dropna()

# Merge
df_merged = pd.merge(df_eng, df_dep_min, on="Empreendimento", how="left")

# =========================================
# Conversão de datas e cálculo do Tempo de Interrupção
# =========================================
# Garante que as colunas existam
if "Data de Abertura" not in df_merged.columns:
    st.error("Coluna 'Data de Abertura' não encontrada em engenharia.")
    st.stop()

# Se não existir "Encerramento", criamos uma coluna vazia
if "Encerramento" not in df_merged.columns:
    df_merged["Encerramento"] = pd.NaT

df_merged["Data de Abertura"] = pd.to_datetime(df_merged["Data de Abertura"], errors="coerce")
df_merged["Encerramento"] = pd.to_datetime(df_merged["Encerramento"], errors="coerce")
df_merged["Data_CVCO"] = pd.to_datetime(df_merged["Data_CVCO"], errors="coerce")

# Define função para calcular tempo de interrupção
def calcular_tempo_interrupcao(row):
    # Se Data de Abertura inválida, retornamos None
    if pd.isna(row["Data de Abertura"]):
        return np.nan
    
    # Start = maior entre Data de Abertura e Data_CVCO (se houver Data_CVCO)
    if pd.isna(row["Data_CVCO"]):
        start = row["Data de Abertura"]
    else:
        start = max(row["Data de Abertura"], row["Data_CVCO"])
    
    # End = Encerramento ou hoje
    if pd.isna(row["Encerramento"]):
        end = pd.to_datetime(datetime.now().date())  # somente data (00:00)
    else:
        end = row["Encerramento"]
    
    diff = (end - start).days
    return diff if diff > 0 else 0  # se negativo, zera

df_merged["Tempo_dias"] = df_merged.apply(calcular_tempo_interrupcao, axis=1)

# =========================================
# Filtros (na tela principal)
# =========================================
st.title("Dashboard - Engenharia (Manutenção e Indicadores)")
st.write("Exemplo de cálculo de **MTTR, MTBF, Disponibilidade e Confiabilidade** usando datas.")

st.subheader("Filtros")
df_filtered = df_merged.copy()

cols_to_filter = [c for c in df_merged.columns if c not in ["Pesquisa"]]
for col in cols_to_filter:
    unique_vals = df_merged[col].dropna().unique().tolist()
    # Se for muitas categorias, pode ser interessante ordená-las
    unique_vals = sorted(unique_vals, key=lambda x: str(x))
    
    # Para dados do tipo string ou categórico
    if df_merged[col].dtype == "object" or str(df_merged[col].dtype).startswith("category"):
        selected_vals = st.multiselect(f"Filtrar por **{col}**", options=unique_vals, default=[])
        if selected_vals:
            df_filtered = df_filtered[df_filtered[col].isin(selected_vals)]
    
    # Para datas
    elif pd.api.types.is_datetime64_any_dtype(df_merged[col]):
        min_date = df_merged[col].min()
        max_date = df_merged[col].max()
        if pd.isna(min_date) or pd.isna(max_date):
            continue
        # Streamlit date_input só aceita range em tupla (data inicial, data final)
        data_range = st.date_input(f"Período de {col}", (min_date.date(), max_date.date()))
        if len(data_range) == 2:
            start_date, end_date = data_range
            df_filtered = df_filtered[(df_filtered[col] >= pd.to_datetime(start_date)) & 
                                      (df_filtered[col] <= pd.to_datetime(end_date))]
    
    # Para numéricos (exemplo: Tempo_dias)
    elif pd.api.types.is_numeric_dtype(df_merged[col]):
        min_val = float(df_merged[col].min())
        max_val = float(df_merged[col].max())
        selected_range = st.slider(f"{col}", min_val, max_val, (min_val, max_val))
        df_filtered = df_filtered[(df_filtered[col] >= selected_range[0]) & 
                                  (df_filtered[col] <= selected_range[1])]

st.write("Amostra dos dados filtrados:")
st.dataframe(df_filtered.head(), use_container_width=True)

# =========================================
# Cálculo de MTTR, MTBF, Disponibilidade, Confiabilidade
# =========================================
st.subheader("Indicadores de Manutenção")

# Precisamos de registros que tenham Data_CVCO válida para o MTBF global
df_filtered_valid = df_filtered.dropna(subset=["Data_CVCO", "Data de Abertura"])

if df_filtered_valid.empty:
    st.warning("Não há dados suficientes (Data_CVCO e Data de Abertura) para calcular indicadores.")
else:
    # MTTR = média de Tempo_dias
    mttr = df_filtered_valid["Tempo_dias"].mean()
    
    # Número de falhas (solicitações) = número de linhas
    num_falhas = len(df_filtered_valid)
    
    # Tempo de Operação Total = soma (Hoje - Data_CVCO) de cada empreendimento
    # (para cada linha, mas convém agrupar por Empreendimento para não contar duplicado)
    # Abordagem simples: agrupar por Empreendimento e somar
    df_op = df_filtered_valid.groupby("Empreendimento")["Data_CVCO"].min().reset_index()
    # Para cada empreendimento, tempo de operação = (hoje - Data_CVCO).days
    hoje = pd.to_datetime(datetime.now().date())
    df_op["Operacao_dias"] = (hoje - df_op["Data_CVCO"]).dt.days.clip(lower=0)
    
    tempo_operacao_total = df_op["Operacao_dias"].sum()
    
    if num_falhas == 0 or tempo_operacao_total == 0:
        st.warning("Não foi possível calcular MTBF pois não há falhas ou tempo de operação válido.")
        mtbf = 0
        disponibilidade = 0
        confiabilidade = 0
    else:
        # MTBF = tempo_operacao_total / num_falhas
        mtbf = tempo_operacao_total / num_falhas
        # Disponibilidade = MTBF / (MTBF + MTTR)
        disponibilidade = mtbf / (mtbf + mttr) if (mtbf + mttr) > 0 else 0
        # Confiabilidade (simplificada) = 1 - (num_falhas / tempo_operacao_total)
        confiabilidade = 1 - (num_falhas / tempo_operacao_total)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("MTTR (dias)", f"{mttr:.2f}")
    col2.metric("MTBF (dias)", f"{mtbf:.2f}")
    col3.metric("Disponibilidade", f"{disponibilidade*100:.2f}%")
    col4.metric("Confiabilidade", f"{confiabilidade*100:.2f}%")

# =========================================
# Top 20 - Garantia Solicitada (Curva ABC)
# =========================================
st.subheader("Top 20 - 'Garantia Solicitada' (Curva ABC)")
if "Garantia Solicitada" not in df_filtered.columns:
    st.warning("Coluna 'Garantia Solicitada' não encontrada após filtros.")
else:
    contagem = df_filtered["Garantia Solicitada"].value_counts().reset_index()
    contagem.columns = ["Garantia", "Contagem"]
    contagem = contagem.sort_values(by="Contagem", ascending=False)
    
    if contagem.empty:
        st.warning("Nenhuma ocorrência de 'Garantia Solicitada' após filtros.")
    else:
        # Curva ABC
        total = contagem["Contagem"].sum()
        contagem["% Acumulado"] = contagem["Contagem"].cumsum() / total * 100
        
        def classifica_abc(pct):
            if pct <= 80:
                return "A"
            elif pct <= 95:
                return "B"
            else:
                return "C"
        
        contagem["ABC"] = contagem["% Acumulado"].apply(classifica_abc)
        top20 = contagem.head(20)
        
        fig_abc = px.bar(
            top20,
            x="Garantia",
            y="Contagem",
            color="ABC",
            title="Top 20 - 'Garantia Solicitada' (Classificação ABC)",
            text="Contagem",
            color_discrete_map={"A": "red", "B": "orange", "C": "green"},
        )
        fig_abc.update_layout(
            xaxis_title="Garantia Solicitada",
            yaxis_title="Quantidade",
            xaxis_tickangle=-45,
            uniformtext_minsize=8,
            uniformtext_mode='show'
        )
        st.plotly_chart(fig_abc, use_container_width=True)

# =========================================
# Evolução Temporal (Data de Abertura)
# =========================================
st.subheader("Evolução Temporal (Ocorrências por Mês/Ano)")
if "Data de Abertura" in df_filtered.columns:
    df_time = df_filtered.dropna(subset=["Data de Abertura"]).copy()
    if not df_time.empty:
        df_time_grouped = df_time.groupby(df_time["Data de Abertura"].dt.to_period("M")).size().reset_index(name="Ocorrências")
        df_time_grouped["Data de Abertura"] = df_time_grouped["Data de Abertura"].dt.to_timestamp()
        
        fig_time = px.line(
            df_time_grouped,
            x="Data de Abertura",
            y="Ocorrências",
            markers=True,
            title="Evolução de Ocorrências (por Mês/Ano)"
        )
        fig_time.update_layout(xaxis_title="Mês/Ano", yaxis_title="Número de Ocorrências")
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("Não há datas de abertura válidas após os filtros.")
else:
    st.info("Coluna 'Data de Abertura' não encontrada para análise temporal.")
