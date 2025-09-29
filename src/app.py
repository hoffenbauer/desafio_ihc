import streamlit as st

from utils.db import (
    cria_banco_sqlite,
    obtem_dados_unicos,
    busca_cidades,
    busca_estacoes,
    busca_coletas,
    busca_poluentes,
)
from paths import DB_PATH as db_path
import geopandas as gpd
from utils.geo import cria_mapa
from utils.plots import cria_grafico
from streamlit_folium import st_folium
import folium

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

estados_opcoes = ufs
estados_val = st.sidebar.pills(
    label="Selecione os estados",
    options=ufs,
    default=ufs,
    key="pills_estados",
    selection_mode="multi",
)
# Estados efetivos para consulta
if not estados_val:
    estados_para_busca = ufs
else:
    estados_para_busca = estados_val

# --- Cidades (dependente dos estados) ---
if estados_val:  # Só mostra o seletor de cidades se ao menos um estado for selecionado
    cidades_disponiveis = busca_cidades(db_path, estados_para_busca)
    cidades_opcoes = cidades_disponiveis
    cidades_val = st.sidebar.multiselect(
        "Selecione as cidades",
        cidades_opcoes,
        default=cidades_opcoes,
        key="cidades",
    )
else:
    st.sidebar.info("Por favor, selecione pelo menos um estado.")
    cidades_val = []

# Cidades efetivas para consulta
if cidades_val:
    cidades_para_busca = cidades_val
else:
    cidades_para_busca = (
        cidades_disponiveis if "cidades_disponiveis" in locals() else []
    )

# --- Estações (dependente das cidades) ---
estacoes_val = []
if (
    cidades_val
):  # Só mostra o seletor de estações se ao menos uma cidade for selecionada
    estacoes_disponiveis = busca_estacoes(db_path, cidades_para_busca)
    estacoes_opcoes = estacoes_disponiveis
    estacoes_val = st.sidebar.multiselect(
        "Selecione as estações",
        estacoes_opcoes,
        default=estacoes_opcoes,
        key="estacoes",
    )
elif cidades_val == [] and estados_val:
    st.sidebar.info("Por favor, selecione pelo menos uma cidade.")
    estacoes_val = []

# --- Poluentes (dependente das estações) ---
poluentes_rotulo = {"pol_a": "Poluente A", "pol_b": "Poluente B"}
poluentes_map_reverso = {v: k for k, v in poluentes_rotulo.items()}
poluentes_val = []
if (
    estacoes_val or incluir_coletas_oceanicas
):  # Só mostra o seletor de poluentes se ao menos uma estação for selecionada
    poluentes_disponiveis = busca_poluentes(db_path, estacoes_val)
    poluentes_opcoes = [poluentes_rotulo.get(p, p) for p in poluentes_disponiveis]
    poluentes_val = st.sidebar.pills(
        "Selecione os poluentes",
        poluentes_opcoes,
        default=poluentes_opcoes,
        selection_mode="multi",
        key="poluentes",
    )
    poluentes_val = [poluentes_map_reverso.get(p, p) for p in poluentes_val]
elif cidades_val == [] and estados_val:
    estacoes_val = []
elif estacoes_val == [] and cidades_val:
    st.sidebar.info("Por favor, selecione pelo menos uma estação.")

# -------------------------
# Estrutura da consulta
# -------------------------
coletas = []
if estados_val and cidades_val and estacoes_val and poluentes_val:
    # Conta os elementos para a query
    estados_cont = len(estados_val)
    cidades_cont = len(cidades_val)
    estacoes_cont = len(estacoes_val)
    poluentes_cont = len(poluentes_val)

    # Se não houver seleção, usa todas as opções disponíveis
    if estados_cont == 0:
        estados_val = ufs
        estados_cont = len(ufs)
    estados_sql = ",".join(["?"] * estados_cont)

    if cidades_cont == 0:
        cidades_val = cidades_disponiveis
        cidades_cont = len(cidades_disponiveis)
    cidades_sql = ",".join(["?"] * cidades_cont)

    if estacoes_cont == 0:
        estacoes_val = estacoes_disponiveis
        estacoes_cont = len(estacoes_disponiveis)
    estacoes_sql = ",".join(["?"] * estacoes_cont)

    if poluentes_cont == 0:
        poluentes_val = poluentes_disponiveis
        poluentes_cont = len(poluentes_disponiveis)
    poluentes_sql = ",".join(["?"] * poluentes_cont)

    # Monta a query SQL para coletas terrestres
    query_terrestre = f"""
    (state IN ({estados_sql})
    AND city IN ({cidades_sql})
    AND station_name IN ({estacoes_sql})
    AND pollutant IN ({poluentes_sql}))
    """
    params = [*estados_val, *cidades_val, *estacoes_val, *poluentes_val]

    if incluir_coletas_oceanicas:
        if estados_val == []:
            sql_query = "SELECT * FROM coletas WHERE state = 'N/A' AND city = 'N/A' AND pollutant IN ('pol_a', 'pol_b')"
        # Adiciona a condição para coletas oceânicas
        query_oceanica = (
            f"OR (state = 'N/A' AND city = 'N/A' AND pollutant IN ({poluentes_sql}))"
        )
        sql_query = f"SELECT * FROM coletas WHERE {query_terrestre} {query_oceanica}"
        # Adiciona os poluentes novamente aos parâmetros para a parte oceânica da query
        params.extend(poluentes_val)
    else:
        sql_query = f"SELECT * FROM coletas WHERE {query_terrestre}"

    # Executa a query
    coletas = busca_coletas(db_path, sql_query, params)
    # TODO REVIEW
elif (poluentes_val == [] and estacoes_val) or (
    incluir_coletas_oceanicas is False and poluentes_val == []
):
    st.sidebar.info("Por favor, selecione pelo menos um poluente.")
elif (estados_val == []) and (incluir_coletas_oceanicas is False):
    st.warning(
        "Por favor, selecione pelo menos um estado para iniciar ou inclua coletas oceânicas."
    )
    coletas = []


# -------------------------
# Painel principal
# -------------------------
# Column layout
col1, col2 = st.columns([2, 1], gap="large")

# Column 1: Metric and Map
ss = None
with col1:
    st.info(f"Número de coletas encontradas: {len(coletas)}")
    st.write("### Mapa das Coletas")
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
                # Debug: Uncomment to inspect click events
                # st.write("Map Data:", map_data)
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

# Column 2: Plot
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

            st.write(f"### Histórico de coletas - Estação {ss}")
            if sd["city"].values[0] != "N/A":
                st.write(f"{sd['city'].values[0]} - {sd['state'].values[0]}")
            if not sd.empty:
                chart = cria_grafico(sd)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("Nenhum dado encontrado para a estação selecionada.")
