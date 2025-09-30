# Pipeline de Dados e Mapas (raiz do repositório)

Este README documenta apenas a parte de pipeline/ETL e geração de mapas Folium que vivem na raiz do repositório em `src/`, lendo dados em `data/` e salvando saídas em `maps/`.

Observação: o aplicativo Streamlit está documentado separadamente em `app/README.md` e não faz parte deste README.

## Estrutura relevante

- `data/`: insumos do pipeline
  - `coletas.db`: banco SQLite opcional (derivado dos dados parquet)
  - `*.csv`, `*.parquet`: arquivos usados na preparação e nos mapas
- `src/`: scripts do pipeline
  - `data_prep.py` e `data_prep.ipynb`: preparação/limpeza dos dados
  - `map.py`: geração do mapa Folium com camadas (pontos, heatmaps, mini-barras)
  - `paths.py`: utilitário de caminhos para localizar `data/` e `maps/`
- `maps/`: saídas HTML geradas (p.ex. `mapa.html`)

## Requisitos

- Python 3.10+
- Pacotes principais:
  - pandas, numpy
  - folium, branca
  - geopandas, shapely (opcional, conforme o fluxo)

Você pode instalar as dependências com um dos arquivos de requisitos disponíveis na raiz:

- `requirements.txt` (runtime)
- `dev-requirements.txt` (ambiente de desenvolvimento)

## Como executar

1. Preparar ambiente Python (opcional, mas recomendado)

   - Crie e ative um virtualenv (ou Conda)
   - Instale dependências: `pip install -r requirements.txt`

2. Verifique/coloque seus dados em `data/`

   - Os scripts assumem que insumos (CSV/Parquet/SQLite) residem em `data/`

3. Execute a preparação (quando aplicável)

   - `src/data_prep.py` e/ou o notebook `src/data_prep.ipynb` fazem limpeza e derivação de colunas

4. Gere o mapa Folium

   - Rode `src/map.py`; a saída padrão será gravada em `maps/mapa.html`

Dica: caso tenha problemas para ver camadas (p.ex. HeatMap) ao abrir `maps/mapa.html` diretamente via `file://`, sirva o arquivo por HTTP local (qualquer servidor estático simples) e acesse em `http://localhost:...`.

## Detalhes dos scripts

### `src/paths.py`

- Resolve caminhos a partir da raiz do repositório usando `Path(__file__).resolve()`
- Exporta constantes para localizar `data/` e `maps/`, usadas por outros scripts

### `src/data_prep.py` e `src/data_prep.ipynb`

- Normaliza colunas, ajusta tipos (datas, números) e produz artefatos intermediários (p.ex. Parquet)
- Valida coordenadas (latitude/longitude) e remove entradas inválidas
- Pode opcionalmente materializar um SQLite (`data/coletas.db`) para consultas rápidas

### `src/map.py`

- Lê o dataset preparado (CSV/Parquet) em `data/`
- Constrói um mapa Folium com:

  - Marcadores de estações/pontos
  - Heatmaps por poluente (com pesos normalizados)
  - Mini-barras (DivIcon/HTML) para visualização rápida por ponto

- Salva a página em `maps/mapa.html`

Notas de robustez implementadas no projeto:

- Alinhamento e normalização de dados para camadas temporais
- Filtros de coordenadas para evitar renderização de pontos inválidos
- Resolução de caminhos que funciona tanto ao executar de `src/` quanto da raiz

## Depuração e dicas

- Se o mapa abre mas camadas (heatmap/overlays) não aparecem:

  - Confira se os dados possuem lat/lon numéricos e dentro de faixas válidas
  - Normalize pesos dos heatmaps (0–1) e garanta que frames/índices estejam alinhados
  - Prefira servir o HTML por HTTP local em vez de abrir via `file://`

- Se houver erro de caminho (FileNotFoundError):
  - Revise `src/paths.py` e garanta que `data/` e `maps/` existam na raiz

## Licença

Este repositório contém dados e código de uso educacional. Verifique os termos dos dados de terceiros antes de redistribuir.
