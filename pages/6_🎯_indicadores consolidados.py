import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
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
    
    # Substituir vírgula por ponto e traços por NaN, e converter a coluna "Chuva" para numérico
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
    page_title="Departamento de Pós Obra",
    page_icon="Home.jpg",
    layout="wide"
)

# Exibição dos logos (usando use_container_width, pois use_column_width está depreciado)
logo_horizontal = 'LOGO_VR.png'
logo_reduzida = 'LOGO_VR_REDUZIDA.png'
col_logo1, col_logo2 = st.columns([3, 1])
with col_logo1:
    st.image(logo_horizontal, use_container_width=True)
with col_logo2:
    st.image(logo_reduzida, width=100)

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
    
    col_empre, col_unidade, col_bloco, col_status = st.columns(4)
    empreendimentos = df_eng["Empreendimento"].dropna().unique().tolist()
    selected_empre = col_empre.multiselect("Empreendimento", options=empreendimentos, default=[])
    
    unidades = df_eng["Unidade"].dropna().unique().tolist()
    selected_unidade = col_unidade.multiselect("Unidade", options=unidades, default=[])
    
    blocos = df_eng["Bloco"].dropna().unique().tolist()
    selected_bloco = col_bloco.multiselect("Bloco", options=blocos, default=[])
    
    statuses = df_eng["Status"].dropna().unique().tolist()
    selected_status = col_status.multiselect("Status", options=statuses, default=[])
    
    col_garantia, col_sistema, col_tipo = st.columns(3)
    garantias = df_eng["Garantia Solicitada"].dropna().unique().tolist()
    selected_garantia = col_garantia.multiselect("Garantia Solicitada", options=garantias, default=[])
    
    sistemas = df_eng["Sistema Construtivo"].dropna().unique().tolist()
    selected_sistema = col_sistema.multiselect("Sistema Construtivo", options=sistemas, default=[])
    
    tipos = df_eng["Tipo de Falha"].dropna().unique().tolist()
    selected_tipo = col_tipo.multiselect("Tipo de Falha", options=tipos, default=[])

# =============================================================================
# Aplicação dos filtros
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

st.markdown('''____________________________________________________________________________________________''')

# =============================================================================
# Exibição das Métricas e Detalhamento
# =============================================================================
with st.container():
    col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
    col_m1.metric("Métrica 1 (0-15 dias)", metrica_1)
    col_m2.metric("Métrica 2 (15-30 dias)", metrica_2)
    col_m3.metric("Métrica 3 (30-45 dias)", metrica_3)
    col_m4.metric("Métrica 4 (45-60 dias)", metrica_4)
    col_m5.metric("Métrica 5 (>60 dias)", metrica_5)
    col_m6.metric("Total Solicitações", metrica_6)

with st.container():
    col_cb1, col_cb2, col_cb3, col_cb4, col_cb5, col_cb6 = st.columns(6)
    show_m1 = col_cb1.checkbox("Mostrar Métrica 1")
    show_m2 = col_cb2.checkbox("Mostrar Métrica 2")
    show_m3 = col_cb3.checkbox("Mostrar Métrica 3")
    show_m4 = col_cb4.checkbox("Mostrar Métrica 4")
    show_m5 = col_cb5.checkbox("Mostrar Métrica 5")

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

st.markdown('''____________________________________________________________________________________________''')

# =============================================================================
# Gráficos e Análises
# =============================================================================

# 1 – Gráfico de Solicitações por Empreendimento (classificação via aba departamento)
# Lógica: usar o "Status_dep" para definir a classificação
if "Status_dep" in df_filtered.columns:
    df_filtered["Classificacao"] = df_filtered["Status_dep"].apply(
        lambda x: "Assistência Técnica" if "assistência técnica" in str(x).strip().lower() else "Fora de Garantia"
    )
else:
    df_filtered["Classificacao"] = "Fora de Garantia"

color_map = {"Assistência Técnica": "orange", "Fora de Garantia": "grey"}
df_chart1 = df_filtered.groupby(["Empreendimento", "Classificacao"]).size().reset_index(name="Count")
with st.container():
    fig1 = px.bar(df_chart1, x="Empreendimento", y="Count", color="Classificacao", barmode="stack",
                  text="Count", color_discrete_map=color_map)
    st.plotly_chart(fig1, use_container_width=True)

# 2 – Gráfico de Solicitações ao Longo do Tempo (Anos e Meses)
df_filtered["AnoMes"] = df_filtered["Data de Abertura"].dt.to_period("M").astype(str)
df_chart2 = df_filtered.groupby("AnoMes").size().reset_index(name="Count")
with st.container():
    fig2 = px.bar(df_chart2, x="AnoMes", y="Count", barmode="stack", text="Count")
    st.plotly_chart(fig2, use_container_width=True)

# 3 – Gráfico Combinado e Gráfico da aba Departamento
col1, col2 = st.columns(2)
with col1:
    df_bar = df_filtered.groupby("AnoMes").size().reset_index(name="Count")
    # Merge com os dados de chuvas: df_chuva já possui a coluna "AnoMes" (criada na função process_calendario_de_chuvas)
    df_combo = pd.merge(df_bar, df_chuva, on="AnoMes", how="left")
    fig3 = px.bar(df_combo, x="AnoMes", y="Count", barmode="stack", text="Count")
    fig3.add_scatter(x=df_combo["AnoMes"], y=df_combo["Chuva"], mode="lines+markers", name="Acumulado de Chuva")
    st.plotly_chart(fig3, use_container_width=True)
