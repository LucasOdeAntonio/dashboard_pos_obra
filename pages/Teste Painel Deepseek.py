import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, date

# =============================================================================
# Configurações e Constantes
# =============================================================================
LOGO_HORIZONTAL = 'LOGO_VR.png'
LOGO_REDUZIDA = 'LOGO_VR_REDUZIDA.png'
FILE_PATH = "base2025.xlsx"

# =============================================================================
# Funções de Processamento de Dados
# =============================================================================
def normalize_columns(df):
    """
    Remove espaços em branco no início/fim e substitui múltiplos espaços internos por um único espaço.
    """
    df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
    return df

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
    if "ANO" in df_chuva.columns:
        df_chuva = process_calendario_de_chuvas(df_chuva)
    else:
        st.warning("A aba 'calendariodechuvas' não está no formato esperado.")
    
    return df_eng, df_dep, df_chuva

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

def get_column(df, expected):
    expected_normalized = expected.replace(" ", "").lower()
    for col in df.columns:
        if col.replace(" ", "").lower() == expected_normalized:
            return col
    return None

def compute_mtbf(group):
    if group["Data CVCO"].isnull().all():
        return np.nan
    max_data_abertura = group["Data de Abertura"].max()
    min_data_cvco = group["Data CVCO"].min()
    op_hours = (max_data_abertura - min_data_cvco).total_seconds() / 3600
    return op_hours / group.shape[0]

def compute_mttr(group):
    closed = group[group["Encerramento"].notna()]
    if closed.empty:
        return np.nan
    total_hours = closed["Tempo de Encerramento"].sum() * 24
    return total_hours / closed.shape[0]

# =============================================================================
# Funções de Visualização
# =============================================================================
def display_metrics(df_filtered):
    metrica_1 = df_filtered[(df_filtered["Dias em Aberto"] >= 0) & (df_filtered["Dias em Aberto"] <= 15)].shape[0]
    metrica_2 = df_filtered[(df_filtered["Dias em Aberto"] > 15) & (df_filtered["Dias em Aberto"] <= 30)].shape[0]
    metrica_3 = df_filtered[(df_filtered["Dias em Aberto"] > 30) & (df_filtered["Dias em Aberto"] <= 45)].shape[0]
    metrica_4 = df_filtered[(df_filtered["Dias em Aberto"] > 45) & (df_filtered["Dias em Aberto"] <= 60)].shape[0]
    metrica_5 = df_filtered[df_filtered["Dias em Aberto"] > 60].shape[0]
    metrica_6 = df_filtered["N°"].count()

    with st.container():
        col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
        col_m1.metric("Métrica 1 (0-15 dias)", metrica_1)
        col_m2.metric("Métrica 2 (15-30 dias)", metrica_2)
        col_m3.metric("Métrica 3 (30-45 dias)", metrica_3)
        col_m4.metric("Métrica 4 (45-60 dias)", metrica_4)
        col_m5.metric("Métrica 5 (>60 dias)", metrica_5)
        col_m6.metric("Total Solicitações", metrica_6)

def display_filters(df_eng):
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

    return selected_anos, selected_meses, selected_chamados, selected_responsaveis, selected_fcr, selected_empre, selected_unidade, selected_bloco, selected_status, selected_garantia, selected_sistema, selected_tipo

def apply_filters(df_eng, selected_anos, selected_meses, selected_chamados, selected_responsaveis, selected_fcr, selected_empre, selected_unidade, selected_bloco, selected_status, selected_garantia, selected_sistema, selected_tipo):
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
    
    return df_filtered

# =============================================================================
# Layout e Execução Principal
# =============================================================================
def main():
    st.set_page_config(
        page_title="Departamento de Pós Obra",
        page_icon="Home.jpg",
        layout="wide"
    )

    # Exibição dos logos
    col_logo1, col_logo2 = st.columns([3, 1])
    with col_logo1:
        st.image(LOGO_HORIZONTAL, use_container_width=True)
    with col_logo2:
        st.image(LOGO_REDUZIDA, width=100)

    st.markdown('<h1 style="color: orange;">PAINEL DE ASSISTÊNCIA TÉCNICA 💥</h1>', unsafe_allow_html=True)
    st.markdown('Acompanhamento de Solicitações de Assistência Técnica')

    # Carregamento dos dados
    df_eng, df_dep, df_chuva = load_and_preprocess_data(FILE_PATH)

    # Tratamento da coluna “Garantia Solicitada”
    df_eng[["Sistema Construtivo", "Tipo de Falha"]] = df_eng["Garantia Solicitada"].apply(tratamento_garantia)

    # Cálculos de Tempo e Métricas (antes dos filtros)
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

    # Integração com a aba "departamento"
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

    # Filtros
    selected_anos, selected_meses, selected_chamados, selected_responsaveis, selected_fcr, selected_empre, selected_unidade, selected_bloco, selected_status, selected_garantia, selected_sistema, selected_tipo = display_filters(df_eng)
    df_filtered = apply_filters(df_eng, selected_anos, selected_meses, selected_chamados, selected_responsaveis, selected_fcr, selected_empre, selected_unidade, selected_bloco, selected_status, selected_garantia, selected_sistema, selected_tipo)

    # Exibição das Métricas
    display_metrics(df_filtered)

    # Restante do código...

if __name__ == "__main__":
    main()