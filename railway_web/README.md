# Railway Web App

Camada web separada para rodar o experimento online usando o toolkit da raiz.

## Rodar localmente

Na raiz do repositório:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sua-chave"
export EXPERIMENT_WEB_TOKEN="uma-senha-para-a-interface"
python3 -m uvicorn railway_web.app:app --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000`.

## Deploy no Railway

1. Crie um projeto no Railway a partir do GitHub.
2. Selecione este repositório.
3. Em `Variables`, adicione `ANTHROPIC_API_KEY` ou outra chave usada pelo modelo.
4. Adicione `EXPERIMENT_WEB_TOKEN` para proteger a execução de jobs.
5. O `railway.json` da raiz usa:

```bash
uvicorn railway_web.app:app --host 0.0.0.0 --port $PORT
```

O app salva CSVs temporários em `railway_web/web_results/`.
