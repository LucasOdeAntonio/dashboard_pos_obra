import streamlit as st
import pandas as pd
import plotly.express as px
import warnings

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
st.markdown('<h1 style="color: orange;">PAINEL DE ASSITÊNCIA TÉCNICA 💥</h1>', unsafe_allow_html=True)

st.markdown('''
       Acompanhamento de Solicitações de Assistência Técnica ''')
# CEBEÇALHO FIM ===============================================================================================================================

# Carregar a base do Excel =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- 
excel_lagoapark = 'lagoapark.xlsx'

try:
    # Carregar a aba do Excel
    df_departamento = pd.read_excel(excel_lagoapark)

    # Remover espaços extras nos nomes das colunas
    df_departamento.columns = df_departamento.columns.str.strip()

    # Conversão de datas para o formato datetime
    df_departamento['Solicitação Abertura'] = pd.to_datetime(df_departamento['Solicitação Abertura'], errors='coerce')
    df_departamento['Solicitação Encerramento'] = pd.to_datetime(df_departamento['Solicitação Encerramento'], errors='coerce')

    # Substituir valores NaT por uma data padrão para evitar erros (agora usando a data de hoje)
    df_departamento['Solicitação Encerramento'].fillna(pd.Timestamp.today(), inplace=True)

    #st.dataframe(df_departamento, use_container_width=True) #HABILITAR CASO QUEIRA VISUALIZAR A TABELA DO ARQUIVO EXCEL.

    # Calcular a diferença entre as datas
    df_departamento['Duração'] = (df_departamento['Solicitação Encerramento'] - df_departamento['Solicitação Abertura']).dt.days

    # Filtrar os dados por situação diferente de "Encerrada"
    df_filtrado = df_departamento[df_departamento['Solicitação Situação'] != 'Encerrada']

    # CONFIGURANDO SIDEBAR ====================================================================================
    obranome = df_departamento['Obra Nome'].unique().tolist()
    obranome_selecionadas = st.sidebar.multiselect("Obra Nome:", obranome, default=[])
   
    situacao = df_departamento['Solicitação Situação'].unique().tolist()
    situacao_selecionadas = st.sidebar.multiselect("Filtrar por Situação:", situacao, default=[])

    procedencia_nome = df_departamento['Solicitação Procedência'].unique().tolist()
    procedencia_nome_selecionadas = st.sidebar.multiselect("Solicitação Procedência:", procedencia_nome, default=[])

    # Aplicando os filtros selecionados
    if obranome_selecionadas:
        df_departamento = df_departamento[df_departamento['Obra Nome'].isin(obranome_selecionadas)]

    if situacao_selecionadas:
        df_departamento = df_departamento[df_departamento['Solicitação Situação'].isin(situacao_selecionadas)]

    if procedencia_nome_selecionadas:
        df_departamento = df_departamento[df_departamento['Solicitação Procedência'].isin(procedencia_nome_selecionadas)]
    # FIM SIDEBAR =============================================================================================

    # Criar mais 4 colunas para o layout
    col9, col10, col11, col12 = st.columns([1, 1, 1, 1])

    # Filtro de "Data de Início" (Agora com valor inicial em branco)
    with col9:
        data_inicio = st.date_input(
            "Selecione a data de início", 
            value=None,  # Não definindo uma data inicial (em branco)
            min_value=df_departamento['Solicitação Abertura'].min(), 
            max_value=df_departamento['Solicitação Abertura'].max(),
            format="DD/MM/YYYY"
        )

    # Filtro de "Data de Encerramento" (Agora com valor inicial em branco)
    with col10:
        data_encerramento = st.date_input(
            "Selecione a data de Encerramento", 
            value=None,  # Não definindo uma data inicial (em branco)
            min_value=df_departamento['Solicitação Encerramento'].min(), 
            max_value=df_departamento['Solicitação Encerramento'].max(),
            format="DD/MM/YYYY"
        )

    # Filtrando as datas selecionadas
    if data_inicio and data_encerramento:
        data_inicio = pd.to_datetime(data_inicio)
        data_encerramento = pd.to_datetime(data_encerramento)

        df_departamento = df_departamento[
            (df_departamento['Solicitação Abertura'] >= data_inicio) & 
            (df_departamento['Solicitação Encerramento'] <= data_encerramento)
        ]
    elif data_inicio:  # Filtra apenas pela data de início
        data_inicio = pd.to_datetime(data_inicio)
        df_departamento = df_departamento[df_departamento['Solicitação Abertura'] >= data_inicio]
    elif data_encerramento:  # Filtra apenas pela data de encerramento
        data_encerramento = pd.to_datetime(data_encerramento)
        df_departamento = df_departamento[df_departamento['Solicitação Encerramento'] <= data_encerramento]

    # Linha com colunas para filtros adicionais
    col13, col14, col15, col16 = st.columns([1, 1, 1, 1])

    with col13:
        grupo_sistema = df_departamento['Grupo de Sistema Construtivo Nome'].unique().tolist()
        grupo_sistema_selecionado = st.multiselect("Grupo de Sistema Construtivo:", grupo_sistema, default=[])
        if grupo_sistema_selecionado:
            df_departamento = df_departamento[df_departamento['Grupo de Sistema Construtivo Nome'].isin(grupo_sistema_selecionado)]

    with col14:
        sistema_construtivo = df_departamento['Sistema Construtivo Nome'].unique().tolist()
        sistema_selecionado = st.multiselect("Sistema Construtivo:", sistema_construtivo, default=[])
        if sistema_selecionado:
            df_departamento = df_departamento[df_departamento['Sistema Construtivo Nome'].isin(sistema_selecionado)]

    with col15:
        causa_raiz = df_departamento['Causa Raiz Nome'].unique().tolist()
        causa_raiz_selecionada = st.multiselect("Causa Raiz:", causa_raiz, default=[])
        if causa_raiz_selecionada:
            df_departamento = df_departamento[df_departamento['Causa Raiz Nome'].isin(causa_raiz_selecionada)]

    with col16:
        colaborador = df_departamento['Colaborador Nome'].unique().tolist()
        colaborador_selecionado = st.multiselect("Colaborador:", colaborador, default=[])
        if colaborador_selecionado:
            df_departamento = df_departamento[df_departamento['Colaborador Nome'].isin(colaborador_selecionado)]

    # Soma total de "Obra Nome"
    total_solicitacoes = len(df_departamento['Obra Nome'])

    # Cálculo do Tempo Médio para Conclusão (MTTC), desconsiderando valores em branco ou datas padrão
    if not df_departamento.empty:
        df_departamento['Tempo Conclusao'] = (
            df_departamento['Solicitação Encerramento'] - df_departamento['Solicitação Abertura']
        ).dt.days
        tempo_medio_conclusao = df_departamento.loc[df_departamento['Tempo Conclusao'] > 0, 'Tempo Conclusao'].mean()
    else:
        tempo_medio_conclusao = 0

    # Agrupar os dados por "Obra Nome" e contar a quantidade de "Obra Nome"
    df_obra = df_departamento.groupby('Obra Nome').size().reset_index(name='Contagem')

    # Agrupar os dados por "Sistema Construtivo Nome" e contar
    df_sistema = df_departamento.groupby('Sistema Construtivo Nome').size().reset_index(name='Contagem')
    st.markdown('''____________________________________________________________________________________________''')

    # Linha com col9 e col10
    col17, col18 = st.columns([1, 3])

    # Gráfico de barras verticais (contagem de "Obra Nome")
    with col17:
        st.bar_chart(df_obra.set_index('Obra Nome')['Contagem'])

    # Gráfico de barras verticais por "Sistema Construtivo Nome"
    with col18:
        fig = px.bar(
            df_sistema,
            x='Sistema Construtivo Nome',
            y='Contagem',
            color='Sistema Construtivo Nome',
            title='Ocorrências por Sistema Construtivo',
            labels={'Contagem': 'Ocorrências', 'Sistema Construtivo Nome': 'Sistema Construtivo'},
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Exibindo o total de solicitações de forma destacada na coluna col3
    with col11:
        st.metric("Número Total de Solicitações", total_solicitacoes)

    # Adicionar box com MTTC na col4
    with col12:
        st.metric("MTTC - Tempo Médio para Conclusão", f"{tempo_medio_conclusao:.2f} dias")

    # 5 – Gráfico para Sistema Construtivo
df_sys = df_filtered.groupby("Sistema Construtivo").size().reset_index(name="Count")
fig_sys = px.bar(
    df_sys,
    x="Sistema Construtivo",
    y="Count",
    barmode="stack",
    text="Count"
)
st.plotly_chart(fig_sys, use_container_width=True)
st.markdown("---")

# 8 – Gráfico para Tipo de Falha
df_falha = df_filtered.groupby("Tipo de Falha").size().reset_index(name="Count")
fig_falha = px.bar(
    df_falha,
    x="Tipo de Falha",
    y="Count",
    barmode="stack",
    text="Count"
)
st.plotly_chart(fig_falha, use_container_width=True)
st.markdown("---")

# 9 – Gráfico Empilhado por Empreendimento (Sistema Construtivo)
df_emp_sys = df_filtered.groupby(["Empreendimento", "Sistema Construtivo"]).size().reset_index(name="Count")
fig_emp_sys = px.bar(
    df_emp_sys,
    x="Empreendimento",
    y="Count",
    color="Sistema Construtivo",
    barmode="stack",
    text="Count"
)
st.plotly_chart(fig_emp_sys, use_container_width=True)
st.markdown("---")

# 10 – Gráfico Empilhado por Empreendimento (Tipo de Falha)
df_emp_falha = df_filtered.groupby(["Empreendimento", "Tipo de Falha"]).size().reset_index(name="Count")
fig_emp_falha = px.bar(
    df_emp_falha,
    x="Empreendimento",
    y="Count",
    color="Tipo de Falha",
    barmode="stack",
    text="Count"
)
st.plotly_chart(fig_emp_falha, use_container_width=True)
st.markdown("---")

# 11 – Gráfico de MTBF por Sistema Construtivo
def compute_mtbf_group(group):
    if group["Data CVCO"].isnull().all():
        return np.nan
    max_data = group["Data de Abertura"].max()
    min_cvco = group["Data CVCO"].min()
    op_hours = (max_data - min_cvco).total_seconds() / 3600
    return op_hours / group.shape[0]

mtbf_sys = df_filtered.groupby("Sistema Construtivo").apply(compute_mtbf_group).reset_index(name="MTBF")
fig_mtbf_sys = px.bar(
    mtbf_sys,
    x="Sistema Construtivo",
    y="MTBF",
    text="MTBF"
)
st.plotly_chart(fig_mtbf_sys, use_container_width=True)
st.markdown("---")

# 12 – Gráfico de MTBF por Tipo de Falha
mtbf_falha = df_filtered.groupby("Tipo de Falha").apply(compute_mtbf_group).reset_index(name="MTBF")
fig_mtbf_falha = px.bar(
    mtbf_falha,
    x="Tipo de Falha",
    y="MTBF",
    text="MTBF"
)
st.plotly_chart(fig_mtbf_falha, use_container_width=True)
st.markdown("---")

# 13 – Gráfico de MTTR por Sistema Construtivo
def compute_mttr_group(group):
    closed = group[group["Encerramento"].notna()]
    if closed.empty:
        return np.nan
    total_hours = closed["Tempo de Encerramento"].sum() * 24
    return total_hours / closed.shape[0]

mttr_sys = df_filtered.groupby("Sistema Construtivo").apply(compute_mttr_group).reset_index(name="MTTR")
fig_mttr_sys = px.bar(
    mttr_sys,
    x="Sistema Construtivo",
    y="MTTR",
    text="MTTR"
)
st.plotly_chart(fig_mttr_sys, use_container_width=True)
st.markdown("---")

# 14 – Gráfico de MTTR por Tipo de Falha
mttr_falha = df_filtered.groupby("Tipo de Falha").apply(compute_mttr_group).reset_index(name="MTTR")
fig_mttr_falha = px.bar(
    mttr_falha,
    x="Tipo de Falha",
    y="MTTR",
    text="MTTR"
)
st.plotly_chart(fig_mttr_falha, use_container_width=True)
st.markdown("---")


    csv_file = 'lagoapark2.csv'
    df_departamento.to_csv(csv_file, index=False, encoding='utf-8')  # Salva sem o índice e com codificação UTF-8

    st.markdown('''____________________________________________________________________________________________''')
    st.dataframe(df_departamento, use_container_width=True)# - HABILITAR CASO QUEIRA VISUALIZAR A TABELA DO ARQUIVO EXCEL.   
    st.success(f"Planilha salva como '{csv_file}'!")
    
except FileNotFoundError:
    st.error("O arquivo Excel não foi encontrado. Por favor, verifique o caminho.")
except Exception as e:
    st.error(f"Ocorreu um erro: {e}")