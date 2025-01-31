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
#st.write("Colunas disponíveis no DataFrame:", df.columns) #Carregar DF para ver colunas (caso de nomes errados)
df.columns = df.columns.str.strip()

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

    fig = px.bar(
    df_grouped,
    x="Obra Nome",
    y="Contagem",
    color="Status",  # Usando "Status" no gráfico
    title="Solicitações por Empreendimento",
    labels={"Obra Nome": "Obra", "Contagem": "Número de Solicitações"},
    barmode="stack",  # Empilhar barras em vez de sobrepor
    text="Contagem",  # Adiciona o texto com o número dentro da barra
    color_discrete_map={  
        "Fora de Garantia": "red",  
        "Assistência Técnica": "orange"  
    }
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

# Indicador: MTBF - Tempo Médio Entre Falhas
# Dividindo o layout em duas colunas
col_mtbf, col_mttr = st.columns(2)

# Coluna 1: MTBF
with col_mtbf:
    st.write("### MTBF - Tempo Médio entre Falhas")

    # Agrupar os dados pelo Sistema Construtivo Nome
    mtbf_data = []

    # Filtro para selecionar o sistema específico
    sistemas_options = [
        "Sistemas hidráulicos",
        "Sistema de prevenção e combate a incêndio",
        "Sistemas Elétricos",
        "Sistema de SPDA",
        "Sistemas de automação",
        "Sistemas de comunicação interna e externa",
        "Sistemas de exaustão, pressurização e ventilação",
        "Sistemas de transporte vertical e horizontal"
    ]

    for sistema in sistemas_options:
        # Filtrando os dados para cada sistema
        df_filtered_mtbf = filtered_df[filtered_df["Sistema Construtivo Nome"] == sistema]

        if not df_filtered_mtbf.empty:
            # Verificar se há mais de uma solicitação para o sistema filtrado
            if len(df_filtered_mtbf) > 1:
                # Calculando a soma das horas de funcionamento em bom estado
                primeira_solicitacao = pd.to_datetime(df_filtered_mtbf["Solicitação Abertura"]).min()
                ultima_solicitacao = pd.to_datetime(df_filtered_mtbf["Solicitação Abertura"]).max()
                horas_bom_funcionamento = (ultima_solicitacao - primeira_solicitacao).total_seconds() / 3600
            else:
                # Se há apenas uma ocorrência, usar a diferença entre a data da solicitação e a data CVCO
                data_solicitacao = pd.to_datetime(df_filtered_mtbf["Solicitação Abertura"]).iloc[0]
                data_cvco = pd.to_datetime(df_filtered_mtbf["Data CVCO"], format="%d/%m/%Y").iloc[0]
                horas_bom_funcionamento = (data_solicitacao - data_cvco).total_seconds() / 3600

            # Contando o número de paradas/de solicitações
            numero_de_paradas = len(df_filtered_mtbf)

            # Calculando o MTBF
            mtbf = horas_bom_funcionamento / numero_de_paradas

            # Adicionando o resultado na lista
            mtbf_data.append({'Sistema': sistema, 'MTBF': mtbf})
        else:
            # Caso não haja dados para o sistema, adicionar um valor nulo
            mtbf_data.append({'Sistema': sistema, 'MTBF': 0})

    # Criando um DataFrame com os dados calculados
    mtbf_df = pd.DataFrame(mtbf_data)

    # Gerando o gráfico de barras com Plotly
    fig = px.bar(
        mtbf_df,
        x="Sistema",
        y="MTBF",
        labels={"MTBF": "Tempo Médio Entre Falhas (horas)"},
        color="Sistema",  # Cor aleatória por sistema
        color_discrete_sequence=px.colors.sequential.Oranges  # Paleta de cores laranja
    )

    # Adicionar rótulos de dados nas colunas
    fig.update_traces(texttemplate='%{y:.2f} horas', textposition='outside')

    # Personalizar o gráfico
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="MTBF (horas)",
        xaxis_tickangle=-45,  # Rotaciona os rótulos do eixo X
        showlegend=False  # Remover a legenda do gráfico
    )

    # Exibir o gráfico
    st.plotly_chart(fig)

