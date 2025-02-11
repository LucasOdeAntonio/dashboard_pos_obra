import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# =============================================================================
# Função para normalizar os nomes das colunas (remove espaços extras)
# =============================================================================
def normalize_columns(df):
    """
    Remove espaços em branco no início/fim e substitui múltiplos espaços internos por um único espaço.
    """
    df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
    return df

# =============================================================================
# Função para processar a aba calendariodechuvas (formato wide para long)
# =============================================================================
def process_calendario_de_chuvas(df):
    """
    Transforma o DataFrame de calendariodechuvas, que está em formato wide,
    para um formato long com as colunas: "ANO", "Mes", "Chuva" e "AnoMes".
    """
    month_columns = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
    df_long = pd.melt(df, id_vars=["ANO"], value_vars=month_columns, var_name="Mes", value_name="Chuva")
    
    # Substituir vírgula por ponto e traços por NaN e converter para numérico
    df_long["Chuva"] = (
        df_long["Chuva"]
        .astype(str)
        .str.replace(",", ".")
        .replace("-", np.nan)
    )
    df_long["Chuva"] = pd.to_numeric(df_long["Chuva"], errors="coerce")
    
    # Mapeia as abreviações dos meses para números com 2 dígitos
    month_map = {
        "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04", "MAI": "05", "JUN": "06",
        "JUL": "07", "AGO": "08", "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12"
    }
    df_long["AnoMes"] = df_long["ANO"].astype(str) + "-" + df_long["Mes"].map(month_map)
    
    return df_long

# =============================================================================
# Função de carregamento e pré-processamento dos dados
# =============================================================================
@st.cache_data
def load_and_preprocess_data(filepath):
    # Aba "engenharia"
    df_eng = pd.read_excel(filepath, sheet_name="engenharia")
    df_eng = normalize_columns(df_eng)
    df_eng["Data de Abertura"] = pd.to_datetime(df_eng["Data de Abertura"], format="%d/%m/%Y", errors="coerce")
    df_eng["Encerramento"] = pd.to_datetime(df_eng["Encerramento"], format="%d/%m/%Y", errors="coerce")
    
    # Aba "departamento"
    df_dep = pd.read_excel(filepath, sheet_name="departamento")
    df_dep = normalize_columns(df_dep)
    if "Data CVCO" in df_dep.columns:
        df_dep["Data CVCO"] = pd.to_datetime(df_dep["Data CVCO"], format="%d/%m/%Y", errors="coerce")
    if "Data Entrega de Obra" in df_dep.columns:
        df_dep["Data Entrega de Obra"] = pd.to_datetime(df_dep["Data Entrega de Obra"], format="%d/%m/%Y", errors="coerce")
    
    # Aba "calendariodechuvas"
    df_chuva = pd.read_excel(filepath, sheet_name="calendariodechuvas")
    df_chuva = normalize_columns(df_chuva)
    # Se estiver no formato wide (com a coluna "ANO"), processa para formato long:
    if "ANO" in df_chuva.columns:
        df_chuva = process_calendario_de_chuvas(df_chuva)
    else:
        st.warning("A aba 'calendariodechuvas' não está no formato esperado.")
    
    return df_eng, df_dep, df_chuva

# =============================================================================
# Configuração do Layout e Cabeçalho
# =============================================================================
st.set_page_config(
    page_icon="Home.jpg",
    layout='wide',
    page_title="Painel Assistência Técnica"
)

# Exibição dos logos (utilizando use_container_width, pois use_column_width está depreciado)
logo_horizontal='LOGO_VR.png'
logo_reduzida="LOGO_VR_REDUZIDA.png"
st.logo(image=logo_horizontal, size="large",icon_image=logo_reduzida)

st.markdown('<h1 style="color: orange;">PAINEL DE ASSISTÊNCIA TÉCNICA 💥</h1>', unsafe_allow_html=True)
st.markdown('Acompanhamento de Solicitações de Assistência Técnica')

# =============================================================================
# Carregamento dos dados
# =============================================================================
file_path = "base2025.xlsx"
df_eng, df_dep, df_chuva = load_and_preprocess_data(file_path)

# =============================================================================
# Tratamento da coluna “Garantia Solicitada”
# =============================================================================
def tratamento_garantia(garantia):
    if pd.isna(garantia):
        return pd.Series([np.nan, np.nan])
    # Substitui " - " por ": "
    garantia = garantia.replace(" - ", ": ")
    if ":" in garantia:
        sistema, tipo = garantia.split(":", 1)
        return pd.Series([sistema.strip(), tipo.strip()])
    else:
        return pd.Series([garantia.strip(), np.nan])

