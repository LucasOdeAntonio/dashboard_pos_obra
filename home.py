import streamlit as st
import pandas as pd
import sys
import os
from PIL import Image

def resource_path(relative_path):
    """
    Obtém o caminho absoluto para um recurso.
    Funciona tanto em desenvolvimento quanto quando empacotado com PyInstaller (modo onefile).
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Configurando Página (usa o resource_path para encontrar o ícone)
st.set_page_config(
    page_icon=resource_path("Home.jpg"),
    layout='wide',
    page_title="Pós Obra - Home"
)

# Carregar os logos usando resource_path e PIL para garantir a leitura correta
logo_horizontal_path = resource_path("LOGO_VR.png")
logo_reduzida_path = resource_path("LOGO_VR_REDUZIDA.png")
try:
    logo_horizontal_image = Image.open(logo_horizontal_path)
    logo_reduzida_image = Image.open(logo_reduzida_path)
except Exception as e:
    st.error("Erro ao carregar os logos: " + str(e))
    logo_horizontal_image = None
    logo_reduzida_image = None

if logo_horizontal_image and logo_reduzida_image:
    st.logo(image=logo_horizontal_image, size="large", icon_image=logo_reduzida_image)
else:
    st.write("Logos não carregados.")

# CEBEÇALHO INÍCIO ===========================================================================================================================
st.markdown('<h1 style="color: orange;">Painel de Resultados 📈</h1>', unsafe_allow_html=True)
st.markdown('''
       Painel para Acompanhamento de Metas Estratégicas - OKR's ''')
st.markdown('''
       Painel de Resultados BI Até 2024 https://app.powerbi.com/view?r=eyJrIjoiYjM0YTU4OWItNGEwOS00MGZkLWE1NGMtYTQyZWM5OGYzYjNiIiwidCI6Ijk5MWEwMGM5LTY1ZGUtNDFjMS04YzUxLTI3N2Q4YzEwZmNkYSJ9 ''')
# CEBEÇALHO FIM ===============================================================================================================================

# COMO FAZER PRA VIR DE EXCEL =================================================================================================================
# Utilize resource_path para carregar o arquivo Excel
excel_home = resource_path("planilha_home.xlsx")

# Lista fixa de meses para ordenar corretamente
ordem_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

try:
    # Lendo o arquivo Excel
    df_original = pd.read_excel(excel_home)

    # Verificando se há colunas 'OBJETIVOS', 'ANO' e 'MÊS'
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

        # Salvando o conteúdo como CSV (nesse caso, salvamos no diretório atual)
        csv_file = "planilha_home.csv"
        df_filtered.to_csv(csv_file, index=False, encoding='utf-8')

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

# Configurando o Sidebar (opcional)
#st.sidebar.image(resource_path("LOGO_VR.png"), width=200, use_container_width=True)
#st.sidebar.text("Desenvolvido por Lucas Oliveira")
#st.sidebar.markdown("**Desenvolvido por Lucas Oliveira**")
