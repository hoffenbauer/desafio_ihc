import warnings
from functools import lru_cache
from typing import Optional

import altair as alt
import folium
import geopandas as gpd
import pandas as pd
import shapely

from pandas.api.types import is_datetime64_any_dtype as is_datetime

# fmt: off
CODIGOS_ESTADOS = {
    "AC": 12, "AL": 27, "AP": 16, "AM": 13, "BA": 29, "CE": 23, "DF": 53, "ES": 32,
    "GO": 52, "MA": 21, "MT": 51, "MS": 50, "MG": 31, "PA": 15, "PB": 25, "PR": 41,
    "PE": 26, "PI": 22, "RJ": 33, "RN": 24, "RS": 43, "RO": 11, "RR": 14, "SC": 42,
    "SP": 35, "SE": 28, "TO": 17
}
# fmt: on


def cria_mapa_geodataframe(
    gdf: gpd.GeoDataFrame, cols: list[str], aliases: Optional[list[str]] = None
) -> folium.Map:
    """Cria um mapa interativo com marcadores para cada ponto no GeoDataFrame.
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame contendo os dados a serem plotados.
        cols (list): Lista de colunas do GeoDataFrame a serem exibidas no tooltip.
        aliases (list, optional): Lista de aliases para as colunas no tooltip. \
            Se None, usa os nomes originais das colunas.
    Returns:
        folium.Map: Mapa interativo com os pontos plotados.
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("O argumento gdf deve ser um GeoDataFrame.")
    if gdf.empty:
        raise ValueError("O GeoDataFrame está vazio.")
    if not all(col in gdf.columns for col in cols):
        raise ValueError(
            "Uma ou mais colunas especificadas em cols não existem no GeoDataFrame."
        )
    if aliases is not None and len(cols) != len(aliases):
        raise ValueError(
            "A lista de aliases deve ter o mesmo tamanho que a lista de cols."
        )

    m = folium.Map(location=[-15, -55], zoom_start=4)

    datetime_cols = gdf.select_dtypes(include=["datetime64[ns]"]).columns.tolist()
    if datetime_cols:
        gdf = transforma_colunas_datetime_para_string(gdf, datetime_cols)

    # Converte para GeoJSON e adiciona ao mapa
    folium.GeoJson(
        gdf.to_json(),
        marker=folium.CircleMarker(radius=6, fill=True, fill_opacity=0.7),
        tooltip=folium.GeoJsonTooltip(
            fields=cols,
            aliases=aliases if aliases else cols,
            localize=True,
        ),
    ).add_to(m)

    return m

def transforma_colunas_datetime_para_string(
    gdf: gpd.GeoDataFrame, cols: list[str], formato: str = "%d/%m/%Y"
) -> gpd.GeoDataFrame:
    """Transforma uma coluna datetime de um GeoDataFrame para o formato string.
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame contendo os dados a serem transformados.
        cols (list): Nomes das colunas a serem transformadas.
        formato (str, optional): Formato da string de data. Padrão é "%d/%m/%Y".
    Returns:
        gpd.GeoDataFrame: GeoDataFrame com as colunas transformadas para string.
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("O argumento gdf deve ser um GeoDataFrame.")

    missing_cols = [col for col in cols if col not in gdf.columns]

    if missing_cols == cols:
        raise ValueError(f"Nenhuma das colunas '{cols}' existe no GeoDataFrame.")
    if missing_cols:
        warnings.warn(f"As colunas {missing_cols} não existem no GeoDataFrame.")

    for col in cols:
        if is_datetime(gdf[col]):
            gdf[col] = gdf[col].dt.strftime(formato)

    return gdf


def gpd_merge(left_gdf, right_df, **merge_kwargs):
    """Realiza um merge entre um GeoDataFrame e um DataFrame, preservando a geometria.
    Args:
        left_gdf (gpd.GeoDataFrame): GeoDataFrame à esquerda do merge.
        right_df (pd.DataFrame): DataFrame à direita do merge.
        **merge_kwargs: Argumentos adicionais para o pd.merge().
    Returns:
        gpd.GeoDataFrame: Resultado do merge como um GeoDataFrame.
    """
    if all(type(df) is pd.DataFrame for df in [left_gdf, right_df]):
        warnings.warn(
            "Ambos os argumentos são DataFrames. Considere usar pd.merge() diretamente.",
            UserWarning,
        )
    if not isinstance(left_gdf, gpd.GeoDataFrame):
        raise TypeError("O argumento left_gdf deve ser um GeoDataFrame.")
    if not isinstance(right_df, pd.DataFrame):
        raise TypeError("O argumento right_df deve ser um DataFrame.")
    merged = pd.merge(left_gdf, right_df, **merge_kwargs)
    return gpd.GeoDataFrame(merged, geometry=left_gdf.geometry.name, crs=left_gdf.crs)


@lru_cache(maxsize=5)
def carrega_locale_altair(locale: str = "pt-BR") -> alt.Locale:
    """Carrega a configuração de localidade (locale) para Altair a partir dos arquivos JSON do D3.

    Args:
        locale (str, optional): Código da localidade a ser carregada. Padrão é "pt_BR".

    Returns:
        alt.Locale: Objeto de localidade para uso em gráficos Altair.

    Raises:
        ValueError: Se os arquivos de locale não forem encontrados ou forem inválidos.
    """
    import json
    from urllib import error, request

    base_format_url = "https://raw.githubusercontent.com/d3/d3-format/refs/heads/main/locale/{locale}.json"
    base_time_url = "https://raw.githubusercontent.com/d3/d3-time-format/refs/heads/main/locale/{locale}.json"

    try:
        with request.urlopen(base_format_url.format(locale=locale)) as f:
            format_json = json.load(f)
        with request.urlopen(base_time_url.format(locale=locale)) as f:
            time_format_json = json.load(f)
    except error.HTTPError as e:
        raise ValueError(
            f"Locale '{locale}' não encontrado nos repositórios D3."
        ) from e
    except Exception as e:
        raise ValueError("Erro ao carregar locale para Altair.") from e

    return alt.Locale(number=format_json, time=time_format_json)


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

    poly = Polygon([point for point in pontos])
    return poly.convex_hull.centroid.coords[0][::-1]