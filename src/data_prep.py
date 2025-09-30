from io import StringIO

# import altair as alt
import geopandas as gpd
import pandas as pd
from shapely import make_valid

from utils.data import carrega_locale_altair, gpd_merge
from utils.geo import cria_mapa_com_graficos, json_municipios

# Configurações de locale para Altair para exibição em notebooks
# Descomentar para funcionar corretamente em notebooks
# alt.renderers.set_embed_options(format_locale="pt-BR", time_format_locale="pt-BR")

# Lê o arquivo CSV removendo aspas duplas
# O CSV original é um CSV "sujo", criado com Excel, que adiciona aspas duplas
# em torno de cada campo, o que causa problemas na leitura.
with open(
    "../data/dados_exemplo_poluentes_no_acentos.csv", "r", encoding="utf-8-sig"
) as f:
    linhas = [linha.replace('"', "") for linha in f]

# Converte as linhas limpas para um buffer em memória
csv_buffer = StringIO("".join(linhas))

# Lê o CSV normalmente após a limpeza
df = pd.read_csv(csv_buffer, sep=",")
#
# Remove a coluna "unit" se todos os valores forem iguais
# Neste caso, todos os valores são "mg/L", então a coluna é desnecessária
if "unit" in df.columns and df["unit"].nunique() == 1:
    df = df.drop(columns=["unit"])

# Converte as colunas de latitude e longitude para o tipo numérico
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

# Remove Estacao do nome das estações e converte para categoria
df["station_name"] = df["station_name"].str.replace("Estacao", "")
df["station_name"] = df["station_name"].str.strip()
df["station_name"] = df["station_name"].astype("category")

# Converte a coluna de data para o tipo datetime
df["sample_dt"] = pd.to_datetime(df["sample_dt"], format="%Y-%m-%d")

# Remove a coluna station_id, já que station_name é suficiente para identificar os pontos de coleta
# Cada station_id tem um station_name único
df = df.drop(columns=["station_id"])

# Transforma o DataFrame para o formato longo (long format) para facilitar a plotagem
# com bibliotecas de visualização
df_longo = df.melt(
    id_vars=["station_name", "lat", "lon", "sample_dt"],
    value_vars=["pol_a", "pol_b"],
    var_name="pollutant",
    value_name="value",
)

gdf = gpd.GeoDataFrame(
    df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326"
)

estados_sudeste = ["ES", "MG", "RJ", "SP"]

municipios_sudeste = json_municipios(estados_sudeste)
municipios_sudeste["geometry"] = make_valid(municipios_sudeste["geometry"])
pontos_coleta = (
    gdf[["station_name", "geometry"]].drop_duplicates().reset_index(drop=True)
)

pontos_coleta_municipios = gpd.sjoin(
    municipios_sudeste, pontos_coleta, how="inner", predicate="intersects"
).drop(columns="index_right")

pontos_coleta_municipios = gpd_merge(
    gdf,
    pontos_coleta_municipios[["station_name", "city", "state"]],
    on="station_name",
    how="left",
)

non_cat_cols = pontos_coleta_municipios.select_dtypes(exclude=["category"]).columns
pontos_coleta_municipios[non_cat_cols] = pontos_coleta_municipios[non_cat_cols].fillna(
    "N/A"
)

pontos_coleta_municipios_longo = pontos_coleta_municipios.melt(
    id_vars=["station_name", "lat", "lon", "sample_dt", "city", "state", "geometry"],
    value_vars=["pol_a", "pol_b"],
    var_name="pollutant",
    value_name="value",
)

pontos_coleta_municipios_longo["sample_dt"] = pd.to_datetime(
    pontos_coleta_municipios_longo["sample_dt"], format="%d/%m/%Y"
)

pontos_coleta_municipios_longo = pontos_coleta_municipios_longo.sort_values("sample_dt")

locale = carrega_locale_altair("pt-BR")
m = cria_mapa_com_graficos(pontos_coleta_municipios_longo, locale)
m.save("../maps/mapa.html")
