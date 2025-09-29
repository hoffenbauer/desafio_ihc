# Visualização Interativa de Poluentes (Streamlit + GeoPandas + Folium)

Aplicação web em Streamlit para explorar coletas de poluentes por estado, cidade, estação e poluente. O app constrói um banco SQLite a partir de um arquivo Parquet e exibe um mapa interativo com marcadores e um gráfico temporal por estação.

## ✨ Principais recursos

- Filtros dinâmicos em cascata (Estados → Cidades → Estações → Poluentes)
- Opção para incluir coletas oceânicas (linhas com state/city = "N/A")
- Mapa Folium interativo com marcadores clicáveis por estação
- Gráfico temporal Altair por estação (seleção via clique no mapa ou seletor)
- Cache de dados e consultas para melhor desempenho (`st.cache_data`)
- Camada de utilitários para UI, SQL e constantes para reduzir duplicações e manter o código limpo

## 📁 Estrutura do projeto

.
├── data/
│ ├── coletas.db # Banco SQLite gerado automaticamente
│ ├── pontos_coleta_municipios_longo.parquet # Fonte dos dados (entrada)
│ └── ...
├── maps/
│ └── ... # (opcional) mapas HTML pré-gerados
├── src/
│ ├── app.py # App Streamlit principal
│ ├── map.ipynb # Notebook de exploração/prototipagem
│ ├── mapa_poluentes.html # Exemplo de mapa HTML pré-gerado
│ ├── paths.py # Caminhos para DB e Parquet
│ └── utils/
│ ├── constants.py # Rótulos e valores de domínio (ex.: poluentes, N/A)
│ ├── data.py # Helpers p/ datas/locale Altair e merges com GeoPandas
│ ├── db.py # Criação do banco e queries (cidades, estações, coletas)
│ ├── geo.py # Criação de mapas Folium e funções geográficas
│ ├── plots.py # Gráficos Altair (linha e boxplot)
│ ├── sql.py # Helpers SQL: placeholders, seleção efetiva, cláusulas
│ └── ui.py # Wrappers de UI (pills/multiselect) e mensagens
├── requirements.in # Lista de alto nível das dependências
├── requirements.txt # Dependências resolvidas e versionadas (pip-compile)
└── README.md

```

## 🗃️ Dados e esquema esperado

A aplicação parte de um arquivo Parquet, definido em `src/paths.py`:

- `PARQUET_PATH = data/pontos_coleta_municipios_longo.parquet`
- `DB_PATH = data/coletas.db`

Na primeira execução/import do módulo `utils/db.py`, o banco SQLite é criado a partir do Parquet (função `cria_banco_sqlite`) e índices úteis são adicionados (`state`, `city`, `station_name`). As chamadas seguintes se beneficiam de cache via `@st.cache_data`.

Colunas esperadas em `coletas` (sensíveis ao app):

- `state` (TEXT) — UF, ex.: "RJ", "SP"; coletas oceânicas usam `"N/A"`
- `city` (TEXT) — nome da cidade; oceânicas usam `"N/A"`
- `station_name` (TEXT)
- `lat` (REAL), `lon` (REAL)
- `sample_dt` (DATE/TEXT) — data/hora da coleta
- `pollutant` (TEXT) — ex.: `pol_a`, `pol_b`
- `value` (REAL) — valor do poluente medido em mg/L
- `unit` (TEXT, opcional)

Valores e rótulos especiais:

- `N/A` (constante `NA_VALUE` em `utils/constants.py`) para coletas sem cidade/estado
- Rótulos amigáveis de poluente: ver `POLUENTES_ROTULO`/`POLUENTES_ROTULO_REVERSO`

## 🚀 Como executar

Pré-requisitos:

- Python 3.12+
- Ambiente virtual recomendado

Passos típicos (Windows/PowerShell):

```powershell
# 1) Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2) Instalar dependências
pip install -r requirements.txt

