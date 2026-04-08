import pandas as pd
import numpy as np
import os

print("Iniciando o processamento dos ensaios de Módulo Resiliente...")

# ==========================================
# CONFIGURAÇÕES E CONSTANTES
# ==========================================
ARQUIVOS = [
    "MR ASIC 11-08-21.csv",
    "MR_AB25_inst_top_base 22-10-21.csv",
    "MR_AB5_inst_top_base 14-10-21.csv",
]

PROCEDIMENTOS = [
    1,
    3,
    5,
    7,
    10,
    12,
    14,
    16,
    18,
    21,
    23,
    25,
    27,
    29,
    32,
    34,
    36,
    38,
    40,
    43,
    45,
    47,
    49,
    51,
    54,
    56,
    58,
    60,
    62,
]

DIST_ANCORAS = 255.0
AREA = (np.pi * (0.15**2)) / 4.0


def calcular_area_shoelace(grupo):
    """Calcula a Energia Dissipada (Área exata do Laço de Histerese fechado)"""
    x = grupo["ea"].values
    y = grupo["q"].values
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


# ==========================================
# LOOP DE PROCESSAMENTO
# ==========================================
for file in ARQUIVOS:
    if not os.path.exists(file):
        print(f"Arquivo {file} não encontrado na pasta. Pulando...")
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
            col_ciclos: "ciclos",
        }
    )

    # ==========================================
    # 3. GERAÇÃO DINÂMICA DA COLUNA 'PROC'
    # ==========================================
    df_raw["step"] = df_raw["ciclos"].diff().fillna(0).lt(0).cumsum()

    step_sizes = df_raw.groupby("step").size()
    is_conditioning = step_sizes > 5000

    valid_procs = PROCEDIMENTOS[:24]
    valid_steps = step_sizes[~is_conditioning].index

    step_to_proc = {
        step: valid_procs[i]
        for i, step in enumerate(valid_steps)
        if i < len(valid_procs)
    }
    df_raw["proc"] = df_raw["step"].map(step_to_proc).fillna(-1)
    df_raw = df_raw[df_raw["proc"] != -1].copy()

    # ==========================================
    # 4. PROCESSAMENTO FÍSICO POR DEGRAU
    # ==========================================
    dados_finais = []

    for p in valid_procs:
        tabela = df_raw[df_raw["proc"] == p].copy()

        if len(tabela) == 0:
            continue

        proc_ciclos = tabela[(tabela["ciclos"] > 1) & (tabela["ciclos"] < 99)].copy()
        proc_ciclos["Procedimento"] = p

        proc_ciclos["deformacao_1"] = proc_ciclos["axial_velho"] / DIST_ANCORAS
        proc_ciclos["deformacao_2"] = proc_ciclos["rdp132091"] / DIST_ANCORAS
        proc_ciclos["deformacao_3"] = proc_ciclos["rdp132089"] / DIST_ANCORAS
        proc_ciclos["ea"] = (
            proc_ciclos["deformacao_1"]
            + proc_ciclos["deformacao_2"]
            + proc_ciclos["deformacao_3"]
        ) / 3.0
        proc_ciclos["q"] = proc_ciclos["forca"] / AREA

        energia_por_ciclo = (
            proc_ciclos.groupby("ciclos")
            .apply(calcular_area_shoelace, include_groups=False)
            .reset_index(name="Area_Energia_Dissipada")
        )

        proc_ciclos = proc_ciclos.merge(energia_por_ciclo, on="ciclos", how="left")

        df_export = proc_ciclos[
            ["Procedimento", "ciclos", "ea", "q", "Area_Energia_Dissipada"]
        ].copy()
        df_export = df_export.rename(columns={"ciclos": "Ciclo"})

        dados_finais.append(df_export)

    # ==========================================
    # 5. EXPORTAÇÃO
    # ==========================================
    if dados_finais:
        df_final = pd.concat(dados_finais, ignore_index=True)
        nome_saida = file.replace(".csv", "_PROCESSADO.parquet")
        df_final.to_parquet(nome_saida, index=False)
        print(f"Salvo com sucesso: {nome_saida}")
        print(f"     -> Processadas {len(df_final)} linhas puras e alinhadas.")

print("\nProcessamento concluído!")
