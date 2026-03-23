import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.colors as pc
import ipywidgets as widgets
from IPython.display import display, Markdown

# ==========================================
# 1. PROCESSAMENTO DE ALTA PERFORMANCE
# ==========================================
ARQUIVO = 'planilha curta.csv'

def carregar_e_calcular(caminho_arquivo):
    df = pd.read_csv(caminho_arquivo)
    df = df.dropna(subset=['ea', 'q', 'Number of cycles'])
    
    # Função vetorizada para o Teorema de Shoelace (Área do Polígono)
    def calcular_shoelace(grupo):
        x = grupo['ea'].values
        y = grupo['q'].values
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    # Agrupa por ciclo e calcula a energia instantaneamente
    df_energia = df.groupby('Number of cycles').apply(calcular_shoelace).reset_index(name='Amortecimento')
    
    # Padroniza para Joules/m³ multiplicando por 1000
    df_energia['Amortecimento'] = df_energia['Amortecimento'] * 1000
    
    return df, df_energia

print("Processando os dados... Isso pode levar alguns segundos.")
df_bruto, df_energia = carregar_e_calcular(ARQUIVO)

# ==========================================
# 2. MÉTRICAS PRINCIPAIS (KPIs)
# ==========================================
total_ciclos = len(df_energia)
media_energia = df_energia['Amortecimento'].mean()
max_energia = df_energia['Amortecimento'].max()
min_energia = df_energia['Amortecimento'].min()
desvio_padrao = df_energia['Amortecimento'].std()

# Exibindo as métricas usando Markdown nativo do Colab
display(Markdown("---"))
display(Markdown("## 📊 Resumo Estatístico do Amortecimento (Energia Dissipada)"))
display(Markdown(f"**Total de Ciclos Analisados:** `{total_ciclos:,}`".replace(',', '.')))
display(Markdown(f"**Média:** `{media_energia:.3f} J/m³`"))
display(Markdown(f"**Máximo (Pico):** `{max_energia:.3f} J/m³`"))
display(Markdown(f"**Mínimo (Vale):** `{min_energia:.3f} J/m³`"))
display(Markdown(f"**Desvio Padrão:** `{desvio_padrao:.3f}`"))
display(Markdown("---"))

# ==========================================
# 3. ANÁLISE MACRO (GRÁFICOS GERAIS E TABELA)
# ==========================================
display(Markdown("### 📈 Evolução e Distribuição da Fadiga"))

# Gráfico 1: Evolução da Energia
fig_evolucao = px.line(df_energia, x='Number of cycles', y='Amortecimento', 
                       title="Tendência de Amortecimento ao longo dos Ciclos",
                       color_discrete_sequence=['#ff7f0e'])
fig_evolucao.update_layout(xaxis_title="Número do Ciclo", yaxis_title="Amortecimento (J/m³)")
fig_evolucao.show()

# Gráfico 2: Distribuição de Frequência (Histograma)
fig_dist = px.histogram(df_energia, x='Amortecimento', marginal='box', 
                        title="Frequência e Concentração da Energia",
                        nbins=50, color_discrete_sequence=['#1f77b4'])
fig_dist.update_layout(xaxis_title="Amortecimento (J/m³)", yaxis_title="Frequência (Qtd. de Ciclos)")
fig_dist.show()

display(Markdown("### 📋 Tabela de Dados Processados"))
display(df_energia.style.format({'Number of cycles': '{:.0f}', 'Amortecimento': '{:.6f}'}))

# ==========================================
# 4. ANÁLISE MICRO (INTERATIVA COM IPYWIDGETS)
# ==========================================
display(Markdown("---"))
display(Markdown("## 🔄 Inspeção Microestrutural: Ciclos de Histerese"))
display(Markdown("*Selecione os ciclos no menu abaixo para inspecionar e sobrepor (Segure `Ctrl` ou `Cmd` para selecionar vários):*"))

ciclos_disponiveis = df_energia['Number of cycles'].tolist()

# Cria o Widget (Menu interativo)
seletor_ciclos = widgets.SelectMultiple(
    options=ciclos_disponiveis,
    value=ciclos_disponiveis[:3] if len(ciclos_disponiveis) >= 3 else ciclos_disponiveis,
    rows=6,
    description='Ciclos:',
    disabled=False
)

# Função que atualiza o gráfico 2D toda vez que o menu é alterado
def plotar_histerese(ciclos_selecionados):
    if not ciclos_selecionados:
        print("⚠️ Por favor, selecione pelo menos um ciclo.")
        return

    qtd_ciclos = len(ciclos_selecionados)
    cores = pc.sample_colorscale('Viridis', [i/(qtd_ciclos-1) if qtd_ciclos > 1 else 0 for i in range(qtd_ciclos)])
    
    fig_2d = go.Figure()
    
    for i, ciclo in enumerate(sorted(ciclos_selecionados)):
        dados_grafico = df_bruto[df_bruto['Number of cycles'] == ciclo]
        
        # O método np.append "fecha" o ciclo visualmente
        x_hist = np.append(dados_grafico['ea'].values, dados_grafico['ea'].values[0])
        y_hist = np.append(dados_grafico['q'].values, dados_grafico['q'].values[0])
        
        # Adiciona a curva no gráfico 2D
        fig_2d.add_trace(go.Scatter(x=x_hist, y=y_hist, mode='lines+markers', name=f'Ciclo {ciclo}',
                                    line=dict(color=cores[i], width=2), marker=dict(size=4)))
        
    # Atualiza o visual do gráfico para deixá-lo grande e limpo
    fig_2d.update_layout(
        title="Ciclos de Histerese (Visão 2D)", 
        xaxis_title="Deformação Axial (ea)", 
        yaxis_title="Tensão Desviadora (q)", 
        hovermode="closest",
        height=600 # Gráfico mais alto para facilitar a visualização
    )
    
    fig_2d.show()

# Conecta o Widget à função de desenhar
widgets.interact(plotar_histerese, ciclos_selecionados=seletor_ciclos);
