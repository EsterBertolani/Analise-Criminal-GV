# Dicionário de dados — camada tratada

## `ocorrencias_tratadas.csv`

| Coluna | Tipo esperado | Descrição |
|---|---:|---|
| `id_evento` | texto | Identificador da ocorrência. Se não existir na origem, é criado por índice. |
| `data_fato` | data/hora | Data do fato convertida com parsing robusto. |
| `hora` | número | Hora inteira entre 0 e 23. Ausente quando inválida/indeterminada. |
| `municipio` | texto | Município padronizado em caixa alta e sem acentos. |
| `bairro` | texto | Bairro padronizado. Quando ausente, recebe `NÃO INFORMADO`. |
| `tipo_crime_original` | texto | Valor original da coluna de natureza/tipo de crime. |
| `categoria_crime` | texto | Categoria final: `Furto` ou `Roubo`. |
| `tipo_local` | texto | Tipo de local/ambiente da ocorrência, quando disponível. |
| `ano` | inteiro | Ano do fato. |
| `mes` | inteiro | Mês do fato. |
| `dia` | inteiro | Dia do mês. |
| `ano_mes` | texto | Período mensal no formato `YYYY-MM`. |
| `dia_semana_num` | inteiro | Dia da semana, 0 = segunda e 6 = domingo. |
| `dia_semana` | texto | Nome do dia da semana. |
| `faixa_horaria` | texto | Madrugada, manhã, tarde, noite ou indeterminado. |
| `data_hora` | data/hora | Combinação aproximada de data e hora para ordenação. |
| `populacao` | número | População municipal anual, se arquivo externo for preenchido. |
| `taxa_100k_evento` | número | Peso unitário por população para cálculos de taxa. |

## `pesos_aoristicos.csv`

| Coluna | Tipo esperado | Descrição |
|---|---:|---|
| `id_evento` | texto | Identificador da ocorrência. |
| `hora_aoristica` | inteiro | Hora possível para a ocorrência. |
| `peso_aoristico` | número | Peso atribuído àquela hora. Soma 1 por ocorrência. |

## `monthly_counts.csv`

| Coluna | Descrição |
|---|---|
| `ano_mes` | Mês de referência. |
| `municipio` | Município. |
| `categoria_crime` | Furto ou roubo. |
| `ocorrencias` | Quantidade de ocorrências no mês. |
| `populacao` | População usada para normalização. |
| `data_mes` | Primeiro dia do mês. |
| `taxa_100k` | Ocorrências por 100 mil habitantes. |

## `predictions_regression.csv`

Contém valores reais e previsões dos modelos de regressão para o período de teste temporal.

## `predictions_classification.csv`

Contém valores reais, classe prevista e probabilidade de alto risco por modelo.