# Cria as novas colunas "Sistema Construtivo" e "Tipo de Falha"
df_eng[["Sistema Construtivo", "Tipo de Falha"]] = df_eng["Garantia Solicitada"].apply(tratamento_garantia)

# =============================================================================
# Cálculos de Tempo e Métricas (antes dos filtros)
# =============================================================================
df_eng["Tempo de Encerramento"] = (df_eng["Encerramento"] - df_eng["Data de Abertura"]).dt.days
hoje = pd.to_datetime(date.today())
df_eng["Dias em Aberto"] = np.where(
    df_eng["Encerramento"].isna(),
    (hoje - df_eng["Data de Abertura"]).dt.days,
    df_eng["Tempo de Encerramento"]
)
total_solicitacoes = df_eng["N°"].count()
df_concluidas = df_eng[df_eng["Encerramento"].notna()]
if not df_concluidas.empty:
    mttc = df_concluidas["Tempo de Encerramento"].sum() / df_concluidas.shape[0]
else:
    mttc = np.nan

# =============================================================================
# Integração com a aba "departamento"
# =============================================================================
def get_column(df, expected):
    expected_normalized = expected.replace(" ", "").lower()
    for col in df.columns:
        if col.replace(" ", "").lower() == expected_normalized:
            return col
    return None

expected_cols = ["Empreendimento", "Data CVCO", "Data Entrega de Obra", "N° Unidades", "Status"]
mapping = {}
for expected in expected_cols:
    found = get_column(df_dep, expected)
    if found is None:
        st.error(f"Coluna '{expected}' não encontrada na aba 'departamento'. Colunas disponíveis: {df_dep.columns.tolist()}")
        st.stop()
    else:
        mapping[expected] = found

df_dep_renamed = df_dep.rename(columns={
    mapping["Empreendimento"]: "Empreendimento",
    mapping["Data CVCO"]: "Data CVCO",
    mapping["Data Entrega de Obra"]: "Data Entrega de Obra",
    mapping["N° Unidades"]: "N° Unidades",
    mapping["Status"]: "Status"
})

# Se o df_eng já possui "Status", a do departamento ficará com o sufixo _dep.
df_eng = df_eng.merge(
    df_dep_renamed[["Empreendimento", "Data CVCO", "Data Entrega de Obra", "N° Unidades", "Status"]],
    on="Empreendimento",
    how="left",
    suffixes=("", "_dep")
)

def compute_mtbf(group):
    if group["Data CVCO"].isnull().all():
        return np.nan
    max_data_abertura = group["Data de Abertura"].max()
    min_data_cvco = group["Data CVCO"].min()
    op_hours = (max_data_abertura - min_data_cvco).total_seconds() / 3600
    return op_hours / group.shape[0]

mtbf_series = df_eng.groupby("Garantia Solicitada").apply(compute_mtbf)

def compute_mttr(group):
    closed = group[group["Encerramento"].notna()]
    if closed.empty:
        return np.nan
    total_hours = closed["Tempo de Encerramento"].sum() * 24
    return total_hours / closed.shape[0]

mttr_series = df_eng.groupby("Garantia Solicitada").apply(compute_mttr)
disponibilidade_series = (mtbf_series / (mtbf_series + mttr_series)) * 100

