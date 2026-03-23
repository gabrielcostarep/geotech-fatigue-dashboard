import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.colors as pc

# Configuração da página do Streamlit
st.set_page_config(page_title="EDA - Geomecânica e Borracha", layout="wide")

st.title("🔬 Análise Exploratória: Escória de Aciaria + Granulado de Borracha")
st.markdown("Dashboard interativo para análise de ensaios triaxiais cíclicos e cálculo de Energia Dissipada.")

# ==========================================
# 1. FUNÇÃO DE CARREGAMENTO E PROCESSAMENTO
# ==========================================
@st.cache_data
def carregar_e_calcular(caminho_arquivo):
    # Ler diretamente do Excel (requer a biblioteca openpyxl instalada)
    df = pd.read_excel(caminho_arquivo)
    
    # Limpeza de linhas vazias
    df = df.dropna(subset=['ea', 'q', 'Number of cycles'])
    
    resultados = []
    ciclos_unicos = df['Number of cycles'].unique()
    
    for ciclo in ciclos_unicos:
        dados_ciclo = df[df['Number of cycles'] == ciclo]
        x = dados_ciclo['ea'].values
        y = dados_ciclo['q'].values
        
        # --- CÁLCULOS DE ENERGIA ---
        # Usando np.trapezoid (atualizado para o NumPy 2.0+)
        area_aberto = np.abs(np.trapezoid(y, x))
        
        # Fechar o ciclo (copiando o primeiro ponto para o final)
        x_fechado, y_fechado = np.append(x, x[0]), np.append(y, y[0])
        area_fechado = np.abs(np.trapezoid(y_fechado, x_fechado))
        
        # Método Shoelace
        area_shoelace = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        
        resultados.append({
            'Ciclo': int(ciclo),
            'Trabalho_Total_Aberto': area_aberto,
            'Amortecimento_Fechado': area_fechado,
            'Shoelace': area_shoelace
        })
        
    df_resultados = pd.DataFrame(resultados)
    return df, df_resultados

# Nome do ficheiro
ARQUIVO_EXCEL = 'planilha curta.xlsx'

try:
    df_bruto, df_energia = carregar_e_calcular(ARQUIVO_EXCEL)
    
    # ==========================================
    # 2. BARRA LATERAL (FILTROS)
    # ==========================================
    st.sidebar.header("Filtros de Análise")
    ciclos_disponiveis = df_energia['Ciclo'].tolist()
    
    # Seleção múltipla para comparar vários ciclos em simultâneo
    ciclos_selecionados = st.sidebar.multiselect(
        "Selecione os Ciclos para comparar a Histerese:", 
        options=ciclos_disponiveis,
        default=ciclos_disponiveis[:3] if len(ciclos_disponiveis) >= 3 else ciclos_disponiveis
    )
    
    # ==========================================
    # 3. CONTEÚDO PRINCIPAL (DASHBOARD)
    # ==========================================
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Ciclos Analisados", len(ciclos_disponiveis))
    col2.metric("Energia Média (Amortecimento)", f"{df_energia['Amortecimento_Fechado'].mean():.6f}")
    col3.metric("Deformação Máxima Atingida", f"{df_bruto['ea'].max():.6f}")
    
    st.divider()

    # --- GRÁFICO 1: CICLO DE HISTERESE INTERATIVO (2D e 3D) ---
    st.subheader("🔄 Evolução do Ciclo de Histerese")
    
    # Criar abas para organizar a visualização
    aba2d, aba3d = st.tabs(["📊 Visão 2D Clássica", "🧊 Visão 3D (Cascata)"])
    
    qtd_ciclos = len(ciclos_selecionados)
    if qtd_ciclos > 0:
        # Paleta de cores em gradiente (Roxo ao Amarelo) com base na quantidade escolhida
        cores = pc.sample_colorscale('Viridis', [i/(qtd_ciclos-1) if qtd_ciclos > 1 else 0 for i in range(qtd_ciclos)])
        
        # Preparar as figuras 2D e 3D
        fig_2d = go.Figure()
        fig_3d = go.Figure()
        
        for i, ciclo in enumerate(sorted(ciclos_selecionados)):
            dados_grafico = df_bruto[df_bruto['Number of cycles'] == ciclo]
            
            # Fechar o ciclo para o desenho ficar completo
            x_hist = np.append(dados_grafico['ea'].values, dados_grafico['ea'].values[0])
            y_hist = np.append(dados_grafico['q'].values, dados_grafico['q'].values[0])
            
            # Eixo Z para o gráfico 3D (matriz preenchida com o número do ciclo)
            z_hist = np.full(len(x_hist), ciclo)
            
            # Adicionar linha no Gráfico 2D
            fig_2d.add_trace(go.Scatter(
                x=x_hist, y=y_hist, 
                mode='lines+markers', 
                name=f'Ciclo {ciclo}',
                line=dict(color=cores[i], width=2),
                marker=dict(size=4)
            ))
            
            # Adicionar linha flutuante no Gráfico 3D
            fig_3d.add_trace(go.Scatter3d(
                x=x_hist, y=z_hist, z=y_hist, 
                mode='lines', 
                name=f'Ciclo {ciclo}',
                line=dict(color=cores[i], width=4)
            ))
            
        # Ajustes de layout do Gráfico 2D
        fig_2d.update_layout(
            xaxis_title="Deformação Axial (ea)",
            yaxis_title="Tensão Desviadora (q)",
            hovermode="closest"
        )
        
        # Ajustes de layout do Gráfico 3D
        fig_3d.update_layout(
            scene=dict(
                xaxis_title='Deformação (ea)',
                yaxis_title='Número do Ciclo',
                zaxis_title='Tensão (q)'
            ),
            margin=dict(l=0, r=0, b=0, t=20),
            hovermode="closest"
        )
        
        # Exibir os gráficos nas respetivas abas
        with aba2d:
            st.plotly_chart(fig_2d, use_container_width=True)
            st.caption("Visão clássica sobreposta. Pode parecer confusa para muitos ciclos próximos.")
            
        with aba3d:
            st.plotly_chart(fig_3d, use_container_width=True)
            st.caption("DICA: Clique e arraste para girar o gráfico 3D. Esta visão separa os ciclos no espaço, permitindo ver o 'Shakedown' perfeitamente!")

    # --- GRÁFICO 2: EVOLUÇÃO DA ENERGIA AO LONGO DOS CICLOS ---
    st.divider()
    st.subheader("📈 Evolução da Energia Dissipada")
    st.markdown("Comparação entre o Trabalho Total (Trapézio Aberto) e o Amortecimento (Trapézio Fechado/Shoelace).")
    
    fig_energia = px.line(
        df_energia, 
        x='Ciclo', 
        y=['Trabalho_Total_Aberto', 'Amortecimento_Fechado'],
        labels={'value': 'Energia Dissipada (Área)', 'variable': 'Método de Cálculo'},
        markers=True
    )
    st.plotly_chart(fig_energia, use_container_width=True)
    
    # --- TABELA DE DADOS FINAIS ---
    st.divider()
    st.subheader("📊 Tabela de Dados Processados")
    st.dataframe(df_energia.style.format({
        'Trabalho_Total_Aberto': '{:.6f}', 
        'Amortecimento_Fechado': '{:.6f}', 
        'Shoelace': '{:.6f}'
    }))

except FileNotFoundError:
    st.error(f"⚠️ Ficheiro '{ARQUIVO_EXCEL}' não encontrado! Certifique-se de que está na mesma pasta que o app.py.")