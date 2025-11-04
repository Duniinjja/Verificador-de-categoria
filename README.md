
# ✅ Verificador de Categoria

Um app simples em **Streamlit** que valida categorias de planilhas financeiras ou administrativas com base em um arquivo **De/Para**.

## ⚙️ Funcionalidades
- Upload de planilhas `.xlsx`, `.xlsm` ou `.csv`;
- Ignora diferenças entre **maiúsculas e minúsculas**;
- Identifica categorias não mapeadas;
- Permite baixar resultados e erros.

## 🧩 Como usar
1. Faça upload da planilha (ex: DRE, despesas etc);
2. Informe o nome da coluna de categoria (ex: `Categoria`);
3. Suba o arquivo de De/Para (`depara_categorias.csv`) ou use o padrão;
4. Veja instantaneamente as inconsistências e baixe o relatório.

## 📦 Requisitos
```bash
pip install -r requirements.txt
```

## ▶️ Rodando localmente
```bash
streamlit run app_web_verificador_v4.py
```

## 🌐 Deploy
Você pode publicar gratuitamente no [Streamlit Cloud](https://share.streamlit.io):
1. Faça login com seu GitHub.
2. Clique em **New app**.
3. Escolha este repositório.
4. Arquivo principal: `app_web_verificador_v4.py`.
5. Deploy 🚀

## 🧑‍💻 Autor
Desenvolvido por **Duniinjja** — projeto pessoal para automatizar conferências de categorias.