# =============================================================================
# Painel Administrativo – Filtros (integrados ao painel, default vazio)
# =============================================================================
with st.expander("Filtros", expanded=True):
    # Primeira linha: 5 colunas
    col_ano, col_mes, col_chamado, col_resp, col_fcr = st.columns(5)
    anos = sorted(df_eng["Data de Abertura"].dropna().dt.year.unique().tolist())
    selected_anos = col_ano.multiselect("Filtro por Ano", options=anos, default=[])
    
    month_options = list(range(1, 13))
    month_names = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio",
                   6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro",
                   11: "Novembro", 12: "Dezembro"}
    selected_meses = col_mes.multiselect("Filtro por Mês", options=month_options, default=[], 
                                         format_func=lambda x: month_names[x])
    
    chamados = df_eng["N°"].dropna().unique().tolist()
    selected_chamados = col_chamado.multiselect("N° do Chamado", options=chamados, default=[])
    
    responsaveis = df_eng["Responsável"].dropna().unique().tolist()
    selected_responsaveis = col_resp.multiselect("Responsável", options=responsaveis, default=[])
    
    if "FCR" in df_eng.columns:
        fcr_values = df_eng["FCR"].dropna().unique().tolist()
        selected_fcr = col_fcr.multiselect("FCR", options=fcr_values, default=[])
    else:
        selected_fcr = []
    
    # Segunda linha: 4 colunas
    col_empre, col_unidade, col_bloco, col_status = st.columns(4)
    empreendimentos = df_eng["Empreendimento"].dropna().unique().tolist()
    selected_empre = col_empre.multiselect("Empreendimento", options=empreendimentos, default=[])
    
    unidades = df_eng["Unidade"].dropna().unique().tolist()
    selected_unidade = col_unidade.multiselect("Unidade", options=unidades, default=[])
    
    blocos = df_eng["Bloco"].dropna().unique().tolist()
    selected_bloco = col_bloco.multiselect("Bloco", options=blocos, default=[])
    
    statuses = df_eng["Status"].dropna().unique().tolist()
    selected_status = col_status.multiselect("Status", options=statuses, default=[])
    
    # Terceira linha: 3 colunas
    col_garantia, col_sistema, col_tipo = st.columns(3)
    garantias = df_eng["Garantia Solicitada"].dropna().unique().tolist()
    selected_garantia = col_garantia.multiselect("Garantia Solicitada", options=garantias, default=[])
    
    sistemas = df_eng["Sistema Construtivo"].dropna().unique().tolist()
    selected_sistema = col_sistema.multiselect("Sistema Construtivo", options=sistemas, default=[])
    
    tipos = df_eng["Tipo de Falha"].dropna().unique().tolist()
    selected_tipo = col_tipo.multiselect("Tipo de Falha", options=tipos, default=[])

# =============================================================================
# Aplicação dos filtros (usando .isin para cada coluna)
# =============================================================================
df_filtered = df_eng.copy()
if selected_anos:
    df_filtered = df_filtered[df_filtered["Data de Abertura"].dt.year.isin(selected_anos)]
if selected_meses:
    df_filtered = df_filtered[df_filtered["Data de Abertura"].dt.month.isin(selected_meses)]
if selected_chamados:
    df_filtered = df_filtered[df_filtered["N°"].astype(str).isin([str(x) for x in selected_chamados])]
if selected_responsaveis:
    df_filtered = df_filtered[df_filtered["Responsável"].isin(selected_responsaveis)]
if selected_fcr:
    df_filtered = df_filtered[df_filtered["FCR"].isin(selected_fcr)]
if selected_empre:
    df_filtered = df_filtered[df_filtered["Empreendimento"].isin(selected_empre)]
if selected_unidade:
    df_filtered = df_filtered[df_filtered["Unidade"].isin(selected_unidade)]
if selected_bloco:
    df_filtered = df_filtered[df_filtered["Bloco"].isin(selected_bloco)]
if selected_status:
    df_filtered = df_filtered[df_filtered["Status"].isin(selected_status)]
if selected_garantia:
    df_filtered = df_filtered[df_filtered["Garantia Solicitada"].isin(selected_garantia)]
if selected_sistema:
    df_filtered = df_filtered[df_filtered["Sistema Construtivo"].isin(selected_sistema)]
if selected_tipo:
    df_filtered = df_filtered[df_filtered["Tipo de Falha"].isin(selected_tipo)]

# =============================================================================
# Re-cálculo das Métricas (baseado nos dados filtrados)
# =============================================================================
metrica_1 = df_filtered[(df_filtered["Dias em Aberto"] >= 0) & (df_filtered["Dias em Aberto"] <= 15)].shape[0]
metrica_2 = df_filtered[(df_filtered["Dias em Aberto"] > 15) & (df_filtered["Dias em Aberto"] <= 30)].shape[0]
metrica_3 = df_filtered[(df_filtered["Dias em Aberto"] > 30) & (df_filtered["Dias em Aberto"] <= 45)].shape[0]
metrica_4 = df_filtered[(df_filtered["Dias em Aberto"] > 45) & (df_filtered["Dias em Aberto"] <= 60)].shape[0]
metrica_5 = df_filtered[df_filtered["Dias em Aberto"] > 60].shape[0]
metrica_6 = df_filtered["N°"].count()

