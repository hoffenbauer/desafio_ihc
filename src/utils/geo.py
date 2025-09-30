"""Funções utilitárias para manipulação de dados geográficos e criação de mapas interativos."""

import warnings
import folium
import geopandas as gpd
import shapely
import pandas as pd
import altair as alt

# fmt: off
CODIGOS_ESTADOS = {
    "AC": 12, "AL": 27, "AP": 16, "AM": 13, "BA": 29, "CE": 23, "DF": 53, "ES": 32,
    "GO": 52, "MA": 21, "MT": 51, "MS": 50, "MG": 31, "PA": 15, "PB": 25, "PR": 41,
    "PE": 26, "PI": 22, "RJ": 33, "RN": 24, "RS": 43, "RO": 11, "RR": 14, "SC": 42,
    "SP": 35, "SE": 28, "TO": 17
}
# fmt: on

def obtem_centroide(pontos: list[shapely.Point] | gpd.GeoSeries) -> tuple[float, float]:
    """Calcula o centroide de um conjunto de pontos.

    Args:
        pontos (list[shapely.Point]|gpd.GeoSeries[shapely.Point]): Conjunto de pontos.

    Returns:
        tuple[float, float]: Coordenadas (latitude, longitude) do centroide.
    """
    if isinstance(pontos, gpd.GeoSeries) and not all(
        isinstance(p, shapely.Point) for p in pontos
    ):
        raise TypeError("GeoSeries deve conter apenas objetos Point.")

    if pontos.empty:
        raise ValueError("A série de pontos está vazia.")
    from shapely.geometry import Polygon

    poly = Polygon([[ponto.x, ponto.y] for ponto in pontos])
    return poly.convex_hull.centroid.coords[0][::-1]


