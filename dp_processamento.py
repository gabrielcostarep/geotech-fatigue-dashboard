import pandas as pd
import numpy as np
import os

# ==========================================
# 1. CONFIGURAÇÕES E CONSTANTES
# ==========================================

ARQUIVOS = [
    "DP_I_p20_q50_ASIC_24_02_22.csv",
    "DP_I_p20_q50_AB25_29-12-21.csv",
    "DP_I p_20kPa_q50_AB5_15-11-21.csv",
]

DIST_ANCORAS = 255.0
AREA = (np.pi * (0.15**2)) / 4.0


def calcular_area_shoelace(grupo):
    """Calcula a Energia Dissipada (Amortecimento) via Teorema de Shoelace"""
    x = grupo["ea"].values
    y = grupo["q"].values
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


# ==========================================
# 2. LOOP DE PROCESSAMENTO
# ==========================================
for file in ARQUIVOS:
    if not os.path.exists(file):
        print(f"Arquivo {file} não encontrado. Verifique o nome.")
        continue

    print(f"\nExtraindo e calculando: {file}")

    linha_cabecalho = 0
    with open(file, "r", encoding="latin1") as f:
        for i, linha in enumerate(f):
            if "number of cycles" in linha.lower():
                linha_cabecalho = i
                break

    df_raw = pd.read_csv(
        file, delimiter=";", decimal=",", encoding="latin1", skiprows=linha_cabecalho
    )
    df_raw.columns = df_raw.columns.str.strip()
    colunas_originais = df_raw.columns.tolist()

    col_forca = [
        c for c in colunas_originais if "for" in c.lower() and "axial" in c.lower()
    ][0]
    col_lvdt = [c for c in colunas_originais if "lvdt" in c.lower()][0]
    col_rdp1 = [c for c in colunas_originais if "132091" in c.lower()][0]
    col_rdp2 = [c for c in colunas_originais if "132089" in c.lower()][0]
    col_ciclos = [c for c in colunas_originais if "number of cycles" in c.lower()][0]

    df_raw = df_raw.rename(
        columns={
            col_forca: "forca",
            col_lvdt: "axial_velho",
            col_rdp1: "rdp132091",
            col_rdp2: "rdp132089",
            col_ciclos: "Ciclo",
        }
    )

    # Remover ciclo 0 (fase de estabilização do pistão)
    df_raw = df_raw[df_raw["Ciclo"] > 0].copy()

    df_raw["deformacao_1"] = df_raw["axial_velho"] / DIST_ANCORAS
    df_raw["deformacao_2"] = df_raw["rdp132091"] / DIST_ANCORAS
    df_raw["deformacao_3"] = df_raw["rdp132089"] / DIST_ANCORAS
    df_raw["ea"] = (
        df_raw["deformacao_1"] + df_raw["deformacao_2"] + df_raw["deformacao_3"]
    ) / 3.0
    df_raw["q"] = df_raw["forca"] / AREA

    energia_por_ciclo = (
        df_raw.groupby("Ciclo")
        .apply(calcular_area_shoelace, include_groups=False)
        .reset_index(name="Area_Energia_Dissipada")
    )

    df_export = df_raw.merge(energia_por_ciclo, on="Ciclo", how="left")

    df_export = df_export[["Ciclo", "ea", "q", "Area_Energia_Dissipada"]]

    # ==========================================
    # 3. EXPORTAÇÃO INDIVIDUAL (PARQUET)
    # ==========================================
    nome_saida = file.replace(".csv", "_PROCESSADO.parquet")
    df_export.to_parquet(nome_saida, index=False)

    print(f"Salvo com sucesso: {nome_saida}")
