import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
import os
from datetime import datetime

# ================================
# Autenticação Simples
# ================================
USERNAME = "lucas.oliveira"
PASSWORD = "lucas123"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("Acesso Restrito")
    user_input = st.text_input("Usuário")
    password_input = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user_input == USERNAME and password_input == PASSWORD:
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
    st.logo(image=logo_horizontal, size="large",icon_image=logo_reduzida)

    st.markdown('<h1 style="color: orange;">Administrativo e Financeiro Pós Obras 💵</h1>', unsafe_allow_html=True)
    st.markdown('Acompanhamento do Quadro Administrativo e Financeiro do Setor de Pós Obra')

    # Carrega os dados
    df_departamento, df_engenharia, df_grd, df_admin = load_data()
    
    # Colunas datetime auxiliares
    df_departamento['Entrega_dt'] = pd.to_datetime(df_departamento['Data Entrega de obra'], format='%d/%m/%Y', errors='coerce')
    df_admin['Previsao_dt'] = pd.to_datetime(df_admin['Previsão Data'], errors='coerce')
    df_grd['Data_Doc_dt'] = pd.to_datetime(df_grd['Data Documento'], errors='coerce')
    
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
        # Gráfico Curva de DEspesas de Manutenção por Obra
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