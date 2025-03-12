import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px  # ADIÇÃO: para gráficos com px.bar
import re
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta  # ADIÇÃO: para cálculo de diferença em meses

# ================================
# Autenticação Simples
# ================================
USERS = {
    "lucas.oliveira": "lucas123",
    "sergio.lopes": "sergio123"  # usuário adicional
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("Acesso Restrito")
    user_input = st.text_input("Usuário")
    password_input = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user_input in USERS and password_input == USERS[user_input]:
            st.session_state["authenticated"] = True
            try:
                st.experimental_rerun()
            except AttributeError:
                st.warning("Sua versão do Streamlit não suporta experimental_rerun. Por favor, atualize seu Streamlit.")
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# ================================
# Funções de Pré-processamento e Carregamento
# ================================
def clean_columns(df):
    """Remove espaços extras dos nomes das colunas, convertendo-os para string."""
    df.columns = df.columns.astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
    return df

def converter_data(df, col_list):
    """Converte as colunas de data para o formato DD/MM/YYYY (datetime)."""
    for col in col_list:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
    return df

def parse_month_year(col):
    """
    Identifica colunas como 'jan/25', 'fev/25', etc. (texto),
    convertendo em datetime(2025,1,1), datetime(2025,2,1), etc.
    Retorna None se não casar.
    """
    months_map = {
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
    }
    match = re.match(r"^([a-zA-Z]{3})/(\d{2})$", col.strip().lower())
    if match:
        mon_str = match.group(1)
        year_str = match.group(2)
        mes = months_map.get(mon_str, None)
        ano = 2000 + int(year_str)
        if mes:
            return datetime(ano, mes, 1)
    return None

def load_data():
    """
    Carrega as abas “departamento”, “engenharia”, “grd_Listagem” e “administrativo”
    do arquivo Excel "base2025.xlsx", aplicando os pré-processamentos:
      - Remoção de espaços extras
      - Conversão de datas (DD/MM/YYYY) para datetime
      - Tratamento de valores em branco (nas abas administrativo e departamento)
      - Na aba grd_Listagem, ignora a primeira linha (células mescladas)
    """
    xls = pd.ExcelFile("base2025.xlsx")
    df_departamento = pd.read_excel(xls, sheet_name="departamento")
    df_engenharia  = pd.read_excel(xls, sheet_name="engenharia")
    df_grd         = pd.read_excel(xls, sheet_name="grd_Listagem", skiprows=1)  # ignora a primeira linha
    df_admin       = pd.read_excel(xls, sheet_name="administrativo")
    
    df_departamento = clean_columns(df_departamento)
    df_engenharia  = clean_columns(df_engenharia)
    df_grd         = clean_columns(df_grd)
    df_admin       = clean_columns(df_admin)
    
    df_departamento = converter_data(df_departamento, ["Data Entrega de obra", "Data CVCO"])
    df_admin       = converter_data(df_admin, ["Previsão Data", "Admissão"])
    df_grd         = converter_data(df_grd, ["Data Documento"])
    
    df_admin = df_admin.replace(r'^\s*$', np.nan, regex=True)
    df_departamento = df_departamento.replace(r'^\s*$', np.nan, regex=True)
    
    return df_departamento, df_engenharia, df_grd, df_admin

# ================================
# Função Principal
# ================================
def main():
    st.set_page_config(
        page_icon="Home.jpg",
        layout='wide',
        page_title="Pós Obra - Financeiro"
    )

    # Exibição dos logos (utilizando use_container_width, pois use_column_width está depreciado)
    logo_horizontal='LOGO_VR.png'
    logo_reduzida="LOGO_VR_REDUZIDA.png"
    st.logo(image=logo_horizontal, size="large", icon_image=logo_reduzida)

    st.markdown('<h1 style="color: orange;">Administrativo e Financeiro Pós Obras 💵</h1>', unsafe_allow_html=True)
    st.markdown('Acompanhamento do Quadro Administrativo e Financeiro do Setor de Pós Obra')

    # Carrega os dados
    df_departamento, df_engenharia, df_grd, df_admin = load_data()
    
    # Colunas datetime auxiliares
    df_departamento['Entrega_dt'] = pd.to_datetime(df_departamento['Data Entrega de obra'], format='%d/%m/%Y', errors='coerce')
    df_admin['Previsao_dt'] = pd.to_datetime(df_admin['Previsão Data'], errors='coerce')
    df_grd['Data_Doc_dt'] = pd.to_datetime(df_grd['Data Documento'], errors='coerce')
    
    # ================================
    # Cálculo da coluna "Periodo" para filtro (aba departamento)
    # ================================
    # Converte a data atual para datetime do Python
    today = pd.Timestamp.today().to_pydatetime()
    
    def classify_period(cvco_date):
        if pd.isnull(cvco_date):
            return "Sem Data CVCO"
        # Converte a data para objeto datetime do Python, se necessário
        cvco_dt = pd.to_datetime(cvco_date).to_pydatetime()
        delta = relativedelta(today, cvco_dt)
        diff_months = delta.years * 12 + delta.months
        if diff_months < 0:
            return "Futuro"
        if diff_months <= 3:
            return "Despesas Pós Entrega"
        elif diff_months <= 12:
            return "Despesas 1° Ano"
        elif diff_months <= 24:
            return "Despesas 2° Ano"
        elif diff_months <= 36:
            return "Despesas 3° Ano"
        elif diff_months <= 48:
            return "Despesas 4° Ano"
        elif diff_months <= 60:
            return "Despesas 5° Ano"
        else:
            return "Despesas após 5 Anos"
    
    if "Data CVCO" in df_departamento.columns:
        df_departamento["Periodo"] = df_departamento["Data CVCO"].apply(classify_period)
    
    # Cria as 3 tabs
    tab_mao_obra, tab_manutencao, tab_equilibrio = st.tabs(["Mão de Obra", "Manutenção", "Ponto de Equilíbrio"])

    # ============================================================
    # TAB MÃO DE OBRA
    # ============================================================
    with tab_mao_obra:
        st.header("👷 Gasto de Mão de Obra (Planejado x Real)")
                
        # Identifica colunas mensais de custo Real (ex.: 'jan/25', 'fev/25', etc.)
        monthly_cols_info = []
        for col in df_admin.columns:
            if isinstance(col, str):
                dt_parsed = parse_month_year(col)
                if dt_parsed:
                    monthly_cols_info.append((dt_parsed, col))
        monthly_cols_info.sort(key=lambda x: x[0])
        
        min_previsao = df_admin['Previsao_dt'].min()
        max_previsao = df_admin['Previsao_dt'].max()
        
        if pd.isna(min_previsao) or pd.isna(max_previsao):
            st.warning("Não foi possível determinar datas para Planejado x Real (ou não há dados).")
        else:
            min_allowed = datetime(2025, 1, 1)
            start_date = max(min_previsao, min_allowed)
            global_min = start_date
            global_max = max_previsao
            if monthly_cols_info:
                min_real = monthly_cols_info[0][0]
                max_real = monthly_cols_info[-1][0]
                global_min = min(global_min, min_real)
                global_max = max(global_max, max_real)
            
            if pd.isna(global_min) or pd.isna(global_max) or global_min > global_max:
                st.warning("Intervalo de datas inconsistente. Verifique os dados.")
            else:
                all_months = pd.date_range(start=global_min, end=global_max, freq='MS')
                
                # Planejado (Acumulado)
                planejado_vals = []
                for m in all_months:
                    val = df_admin.loc[df_admin['Previsao_dt'] <= m, 'Previsão Mão de Obra'].fillna(0).sum()
                    planejado_vals.append(val)
                df_planejado = pd.DataFrame({'Month': all_months, 'Planejado': planejado_vals})
                
                # Real (Mensal, não cumulativo)
                real_df_list = []
                for dt_col, col_name in monthly_cols_info:
                    col_sum = df_admin[col_name].fillna(0).sum()
                    real_df_list.append({'Month': dt_col, 'Real': col_sum})
                if len(real_df_list) == 0:
                    df_real = pd.DataFrame({'Month': all_months, 'Real': [0]*len(all_months)}).set_index('Month')
                else:
                    df_real = pd.DataFrame(real_df_list).set_index('Month')
                    df_real = df_real.reindex(all_months, fill_value=0)
                
                df_real.reset_index(inplace=True)
                df_real.rename(columns={'index': 'Month'}, inplace=True)
                
                final_df = pd.merge(df_planejado, df_real, on='Month', how='outer').fillna(0)
                final_df.sort_values(by='Month', inplace=True)
                final_df['Month_str'] = final_df['Month'].dt.strftime('%b/%y')
                
                final_df = final_df[(final_df['Planejado'] != 0) | (final_df['Real'] != 0)]
                
                if final_df.empty:
                    st.warning("Não há dados para exibir no período calculado.")
                else:
                    fig1 = go.Figure(data=[
                        go.Bar(
                            name='Planejado (Acumulado)',
                            x=final_df['Month_str'],
                            y=final_df['Planejado'],
                            marker_color='lightgrey',
                            marker_line_color='darkgrey',
                            marker_line_width=1
                        ),
                        go.Bar(
                            name='Real (Mensal)',
                            x=final_df['Month_str'],
                            y=final_df['Real'],
                            marker_color='lightsalmon',
                            marker_line_color='darkorange',
                            marker_line_width=1
                        )
                    ])
                    fig1.update_layout(
                        barmode='group',
                        xaxis_title='Período (Mês/Ano)',
                        yaxis_title='Gasto (R$)',
                        legend=dict(x=0, y=1.1, orientation='h')
                    )
                    st.plotly_chart(fig1, use_container_width=True, key="fig1")
        
        st.markdown('-----')
        
        # Métricas de Gasto de Mão de Obra por ANO
        st.header("👷‍♂️ Despesas de Mão de Obra (por ANO)")
        anos_final_df = final_df['Month'].dt.year.unique()
        anos_final_df = [year for year in anos_final_df if year >= 2025]
        anos_final_df = sorted(anos_final_df)
        
        opcoes_anos = ["Nenhum"] + [str(a) for a in anos_final_df]
        ano_selecionado = st.selectbox("Selecione o ANO (Seleção Única)", opcoes_anos, index=0)
        
        if ano_selecionado == "Nenhum":
            planejado_ano = 0.0
            real_ano = 0.0
            delta = 0.0
            perc = 0.0
        else:
            ano = int(ano_selecionado)
            mask_ano = final_df['Month'].dt.year == ano
            planejado_ano = final_df.loc[mask_ano, 'Planejado'].sum()
            real_ano = final_df.loc[mask_ano, 'Real'].sum()
            delta = real_ano - planejado_ano
            perc = (real_ano / planejado_ano * 100) if planejado_ano != 0 else 0.0
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(label=f"Gasto Planejado {ano_selecionado}", value=f"R${planejado_ano:,.2f}")
        with c2:
            st.metric(label=f"Gasto Real {ano_selecionado}", value=f"R${real_ano:,.2f}")
        with c3:
            st.metric(label="Delta (Real - Planejado)", value=f"R${delta:,.2f}")
        with c4:
            st.metric(label="% Atingimento", value=f"{perc:,.2f}%")
        
        st.markdown('-----')
        # ================================
        # NOVA FUNCIONALIDADE: Tabela de Custo de Mão de Obra por Colaborador
        # Utiliza as colunas "Colaborador" e "Salário Bruto" da aba "administrativo"
        # ================================
        st.header("💰 Distribuição de Custo de Mão de Obra por Colaborador")
        if "Colaborador" in df_admin.columns and "Salário Bruto" in df_admin.columns:
            df_colab = df_admin.groupby("Colaborador")["Salário Bruto"].sum().reset_index()
            total_salario = df_colab["Salário Bruto"].sum()
            df_colab["Percentual (%)"] = (df_colab["Salário Bruto"] / total_salario * 100).round(2)
            st.dataframe(df_colab)
        else:
            st.warning("As colunas 'Colaborador' e/ou 'Salário Bruto' não foram encontradas na aba administrativo.")
    
    # ============================================================
    # TAB MANUTENÇÃO
    # ============================================================
    with tab_manutencao:
        st.header("🗓️ Calendário de Previsão de Gastos de Manutenção")
        
        # Define Data_Entrega_Final e Entrega_Year
        df_departamento['Data_Entrega_Final'] = df_departamento.apply(
            lambda row: row['Data CVCO'] if pd.notna(row.get('Data CVCO')) and row.get('Data CVCO') != row.get('Data Entrega de obra')
                        else row.get('Data Entrega de obra'), axis=1)
        df_departamento['Entrega_Year'] = pd.to_datetime(
            df_departamento['Data_Entrega_Final'], format='%d/%m/%Y', errors='coerce'
        ).dt.year
        
        # Calcula Orçamento (1,5%)
        df_departamento['Orçamento (1,5%)'] = df_departamento['Custo de Construção'] * 0.015
        
        # Define forecast_years: considerar somente anos a partir de 2025
        if not df_departamento['Entrega_Year'].dropna().empty:
            max_year = int(df_departamento['Entrega_Year'].max())
            forecast_years = [year for year in range(2025, max_year + 1)]
        else:
            forecast_years = []
        
        # Monta a tabela de previsão
        previsao_table = df_departamento[['Empreendimento', 'Custo de Construção', 'Entrega_Year']].copy()
        for year in forecast_years:
            diff = year - previsao_table['Entrega_Year']
            conditions = [
                (diff < 0),  # Se o ano de forecast for menor que o ano de entrega, célula = 0
                (diff <= 1),
                (diff == 2),
                (diff == 3),
                (diff == 4),
                (diff == 5),
                (diff > 5)
            ]
            choices = [
                0,
                0.5,
                0.2,
                0.1,
                0.1,
                0.1,
                0.0
            ]
            fator = np.select(conditions, choices, default=0)
            col_name = f'Previsão ({year})'
            previsao_table[col_name] = df_departamento['Custo de Construção'] * 0.015 * fator
        
        # Expande a Tabela de Previsão (Regra Aplicada) com formatação em moeda (2 casas)
        format_dict = {col: "R${:,.2f}" for col in previsao_table.columns if col not in ["Empreendimento", "Entrega_Year"]}
        with st.expander("Tabela de Previsão (Regra Aplicada)", expanded=True):
            st.dataframe(previsao_table.fillna(0).style.format(format_dict), use_container_width=True)
        
        # Tabela Editável (Ajuste Manual) com formatação em moeda (2 casas)
        PERSISTENCE_FILE = "maintenance_data.pkl"
        with st.expander("Tabela Editável (Ajuste Manual)", expanded=True):
            if os.path.exists(PERSISTENCE_FILE):
                default_data = pd.read_pickle(PERSISTENCE_FILE)
            else:
                default_data = previsao_table.fillna(0).copy()
            if "maintenance_data" not in st.session_state:
                st.session_state["maintenance_data"] = default_data.copy()
            if st.button("Reset Ajustes", key="reset_button"):
                st.session_state["maintenance_data"] = previsao_table.fillna(0).copy()
                st.session_state["maintenance_data"].to_pickle(PERSISTENCE_FILE)
            if hasattr(st, 'data_editor'):
                edited_df = st.data_editor(
                    st.session_state["maintenance_data"],
                    key="maintenance_editor",
                    use_container_width=True
                )
                st.session_state["maintenance_data"] = edited_df.copy()
                st.session_state["maintenance_data"].to_pickle(PERSISTENCE_FILE)
            else:
                st.warning("Atualize seu Streamlit para a versão que suporta edição interativa.")
                st.dataframe(st.session_state["maintenance_data"].style.format(format_dict), use_container_width=True)
            # Exibe uma visualização formatada (apenas para visualização)
            st.write("Tabela Ajustada conforme Planejamento Estratégico:")
            st.dataframe(st.session_state["maintenance_data"].style.format(format_dict), use_container_width=True)
        
        # Usa os dados editados (persistentes) como fonte para a soma
        data_source = st.session_state.get("maintenance_data", previsao_table.fillna(0))
        forecast_summary = {year: data_source[f'Previsão ({year})'].sum() for year in forecast_years} if forecast_years else {}
        forecast_df = pd.DataFrame(list(forecast_summary.items()), columns=['Ano', 'Despesa Planejada'])
        
        # Calcula o valor Real, excluindo registros onde "Cód. Alternativo Serviço" é "ADM"
        df_grd['Ano_Doc'] = df_grd['Data_Doc_dt'].dt.year
        cond_exclude = df_grd["Cód. Alternativo Serviço"].astype(str).str.strip().str.upper() == "ADM"
        df_grd_filtered = df_grd[~cond_exclude]
        real_by_year = df_grd_filtered.groupby('Ano_Doc')['Valor Conv.'].sum().reset_index().rename(
            columns={'Ano_Doc': 'Ano', 'Valor Conv.': 'Despesa Real'}
        )
        st.markdown('-----')
        st.header('🛒 Despesas em Manutenção (Anual)')
        # Filtra para considerar somente anos >= 2025
        real_by_year = real_by_year[real_by_year['Ano'] >= 2025]
        
        despesa_df = pd.merge(forecast_df, real_by_year, on='Ano', how='outer').fillna(0)
        
        fig3 = go.Figure(data=[
            go.Bar(
                name='Planejado',
                x=despesa_df['Ano'].astype(str),
                y=despesa_df['Despesa Planejada'],
                marker_color='lightgray',
                marker_line_color='darkgray',
                marker_line_width=1,
                text=[f"R${val:,.2f}" for val in despesa_df['Despesa Planejada']],
                textposition='outside'
            ),
            go.Bar(
                name='Real',
                x=despesa_df['Ano'].astype(str),
                y=despesa_df['Despesa Real'],
                marker_color='lightsalmon',
                marker_line_color='darkorange',
                marker_line_width=1,
                text=[f"R${val:,.2f}" for val in despesa_df['Despesa Real']],
                textposition='outside'
            )
        ])
        fig3.update_layout(
            barmode='group',
            xaxis_title='',
            yaxis_title='Despesa (R$)',
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )
        st.plotly_chart(fig3, use_container_width=True, key="fig3")
        
        st.markdown('-----')
        # Gráfico Curva de Despesas de Manutenção por Obra
        st.header('🏘️ Despesas em Manutenção (por Empreendimento)')
        status_options = ["Fora de Garantia", "Assistência Técnica"]
        selected_status = st.multiselect("Selecione o Status", status_options, default=[])
        if not selected_status:
            selected_status = status_options
        
        df_filtered = df_departamento[df_departamento["Status"].isin(selected_status)]
        
        maintenance_list = []
        for idx, row in df_filtered.iterrows():
            empreendimento = row['Empreendimento']
            # Barra Planejado = Custo de Construção * 0,015
            planejado_val = row['Custo de Construção'] * 0.015
            # Para a barra Real, verificamos se o texto de "Cód. Alternativo Serviço" está contido na string do empreendimento.
            # Usamos uma comparação case-insensitive.
            real_val = 0
            for serv in df_grd["Cód. Alternativo Serviço"].dropna().unique():
                serv_clean = serv.strip().upper()
                if serv_clean == "ADM":
                    continue  # Exclui ADM
                if serv_clean in empreendimento.upper():
                    # Soma o "Valor Conv." para os registros que contêm este serviço
                    mask = df_grd["Cód. Alternativo Serviço"].astype(str).apply(lambda x: serv_clean in x.strip().upper())
                    real_val += df_grd.loc[mask, "Valor Conv."].sum()
            maintenance_list.append({
                'Empreendimento': empreendimento,
                'Despesa Planejada': planejado_val,
                'Despesa Real': real_val
            })
        maintenance_df = pd.DataFrame(maintenance_list)
        
        fig4 = go.Figure(data=[
            go.Bar(
                name='Planejado',
                x=maintenance_df['Empreendimento'],
                y=maintenance_df['Despesa Planejada'],
                marker_color='lightgray',
                marker_line_color='darkgray',
                marker_line_width=1,
                text=[f"R${val:,.2f}" for val in maintenance_df['Despesa Planejada']],
                textposition='outside',
            ),
            go.Bar(
                name='Real',
                x=maintenance_df['Empreendimento'],
                y=maintenance_df['Despesa Real'],
                marker_color='lightsalmon',
                marker_line_color='darkorange',
                marker_line_width=1,
                text=[f"R${val:,.2f}" for val in maintenance_df['Despesa Real']],
                textposition='outside',
            )
        ])
        fig4.update_layout(
            barmode='group',
            xaxis_title='',
            yaxis_title='Despesa (R$)',
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            xaxis_tickangle=-45,
            yaxis=dict(
                dtick=100000,
                tickformat='R$,.2f'
            )
        )
        st.plotly_chart(fig4, use_container_width=True, key="fig4")
        
        st.markdown('-----')
        # ================================
        # NOVA FUNCIONALIDADE (TAB MANUTENÇÃO):
        # 1. Tabela Interativa da aba grd_Listagem com filtros e renomeação de colunas
        # 2. Gráfico de barras empilhadas (Descrição Grupo x Descrição Item) com totalização de Valor
        # ================================
        st.header("🔎 Consulta Interativa - grd_Listagem")
        # Seleciona as colunas e renomeia conforme solicitado
        cols_needed = ["Data Documento", "Documento", "Descrição Projeto", "Cód. Alternativo Serviço", "Descrição Grupo", "Descrição Item", "Valor Conv."]
        if all(col in df_grd.columns for col in cols_needed):
            df_grd_interativo = df_grd[cols_needed].copy()
            df_grd_interativo.rename(columns={
                "Documento": "NF",
                "Descrição Projeto": "Projeto Mega",
                "Cód. Alternativo Serviço": "Empreendimento",
                "Valor Conv.": "Valor"
            }, inplace=True)
            # Filtros interativos
            selected_empreendimento = st.multiselect("Empreendimento", options=df_grd_interativo["Empreendimento"].unique(), default=[])
            selected_projeto = st.multiselect("Projeto Mega", options=df_grd_interativo["Projeto Mega"].unique(), default=[])
            selected_grupo = st.multiselect("Descrição Grupo", options=df_grd_interativo["Descrição Grupo"].unique(), default=[])
            search_term = st.text_input("Buscar em Projeto Mega")
            df_filtered_grd = df_grd_interativo.copy()
            if selected_empreendimento:
                df_filtered_grd = df_filtered_grd[df_filtered_grd["Empreendimento"].isin(selected_empreendimento)]
            if selected_projeto:
                df_filtered_grd = df_filtered_grd[df_filtered_grd["Projeto Mega"].isin(selected_projeto)]
            if selected_grupo:
                df_filtered_grd = df_filtered_grd[df_filtered_grd["Descrição Grupo"].isin(selected_grupo)]
            if search_term:
                df_filtered_grd = df_filtered_grd[df_filtered_grd["Projeto Mega"].str.contains(search_term, case=False, na=False)]
            st.dataframe(df_filtered_grd)
        else:
            st.warning("Algumas colunas necessárias não foram encontradas na aba grd_Listagem.")
        
        st.markdown('-----')
        st.header("📊 Gráfico Empilhado - Valor Conv. por Grupo e Item")
        if not df_filtered_grd.empty:
            stacked_fig = px.bar(
                df_filtered_grd,
                x="Descrição Grupo",
                y="Valor",
                color="Descrição Item",
                text="Valor",
                title="Total de Valor por Grupo (empilhado por Item)"
            )
            stacked_fig.update_layout(barmode='stack')
            st.plotly_chart(stacked_fig, use_container_width=True)
        else:
            st.info("Sem dados para exibir o gráfico empilhado.")
        
        st.markdown('-----')
        # ================================
        # NOVA FUNCIONALIDADE (Métricas e Gráficos por Empreendimento)
        # Custo por Unidade: utiliza df_departamento (colunas Empreendimento e N° Unidades e Despesa Manutenção)
        # Custo por N° de Chamados: utiliza df_engenharia (contagem de ocorrências da coluna N°)
        # ================================
        st.header("💸 Métricas de Custo")
        if "Empreendimento" in df_departamento.columns and "N° Unidades" in df_departamento.columns and "Despesa Manutenção" in df_departamento.columns:
            df_depto = df_departamento[["Empreendimento", "N° Unidades", "Despesa Manutenção"]].dropna()
            # Custo por Unidade para cada empreendimento
            df_depto["Custo por Unidade"] = df_depto.apply(lambda row: row["Despesa Manutenção"] / row["N° Unidades"] if row["N° Unidades"] != 0 else 0, axis=1)
        else:
            df_depto = pd.DataFrame()
        
        if "Empreendimento" in df_engenharia.columns and "N°" in df_engenharia.columns:
            df_calls = df_engenharia.groupby("Empreendimento")["N°"].count().reset_index().rename(columns={"N°": "Chamados"})
            if not df_depto.empty:
                df_metrics = pd.merge(df_depto, df_calls, on="Empreendimento", how="left")
                df_metrics["Chamados"].fillna(0, inplace=True)
                df_metrics["Custo por Chamado"] = df_metrics.apply(lambda row: row["Despesa Manutenção"] / row["Chamados"] if row["Chamados"] > 0 else 0, axis=1)
            else:
                df_metrics = pd.DataFrame()
        else:
            df_metrics = pd.DataFrame()
        
        # Cálculo total (soma geral)
        if not df_depto.empty:
            total_despesa = df_depto["Despesa Manutenção"].sum()
            total_unidades = df_depto["N° Unidades"].sum()
            total_custo_unidade = total_despesa / total_unidades if total_unidades != 0 else 0
        else:
            total_custo_unidade = 0
        if not df_metrics.empty:
            total_chamados = df_metrics["Chamados"].sum()
            total_custo_chamado = total_despesa / total_chamados if total_chamados != 0 else 0
        else:
            total_custo_chamado = 0
        
        col_metric1, col_metric2 = st.columns(2)
        with col_metric1:
            st.metric("Custo por Unidade (Total)", f"R${total_custo_unidade:,.2f}")
        with col_metric2:
            st.metric("Custo por N° de Chamados (Total)", f"R${total_custo_chamado:,.2f}")
        
        st.markdown('-----')
        st.header("📊 Gráficos por Empreendimento")
        if not df_depto.empty:
            fig_unidade = px.bar(
                df_depto,
                x="Empreendimento",
                y="Custo por Unidade",
                text="Custo por Unidade",
                title="Custo por Unidade por Empreendimento"
            )
            fig_unidade.update_traces(marker_line_color='black', marker_line_width=1)
            st.plotly_chart(fig_unidade, use_container_width=True)
        else:
            st.info("Dados insuficientes para calcular Custo por Unidade.")
        
        if not df_metrics.empty:
            fig_chamado = px.bar(
                df_metrics,
                x="Empreendimento",
                y="Custo por Chamado",
                text="Custo por Chamado",
                title="Custo por N° de Chamados por Empreendimento"
            )
            fig_chamado.update_traces(marker_line_color='black', marker_line_width=1)
            st.plotly_chart(fig_chamado, use_container_width=True)
        else:
            st.info("Dados insuficientes para calcular Custo por N° de Chamados.")
        
        st.markdown('-----')
        # ================================
        # NOVA FUNCIONALIDADE: Filtro de Período e Gráficos de Gasto
        # Filtros: Período (baseado na coluna "Periodo" de df_departamento), Empreendimento e Status
        # ================================
        st.header("⏱️ Filtro de Período e Gasto")
        period_options = ["Despesas Pós Entrega", "Despesas 1° Ano", "Despesas 2° Ano", "Despesas 3° Ano", "Despesas 4° Ano", "Despesas 5° Ano", "Despesas após 5 Anos"]
        selected_periods = st.multiselect("Selecione os Períodos", options=period_options, default=[])
        selected_empreendimento_period = st.multiselect("Empreendimento (Filtro)", options=df_departamento["Empreendimento"].unique(), default=[])
        selected_status_period = st.multiselect("Status (Filtro)", options=df_departamento["Status"].unique(), default=[])
        
        df_depto_filtered = df_departamento.copy()
        if selected_periods:
            df_depto_filtered = df_depto_filtered[df_depto_filtered["Periodo"].isin(selected_periods)]
        if selected_empreendimento_period:
            df_depto_filtered = df_depto_filtered[df_depto_filtered["Empreendimento"].isin(selected_empreendimento_period)]
        if selected_status_period:
            df_depto_filtered = df_depto_filtered[df_depto_filtered["Status"].isin(selected_status_period)]
        
        # Gráfico de Gasto por Período (total) – utilizando a coluna "Despesa Manutenção"
        periodo_summary = df_depto_filtered.groupby("Periodo")["Despesa Manutenção"].sum().reset_index()
        fig_period = px.bar(
            periodo_summary,
            x="Periodo",
            y="Despesa Manutenção",
            color="Periodo",
            title="Gasto por Período"
        )
        st.plotly_chart(fig_period, use_container_width=True)
        
        # Gráfico de Gasto por Período por Empreendimento
        periodo_emp_summary = df_depto_filtered.groupby(["Periodo", "Empreendimento"])["Despesa Manutenção"].sum().reset_index()
        fig_period_emp = px.bar(
            periodo_emp_summary,
            x="Periodo",
            y="Despesa Manutenção",
            color="Empreendimento",
            title="Gasto por Período por Empreendimento",
            barmode="group"
        )
        st.plotly_chart(fig_period_emp, use_container_width=True)
    
    # ============================================================
    # TAB PONTO DE EQUILÍBRIO
    # ============================================================
    with tab_equilibrio:
        st.header("⚖️ Ponto de Equilíbrio por Empreendimento")
        
        # Filtro por Status: se nenhum for selecionado, define automaticamente os dois
        status_filter = st.multiselect(
            "Filtrar por Status", 
            options=["Assistência Técnica", "Fora de Garantia"],
            default=[]
        )
        if len(status_filter) == 0:
            status_filter = ["Assistência Técnica", "Fora de Garantia"]
        
        # Recupera a Tabela Ajustada (Manutenção) armazenada na sessão
        if "maintenance_data" in st.session_state:
            maint_df = st.session_state["maintenance_data"].copy()
        else:
            st.warning("Dados da Tabela Ajustada conforme Planejamento Estratégico não encontrados.")
            maint_df = pd.DataFrame()
        
        if maint_df.empty:
            st.warning("Não há dados de manutenção disponíveis para calcular a soma da previsão.")
        else:
            # Colunas que começam com "Previsão ("
            forecast_cols = [col for col in maint_df.columns if col.startswith("Previsão (")]
            if not forecast_cols:
                st.warning("Nenhuma coluna de previsão encontrada na Tabela Ajustada.")
            else:
                # Calcula a soma das previsões (Soma Previsão)
                maint_df["Soma Previsão"] = maint_df[forecast_cols].sum(axis=1)
                
                # Seleciona as colunas relevantes da Tabela Ajustada
                resultado = maint_df[["Empreendimento", "Soma Previsão"]].copy()
                
                # Para os cálculos, precisamos das colunas "Custo de Construção", "Despesa Manutenção" e "Status" da aba departamento.
                extra_cols = ["Empreendimento", "Status", "Custo de Construção", "Despesa Manutenção"]
                extra_data = df_departamento[extra_cols].copy()
                resultado = resultado.merge(extra_data, on="Empreendimento", how="left")
                
                # Cálculo de (PE) Real por Obra:
                # Fórmula: 100 * (Despesa Manutenção / Custo de Construção)
                resultado["(PE) Real por Obra"] = np.where(
                    resultado["Custo de Construção"] == 0,
                    0,
                    (resultado["Despesa Manutenção"] / resultado["Custo de Construção"]) * 100
                )
                
                # Cálculo de (PE) Tendência:
                # Fórmula: 100 * ((Soma Previsão + Despesa Manutenção) / Custo de Construção)
                resultado["(PE) Tendência"] = np.where(
                    resultado["Custo de Construção"] == 0,
                    0,
                    ((resultado["Soma Previsão"] + resultado["Despesa Manutenção"]) / resultado["Custo de Construção"]) * 100
                )
                
                # Aplica o filtro de Status
                resultado = resultado[resultado["Status"].isin(status_filter)]
                
                # Remove as colunas que não queremos exibir na tabela final
                resultado = resultado.drop(columns=["Status", "Custo de Construção", "Despesa Manutenção"])
                
                # Formata as colunas
                format_dict = {
                    "Soma Previsão": "{:,.2f}",
                    "(PE) Real por Obra": "{:,.2f}%",
                    "(PE) Tendência": "{:,.2f}%"
                }
                
                # Expander para a tabela
                with st.expander("Mostrar/Ocultar Tabela de Ponto de Equilíbrio"):
                    st.dataframe(resultado.style.format(format_dict), use_container_width=True)
                
                # --- GRÁFICO DE BARRAS ---
                st.markdown('-----')
                fig = go.Figure()
                # Barra para (PE) Real por Obra: laranja com borda laranja escuro
                fig.add_trace(go.Bar(
                    x=resultado["Empreendimento"],
                    y=resultado["(PE) Real por Obra"],
                    name="(PE) Real por Obra",
                    marker=dict(
                        color="orange",
                        line=dict(color="darkorange", width=1)
                    ),
                    text=resultado["(PE) Real por Obra"].apply(lambda x: f"{x:.2f}%"),
                    textposition="auto"
                ))
                # Barra para (PE) Tendência: cinza claro com borda cinza escuro
                fig.add_trace(go.Bar(
                    x=resultado["Empreendimento"],
                    y=resultado["(PE) Tendência"],
                    name="(PE) Tendência",
                    marker=dict(
                        color="lightgray",
                        line=dict(color="darkgray", width=1)
                    ),
                    text=resultado["(PE) Tendência"].apply(lambda x: f"{x:.2f}%"),
                    textposition="auto"
                ))
                # Linha vermelha horizontal em y = 1.5
                fig.add_shape(
                    type="line",
                    x0=0, x1=1, xref="paper",
                    y0=1.5, y1=1.5,
                    line=dict(color="red", width=2, dash="dash")
                )
                fig.update_layout(
                    title="",
                    xaxis_title="",
                    yaxis_title="Percentual (%)",
                    barmode="group",
                    xaxis_tickangle=-45,
                    yaxis=dict(dtick=0.5),
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()