def cria_mapa(gdf: gpd.GeoDataFrame) -> folium.Map:
    """Cria um mapa interativo com marcadores para cada ponto no GeoDataFrame.
    Args:
        df (gpd.GeoDataFrame): GeoDataFrame contendo os dados a serem plotados.
            Deve conter as colunas: 'station_name', 'city', 'state', 'lat', 'lon', 'geometry'.

    Returns:
        folium.Map: Mapa interativo com os pontos plotados.
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("O argumento gdf deve ser um GeoDataFrame.")
    if gdf.empty:
        raise ValueError("O GeoDataFrame está vazio.")

    centroide = obtem_centroide(pontos=gdf["geometry"])
    m = folium.Map(location=centroide, zoom_start=7)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
        name="CartoDB Positron",
        control=False,
    ).add_to(m)

    for row in gdf.itertuples():
        nome_estacao = row.station_name
        cidade = row.city
        estado = row.state
        lat = row.lat
        lon = row.lon

        if cidade == "N/A":
            tooltip = f"\
            <b>Estação:</b> {nome_estacao}"
        else:
            tooltip = f"\
                <b>Estação:</b> {nome_estacao}<br>\
                <b>Cidade:</b> {cidade}<br>\
                <b>Estado:</b> {estado}"

        marker = folium.Marker(
            location=(lat, lon),
            icon=folium.Icon(
                icon="flask",
                prefix="fa",
                color="green" if cidade != "N/A" else "blue",
            ),
            tooltip=f"{nome_estacao}",
            popup=folium.Popup(tooltip, max_width=250),
        )

        marker.add_to(m)

    return m


@lru_cache
def json_municipios(ufs: list[str] | str) -> gpd.GeoDataFrame:
    """Carrega os dados geográficos dos municípios brasileiros para os estados especificados.

    Args:
        ufs (list[str] | str): Lista de siglas dos estados ou uma única sigla.

    Returns:
        gpd.GeoDataFrame: GeoDataFrame contendo os dados dos municípios dos estados especificados.

    Raises:
        ValueError: Se nenhum estado válido for fornecido.
    """
    url_municipios = "https://raw.githubusercontent.com/tbrugz/geodata-br/refs/heads/master/geojson/geojs-{codigo}-mun.json"

    if isinstance(ufs, str):
        ufs = [ufs.upper()]
    else:
        ufs = [uf.upper() for uf in ufs]

    ufs_validos = [uf for uf in ufs if uf in CODIGOS_ESTADOS]
    ufs_invalidos = set(ufs) - set(ufs_validos)

    if ufs_invalidos:
        warnings.warn(f"Estados inválidos ignorados: {', '.join(ufs_invalidos)}")

    if not ufs_validos:
        raise ValueError("Nenhum estado válido fornecido.")

    gdfs = []
    for uf in ufs_validos:
        gdf = gpd.read_file(url_municipios.format(codigo=CODIGOS_ESTADOS[uf]))
        gdf.columns = ["id", "city", "desc", "geometry"]
        gdf["state"] = uf
        gdf = gdf[["id", "city", "state", "geometry"]]
        gdfs.append(gdf)

    municipios = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs="EPSG:4326")
    municipios["geometry"] = shapely.make_valid(municipios["geometry"])

    return municipios


def cria_mapa_com_graficos(gdf: gpd.GeoDataFrame, locale: alt.Locale) -> folium.Map:
    """Cria um mapa interativo com marcadores que exibem gráficos Altair em popups.
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame contendo os dados a serem plotados.
            Deve conter as colunas: 'station_name', 'city', 'state', 'lat', 'lon', 'geometry', 'sample_dt', 'value', 'pollutant'.
    Returns:
        folium.Map: Mapa interativo com os pontos plotados e gráficos nos popups.
    """
    if not isinstance(locale, alt.Locale):
        raise TypeError("O argumento locale deve ser um alt.Locale.")
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("O argumento gdf deve ser um GeoDataFrame.")
    if gdf.empty:
        raise ValueError("O GeoDataFrame está vazio.")

    # fmt: off
    required_cols = [
        "station_name", "city", "state",
        "lat", "lon", "geometry",
        "sample_dt", "value", "pollutant",
    ]
    # fmt: on

    missing_cols = [col for col in required_cols if col not in gdf.columns]
    if missing_cols:
        raise ValueError(
            f"Há colunas faltantes no GeoDataFrame: {', '.join(missing_cols)}"
        )
    if not all(isinstance(p, shapely.Point) for p in gdf["geometry"]):
        raise TypeError("A coluna 'geometry' deve conter apenas objetos Point.")

    centroide = obtem_centroide(pontos=gdf["geometry"])
    m = folium.Map(location=centroide, zoom_start=8)

    gdf["pollutant"] = gdf["pollutant"].replace({"pol_a": "A", "pol_b": "B"})

    for row in gdf.itertuples():
        nome_estacao = row.station_name
        cidade = row.city
        estado = row.state
        lat = row.lat
        lon = row.lon

        # Filtra dados para a estação
        dados_estacao = gdf[gdf["station_name"] == nome_estacao]

        if dados_estacao.empty:
            continue

        # Cria gráfico Altair
        chart = (
            alt.Chart(dados_estacao)
            .mark_line(point=alt.OverlayMarkDef(filled=False, fill="white"))
            .encode(
                x=alt.X("sample_dt:T", axis=alt.Axis(format="%d %b", title="Data")),
                y=alt.Y("value:Q", title="Valor (mg/L)"),
                color=alt.Color(
                    "pollutant:N",
                    legend=alt.Legend(title="Poluente"),
                    scale=alt.Scale(range=["green", "purple"]),
                ),
                tooltip=[
                    alt.Tooltip("station_name:N", title="Estação"),
                    alt.Tooltip(
                        "sample_dt:T", title="Data da coleta", format="%d-%m-%Y"
                    ),
                    alt.Tooltip("value:Q", title="Valor (mg/L)"),
                ],
            )
            .properties(
                width=280,
                height=220,
                title=(
                    f"Estação {nome_estacao}"
                    f"{'' if cidade == 'N/A' else f' - {cidade}'}"
                    f"{'' if estado == 'N/A' else f'/{estado}'}"
                ),
            )
            .configure_title(fontSize=14, font="Courier", color="gray", anchor="start")
            .configure_legend(labelFontSize=10, titleFontSize=12)
        ).configure(locale=locale)

        # popup com espaço suficiente
        vega = folium.VegaLite(chart, width=400, height=260)
        popup = folium.Popup(max_width=400)
        vega.add_to(popup)

        tooltip = f"<b>Estação:</b> {nome_estacao}<br><b>Cidade:</b> {cidade}<br><b>Estado:</b> {estado}"
        # Cria marcador
        marker = folium.Marker(
            location=(lat, lon),
            icon=folium.Icon(icon="flask-vial", prefix="fa", color="green"),
            tooltip=tooltip,
            popup=popup,
        )
        popup.add_to(marker)
        marker.add_to(m)

    return m