st.markdown("---")

# =============================================================================
# Exibição das Métricas e Detalhamento
# =============================================================================
st.markdown('### Acompanhamento das Solicitações')
with st.container():
    col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
    col_m1.metric("Solicitações entre 0-15 dias", metrica_1)
    col_m2.metric("Solicitações entre 15-30 dias", metrica_2)
    col_m3.metric("Solicitações entre 30-45 dias", metrica_3)
    col_m4.metric("Solicitações entre 45-60 dias", metrica_4)
    col_m5.metric("Solicitações >60 dias", metrica_5)
    col_m6.metric("Total Solicitações", metrica_6)

with st.container():
    col_cb1, col_cb2, col_cb3, col_cb4, col_cb5, col_cb6 = st.columns(6)
    show_m1 = col_cb1.checkbox("Exibir Solicitações 0-15")
    show_m2 = col_cb2.checkbox("Exibir Solicitações 15-30")
    show_m3 = col_cb3.checkbox("Exibir Solicitações 30-45")
    show_m4 = col_cb4.checkbox("Exibir Solicitações 45-60")
    show_m5 = col_cb5.checkbox("Exibir Solicitações >60")

if show_m1:
    st.write("Dados Métrica 1 (0-15 dias)",
             df_filtered[(df_filtered["Dias em Aberto"] >= 0) & (df_filtered["Dias em Aberto"] <= 15)])
if show_m2:
    st.write("Dados Métrica 2 (15-30 dias)",
             df_filtered[(df_filtered["Dias em Aberto"] > 15) & (df_filtered["Dias em Aberto"] <= 30)])
if show_m3:
    st.write("Dados Métrica 3 (30-45 dias)",
             df_filtered[(df_filtered["Dias em Aberto"] > 30) & (df_filtered["Dias em Aberto"] <= 45)])
if show_m4:
    st.write("Dados Métrica 4 (45-60 dias)",
             df_filtered[(df_filtered["Dias em Aberto"] > 45) & (df_filtered["Dias em Aberto"] <= 60)])
if show_m5:
    st.write("Dados Métrica 5 (>60 dias)", df_filtered[df_filtered["Dias em Aberto"] > 60])

st.markdown("---")

# =============================================================================
# Gráficos e Análises (um abaixo do outro)
# =============================================================================

# 1 – Gráfico de Solicitações ao Longo do Tempo (Anos e Meses)
st.markdown('### 🏗️Solicitações de Assistência Técnica')
df_filtered["AnoMes"] = df_filtered["Data de Abertura"].dt.to_period("M").astype(str)
df_chart2 = df_filtered.groupby("AnoMes").size().reset_index(name="Count")
fig1 = px.bar(
    df_chart2,
    x="AnoMes",
    y="Count",
    barmode="stack",
    text="Count",
    color_discrete_sequence=["#FFCC99"],  # Laranja claro
    labels={"AnoMes": "", "Count": ""},  # Remove nomes dos eixos
)

fig1.update_traces(
    marker_line_color="#FF9933",  # Laranja mais escuro para a borda
    marker_line_width=1.5         # Largura da borda
)

# Remove as linhas horizontais e os números do eixo Y
fig1.update_layout(
    yaxis=dict(
        showgrid=False,  # Remove as linhas horizontais
        showticklabels=False  # Remove os números do eixo Y
    )
)

st.plotly_chart(fig1, use_container_width=True)
st.markdown("---")

# 2 - Gráfico de Pirâmide (por ano)
# Extraímos o ano da "Data Abertura" e agrupamos para obter a contagem
df_pyramid = df_filtered.copy()
df_pyramid["Ano"] = df_pyramid["Data de Abertura"].dt.year
df_pyramid_grouped = df_pyramid.groupby("Ano").size().reset_index(name="Count")
df_pyramid_grouped = df_pyramid_grouped.sort_values("Ano", ascending=True)

# Criação do gráfico de barras horizontais (pirâmide)
fig2 = px.bar(
    df_pyramid_grouped,
    x="Count",
    y="Ano",
    orientation="h",
    text="Count",
    color_discrete_sequence=["#FFCC99"],  # Laranja claro
    labels={"Count": "", "Ano": ""},  # Remove nomes dos eixos
)
fig2.update_traces(
    marker_line_color="#FF9933",  # Laranja escuro para a borda
    marker_line_width=1.5,
    textposition="inside"
)

