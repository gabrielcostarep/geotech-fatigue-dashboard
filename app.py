import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.colors as pc

# Configuração da página para ocupar a tela inteira
st.set_page_config(page_title="Dashboard Geotécnico - Fadiga", layout="wide")

st.title("Análise de Fadiga: Escória de Aciaria + Borracha")
st.markdown("""
Este painel processa ensaios triaxiais cíclicos de longa duração. 
A energia dissipada em cada ciclo é calculada geometricamente através do **Teorema de Shoelace (Fórmula de Gauss)**.
""")

# ==========================================
# 1. FUNÇÃO DE ALTA PERFORMANCE (BIG DATA)
# ==========================================
ARQUIVO = 'planilha curta.csv'

@st.cache_data
def carregar_e_calcular(caminho_arquivo):
    df = pd.read_csv(caminho_arquivo)
    df = df.dropna(subset=['ea', 'q', 'Number of cycles'])
    
    # Função vetorizada para o Teorema de Shoelace
    def calcular_shoelace(grupo):
        x = grupo['ea'].values
        y = grupo['q'].values
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    # Agrupa e calcula a energia. include_groups=False resolve o aviso (FutureWarning) do Pandas no terminal!
    df_energia = df.groupby('Number of cycles').apply(calcular_shoelace, include_groups=False).reset_index(name='Amortecimento')
    
    # Converte de kJ/m³ para J/m³ para facilitar a visualização
    df_energia['Amortecimento'] = df_energia['Amortecimento'] * 1000
    
    return df, df_energia

try:
    with st.spinner("Processando ciclos de histerese..."):
        df_bruto, df_energia = carregar_e_calcular(ARQUIVO)
    
    # ==========================================
    # 2. MÉTRICAS PRINCIPAIS (KPIs)
    # ==========================================
    st.divider()
    st.subheader("Resumo Estatístico do Amortecimento")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_ciclos = len(df_energia)
    media_energia = df_energia['Amortecimento'].mean()
    max_energia = df_energia['Amortecimento'].max()
    min_energia = df_energia['Amortecimento'].min()
    desvio_padrao = df_energia['Amortecimento'].std()
    
    col1.metric("Total de Ciclos", f"{total_ciclos:,}".replace(',', '.'))
    col2.metric("Média (J/m³)", f"{media_energia:.3f}")
    col3.metric("Máximo (Pico)", f"{max_energia:.3f}")
    col4.metric("Mínimo (Vale)", f"{min_energia:.3f}")
    col5.metric("Desvio Padrão", f"{desvio_padrao:.3f}")

    # ==========================================
    # 3. ANÁLISE MACRO
    # ==========================================
    st.divider()
    col_macro1, col_macro2 = st.columns(2)
    
    with col_macro1:
        st.subheader("Evolução da Fadiga (Tendência)")
        fig_evolucao = px.line(df_energia, x='Number of cycles', y='Amortecimento', 
                               color_discrete_sequence=['#ff7f0e'])
        fig_evolucao.update_layout(xaxis_title="Número do Ciclo", yaxis_title="Amortecimento (J/m³)")
        st.plotly_chart(fig_evolucao, use_container_width=True)

    with col_macro2:
        st.subheader("Distribuição de Frequência")
        fig_dist = px.histogram(df_energia, x='Amortecimento', marginal='box', 
                                nbins=50, color_discrete_sequence=['#1f77b4'])
        fig_dist.update_layout(xaxis_title="Amortecimento (J/m³)", yaxis_title="Frequência (Qtd. de Ciclos)")
        st.plotly_chart(fig_dist, use_container_width=True)

    # ==========================================
    # 4. ANÁLISE MICRO (INSPEÇÃO DE CICLOS)
    # ==========================================
    st.divider()
    st.subheader("Inspeção Microestrutural: Ciclo de Histerese")
    
    ciclos_disponiveis = df_energia['Number of cycles'].tolist()
    ciclos_selecionados = st.multiselect(
        "Selecione os Ciclos para sobrepor e analisar:", 
        options=ciclos_disponiveis,
        default=ciclos_disponiveis[:3] if len(ciclos_disponiveis) >= 3 else ciclos_disponiveis
    )
    
    qtd_ciclos = len(ciclos_selecionados)
    if qtd_ciclos > 0:
        cores = pc.sample_colorscale('Viridis', [i/(qtd_ciclos-1) if qtd_ciclos > 1 else 0 for i in range(qtd_ciclos)])
        
        fig_2d = go.Figure()
        
        for i, ciclo in enumerate(sorted(ciclos_selecionados)):
            dados_grafico = df_bruto[df_bruto['Number of cycles'] == ciclo]
            
            x_hist = np.append(dados_grafico['ea'].values, dados_grafico['ea'].values[0])
            y_hist = np.append(dados_grafico['q'].values, dados_grafico['q'].values[0])
            
            fig_2d.add_trace(go.Scatter(x=x_hist, y=y_hist, mode='lines+markers', name=f'Ciclo {ciclo}',
                                        line=dict(color=cores[i], width=2), marker=dict(size=4)))
            
        fig_2d.update_layout(xaxis_title="Deformação Axial (ea)", yaxis_title="Tensão Desviadora (q)", hovermode="closest", height=600)
        st.plotly_chart(fig_2d, use_container_width=True)

    # ==========================================
    # 5. DADOS BRUTOS (TABELA COM PAGINAÇÃO)
    # ==========================================
    st.divider()
    st.subheader("Tabela Completa de Dados")
    st.markdown("Navegue por todos os ciclos processados.")

    col_pag1, col_pag2 = st.columns([1, 3])
    
    with col_pag1:
        linhas_por_pagina = st.selectbox("Ciclos por página:", [100, 500, 1000, 5000], index=0)
        
        # Lógica matemática da paginação
        total_paginas = (total_ciclos // linhas_por_pagina) + (1 if total_ciclos % linhas_por_pagina > 0 else 0)
        
        if total_paginas > 0:
            pagina_atual = st.number_input(f"Página (1 a {total_paginas}):", min_value=1, max_value=total_paginas, value=1)
        else:
            pagina_atual = 1

    with col_pag2:
        if total_paginas > 0:
            inicio = (pagina_atual - 1) * linhas_por_pagina
            fim = inicio + linhas_por_pagina
            
            # Fatiando o DataFrame (mostrando só o pedaço da página atual)
            df_pagina = df_energia.iloc[inicio:fim]
            
            st.dataframe(
                df_pagina.style.format({
                    'Number of cycles': '{:.0f}', 
                    'Amortecimento': '{:.6f}'
                }),
                use_container_width=True,
                height=400 # Fixa a altura da tabela para a página não ficar "pulando" de tamanho
            )
            st.caption(f"Exibindo ciclos {inicio + 1} a {min(fim, total_ciclos)} de um total de {total_ciclos}.")

except FileNotFoundError:
    st.error(f"⚠️ O arquivo '{ARQUIVO}' não foi encontrado. Certifique-se de que o nome está correto e na mesma pasta.")
