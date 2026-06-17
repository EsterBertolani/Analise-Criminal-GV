# Fontes externas adicionadas

## População municipal

Arquivo: `populacao_municipios_gv.csv`

Contém a população estimada de 2025 dos municípios da Grande Vitória, consultada no IBGE Cidades e Estados. Para o MVP, o mesmo valor de referência foi replicado de 2021 a 2026, permitindo calcular taxas comparativas por 100 mil habitantes no recorte completo.

## Vizinhança municipal

Arquivo: `vizinhanca_municipios_gv.csv`

Lista de adjacências municipais usada como alternativa leve ao GeoJSON para calcular LISA aproximado/local sem depender de `geopandas`, `libpysal` e `esda`. Se você adicionar `municipios_gv.geojson`, o pipeline prioriza o cálculo espacial com GeoJSON e PySAL.
