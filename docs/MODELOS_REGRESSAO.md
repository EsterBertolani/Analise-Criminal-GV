# Modelos de regressão

A trilha de regressão do MVP tem como objetivo prever contagens mensais de ocorrências de furtos e roubos.

## Estratégia

Os dados são agregados mensalmente e transformados em atributos temporais. A validação respeita a ordem cronológica para evitar vazamento de dados futuros.

## Métricas

- MAE: erro absoluto médio.
- RMSE: raiz do erro quadrático médio.

## Arquivos relacionados

- `src/models/regression.py`
- `src/models/train_all.py`
- `tests/test_temporal_split.py`

## Saídas esperadas

- `metrics_regression.csv`
- `predictions_regression.csv`
