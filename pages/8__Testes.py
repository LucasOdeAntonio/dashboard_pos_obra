import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# Configuração de layout
st.set_page_config(
    page_title="Departamento de Pós Obra",
    page_icon="Home.jpg",
    layout='wide'
)

logo_horizontal='LOGO_VR.png'
logo_reduzida="LOGO_VR_REDUZIDA.png"
st.logo(image=logo_horizontal, size="large",icon_image=logo_reduzida)

# Cabeçalho
st.markdown('<h1 style="color: orange;">PAINEL DE ASSISTÊNCIA TÉCNICA 💥</h1>', unsafe_allow_html=True)
st.markdown('Acompanhamento de Solicitações de Assistência Técnica')

# Cacheando os dados
@st.cache_data
def load_and_preprocess_data(url):
    df = pd.read_csv(url)
    df["Solicitação Abertura"] = pd.to_datetime(df["Solicitação Abertura"], format="%d/%m/%Y", errors="coerce")
    df["Solicitação Encerramento"] = pd.to_datetime(df["Solicitação Encerramento"], format="%d/%m/%Y", errors="coerce")
    today = datetime.today()
    df["Solicitação Encerramento"].fillna(today, inplace=True)
    df["Duração"] = (df["Solicitação Encerramento"] - df["Solicitação Abertura"]).dt.days
    return df

google_sheet_url = "https://docs.google.com/spreadsheets/d/1kjX6aEi4rGHOFmFPH9uKDnCdEGYvMiFQUpfoYvBkvO4/export?format=csv"
df = load_and_preprocess_data(google_sheet_url)

# Primeira linha de filtros
col_ano, col_mes, col_situacao_juridica, col_situacao_financeira = st.columns(4)

with col_ano:
    ano_min = int(df["Solicitação Abertura"].dt.year.min()) if not pd.isna(df["Solicitação Abertura"].dt.year.min()) else 2020
    ano_max = int(df["Solicitação Abertura"].dt.year.max()) if not pd.isna(df["Solicitação Abertura"].dt.year.max()) else 2025
    selected_ano = st.selectbox(
        "Filtrar por Ano:",
        options=[None] + list(range(ano_min, ano_max + 1)),
        format_func=lambda x: "Todos" if x is None else x,
    )

