
import io
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Verificador de Categoria", page_icon="✅", layout="centered")
st.title("✅ Verificador de Categoria")
st.caption("Envie sua planilha; validamos a coluna de categorias. Se o De/Para padrão não existir, você pode subir um arquivo de De/Para abaixo.")

# --- Localização robusta do De/Para ---
APP_DIR = Path(__file__).parent
CANDIDATES = [
    APP_DIR / "depara_categorias.csv",
    APP_DIR / "data" / "depara_categorias.csv",
    Path("depara_categorias.csv"),
    Path("data") / "depara_categorias.csv",
]
DEFAULT_DEPARA_PATH = next((p for p in CANDIDATES if p.exists()), None)

with st.expander("Configuração do De/Para", expanded=False):
    st.markdown("""
    O app procura automaticamente por `depara_categorias.csv` nas seguintes localizações:
    1) mesma pasta do app  
    2) `./data/depara_categorias.csv`  
    Se não encontrar, você pode **enviar** o De/Para manualmente (CSV/Excel) abaixo.
    """)
    st.write("Arquivo padrão encontrado:" if DEFAULT_DEPARA_PATH else "Nenhum arquivo padrão encontrado.")
    if DEFAULT_DEPARA_PATH:
        st.code(str(DEFAULT_DEPARA_PATH))

# Uploader opcional de De/Para (só se não existir localmente)
depara_upload = None
if DEFAULT_DEPARA_PATH is None:
    depara_upload = st.file_uploader("De/Para (CSV ou Excel) — opcional, use se o padrão não estiver no repo", type=["csv","xlsx","xlsm","xltx","xltm","txt"], key="depara")

# Entrada do nome da coluna
coluna_categoria = st.text_input("Nome da coluna de categoria", value="Categoria")

# Upload do arquivo de dados
uploaded = st.file_uploader("Suba aqui sua planilha para verificar", type=["xlsx","xlsm","csv","txt"], accept_multiple_files=False)

def read_any(file):
    name = file.name if hasattr(file, "name") else str(file)
    if name.lower().endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        return pd.read_excel(file, dtype=str)
    else:
        try:
            return pd.read_csv(file, dtype=str)
        except Exception:
            return pd.read_csv(file, sep=";", dtype=str)

def normalize_cols(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

@st.cache_data(show_spinner=False)
def load_depara_from_path(path: Path):
    df = pd.read_csv(path, dtype=str)
    df = df.rename(columns=lambda c: str(c).strip())
    if not {"Categoria","DRE"}.issubset(set(df.columns)):
        raise ValueError("O arquivo de/para precisa ter as colunas 'Categoria' e 'DRE'.")
    df["Categoria"] = df["Categoria"].astype(str).str.strip()
    df["DRE"] = df["DRE"].astype(str).str.strip()
    return df

def load_depara_from_upload(file):
    df = read_any(file)
    df = df.rename(columns=lambda c: str(c).strip())
    # tenta mapear nomes
    origem = next((c for c in df.columns if c.lower() in ("categoria","origem","de")), df.columns[0])
    destino = next((c for c in df.columns if c.lower() in ("dre","para","destino","categoria_dre")), df.columns[-1])
    df = df[[origem, destino]].rename(columns={origem:"Categoria", destino:"DRE"})
    df["Categoria"] = df["Categoria"].astype(str).str.strip()
    df["DRE"] = df["DRE"].astype(str).str.strip()
    return df

def run_check(df_dados, df_depara, col_cat):
    df = normalize_cols(df_dados)
    if col_cat not in df.columns:
        raise ValueError(f\"Coluna '{col_cat}' não encontrada. Colunas: {list(df.columns)}\")
    df[col_cat] = df[col_cat].astype(str).str.strip()
    out = df.merge(df_depara, how="left", left_on=col_cat, right_on="Categoria")
    out["Motivo"] = out["DRE"].isna().map({True: "categoria_nao_mapeada", False: ""})
    erros = out[out["Motivo"] != ""].copy()
    return out, erros

if uploaded is not None:
    try:
        with st.spinner("Carregando De/Para e validando..."):
            # Decide a fonte do De/Para
            if DEFAULT_DEPARA_PATH is not None:
                depara_df = load_depara_from_path(DEFAULT_DEPARA_PATH)
            elif depara_upload is not None:
                depara_df = load_depara_from_upload(depara_upload)
            else:
                raise FileNotFoundError("De/Para não encontrado. Suba um arquivo de De/Para ou inclua 'depara_categorias.csv' no repo.")

            dados_df = read_any(uploaded)
            out_df, erros_df = run_check(dados_df, depara_df, coluna_categoria)

        total = len(out_df)
        invalidos = len(erros_df)
        validos = total - invalidos
        st.success(f"Concluído: Total **{total}** · Válidas **{validos}** · Não mapeadas **{invalidos}**")

        if invalidos > 0:
            st.subheader("Amostra de problemas")
            st.dataframe(erros_df.head(50), use_container_width=True)
        else:
            st.info("Nenhuma categoria não mapeada encontrada. 🎉")

        erros_csv = erros_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Baixar erros_categorias.csv", erros_csv, file_name="erros_categorias.csv", mime="text/csv")

        xbuf = io.BytesIO()
        with pd.ExcelWriter(xbuf, engine="openpyxl") as writer:
            out_df.to_excel(writer, index=False, sheet_name="VALIDADO")
        st.download_button("Baixar planilha_validada.xlsx", xbuf.getvalue(), file_name="planilha_validada.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.caption("Obs.: Arquivos .xlsm são apenas lidos; macros não são executadas nem preservadas nas saídas.")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
else:
    st.info("Selecione sua planilha (.xlsx, .xlsm, .csv) para iniciar a verificação.")
