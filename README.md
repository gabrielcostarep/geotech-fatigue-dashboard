# 🔬 Dashboard Geotécnico: Análise de Fadiga e Histerese

🚧 **Status do Projeto:** Em desenvolvimento (Work In Progress) 🚧

## 📖 Sobre o Projeto
Este repositório contém uma aplicação web interativa desenvolvida para a Análise Exploratória de Dados (EDA) de ensaios triaxiais cíclicos de longa duração. O foco do estudo é analisar o comportamento mecânico, a fadiga e a capacidade de amortecimento de materiais granulares (como escória de aciaria misturada com granulado de borracha) aplicados à infraestrutura de transportes.

A ferramenta automatiza o processamento de grandes volumes de dados de sensores de laboratório (suportando ensaios de até 1 milhão de ciclos) e extrai métricas físicas cruciais de forma dinâmica.

## ✨ Principais Funcionalidades (Atuais e Planejadas)
- **Processamento de Big Data Geotécnico:** Algoritmos vetorizados para lidar com milhões de linhas de dados de sensores.
- **Cálculo de Energia Dissipada:** Implementação matemática precisa do Teorema de Shoelace (Fórmula de Gauss) para calcular a área interna dos ciclos de histerese, isolando o amortecimento puro da deformação plástica.
- **Visualização Macro:** Gráficos de tendência de evolução temporal e distribuição de frequência de energia (Histogramas/Boxplots).
- **Inspeção Microestrutural:** Gráficos interativos para sobreposição e análise detalhada dos laços de histerese (Tensão vs. Deformação) ciclo a ciclo.

## 🛠️ Tecnologias Utilizadas
- **Linguagem:** Python 3.x
- **Interface Web:** Streamlit
- **Manipulação de Dados:** Pandas, NumPy
- **Visualização Interativa:** Plotly
