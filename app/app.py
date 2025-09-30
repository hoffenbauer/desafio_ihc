import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import sys
from pathlib import Path

# Garante que app/src esteja no sys.path para permitir imports de utils e paths
APP_ROOT = Path(__file__).resolve().parent
APP_SRC = APP_ROOT / "src"
if str(APP_SRC) not in sys.path:
    sys.path.insert(0, str(APP_SRC))

from paths import DB_PATH as db_path
from utils.constants import NA_VALUE, POLUENTES_ROTULO, POLUENTES_ROTULO_REVERSO
from utils.db import (
    busca_cidades,
    busca_coletas,
    busca_estacoes,
    busca_poluentes,
    cria_banco_sqlite,
    obtem_dados_unicos,
)
from utils.geo import cria_mapa
from utils.plots import cria_boxplot, cria_grafico
from utils.sql import efetiva_selecao, monta_filtro_terrestre, placeholders
from utils.ui import avisa_se, informa_se, multiselecao_todos_padrao, pills_multi


# -------------------------
# Configurações iniciais
# -------------------------
cria_banco_sqlite()
st.set_page_config(
    page_title="Visualização de Coletas de Poluentes",
    layout="wide",
    initial_sidebar_state="expanded",
)
# -------------------------
# Sidebar: filtros
# -------------------------
st.sidebar.header("Filtros")
incluir_coletas_oceanicas = st.sidebar.checkbox(
    "Incluir coletas oceânicas?", value=True, key="incluir_oceanicas"
)

# -------------------------
# Controle de visibilidade dos filtros
# -------------------------

# --- Estados ---
ufs = obtem_dados_unicos(db_path, "state")

estados_val = pills_multi(
    label="Selecione os estados",
    options=ufs,
    default=ufs,
    key="pills_estados",
)
# Estados efetivos para consulta (se vazio, usa todos)
estados_para_busca = efetiva_selecao(estados_val, ufs)

# --- Cidades (dependente dos estados) ---
if estados_val:  # Só mostra o seletor de cidades se ao menos um estado for selecionado
    cidades_disponiveis = busca_cidades(db_path, estados_para_busca)
    cidades_val = multiselecao_todos_padrao(
        "Selecione as cidades", cidades_disponiveis, key="cidades"
    )
else:
    informa_se(True, "Por favor, selecione pelo menos um estado.")
    cidades_val = []

# Cidades efetivas para consulta
cidades_para_busca = (
    efetiva_selecao(cidades_val, cidades_disponiveis)
    if "cidades_disponiveis" in locals()
    else []
)

# --- Estações (dependente das cidades) ---
estacoes_val = []
if (
    cidades_val
):  # Só mostra o seletor de estações se ao menos uma cidade for selecionada
    estacoes_disponiveis = busca_estacoes(db_path, cidades_para_busca)
    estacoes_val = multiselecao_todos_padrao(
        "Selecione as estações", estacoes_disponiveis, key="estacoes"
    )
elif cidades_val == [] and estados_val:
    informa_se(True, "Por favor, selecione pelo menos uma cidade.")
    estacoes_val = []

# --- Poluentes (dependente das estações) ---
poluentes_val = []
if (
    estacoes_val or incluir_coletas_oceanicas
):  # Só mostra o seletor de poluentes se ao menos uma estação for selecionada
    poluentes_disponiveis = busca_poluentes(db_path, estacoes_val)
    poluentes_opcoes = [POLUENTES_ROTULO.get(p, p) for p in poluentes_disponiveis]
    selecionados = pills_multi(
        "Selecione os poluentes",
        poluentes_opcoes,
        default=poluentes_opcoes,
        key="poluentes",
    )
    poluentes_val = [POLUENTES_ROTULO_REVERSO.get(p, p) for p in selecionados]
elif cidades_val == [] and estados_val:
    estacoes_val = []
elif estacoes_val == [] and cidades_val:
    informa_se(True, "Por favor, selecione pelo menos uma estação.")

# -------------------------
# Estrutura da consulta
# -------------------------
coletas = []
if estados_val and cidades_val and estacoes_val and poluentes_val:
    # Seleções efetivas (se vazio, usa todas as disponíveis em cada nível)
    estados_ok = efetiva_selecao(estados_val, ufs)
    cidades_ok = efetiva_selecao(cidades_val, cidades_disponiveis)
    estacoes_ok = efetiva_selecao(estacoes_val, estacoes_disponiveis)
    poluentes_ok = efetiva_selecao(poluentes_val, poluentes_disponiveis)

    # Monta filtro terrestre e params
    filtro_terrestre, params = monta_filtro_terrestre(
        estados_ok, cidades_ok, estacoes_ok, poluentes_ok
    )

    if incluir_coletas_oceanicas:
        pol_sql = placeholders(len(poluentes_ok))
        query_oceanica = f" OR (state = '{NA_VALUE}' AND city = '{NA_VALUE}' AND pollutant IN ({pol_sql}))"
        sql_query = f"SELECT * FROM coletas WHERE {filtro_terrestre}{query_oceanica}"
        params = [*params, *poluentes_ok]
    else:
        sql_query = f"SELECT * FROM coletas WHERE {filtro_terrestre}"

    # Executa a query
    coletas = busca_coletas(db_path, sql_query, params)
