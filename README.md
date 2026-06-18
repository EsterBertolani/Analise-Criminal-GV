# Análise Preditiva de Furtos e Roubos na Grande Vitória

MVP final do Projeto Integrador III em Ciência de Dados, desenvolvido para analisar crimes contra o patrimônio — furtos e roubos — nos municípios da Grande Vitória, no Espírito Santo.

A aplicação integra **ETL**, **análise exploratória**, **modelagem preditiva**, **análise espacial** e um **dashboard interativo em Streamlit**, utilizando dados públicos de ocorrências criminais e informações populacionais/geográficas auxiliares.

---

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Objetivo](#objetivo)
- [Municípios analisados](#municípios-analisados)
- [Fontes de dados](#fontes-de-dados)
- [Arquitetura do projeto](#arquitetura-do-projeto)
- [Funcionalidades do MVP](#funcionalidades-do-mvp)
- [Pipeline de dados](#pipeline-de-dados)
- [Modelos preditivos](#modelos-preditivos)
- [Dashboard Streamlit](#dashboard-streamlit)
- [Como executar o projeto](#como-executar-o-projeto)
- [Estratégia de cache](#estratégia-de-cache)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Resultados principais](#resultados-principais)
- [Limitações metodológicas](#limitações-metodológicas)
- [Próximos passos](#próximos-passos)
- [Equipe](#equipe)

---

## Sobre o projeto

Este projeto tem como tema a **análise preditiva de crimes contra o patrimônio na Grande Vitória**, com foco em furtos e roubos registrados entre **março de 2021 e abril de 2026**.

A proposta é transformar registros públicos de segurança em um produto analítico capaz de apoiar a leitura de padrões criminais, principalmente em três dimensões:

1. **Temporal**: evolução mensal, horários de maior incidência, dias da semana e sazonalidade.
2. **Espacial**: distribuição por município, taxas por 100 mil habitantes e análise de autocorrelação espacial.
3. **Preditiva**: previsão de contagens mensais e identificação de municípios em situação de maior risco.

O MVP final foi desenvolvido em Python e disponibilizado por meio de uma aplicação interativa em Streamlit.

---

## Objetivo

O objetivo principal é construir uma solução de ciência de dados que permita:

- analisar a evolução de furtos e roubos na Grande Vitória;
- identificar municípios com maior concentração de ocorrências;
- comparar municípios por contagens absolutas e taxas populacionais;
- observar padrões temporais por mês, dia da semana e hora do fato;
- aplicar modelos preditivos para apoiar a tomada de decisão;
- apresentar os resultados em um painel interativo, acessível e reprodutível.

---

## Municípios analisados

O recorte espacial considera os sete municípios da Grande Vitória:

- Cariacica
- Fundão
- Guarapari
- Serra
- Viana
- Vila Velha
- Vitória

---

## Fontes de dados

### Dados principais

A base principal utilizada é composta por microdados públicos de ocorrências de crimes contra o patrimônio, disponibilizados pela Secretaria de Estado da Segurança Pública e Defesa Social do Espírito Santo (SESP-ES).

O arquivo bruto esperado pelo pipeline deve estar em:

```text
data/raw/MICRODADOS_OCORRENCIAS.csv
```

Por questões de tamanho e reprodutibilidade, o arquivo bruto real não deve ser versionado diretamente no GitHub. O projeto mantém a estrutura preparada para que o usuário baixe a base oficial e a coloque na pasta `data/raw`.

### Dados auxiliares

Também são utilizados arquivos auxiliares em `data/external`:

```text
data/external/populacao_municipios_gv.csv
data/external/vizinhanca_municipios_gv.csv
```

Esses arquivos permitem calcular:

- população de referência por município;
- taxa acumulada por 100 mil habitantes;
- vizinhança municipal simplificada para cálculo de LISA quando não houver GeoJSON disponível.

---

## Arquitetura do projeto

O projeto foi organizado em camadas para separar responsabilidades:

1. **Camada de dados brutos**  
   Armazena arquivos originais baixados da fonte pública.

2. **Camada de ETL**  
   Faz leitura, padronização, filtros, tratamento de datas, tratamento de horários e geração de variáveis.

3. **Camada exploratória**  
   Gera agregações temporais, espaciais e estatísticas descritivas.

4. **Camada de modelagem**  
   Treina modelos de regressão e classificação com validação temporal.

5. **Camada de cache**  
   Salva arquivos pré-computados para consumo rápido pelo Streamlit.

6. **Camada de apresentação**  
   Dashboard Streamlit com KPIs, gráficos, tabelas, filtros e interpretação dos resultados.

---

## Funcionalidades do MVP

O MVP inclui:

- leitura de microdados reais;
- filtro para municípios da Grande Vitória;
- filtro para furtos e roubos;
- padronização de datas e horários;
- tratamento de registros com horário incompleto;
- agregações temporais;
- histogramas horários;
- heatmap de hora por dia da semana;
- ranking de municípios por ocorrências;
- cálculo de taxa por 100 mil habitantes;
- cálculo aproximado de LISA com matriz de vizinhança municipal;
- modelos de regressão para previsão de contagens;
- modelos de classificação para identificação de alto risco;
- validação temporal sem embaralhar os dados;
- cache de resultados para carregamento rápido;
- dashboard interativo em Streamlit.

---

## Pipeline de dados

O pipeline principal é executado pelo script:

```bash
python scripts/run_pipeline.py --csv data/raw/MICRODADOS_OCORRENCIAS.csv
```

Ele realiza as seguintes etapas:

```text
[1/5] ETL
[2/5] Agregações exploratórias
[3/5] Saídas espaciais
[4/5] Modelos preditivos com validação temporal
[5/5] Cache do dashboard
```

### Etapa 1 — ETL

A etapa de ETL faz:

- leitura do CSV bruto;
- detecção das principais colunas;
- padronização dos nomes dos municípios;
- padronização dos tipos de crime;
- conversão de datas;
- conversão de horários;
- criação de variáveis derivadas;
- filtro por período;
- filtro por municípios da Grande Vitória;
- filtro por furtos e roubos;
- geração do arquivo de qualidade dos dados.

O diagnóstico é salvo em:

```text
data/processed/qualidade_dados.json
```

### Etapa 2 — Agregações exploratórias

São geradas tabelas para:

- ocorrências por mês;
- ocorrências por município;
- ocorrências por tipo de crime;
- ocorrências por hora;
- matriz de hora por dia da semana;
- evolução temporal por município.

### Etapa 3 — Saídas espaciais

A etapa espacial calcula:

- total de ocorrências por município;
- população de referência;
- taxa acumulada por 100 mil habitantes;
- indicador LISA aproximado;
- classificação de clusters espaciais quando possível.

### Etapa 4 — Modelos preditivos

O pipeline treina e avalia modelos de regressão e classificação, respeitando a ordem cronológica dos dados.

### Etapa 5 — Cache

A última etapa copia e organiza os arquivos necessários para o painel Streamlit em:

```text
data/cache/
```

O objetivo é evitar que o dashboard recalcule ETL, agregações e modelos a cada execução.

---

## Modelos preditivos

O projeto possui duas frentes de modelagem.

### 1. Regressão

Objetivo: prever a quantidade mensal de ocorrências.

Modelos previstos ou utilizados:

- baseline temporal;
- regressão baseada em atributos temporais;
- modelos baseados em árvores/ensemble quando disponíveis.

Métricas:

- MAE;
- RMSE.

A validação é temporal, ou seja, o modelo é treinado com meses anteriores e testado em meses posteriores.

### 2. Classificação

Objetivo: identificar municípios-mês classificados como alto risco.

A variável alvo é construída a partir da taxa/contagem mensal, classificando como alto risco os registros acima de um determinado limiar estatístico.

Modelos previstos ou utilizados:

- regressão logística;
- árvore de decisão;
- random forest;
- gradient boosting, quando disponível.

Métricas:

- Precision;
- Recall;
- F1-score;
- AUC.

Assim como na regressão, a validação respeita a ordem temporal para evitar vazamento de dados futuros no treinamento.

---

## Dashboard Streamlit

A aplicação interativa está em:

```text
app/streamlit_app.py
```

Para executar:

```bash
python -m streamlit run app/streamlit_app.py
```

O painel possui as seguintes abas:

### Visão geral

Apresenta os principais KPIs do projeto:

- total de ocorrências;
- período analisado;
- municípios incluídos;
- tipos de crime;
- gráficos gerais de distribuição.

### Temporal

Apresenta análises de tempo:

- evolução mensal;
- distribuição por hora;
- heatmap de hora por dia da semana;
- comparação temporal entre municípios.

### Espacial

Apresenta análises territoriais:

- ranking por município;
- taxa por 100 mil habitantes;
- tabela de autocorrelação espacial/LISA;
- comparação entre municípios.

### Modelos

Apresenta os resultados dos modelos:

- métricas de regressão;
- métricas de classificação;
- previsões;
- tabela de importância de variáveis, quando disponível.

### Documentação

Resume metodologia, limitações, fontes e interpretação dos resultados.

---

## Como executar o projeto

### 1. Clonar ou baixar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd mvp_criminalidade_gv
```

Ou baixar o projeto em ZIP e extrair a pasta.

### 2. Criar ambiente virtual

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se houver erro de permissão no PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

Versão recomendada para execução do MVP:

```bash
pip install -r requirements-lite.txt
```

Versão completa, com bibliotecas geoespaciais adicionais:

```bash
pip install -r requirements.txt
```

### 4. Adicionar os dados reais

Coloque o CSV oficial em:

```text
data/raw/MICRODADOS_OCORRENCIAS.csv
```

### 5. Rodar o pipeline

```bash
python scripts/run_pipeline.py --csv data/raw/MICRODADOS_OCORRENCIAS.csv
```

Ao final, o terminal deve mostrar algo semelhante a:

```text
[1/5] ETL
[2/5] Agregações exploratórias
[3/5] Saídas espaciais
[4/5] Modelos preditivos com validação temporal
[5/5] Cache do dashboard
Cache gerado com arquivos. Ausentes: []
```

### 6. Abrir o dashboard

```bash
python -m streamlit run app/streamlit_app.py
```

A aplicação será aberta no navegador.

---

## Estratégia de cache

O Streamlit não executa o pipeline nem treina modelos durante a navegação.

Em vez disso, a aplicação lê arquivos pré-computados em:

```text
data/cache/
```

Essa estratégia melhora a performance porque:

- evita reprocessar milhares de linhas a cada reload;
- evita retreinar modelos durante a apresentação;
- reduz risco de travamentos;
- permite que o dashboard carregue rapidamente;
- separa processamento pesado da camada visual.

Quando os dados forem atualizados, basta executar novamente:

```bash
python scripts/run_pipeline.py --csv data/raw/MICRODADOS_OCORRENCIAS.csv
```

---

## Estrutura de pastas

```text
mvp_criminalidade_gv/
├── app/
│   └── streamlit_app.py
├── configs/
│   └── settings.yaml
├── data/
│   ├── raw/
│   │   └── MICRODADOS_OCORRENCIAS.csv
│   ├── processed/
│   ├── cache/
│   └── external/
│       ├── populacao_municipios_gv.csv
│       └── vizinhanca_municipios_gv.csv
├── docs/
│   ├── ARQUITETURA.md
│   ├── DICIONARIO_DADOS.md
│   └── ROTEIRO_VIDEO.md
├── notebooks/
├── scripts/
│   ├── generate_demo_data.py
│   ├── run_pipeline.py
│   └── build_cache.py
├── src/
│   ├── analysis/
│   ├── cache/
│   ├── data/
│   ├── features/
│   └── models/
├── tests/
├── .gitignore
├── README.md
├── requirements.txt
└── requirements-lite.txt
```

---

## Resultados principais

Com a base real processada no MVP, o pipeline filtrou **120.696 ocorrências** de furtos e roubos na Grande Vitória entre **março de 2021 e abril de 2026**.

Distribuição por município:

| Município | Ocorrências |
|---|---:|
| Serra | 33.320 |
| Vila Velha | 28.833 |
| Vitória | 26.135 |
| Cariacica | 24.465 |
| Guarapari | 4.987 |
| Viana | 2.229 |
| Fundão | 727 |

Esses valores mostram maior concentração absoluta de registros nos municípios mais populosos e urbanizados da região, reforçando a importância de combinar contagens absolutas com taxas por 100 mil habitantes.

---

## Limitações metodológicas

Algumas limitações devem ser consideradas na interpretação dos resultados:

1. **Subnotificação**  
   Os dados representam crimes registrados oficialmente, não necessariamente a totalidade dos crimes ocorridos.

2. **Qualidade do preenchimento**  
   Campos como horário, bairro e tipo de local podem apresentar ausências ou inconsistências.

3. **Taxa populacional acumulada**  
   A taxa por 100 mil habitantes usa população municipal de referência, servindo como aproximação comparativa para o período analisado.

4. **LISA simplificado**  
   Quando não há GeoJSON oficial disponível, a autocorrelação espacial é calculada por uma matriz simplificada de vizinhança municipal.

5. **Modelagem preditiva**  
   Os modelos indicam padrões estatísticos observados nos dados históricos, mas não explicam causalidade e não devem ser usados isoladamente para decisões operacionais sensíveis.

---

## Próximos passos

Possíveis melhorias futuras:

- integrar GeoJSON oficial dos municípios da Grande Vitória;
- usar população anual por município para taxas ano a ano;
- incorporar feriados e eventos sazonais como variáveis exógenas;
- ampliar análise por bairro;
- incluir mapas coropléticos;
- melhorar interpretação dos modelos com SHAP ou permutation importance;
- automatizar atualização periódica do pipeline;
- publicar o dashboard em ambiente cloud.

---

## Impacto social

O projeto busca apoiar a compreensão de padrões de criminalidade patrimonial na Grande Vitória, contribuindo para:

- planejamento de políticas públicas;
- alocação mais eficiente de recursos;
- identificação de períodos e regiões críticas;
- comunicação de dados de segurança de forma acessível;
- fortalecimento do uso de dados abertos em problemas urbanos reais.

A proposta não substitui análises oficiais de segurança pública, mas oferece uma camada exploratória e preditiva que pode apoiar discussões sobre prevenção, planejamento urbano e transparência.

---

## Equipe

Projeto desenvolvido para a disciplina de Projeto Integrador III — Ciência de Dados.

Integrantes:

- Alexsander Amorim Borchardt
- Ester da Silva Bertolani
- Larissa Moraes de Jesus
- Lucas Gonçalves Rufino de Souza
- Marcelo Henrique Fortaleza Mindas
- Vanderson de Almeida Alves

---

## Tecnologias utilizadas

- Python
- pandas
- numpy
- scikit-learn
- statsmodels
- plotly
- streamlit
- geopandas
- PySAL
- joblib
- pyyaml

---

## Observação sobre versionamento de dados

Arquivos muito grandes, como o microdado bruto oficial, devem permanecer fora do GitHub.

A pasta `data/raw` mantém apenas a estrutura do projeto. Para reproduzir a análise, o usuário deve baixar a base oficial e inserir o arquivo no caminho esperado:

```text
data/raw/MICRODADOS_OCORRENCIAS.csv
```

Os arquivos processados e de cache podem ser regenerados executando o pipeline.
