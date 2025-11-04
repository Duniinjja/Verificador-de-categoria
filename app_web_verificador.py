
import io
from pathlib import Path
import pandas as pd
import streamlit as st

# App config
st.set_page_config(page_title="Verificador de Categoria", page_icon="✅", layout="centered")
st.title("✅ Verificador de Categoria")
st.caption("Envie sua planilha; validamos a coluna de categorias usando o De/Para padrão.")

# Caminho do De/Para padrão (Categoria -> DRE)
DEFAULT_DEPARA_PATH = Path("/mnt/data/depara_categorias.csv")

# Campo para nome da coluna de categoria
coluna_categoria = st.text_input("Nome da coluna de categoria", value="Categoria", help="Informe como a coluna aparece na sua planilha (ex.: 'Categoria').")

# Botão único de upload
uploaded = st.file_uploader("Suba aqui sua planilha para verificar", type=["xlsx","xlsm","csv","txt"], accept_multiple_files=False)

def read_any(file):
    name = file.name if hasattr(file, "name") else str(file)
    if name.lower().endswith((".xlsx", ".xlsm")):
        return pd.read_excel(file, dtype=str)
    else:
        # csv/txt
        try:
            return pd.read_csv(file, dtype=str)
        except Exception:
            return pd.read_csv(file, sep=";", dtype=str)

def normalize_cols(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

@st.cache_data(show_spinner=False)
def load_depara():
    df = pd.read_csv(DEFAULT_DEPARA_PATH, dtype=str)
    df = df.rename(columns=lambda c: str(c).strip())
    if not {"Categoria","DRE"}.issubset(set(df.columns)):
        raise ValueError("O arquivo de/para precisa ter as colunas 'Categoria' e 'DRE'.")
    df["Categoria"] = df["Categoria"].astype(str).str.strip()
    df["DRE"] = df["DRE"].astype(str).str.strip()
    return df

def run_check(df_dados, df_depara, col_cat):
    df = normalize_cols(df_dados)
    if col_cat not in df.columns:
        raise ValueError(f"Coluna '{col_cat}' não encontrada. Colunas: {list(df.columns)}")
    df[col_cat] = df[col_cat].astype(str).str.strip()
    out = df.merge(df_depara, how="left", left_on=col_cat, right_on="Categoria")
    out["Motivo"] = out["DRE"].isna().map({True: "categoria_nao_mapeada", False: ""})
    erros = out[out["Motivo"] != ""].copy()
    return out, erros

# Corpo principal: processa assim que o usuário faz upload
if uploaded is not None:
    try:
        with st.spinner("Validando categorias..."):
            depara_df = load_depara()
            dados_df = read_any(uploaded)
            out_df, erros_df = run_check(dados_df, depara_df, coluna_categoria)

        total = len(out_df)
        invalidos = len(erros_df)
        validos = total - invalidos
        st.success(f"Concluído: Total **{total}** · Válidas **{validos}** · Não mapeadas **{invalidos}**")

        # Amostra
        if invalidos > 0:
            st.subheader("Amostra de problemas")
            st.dataframe(erros_df.head(50), use_container_width=True)
        else:
            st.info("Nenhuma categoria não mapeada encontrada. 🎉")

        # Downloads
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
    st.info("Clique acima para selecionar sua planilha (.xlsx, .xlsm, .csv).")