elif (poluentes_val == [] and estacoes_val) or (
    incluir_coletas_oceanicas is False and poluentes_val == []
):
    informa_se(True, "Por favor, selecione pelo menos um poluente.")
elif (estados_val == []) and (incluir_coletas_oceanicas is False):
    avisa_se(
        True,
        "Por favor, selecione pelo menos um estado para iniciar ou inclua coletas oceânicas.",
    )
    coletas = []


# -------------------------
# Painel principal
# -------------------------
col1, col2 = st.columns([2, 1], gap="large")

# Coluna 1: Mapa e contagem de registros
ss = None
with col1:
    st.sidebar.info(f"Número de coletas: {len(coletas)}")
    st.write("### Mapa das Coletas")
    st.write("Clique em um ponto no mapa obter mais informações sobre a estação.")
    if len(coletas) > 0:
        try:
            if "lat" in coletas.columns and "lon" in coletas.columns:
                gdf = gpd.GeoDataFrame(
                    coletas,
                    geometry=gpd.points_from_xy(coletas["lon"], coletas["lat"]),
                    crs="EPSG:4326",
                )
                gdf = gdf[["station_name", "city", "state", "lat", "lon", "geometry"]]
                m = cria_mapa(gdf)
                map_data = st_folium(
                    m,
                    width=700,
                    height=500,
                    returned_objects=["last_object_clicked_tooltip"],
                )

                if map_data and map_data.get("last_object_clicked_tooltip"):
                    clicked_station = map_data["last_object_clicked_tooltip"]
                    if (
                        clicked_station
                        and clicked_station in coletas["station_name"].values
                    ):
                        ss = clicked_station
            else:
                st.warning(
                    "Coletas não contém colunas 'lat' e 'lon'. Exibindo mapa padrão."
                )
                m = folium.Map(location=[-23.5505, -46.6333], zoom_start=6)
                st_folium(m, width=750, height=750)
        except Exception as e:
            st.error(f"Erro ao carregar o mapa: {str(e)}")


# Coluna 2: Gráfico de coletas
with col2:
    if len(coletas) > 0:
        if "selected_station" not in st.session_state:
            st.session_state.selected_station = None
        if ss is None:
            unique_stations = coletas["station_name"].unique().tolist()
            selected_station = st.selectbox(
                "Escolha uma estação para visualizar o gráfico (ou clique no mapa)",
                options=["Nenhuma"] + unique_stations,
                index=0,
                key="station_fallback",
            )
            if selected_station != "Nenhuma":
                ss = selected_station
        if ss:
            sd = coletas[coletas["station_name"] == ss]
            sd["sample_dt"] = pd.to_datetime(sd["sample_dt"])

            st.write(f"### Estação {ss}")
            if sd["city"].values[0] != "N/A":
                st.write(f"{sd['city'].values[0]} - {sd['state'].values[0]}")
            if not sd.empty:
                chart = cria_grafico(sd)
                bplot = cria_boxplot(sd)
                st.write("#####  Histórico de coletas")
                st.altair_chart(chart, use_container_width=True)
                st.write("#####  Boxplot de coletas")
                st.altair_chart(bplot, use_container_width=True)

                st.write("##### Informações das coletas")
                st.write(f"###### Número: {len(sd)}")
                st.write(
                    f"###### Data: {sd['sample_dt'].min().date().strftime('%d/%m/%Y')} a {sd['sample_dt'].max().date().strftime('%d/%m/%Y')}"
                )
                col1, col2 = st.columns(2)
                with col1:
                    st.write("##### Poluente A")
                    st.write(
                        f"###### Média: {sd[sd['pollutant'] == 'A']['value'].mean():.2f} mg/L"
                    )
                    st.write(
                        f"###### Desvio Padrão: {sd[sd['pollutant'] == 'A']['value'].std():.2f} mg/L"
                    )
                    st.write(
                        f"###### Mediana: {sd[sd['pollutant'] == 'A']['value'].median():.2f} mg/L"
                    )
                    st.write(
                        f"###### Mínimo: {sd[sd['pollutant'] == 'A']['value'].min():.2f} mg/L"
                    )
                    st.write(
                        f"###### Máximo: {sd[sd['pollutant'] == 'A']['value'].max():.2f} mg/L"
                    )
                with col2:
                    st.write("##### Poluente B")
                    st.write(
                        f"###### Média: {sd[sd['pollutant'] == 'B']['value'].mean():.2f} mg/L"
                    )
                    st.write(
                        f"###### Desvio Padrão: {sd[sd['pollutant'] == 'B']['value'].std():.2f} mg/L"
                    )
                    st.write(
                        f"###### Mediana: {sd[sd['pollutant'] == 'B']['value'].median():.2f} mg/L"
                    )
                    st.write(
                        f"###### Mínimo: {sd[sd['pollutant'] == 'B']['value'].min():.2f} mg/L"
                    )
                    st.write(
                        f"###### Máximo: {sd[sd['pollutant'] == 'B']['value'].max():.2f} mg/L"
                    )

            else:
                st.warning("Nenhum dado encontrado para a estação selecionada.")