# 3) Garanta que o Parquet existe em data/pontos_coleta_municipios_longo.parquet
# 4) Rodar o app
streamlit run src/app.py
```

Na primeira execução, o banco `data/coletas.db` será gerado automaticamente a partir do Parquet.

## 🧭 Uso da interface

- Sidebar

  - Estados (pills multi-seleção): por padrão, todos os estados disponíveis
  - Cidades: aparece após escolher estados; por padrão, todas as cidades disponíveis
  - Estações: após cidades; por padrão, todas as estações disponíveis
  - Poluentes (pills): rótulos amigáveis mapeados para `pol_a`/`pol_b`
  - Incluir coletas oceânicas? (checkbox): adiciona linhas onde `state=city='N/A'`

- Painel principal
  - Métrica com o número de coletas filtradas
  - Mapa Folium (clique em um marcador para selecionar a estação)
  - Seletor de estação (fallback) e gráfico Altair (série temporal por estação)

Regras de seleção:

- Se uma seleção ficar vazia em um nível (ex.: nenhuma cidade marcada), o app considera “todas disponíveis” daquele nível (normalização centralizada em `utils/sql.py::efetiva_selecao`).
- Oceânicas: quando ativo, adiciona um OR para `(state='N/A' AND city='N/A' AND pollutant IN (...))`.

## 🧩 Principais módulos e responsabilidades

- `utils/db.py`

  - `cria_banco_sqlite`: cria/popula o SQLite a partir do Parquet e cria índices
  - `obtem_dados_unicos(coluna)`: valores distintos por coluna (ex.: estados)
  - `busca_cidades(estados)`, `busca_estacoes(cidades)`, `busca_poluentes(...)`
  - `busca_coletas(sql, params)`: retorna DataFrame resultante da consulta

- `utils/sql.py`

  - `placeholders(n)`: monta `?, ?, ?` para o SQLite3
  - `efetiva_selecao(selecao, padrao)`: usa “todas disponíveis” quando vazio
  - `clausula_in(coluna, valores)`: retorna `"coluna IN (...)"` e params
  - `monta_filtro_terrestre(estados, cidades, estacoes, poluentes)`

- `utils/constants.py`

  - `NA_VALUE = "N/A"`, `POLUENTES_ROTULO`, `POLUENTES_ROTULO_REVERSO`

- `utils/ui.py`

  - `pills_multi`, `multiselect_full_default`: wrappers de UI padronizados
  - `info_if`, `warn_if`: mensagens condicionais

- `utils/geo.py`

  - `cria_mapa(gdf)`: mapa Folium com marcadores; usa centróide dos pontos
  - `json_municipios(ufs)`: baixa GeoJSON de municípios (útil para camadas adicionais)
  - `cria_mapa_com_graficos`: exemplo de popup com gráfico Altair

- `utils/plots.py`

  - `cria_grafico(df)`: linha temporal (Data vs. valor) por poluente
  - `cria_boxplot(df)`: distribuição por poluente (log-transform opcional)

- `utils/data.py`
  - `transforma_colunas_datetime_para_string`: utilitário leve p/ datetimes
  - `carrega_locale_altair("pt-BR")`: localidade para eixos/formatos em Altair

## 🔧 Considerações de performance

- Índices no SQLite: `state`, `city`, `station_name` (considere adicionar `pollutant`)
- Cache de consultas: `@st.cache_data` reduz leituras/joins repetidos
- Mapa Folium: para conjuntos muito grandes, considere `FastMarkerCluster` ou GeoJSON com `folium.GeoJson`
- Gráficos Altair: filtrar por estação reduz a carga no navegador

## 🧪 Desenvolvimento e qualidade

- Tipagem leve nos utilitários principais para facilitar manutenção
- Separação de responsabilidades (UI, SQL, DB, geo, plots)
- Observação: `utils/db.py` hoje exibe mensagens no sidebar ao importar (efeito colateral). 

## 🐛 Solução de problemas (Windows)

- Erros ao instalar GeoPandas/pyogrio/pyproj/shapely:
  - Use as versões fixadas em `requirements.txt`
  - Caso necessário, use wheels precompilados (por exemplo, Christoph Gohlke)
- Banco não é criado
  - Verifique se `data/pontos_coleta_municipios_longo.parquet` existe e tem as colunas esperadas
- Mapa vazio ou sem lat/lon
  - O app exibe um mapa padrão se `lat`/`lon` não estiverem presentes no DataFrame filtrado
- Gráfico não aparece
  - A seleção deve conter `sample_dt`, `value` e `pollutant` para plotagem

## 🗺️ Materiais auxiliares

- `src/map.ipynb`: notebook de prototipagem (ex.: alternativas ao `iterrows`, GeoJSON, FastMarkerCluster)
- `src/mapa_poluentes.html`: exemplo de mapa HTML gerado offline (não é utilizado diretamente pelo app)

