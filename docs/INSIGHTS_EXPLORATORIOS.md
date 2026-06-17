# Insights exploratórios

Este documento registra os principais achados exploratórios do MVP de análise de furtos e roubos na Grande Vitória.

## Eixos analisados

- Evolução mensal das ocorrências.
- Distribuição por hora do fato.
- Distribuição por dia da semana.
- Heatmap hora × dia da semana.
- Comparação entre municípios.
- Comparação entre furto e roubo.

## Interpretação geral

A análise exploratória permite observar padrões de concentração temporal e territorial dos registros de furtos e roubos. A leitura combinada dos gráficos ajuda a identificar períodos de maior ocorrência e municípios com maior participação no total de registros.

## Como validar

Após rodar o pipeline, conferir os arquivos em `data/cache/`:

- `monthly_counts.csv`
- `hourly_profile.csv`
- `heatmap_hour_weekday.csv`
- `municipal_summary.csv`
- `crime_type_summary.csv`
