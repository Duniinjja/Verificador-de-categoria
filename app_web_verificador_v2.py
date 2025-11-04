import io
import os
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Verificador de Categoria (Despesas/Receitas)", page_icon="🔠", layout="wide")
st.title("🔠 Verificador de Categoria")

APP_DIR = Path(__file__).parent

# --- caminhos padrão ---
CANDIDATES_DESP = [
    APP_DIR / "depara_categorias.csv",
    APP_DIR / "data" / "depara_categorias.csv",
    Path("depara_categorias.csv"),
    Path("data") / "depara_categorias.csv",
]
DEFAULT_DEPARA_DESP = next((p for p in CANDIDATES_DESP if p.exists()), None)

CANDIDATES_REC = [
    APP_DIR / "depara_receita.csv",
    APP_DIR / "data" / "depara_receita.csv",
    Path("depara_receita.csv"),
    Path("data") / "depara_receita.csv",
]
DEFAULT_DEPARA_REC = next((p for p in CANDIDATES_REC if p.exists()), None)

# ----------------- UI -----------------
tipo = st.radio("Selecione o tipo de verificação", ["Despesas", "Receitas"], horizontal=True)
coluna_padrao = "Categoria" if tipo == "Despesas" else "Produto"

with st.expander("Configuração do De/Para", expanded=False):
    if tipo == "Despesas":
        st.markdown("**De/Para (Despesas)** — esperado: `depara_categorias.csv`")
        st.code(str(DEFAULT_DEPARA_DESP) if DEFAULT_DEPARA_DESP else "Arquivo padrão não encontrado")
    else:
        st.markdown("**De/Para (Receitas)** — esperado: `depara_receita.csv`")
        st.code(str(DEFAULT_DEPARA_REC) if DEFAULT_DEPARA_REC else "Arquivo padrão não encontrado")

    # 👇 Avançado (opcional). Fica DESLIGADO por padrão.
    depara_upload = None
    if st.checkbox("Enviar De/Para customizado (avançado)", value=False):
        depara_upload = st.file_uploader(
            "De/Para (CSV/Excel) — use apenas se o arquivo padrão não estiver no repositório",
            type=["csv", "xlsx", "xlsm", "xltx", "xltm", "txt"],
            key="depara_custom"
        )
    else:
        depara_upload = None

coluna_categoria = st.text_input("Nome da coluna de categoria na planilha", value=coluna_padrao)

# ✅ ÚNICO upload visível no fluxo normal
dados_file = st.file_uploader("Suba a planilha de dados", type=["xlsx", "xlsm", "csv", "txt"], accept_multiple_files=False)

# ----------------- helpers -----------------
def read_any(file, sheet_name=None):
    name = file.name if hasattr(file, "name") else str(file)
    if name.lower().endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        return pd.read_excel(file, dtype=str, sheet_name=sheet_name)  # se None: 1ª aba
    else:
        try:
            return pd.read_csv(file, dtype=str)
        except Exception:
            return pd.read_csv(file, sep=";", dtype=str)

def load_depara_generic(file_or_path):
    """Lê De/Para com duas colunas (Categoria -> DRE). Insensível a caixa."""
    df = read_any(file_or_path)
    df = df.rename(columns=lambda c: str(c).strip())
    origem = next((c for c in df.columns if c.lower() in ("categoria","origem","de")), df.columns[0])
    destino = next((c for c in df.columns if c.lower() in ("dre","para","destino","categoria_dre")), df.columns[-1])
    df = df[[origem, destino]].rename(columns={origem: "Categoria", destino: "DRE"})
    df["Categoria"] = df["Categoria"].astype(str).str.strip()
    df["DRE"] = df["DRE"].astype(str).str.strip()
    df["chave_lower"] = df["Categoria"].str.lower()
    return df

# ----------------- processamento -----------------
if dados_file is not None:
    try:
        # 1) Seleciona De/Para conforme o tipo, priorizando arquivo padrão; upload só se usuário ativar opção avançada
        if tipo == "Despesas":
            if DEFAULT_DEPARA_DESP is not None and depara_upload is None:
                depara_df = load_depara_generic(DEFAULT_DEPARA_DESP)
            elif depara_upload is not None:
                depara_df = load_depara_generic(depara_upload)
            else:
                st.error("Faltou o De/Para de Despesas (depara_categorias.csv).")
                st.stop()
        else:  # Receitas
            if DEFAULT_DEPARA_REC is not None and depara_upload is None:
                depara_df = load_depara_generic(DEFAULT_DEPARA_REC)
            elif depara_upload is not None:
                depara_df = load_depara_generic(depara_upload)
            else:
                st.error("Faltou o De/Para de Receitas (depara_receita.csv).")
                st.stop()

        # 2) Aba padrão: 'despesa' para Despesas, 'receita' para Receitas (pode mudar no seletor)
        ext = os.path.splitext(dados_file.name)[1].lower()
        if ext in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
            xl = pd.ExcelFile(dados_file)
            abas = xl.sheet_names
            alvo = "despesa" if tipo == "Despesas" else "receita"
            default_aba = next((a for a in abas if alvo in a.lower()), abas[0])
            sheet_selected = st.selectbox("Aba a processar", abas, index=abas.index(default_aba))
            dados_df = xl.parse(sheet_selected, dtype=str)
        else:
            dados_df = read_any(dados_file)

        # 3) Normaliza e valida coluna
        dados_df.columns = [str(c).strip() for c in dados_df.columns]
        if coluna_categoria not in dados_df.columns:
            raise ValueError(f"Coluna '{coluna_categoria}' não encontrada. Colunas: {list(dados_df.columns)}")

        dados_df[coluna_categoria] = dados_df[coluna_categoria].astype(str).str.strip()
        dados_df["chave_lower"] = dados_df[coluna_categoria].str.lower()

        # 4) Merge
        out = dados_df.merge(
            depara_df[["chave_lower", "DRE", "Categoria"]],
            how="left", on="chave_lower", suffixes=("", "_map")
        )
        out["Motivo"] = out["DRE"].isna().map({True: "categoria_nao_mapeada", False: ""})
        erros = out[out["Motivo"] != ""]

        # 5) UI
        st.success(f"Verificação concluída ({tipo.lower()}): {len(out)} linhas · {len(erros)} não mapeadas.")
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
