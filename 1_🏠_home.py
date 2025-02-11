import streamlit as st
import pandas as pd

# Configurando Página
st.set_page_config(
    page_icon="Home.jpg",
    layout='wide',
    page_title="Departamento de Pós Obra"
)

#Logo superior no sidebar, imagem grande e reduzida.
logo_horizontal='LOGO_VR.png'
logo_reduzida="LOGO_VR_REDUZIDA.png"
st.logo(image=logo_horizontal, size="large",icon_image=logo_reduzida)


# CEBEÇALHO INÍCIO ===========================================================================================================================
#st.image("LOGO_VR.png", caption="") - pra adicionar imagens
st.markdown('<h1 style="color: orange;">PAINEL DE RESULTADOS 📈</h1>', unsafe_allow_html=True)
st.image("fluxograma.png", caption="")


st.markdown('''
       Painel para Acompanhamento de Metas Estratégicas - OKR's ''')
st.markdown('''
       Painel de Resultados BI Até 2024 https://app.powerbi.com/view?r=eyJrIjoiYjM0YTU4OWItNGEwOS00MGZkLWE1NGMtYTQyZWM5OGYzYjNiIiwidCI6Ijk5MWEwMGM5LTY1ZGUtNDFjMS04YzUxLTI3N2Q4YzEwZmNkYSJ9 ''')
# CEBEÇALHO FIM ===============================================================================================================================

# COMO FAZER PRA VIR DE EXCEL =================================================================================================================
excel_home = 'planilha_home.xlsx'

# Lista fixa de meses para ordenar corretamente
ordem_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

try:
    # Lendo o arquivo Excel
    df_original = pd.read_excel(excel_home)

    # Verificando se há colunas 'OBJETIVOS', 'ANO', e 'MÊS'
    if all(col in df_original.columns for col in ['OBJETIVOS', 'ANO', 'MÊS']):
        # Garantindo que a coluna 'MÊS' contenha strings válidas
        df_original['MÊS'] = df_original['MÊS'].apply(lambda x: str(x).capitalize() if not pd.isna(x) else "")
        # Ajustando a coluna 'ANO' para exibição e filtragem como string
        df_original['ANO'] = df_original['ANO'].apply(lambda x: str(int(x)) if not pd.isna(x) else "")
        # Convertendo a coluna 'OBJETIVOS' para string
        df_original['OBJETIVOS'] = df_original['OBJETIVOS'].apply(lambda x: str(x) if not pd.isna(x) else "")

        # Filtros dinâmicos
        df_filtered = df_original.copy()

        # Filtro de Ano
        anos_disponiveis = sorted(df_filtered['ANO'].unique())
        ano_selecionado = st.sidebar.selectbox(
            "Selecione o Ano",
            options=["Todos"] + anos_disponiveis
        )

        # Filtrando os dados pelo ano
        if ano_selecionado != "Todos":
            df_filtered = df_filtered[df_filtered['ANO'] == ano_selecionado]

        # Filtro de Mês
        meses_disponiveis = sorted(
            [mes for mes in df_filtered['MÊS'].unique() if mes in ordem_meses],
            key=lambda x: ordem_meses.index(x)
        )
        mes_selecionado = st.sidebar.selectbox(
            "Selecione o Mês",
            options=["Todos"] + meses_disponiveis
        )

        # Filtrando os dados pelo mês
        if mes_selecionado != "Todos":
            df_filtered = df_filtered[df_filtered['MÊS'] == mes_selecionado]

        # Atualizando o filtro de Objetivos com base nos filtros de Ano e Mês
        objetivos_disponiveis = sorted(df_filtered['OBJETIVOS'].unique())
        objetivo_selecionado = st.sidebar.selectbox(
            "Selecione o Objetivo",
            options=["Todos"] + objetivos_disponiveis
        )

        # Filtrando os dados pelo Objetivo
        if objetivo_selecionado != "Todos":
            df_filtered = df_filtered[df_filtered['OBJETIVOS'] == objetivo_selecionado]

        # Exibindo os valores selecionados no título
        if objetivo_selecionado != "Todos":
            st.markdown(f"# {objetivo_selecionado}")
        else:
            st.markdown("# Dados de Todos os Objetivos")

        if ano_selecionado != "Todos":
            st.markdown(f"Dados do Ano Selecionado: {ano_selecionado}")
        else:
            st.markdown("Dados de Todos os Anos")

        if mes_selecionado != "Todos":
            st.markdown(f"Dados do Mês Selecionado: {mes_selecionado}")
        else:
            st.markdown("Dados de Todos os Meses")

        # Salvando o conteúdo como CSV
        csv_file = 'planilha_home.csv'
        df_filtered.to_csv(csv_file, index=False, encoding='utf-8')  # Salva sem o índice e com codificação UTF-8

        st.markdown("### Objetivos e Indicadores Estratégicos")
        # Exibindo o DataFrame filtrado no Streamlit com largura ajustada
        st.dataframe(df_filtered, use_container_width=True)

        st.success(f"Planilha salva como '{csv_file}'!")
    else:
        st.warning("As colunas 'OBJETIVOS', 'ANO' e 'MÊS' não foram encontradas na planilha. Nenhum filtro será aplicado.")
except FileNotFoundError:
    st.error("O arquivo Excel não foi encontrado. Por favor, verifique o caminho.")
except Exception as e:
    st.error(f"Ocorreu um erro: {e}")
# FIM DE COMO FAZER PRA VIR DE EXCEL ===========================================================================================================


# Configurando o Sidebar
#st.sidebar.image("LOGO_VR.png", width=200, use_container_width=True)
#st.sidebar.text("Desenvolvido por Lucas Oliveira")
#st.sidebar.markdown("**Desenvolvido por Lucas Oliveira**")