# Ajustando o eixo Y para exibir apenas números inteiros
fig2.update_yaxes(
    autorange="reversed",  # Mantém a ordem decrescente dos anos
    tickmode="linear",  # Define a escala como linear
    dtick=1,  # Define os intervalos do eixo Y como 1 (apenas inteiros)
    tickformat="d"  # Garante que os valores sejam exibidos como inteiros
)

fig2.update_layout(
    height=300,  # Define a altura do gráfico para 300 pixels
    yaxis=dict(
        showgrid=False,  # Remove as linhas horizontais
        showticklabels=True,  # Remove os números do eixo Y
    ),
    xaxis=dict(
        showticklabels=False # Remove os números do eixo X
    )
)

# 3 - Gráfico de Solicitações por Empreendimento
# Agrupamos por "Empreendimento"
df_empreendimento = df_filtered.groupby("Empreendimento").size().reset_index(name="Count")
fig3 = px.bar(
    df_empreendimento,
    x="Empreendimento",
    y="Count",
    text="Count",
    color_discrete_sequence=["#FFCC99"],
    labels={"Empreendimento": "", "Count": ""},  # Remove nomes dos eixos
)
fig3.update_traces(
    marker_line_color="#FF9933",
    marker_line_width=1.5,
    textposition="inside"
)

# Remove as linhas horizontais e os números do eixo Y
fig3.update_layout(
    yaxis=dict(
        showgrid=False,  # Remove as linhas horizontais
        showticklabels=False,  # Remove os números do eixo Y
    )
)

# 4 - Gráfico de Rosca para Status (Improcedente vs Concluída)
# Filtramos os status de interesse e agrupamos
df_status_pie = df_filtered[df_filtered["Status"].isin(["Improcedente", "Concluída"])] \
    .groupby("Status").size().reset_index(name="Count")

# Definindo as cores para cada status
pie_colors = []
pie_line_colors = []
for status in df_status_pie["Status"]:
    if status == "Improcedente":
        pie_colors.append("#D3D3D3")   # Cinza claro
        pie_line_colors.append("#A9A9A9")  # Cinza escuro
    elif status == "Concluída":
        pie_colors.append("#FFCC99")  # Laranja claro
        pie_line_colors.append("#FF9933")  # Laranja escuro

fig4 = px.pie(
    df_status_pie,
    names="Status",
    values="Count",
    hole=0.4
)
fig4.update_traces(
    textposition='inside',
    textinfo='percent+label',
    marker=dict(
        colors=pie_colors,
        line=dict(color=pie_line_colors, width=1.5)
    )
)

fig4.update_layout(
    showlegend=False,  # Remove a legenda
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=10, r=10, t=30, b=10),
    font=dict(size=12)
)

# 5 - Gráfico de Barras Horizontais para Status
# Consideramos os status de interesse
statuses_interested = ["Improcedente", "Concluída", "Em andamento", "Nova"]
df_status_bar = df_filtered[df_filtered["Status"].isin(statuses_interested)] \
    .groupby("Status").size().reset_index(name="Count")

# Mapeamento de cores para cada status
color_map = {
    "Improcedente": {"fill": "#D3D3D3", "border": "#A9A9A9"},
    "Concluída": {"fill": "#FFCC99", "border": "#FF9933"},
    "Em andamento": {"fill": "#ADD8E6", "border": "#00008B"},  # Azul claro e azul escuro
    "Nova": {"fill": "#90EE90", "border": "#006400"}            # Verde claro e verde escuro
}

fig5 = go.Figure()
for _, row in df_status_bar.iterrows():
    status = row["Status"]
    count = row["Count"]
    fig5.add_trace(go.Bar(
         x=[count],
         y=[status],
         orientation='h',
         marker=dict(
             color=color_map[status]["fill"],
             line=dict(color=color_map[status]["border"], width=1.5)
         ),
         text=[count],
         textposition='inside',
         name=status
    ))
# Opcional: remover a legenda, se não for necessária
fig5.update_layout(showlegend=False)
fig5.update_layout(
    xaxis=dict(
        showgrid=False,      # Remove as linhas do grid
        showticklabels=False  # Remove os números do eixo X
    )
)