# Coluna 2: MTTR
with col_mttr:
    st.write("### MTTR - Tempo Médio entre Reparos")

    # Garantir que as colunas de datas estejam no formato datetime
    df["Data CVCO"] = pd.to_datetime(df["Data CVCO"], errors="coerce")
    df["Solicitação Abertura"] = pd.to_datetime(df["Solicitação Abertura"], errors="coerce")
    df["Solicitação Encerramento"] = pd.to_datetime(df["Solicitação Encerramento"], errors="coerce")

    # Lista para armazenar os resultados do MTTR
    mttr_data = []

    for sistema in sistemas_options:
        # Filtrando os dados para cada sistema
        df_filtered_mttr = df[df["Sistema Construtivo Nome"] == sistema]

        # Contagem de solicitações para o sistema filtrado
        num_solicitacoes_mttr = df_filtered_mttr.shape[0]

        if num_solicitacoes_mttr > 1:
            # Mais de uma solicitação
            somatorio_tempo_reparo = (
                df_filtered_mttr["Solicitação Encerramento"].max()
                - df_filtered_mttr["Solicitação Abertura"].min()
            ).total_seconds() / 3600  # Converter para horas
        elif num_solicitacoes_mttr == 1:
            # Apenas uma solicitação
            unica_solicitacao = df_filtered_mttr.iloc[0]
            somatorio_tempo_reparo = (
                unica_solicitacao["Solicitação Encerramento"]
                - unica_solicitacao["Data CVCO"]
            ).total_seconds() / 3600  # Converter para horas
        else:
            # Sem solicitações para o sistema
            somatorio_tempo_reparo = 0

        # Calcular o MTTR
        mttr = somatorio_tempo_reparo / num_solicitacoes_mttr if num_solicitacoes_mttr > 0 else 0

        # Adicionar os resultados à lista
        mttr_data.append({"Sistema": sistema, "MTTR": mttr})

    # Criando um DataFrame com os dados calculados
    mttr_df = pd.DataFrame(mttr_data)

    # Gerando o gráfico de barras com Plotly
    fig = px.bar(
        mttr_df,
        x="Sistema",
        y="MTTR",
        labels={"MTTR": "Tempo Médio Entre Reparos (horas)"},
        color="Sistema",  # Cor aleatória por sistema
        color_discrete_sequence=px.colors.sequential.Oranges  # Paleta de cores correta
    )

    # Adicionar rótulos de dados nas colunas
    fig.update_traces(texttemplate='%{y:.2f} horas', textposition='outside')

    # Personalizar o gráfico
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="MTTR (horas)",
        xaxis_tickangle=-45,
        showlegend=False  # Rotaciona os rótulos do eixo X
    )

    # Exibir o gráfico
    st.plotly_chart(fig)

st.markdown('''_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _''')

# Adicionar filtros de ano, responsável, situação procedência e sistema construtivo
tabela_filtros = st.columns(4)

with tabela_filtros[0]:
    anos_disponiveis = sorted(df["Solicitação Encerramento"].dropna().dt.year.unique())
    ano_selecionado = st.multiselect("Filtrar por Ano de Encerramento", anos_disponiveis, default=[])

with tabela_filtros[1]:
    responsaveis_disponiveis = sorted(df["Responsável"].dropna().unique())
    responsavel_selecionado = st.multiselect("Filtrar por Responsável", responsaveis_disponiveis, default=[])

with tabela_filtros[2]:
    situacoes_disponiveis = sorted(df["Solicitação Procedência"].dropna().unique())
    situacao_selecionada = st.multiselect("Filtrar por Solicitação Procedência", situacoes_disponiveis, default=[])

with tabela_filtros[3]:
    sistemas_disponiveis = sorted(df["Sistema Construtivo Nome"].dropna().unique())
    sistema_selecionado = st.multiselect("Filtrar por Sistema Construtivo", sistemas_disponiveis, default=[])

# Filtrar o DataFrame pelos filtros selecionados, se houver seleção
df_mttc = df.dropna(subset=["Solicitação Abertura", "Solicitação Encerramento"])
if ano_selecionado:
    df_mttc = df_mttc[df_mttc["Solicitação Encerramento"].dt.year.isin(ano_selecionado)]
if responsavel_selecionado:
    df_mttc = df_mttc[df_mttc["Responsável"].isin(responsavel_selecionado)]
if situacao_selecionada:
    df_mttc = df_mttc[df_mttc["Solicitação Procedência"].isin(situacao_selecionada)]
if sistema_selecionado:
    df_mttc = df_mttc[df_mttc["Sistema Construtivo Nome"].isin(sistema_selecionado)]

# Filtrar apenas as solicitações com "Solicitação Situação" igual a "Encerrada"
df_mttc = df_mttc[df_mttc["Solicitação Situação"] == "Encerrada"]

# Calcular o MTTC para todas as obras
mttc_geral = (df_mttc["Solicitação Encerramento"] - df_mttc["Solicitação Abertura"]).dt.days.mean()

# Exibir o MTTC para todas as obras
st.write('### MTTC - Tempo Médio de Conclusão (Por Obra)')
st.metric("Tempo Médio para Conclusão", f"{mttc_geral:.2f} dias")

# Calcular o MTTC por obra
mttc_por_obra = df_mttc.groupby("Obra Nome").apply(
    lambda x: (x["Solicitação Encerramento"] - x["Solicitação Abertura"]).dt.days.mean()
).reset_index(name="MTTC")

# Gerar o gráfico de barras com Plotly
fig = px.bar(
    mttc_por_obra,
    x="Obra Nome",
    y="MTTC",
    labels={"MTTC": "Tempo Médio para Conclusão (dias)"},
    color="Obra Nome",  # Cor aleatória por obra
    color_discrete_sequence=px.colors.qualitative.Pastel1  # Define uma paleta de cores
)

# Adicionar rótulo de dados nas colunas
fig.update_traces(texttemplate='%{y:.2f} dias', textposition='outside')

# Remover a legenda do eixo X
fig.update_layout(xaxis_title="", showlegend=False)

# Exibir o gráfico
st.plotly_chart(fig)
st.dataframe(df_mttc, use_container_width=True)  # Habilitar para visualizar a tabela do arquivo Excel.
