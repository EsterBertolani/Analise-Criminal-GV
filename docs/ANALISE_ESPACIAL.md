# Análise espacial

A camada espacial do MVP compara os municípios da Grande Vitória a partir das ocorrências registradas, da população de referência e de uma matriz de vizinhança simplificada.

## Indicadores

- Total de ocorrências por município.
- População de referência.
- Taxa acumulada por 100 mil habitantes.
- LISA aproximado por vizinhança municipal.

## Arquivos externos

- `data/external/populacao_municipios_gv.csv`
- `data/external/vizinhanca_municipios_gv.csv`

## Observação metodológica

Quando não há GeoJSON municipal oficial disponível, o projeto usa uma vizinhança manual simplificada como alternativa para gerar uma leitura espacial preliminar. Essa abordagem é adequada para MVP, mas pode ser refinada futuramente com malhas geográficas oficiais.