### Layout em Container com 4 Colunas (proporções 1,3,1,2)
with st.container():
    # Primeira linha: Pirâmide (fig1) e Empreendimentos (fig2)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('### 🟰 Total de Solicitações')
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        st.markdown('### 🏙️ Solicitações Por Empreendimento')
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # Segunda linha: Rosca (fig3) e Barras Horizontais de Status (fig4)
    col3, col4 = st.columns(2)
    with col3:
        st.markdown('### 🗂️ Situação das Solicitações')
        st.plotly_chart(fig4, use_container_width=True)
    with col4:
        st.markdown('### 📂 Status das Solicitações')
        st.plotly_chart(fig5, use_container_width=True)

    st.markdown("---")

# 6 – Gráfico Combinado: Solicitações + Acumulado de Chuva
st.markdown("### 🧮 Solicitações ❌ Acumulado de Chuva ⛈️")
df_bar = df_filtered.groupby("AnoMes").size().reset_index(name="Count")
df_combo = pd.merge(df_bar, df_chuva, on="AnoMes", how="left")

# Criar o gráfico de barras com cores ajustadas
fig6 = px.bar(
    df_combo,
    x="AnoMes",
    y="Count",
    barmode="stack",
    text="Count",
    color_discrete_sequence=["#D3D3D3"],  # Cinza claro
    labels={"AnoMes": "", "Count": ""},  # Remove nomes dos eixos
)

fig6.update_traces(
    marker_line_color="#808080",  # Cinza escuro para bordas
    marker_line_width=1.5,
    textposition="inside"
)

# Adicionar a linha com cor ajustada e rótulos de dados
fig6.add_scatter(
    x=df_combo["AnoMes"],
    y=df_combo["Chuva"],
    mode="lines+markers+text",
    name="Acumulado de Chuva",
    line=dict(color="#D55E00", width=2),  # Laranja escuro
    marker=dict(color="#D55E00", size=6),
    text=df_combo["Chuva"],  # Rótulos de dados
    textposition="top center"
)

# Remover grid, labels e valores do eixo Y
fig6.update_layout(
    yaxis=dict(
        showgrid=False,
        showticklabels=False  # Remove valores do eixo Y
    ),
    xaxis=dict(
        showgrid=False
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False,  # Remove a legenda
    margin=dict(l=10, r=10, t=30, b=30)
)

st.plotly_chart(fig6, use_container_width=True)
st.markdown("---")

# 7 – MTTC – Tempo Médio de Conclusão (Por Obra)
st.write("### MTTC - Tempo Médio de Conclusão (Por Obra)")
st.metric("MTTC Geral", f"{mttc:.2f} dias")

# Calcular o MTTC por empreendimento
mttc_por_obra = df_filtered[df_filtered["Encerramento"].notna()] \
    .groupby("Empreendimento")["Tempo de Encerramento"].mean() \
    .reset_index(name="MTTC")

# Criar esquema de cores pastel
cores_principais = px.colors.qualitative.Pastel1  

# Definir bordas um pouco mais escuras para as colunas
bordas_escurecidas = ["#D4A373", "#A3C4BC", "#9A8C98", "#E9C46A", "#F4A261", "#E76F51", 
                      "#6D6875", "#4A4E69", "#9B5DE5", "#E63946"]  

# Criar gráfico
fig_mttc = px.bar(
    mttc_por_obra,
    x="Empreendimento",
    y="MTTC",
    color="Empreendimento",
    color_discrete_sequence=cores_principais,
    text=mttc_por_obra["MTTC"].apply(lambda x: f"{x:.2f}")  # Rótulo com 2 casas decimais
)

# Aplicar bordas escuras manualmente
for trace, border_color in zip(fig_mttc.data, bordas_escurecidas):
    trace.marker.line.width = 1.5
    trace.marker.line.color = border_color

# Ajustar layout para remover grid, labels e posicionar a legenda à direita
fig_mttc.update_layout(
    xaxis=dict(
        showgrid=False,  
        showticklabels=False,  # Remover labels do eixo X
        title=""  # Remover título do eixo X
    ),
    yaxis=dict(
        showgrid=False,  
        showticklabels=False,  # Remover números do eixo Y
        title=""  # Remover título do eixo Y
    ),
    legend=dict(
        orientation="v",  # Mantém a legenda vertical
        x=1.02,  # Move para a direita
        y=1, 
        title=None  # Remove o título "Empreendimento" da legenda
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=10, r=200, t=30, b=10),  # Ajuste para acomodar a legenda na direita
)

st.plotly_chart(fig_mttc, use_container_width=True)