with col2:
    if "Data Entrega de Obra" in df_dep_renamed.columns and "N° Unidades" in df_dep_renamed.columns:
        df_dep_renamed["Ano_Entrega"] = df_dep_renamed["Data Entrega de Obra"].dt.year
        df_chart_dep = df_dep_renamed.groupby("Ano_Entrega")["N° Unidades"].sum().reset_index()
        fig4 = px.bar(df_chart_dep, x="Ano_Entrega", y="N° Unidades", barmode="stack", text="N° Unidades")
        st.plotly_chart(fig4, use_container_width=True)

st.markdown('''____________________________________________________________________________________________''')

# 4 – Gráficos para Sistema Construtivo e Tipo de Falha
col_sys, col_falha = st.columns(2)
with col_sys:
    df_sys = df_filtered.groupby("Sistema Construtivo").size().reset_index(name="Count")
    fig_sys = px.bar(df_sys, x="Sistema Construtivo", y="Count", barmode="stack", text="Count")
    st.plotly_chart(fig_sys, use_container_width=True)
with col_falha:
    df_falha = df_filtered.groupby("Tipo de Falha").size().reset_index(name="Count")
    fig_falha = px.bar(df_falha, x="Tipo de Falha", y="Count", barmode="stack", text="Count")
    st.plotly_chart(fig_falha, use_container_width=True)

# 5 – Gráficos Empilhados por Empreendimento
col_emp_sys, col_emp_falha = st.columns(2)
with col_emp_sys:
    df_emp_sys = df_filtered.groupby(["Empreendimento", "Sistema Construtivo"]).size().reset_index(name="Count")
    fig_emp_sys = px.bar(df_emp_sys, x="Empreendimento", y="Count", color="Sistema Construtivo", barmode="stack", text="Count")
    st.plotly_chart(fig_emp_sys, use_container_width=True)
with col_emp_falha:
    df_emp_falha = df_filtered.groupby(["Empreendimento", "Tipo de Falha"]).size().reset_index(name="Count")
    fig_emp_falha = px.bar(df_emp_falha, x="Empreendimento", y="Count", color="Tipo de Falha", barmode="stack", text="Count")
    st.plotly_chart(fig_emp_falha, use_container_width=True)

st.markdown('''____________________________________________________________________________________________''')

# 6 – Gráficos de MTBF por Sistema Construtivo e Tipo de Falha
def compute_mtbf_group(group):
    if group["Data CVCO"].isnull().all():
        return np.nan
    max_data = group["Data de Abertura"].max()
    min_cvco = group["Data CVCO"].min()
    op_hours = (max_data - min_cvco).total_seconds() / 3600
    return op_hours / group.shape[0]

mtbf_sys = df_filtered.groupby("Sistema Construtivo").apply(compute_mtbf_group).reset_index(name="MTBF")
mtbf_falha = df_filtered.groupby("Tipo de Falha").apply(compute_mtbf_group).reset_index(name="MTBF")
col_mtbf_sys, col_mtbf_falha = st.columns(2)
with col_mtbf_sys:
    fig_mtbf_sys = px.bar(mtbf_sys, x="Sistema Construtivo", y="MTBF", text="MTBF")
    st.plotly_chart(fig_mtbf_sys, use_container_width=True)
with col_mtbf_falha:
    fig_mtbf_falha = px.bar(mtbf_falha, x="Tipo de Falha", y="MTBF", text="MTBF")
    st.plotly_chart(fig_mtbf_falha, use_container_width=True)

# 7 – Gráficos de MTTR por Sistema Construtivo e Tipo de Falha
def compute_mttr_group(group):
    closed = group[group["Encerramento"].notna()]
    if closed.empty:
        return np.nan
    total_hours = closed["Tempo de Encerramento"].sum() * 24
    return total_hours / closed.shape[0]

mttr_sys = df_filtered.groupby("Sistema Construtivo").apply(compute_mttr_group).reset_index(name="MTTR")
mttr_falha = df_filtered.groupby("Tipo de Falha").apply(compute_mttr_group).reset_index(name="MTTR")
col_mttr_sys, col_mttr_falha = st.columns(2)
with col_mttr_sys:
    fig_mttr_sys = px.bar(mttr_sys, x="Sistema Construtivo", y="MTTR", text="MTTR")
    st.plotly_chart(fig_mttr_sys, use_container_width=True)
with col_mttr_falha:
    fig_mttr_falha = px.bar(mttr_falha, x="Tipo de Falha", y="MTTR", text="MTTR")
    st.plotly_chart(fig_mttr_falha, use_container_width=True)

st.markdown('''____________________________________________________________________________________________''')

# 8 – MTTC – Tempo Médio de Conclusão (Por Obra)
st.write("### MTTC - Tempo Médio de Conclusão (Por Obra)")
st.metric("MTTC Geral", f"{mttc:.2f} dias")
mttc_por_obra = df_filtered[df_filtered["Encerramento"].notna()].groupby("Empreendimento")["Tempo de Encerramento"].mean().reset_index(name="MTTC")
fig_mttc = px.bar(
    mttc_por_obra,
    x="Empreendimento",
    y="MTTC",
    color="Empreendimento",
    color_discrete_sequence=px.colors.qualitative.Pastel1,
    text="MTTC"
)
st.plotly_chart(fig_mttc, use_container_width=True)
