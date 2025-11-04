
# Verificador de Categoria — Web (Streamlit)

Este app web permite enviar uma planilha e verificar a coluna de categorias usando um **De/Para padrão** (`/mnt/data/depara_categorias.csv`).

## Executar localmente
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements_web.txt

streamlit run app_web_verificador.py
```

## Deploy (opções rápidas)
- **Streamlit Community Cloud**: faça upload de `app_web_verificador.py`, `requirements_web.txt` e do `depara_categorias.csv`.
- **Render/Railway/Heroku**: crie um serviço web e rode `streamlit run app_web_verificador.py --server.port $PORT --server.address 0.0.0.0`.

> Atualize o arquivo `depara_categorias.csv` sempre que mudar seu mapeamento de categorias.
