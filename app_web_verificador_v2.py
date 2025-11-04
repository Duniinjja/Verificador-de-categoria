import io
import os
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Verificador de Categoria (case-insensitive)", page_icon="🔠", layout="wide")
st.title("🔠 Verificador de Categoria")

APP_DIR = Path(__file__).parent
CANDIDATES = [
    APP_DIR / "depara_categorias.csv",
    APP_DIR / "data" / "depara_categorias.csv",
    Path("depara_categorias.csv"),
    Path("data") / "depara_categorias.csv",
]
DEFAULT_DEPARA_PATH = next((p for p in CANDIDATES if p.exists()), None)

# --- Upload do de/para ---
with st.expander("Configuração do De/Para", expanded=False):
    st.markdown("O app procura `depara_categorias.csv` na mesma pasta ou em `./data/`.")
    if DEFAULT_DEPARA_PATH:
        st.code(str(DEFAULT_DEPARA_PATH))
    else:
        st.warning("Nenhum arquivo padrão encontrado. Envie um De/Para abaixo.")

depara_upload = None
if DEFAULT_DEPARA_PATH is None:
    depara_upload = st.file_uploader("De/Para (CSV ou Excel)", type=["csv","xlsx","xlsm","xltx","xltm","txt"], key="depara")

coluna_categoria = st.text_input("Nome da coluna de categoria", value="Categoria")
dados_file = st.file_uploader("Suba a planilha de dados", type=["xlsx","xlsm","csv","txt"], accept_multiple_files=False)

# --- leitura genérica com suporte a 'sheet_name' ---
def read_any(file, sheet_name=None):
    name = file.name if hasattr(file, "name") else str(file)
    if name.lower().endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        return pd.read_excel(file, dtype=str, sheet_name=sheet_name)  # se None, lê a 1ª aba
    else:
        try:
            return pd.read_csv(file, dtype=str)
        except Exception:
            return pd.read_csv(file, sep=";", dtype=str)

def load_depara(file_or_path):
    df = read_any(file_or_path)
    df = df.rename(columns=lambda c: str(c).strip())
    origem = next((c for c in df.columns if c.lower() in ("categoria","origem","de")), df.columns[0])
    destino = next((c for c in df.columns if c.lower() in ("dre","para","destino","categoria_dre")), df.columns[-1])
    df = df[[origem, destino]].rename(columns={origem:"Categoria", destino:"DRE"})
    df["Categoria"] = df["Categoria"].astype(str).str.strip()
    df["DRE"] = df["DRE"].astype(str).str.strip()
    df["chave_lower"] = df["Categoria"].str.lower()
    return df

if dados_file is not None:
    try:
        # carregar de/para
        if DEFAULT_DEPARA_PATH:
            depara_df = load_depara(DEFAULT_DEPARA_PATH)
        elif depara_upload:
            depara_df = load_depara(depara_upload)
        else:
            st.error("Faltou o De/Para. Envie um arquivo de/para ou inclua 'depara_categorias.csv'.")
            st.stop()

        # --- escolher a aba (prioriza 'despesa') se for Excel ---
        ext = os.path.splitext(dados_file.name)[1].lower()
        if ext in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
            xl = pd.ExcelFile(dados_file)
            abas = xl.sheet_names
            # padrão: primeira aba que contenha 'despesa' no nome; senão a 1ª
            default_aba = next((a for a in abas if "despesa" in a.lower()), abas[0])
            sheet_selected = st.selectbox("Aba a processar", abas, index=abas.index(default_aba))
            dados_df = xl.parse(sheet_selected, dtype=str)
        else:
            # CSV/TXT
            dados_df = read_any(dados_file)

        dados_df.columns = [str(c).strip() for c in dados_df.columns]
        if coluna_categoria not in dados_df.columns:
            raise ValueError(f"Coluna '{coluna_categoria}' não encontrada. Colunas: {list(dados_df.columns)}")

        dados_df[coluna_categoria] = dados_df[coluna_categoria].astype(str).str.strip()
        dados_df["chave_lower"] = dados_df[coluna_categoria].str.lower()

        out = dados_df.merge(
            depara_df[["chave_lower","DRE","Categoria"]],
            how="left", on="chave_lower", suffixes=("", "_map")
        )
        out["Motivo"] = out["DRE"].isna().map({True: "categoria_nao_mapeada", False: ""})
        erros = out[out["Motivo"]!=""]

        st.success(f"Verificação concluída: {len(out)} linhas · {len(erros)} não mapeadas.")
        st.dataframe(erros.head(100), use_container_width=True)

        erros_csv = erros.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Baixar erros_categorias.csv", erros_csv, "erros_categorias.csv")

        xbuf = io.BytesIO()
        with pd.ExcelWriter(xbuf, engine="openpyxl") as writer:
            out.to_excel(writer, index=False, sheet_name="VALIDADO")
        st.download_button("Baixar planilha_validada.xlsx", xbuf.getvalue(), "planilha_validada.xlsx")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
else:
    st.info("Envie a planilha (.xlsx, .xlsm, .csv) para iniciar.")
