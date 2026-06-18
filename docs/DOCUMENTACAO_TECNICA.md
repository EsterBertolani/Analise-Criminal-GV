# Documentação técnica — MVP Criminalidade GV

## Visão geral

O projeto integra ETL, análise exploratória, modelagem preditiva, análise espacial e dashboard Streamlit para análise de furtos e roubos na Grande Vitória.

## Execução

```bash
python scripts/run_pipeline.py --csv data/raw/MICRODADOS_OCORRENCIAS.csv
python -m streamlit run app/streamlit_app.py
```

## Camadas

1. Dados brutos em `data/raw/`.
2. Processamento em `src/data/`.
3. Features em `src/features/`.
4. Análises em `src/analysis/`.
5. Modelos em `src/models/`.
6. Cache em `src/cache/`.
7. Interface em `app/`.

## Cache

O dashboard lê arquivos pré-computados em `data/cache/`, evitando reprocessamento durante a navegação.
