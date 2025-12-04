import os
import pandas as pd
import matplotlib.pyplot as plt

PATH_CSV = "ambiental_queimadas.csv"
OUT_DIR = "saidas_ambiental"
LIMITE_ALERTA = 80
os.makedirs(OUT_DIR, exist_ok=True)

MESES_ORDEM = {
    "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4,
    "Mai": 5, "Jun": 6, "Jul": 7, "Ago": 8,
    "Set": 9, "Out": 10, "Nov": 11, "Dez": 12
}

def carregar_e_normalizar(path):
    df = pd.read_csv(path, header=0)
    print("Colunas lidas originalmente:", df.columns.tolist())
    df.columns = [c.strip() for c in df.columns.astype(str)]
    # renomear primeira coluna para 'mes' se necessário
    if df.columns[0].lower() not in ("mes", "month"):
        df = df.rename(columns={df.columns[0]: "mes"})
    # encontrar coluna de focos (qualquer nome que contenha 'foco' ou 'focos')
    foco_col = None
    for c in df.columns:
        if "foco" in c.lower():
            foco_col = c
            break
    if foco_col is None:
        # se não achou, assume a segunda coluna
        foco_col = df.columns[1]
    df = df.rename(columns={foco_col: "focos_queimada"})
    df["mes"] = df["mes"].astype(str).str.strip()
    df["focos_queimada"] = pd.to_numeric(df["focos_queimada"], errors="coerce").fillna(0).astype(int)
    df["mes_num"] = df["mes"].map(MESES_ORDEM)
    # se mapeamento deu NaN (por exemplo nomes completos), tenta primeiros 3 letras com capitalização
    if df["mes_num"].isna().any():
        df["mes_abrev"] = df["mes"].str[:3].str.capitalize()
        df["mes_num"] = df["mes_abrev"].map(MESES_ORDEM)
        df.drop(columns=["mes_abrev"], inplace=True)
    df = df.sort_values("mes_num").reset_index(drop=True)
    return df

def identificar_mes_critico(df):
    idx = df["focos_queimada"].idxmax()
    return df.loc[idx, "mes"], int(df.loc[idx, "focos_queimada"])

def aplicar_alertas(df):
    df = df.copy()
    df["alerta"] = df["focos_queimada"].apply(lambda x: "ALERTA" if x > LIMITE_ALERTA else "-")
    return df

def gerar_grafico(df):
    plt.figure(figsize=(10,4))
    plt.plot(df["mes"], df["focos_queimada"], marker="o")
    for i, row in df.iterrows():
        if row["alerta"] == "ALERTA":
            plt.scatter(row["mes"], row["focos_queimada"], s=80, facecolors='none', edgecolors='r', linewidths=1.5)
    plt.title("Sazonalidade de Queimadas")
    plt.xlabel("Mês")
    plt.ylabel("Focos")
    plt.grid(True, linestyle=":")
    caminho = os.path.join(OUT_DIR, "grafico_queimadas.png")
    plt.savefig(caminho, bbox_inches="tight")
    plt.close()
    return caminho

def salvar_relatorio(df, mes_crit, focos_crit):
    caminho = os.path.join(OUT_DIR, "relatorio_ambiental.txt")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("Relatório – Análise Sazonal de Queimadas\n")
        f.write("----------------------------------------\n\n")
        f.write(f"Mês com mais focos: {mes_crit} ({focos_crit} focos)\n\n")
        f.write(f"Patamar de alerta: > {LIMITE_ALERTA} focos\n\n")
        f.write("Meses acima do patamar:\n")
        alertas = df[df["alerta"] == "ALERTA"]
        if alertas.empty:
            f.write("Nenhum mês ultrapassou o limite.\n")
        else:
            for _, row in alertas.iterrows():
                f.write(f"- {row['mes']}: {int(row['focos_queimada'])} focos\n")
    return caminho

def run(path_csv=PATH_CSV):
    df = carregar_e_normalizar(path_csv)
    mes_crit, focos_crit = identificar_mes_critico(df)
    df_alertas = aplicar_alertas(df)
    img_path = gerar_grafico(df_alertas)
    rel_path = salvar_relatorio(df_alertas, mes_crit, focos_crit)
    out_csv = os.path.join(OUT_DIR, "dados_processados.csv")
    df_alertas.to_csv(out_csv, index=False)
    print("Processamento concluído.")
    print("Mês crítico:", mes_crit, "-", focos_crit)
    print("Gráfico salvo em:", img_path)
    print("Relatório salvo em:", rel_path)
    print("CSV processado salvo em:", out_csv)

if __name__ == "__main__":
    run()
