import warnings

from functools import lru_cache
import altair as alt
import geopandas as gpd
import pandas as pd

from pandas.api.types import is_datetime64_any_dtype as is_datetime


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