with col_mes:
    selected_mes = st.selectbox(
        "Filtrar por Mês:",
        options=[None, "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
        format_func=lambda x: "Todos" if x is None else x,
    )

with col_situacao_juridica:
    selected_situacao_juridica = st.checkbox(
        "Situação Regulatória Jurídica",
        value=False
    )

with col_situacao_financeira:
    selected_situacao_financeira = st.checkbox(
        "Situação Regulatória Financeira",
        value=False
    )

# Segunda linha de filtros
col_obra_nome, col_local_nome, col_solicitacao_procedencia, col_status, col_responsavel = st.columns(5)

with col_obra_nome:
    selected_obra_nome = st.multiselect(
        "Filtrar por Nome do Empreendimento:",
        options=df["Obra Nome"].unique(),
        default=[]
    )

with col_local_nome:
    selected_local_nome = st.multiselect(
        "Filtrar por Bloco/Unidade:",
        options=df["Local Nome"].unique(),
        default=[]
    )

with col_solicitacao_procedencia:
    selected_solicitacao_procedencia = st.multiselect(
        "Filtrar por Solicitação Procedência:",
        options=df["Solicitação Procedência"].unique(),
        default=[]
    )

with col_status:
    selected_status = st.multiselect(
        "Status do Empreendimento:",
        options=df["Status"].unique(),
        default=[]
    )

with col_responsavel:
    selected_responsavel = st.multiselect(
        "Filtrar por Responsável:",
        options=["Todos"] + df["Responsável"].unique().tolist(),
        default=[]
    )
st.markdown('''____________________________________________________________________________________________''')

# Aplicando os filtros de data
filtered_df = df.copy()
if selected_ano is not None:
    filtered_df = filtered_df[filtered_df["Solicitação Abertura"].dt.year == selected_ano]

if selected_mes is not None:
    months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_index = months.index(selected_mes) + 1
    filtered_df = filtered_df[filtered_df["Solicitação Abertura"].dt.month == mes_index]

if selected_obra_nome:
    filtered_df = filtered_df[filtered_df["Obra Nome"].isin(selected_obra_nome)]

if selected_local_nome:
    filtered_df = filtered_df[filtered_df["Local Nome"].isin(selected_local_nome)]

if selected_solicitacao_procedencia:
    filtered_df = filtered_df[filtered_df["Solicitação Procedência"].isin(selected_solicitacao_procedencia)]

if selected_status:
    filtered_df = filtered_df[filtered_df["Status"].isin(selected_status)]

if selected_situacao_juridica:
    filtered_df = filtered_df[filtered_df["Situação Regulatória Jurídica"] == "Sim"]

if selected_situacao_financeira:
    filtered_df = filtered_df[filtered_df["Situação Regulatória Financeira"] == "Sim"]

if selected_responsavel:
    filtered_df = filtered_df[filtered_df["Responsável"].isin(selected_responsavel)]
else:
    filtered_df = filtered_df  # Se nada for selecionado, mantém os dados como estão

# Métricas
filtered_df_not_closed = filtered_df[filtered_df["Solicitação Situação"] != "Encerrada"]

filtered_df_0_15 = filtered_df_not_closed[(filtered_df_not_closed["Duração"] >= 0) & (filtered_df_not_closed["Duração"] <= 15)]
filtered_df_15_30 = filtered_df_not_closed[(filtered_df_not_closed["Duração"] > 15) & (filtered_df_not_closed["Duração"] <= 30)]
filtered_df_30_45 = filtered_df_not_closed[(filtered_df_not_closed["Duração"] > 30) & (filtered_df_not_closed["Duração"] <= 45)]
filtered_df_45_plus = filtered_df_not_closed[filtered_df_not_closed["Duração"] > 45]

# Adicionando a nova métrica de total de solicitações
metric_1 = len(filtered_df_0_15)
metric_2 = len(filtered_df_15_30)
metric_3 = len(filtered_df_30_45)
metric_4 = len(filtered_df_45_plus)
metric_5 = len(filtered_df)  # Contagem total de solicitações após os filtros

# Exibindo as métricas
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Solicitações em Aberto há 0-15 dias", metric_1)
col2.metric("Solicitações em Aberto há 15-30 dias", metric_2)
col3.metric("Solicitações em Aberto há 30-45 dias", metric_3)
col4.metric("Solicitações em Aberto há >45 dias", metric_4)
col5.metric("Total de Solicitações", metric_5)  # Exibindo o total

# Checkboxes para exibir dados e filtrar gráfico
#st.markdown("### Mostrar Solicitações")

# Alteração para 5 colunas, com a última coluna vazia
col5, col6, col7, col8, col9 = st.columns(5)
show_0_15 = col5.checkbox("Mostrar Solicitações (0-15 dias)")
show_15_30 = col6.checkbox("Mostrar Solicitações (15-30 dias)")
show_30_45 = col7.checkbox("Mostrar Solicitações (30-45 dias)")
show_45_plus = col8.checkbox("Mostrar Solicitações (>45 dias)")
# A última coluna (col9) permanece vazia


# Condições para filtro adicional
if show_0_15 or show_15_30 or show_30_45 or show_45_plus:
    filtered_graph_df = pd.concat([ 
        filtered_df_0_15 if show_0_15 else pd.DataFrame(),
        filtered_df_15_30 if show_15_30 else pd.DataFrame(),
        filtered_df_30_45 if show_30_45 else pd.DataFrame(),
        filtered_df_45_plus if show_45_plus else pd.DataFrame()
    ])
else:
    filtered_graph_df = filtered_df
st.markdown('''____________________________________________________________________________________________''')#

# Gráfico de barras por "Obra Nome"
#st.markdown("### Distribuição de Solicitações por Obra Nome")

if not filtered_graph_df.empty:
    # Contagem de solicitações por "Obra Nome" e "Status"
    df_grouped = filtered_graph_df.groupby(["Obra Nome", "Status"]).size().reset_index(name="Contagem")

    # Criação do gráfico de barras
    fig = px.bar(
        df_grouped,
        x="Obra Nome",
        y="Contagem",
        color="Status",  # Usando "Status" no gráfico
        title="Solicitações por Empreendimento",
        labels={"Obra Nome": "Obra", "Contagem": "Número de Solicitações"},
        barmode="stack",  # Empilhar barras em vez de sobrepor
        text="Contagem"  # Adiciona o texto com o número dentro da barra
    )

    # Atualizar o gráfico
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        showlegend=True,  # Exibir legenda
        xaxis=dict(showline=False),  # Remover linha do eixo X
        yaxis=dict(showline=False),  # Remover linha do eixo Y
        height=400,  # Ajustar altura do gráfico
        margin=dict(t=40, b=80, l=40, r=40),  # Ajustar margens para visualização
    )

    # Aumentar o tamanho dos rótulos de dados para facilitar leitura
    fig.update_traces(
        texttemplate='%{text}', 
        textposition='inside',  # Colocar rótulo dentro da barra
        insidetextanchor='middle',  # Alinhar texto dentro da barra
        textfont=dict(size=14)  # Tamanho maior dos rótulos
    )

    # Exibir gráfico
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Não há dados disponíveis para exibição do gráfico.")

# Exibição dos dados filtrados
if show_0_15:
    st.write("### Solicitações (0-15 dias)")
    st.dataframe(filtered_df_0_15)
if show_15_30:
    st.write("### Solicitações (15-30 dias)")
    st.dataframe(filtered_df_15_30)
if show_30_45:
    st.write("### Solicitações (30-45 dias)")
    st.dataframe(filtered_df_30_45)
if show_45_plus:
    st.write("### Solicitações (>45 dias)")
    st.dataframe(filtered_df_45_plus)
st.markdown('''____________________________________________________________________________________________''')#

st.write('### Análise de Indicadores')
