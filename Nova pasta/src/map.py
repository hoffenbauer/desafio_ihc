import pandas as pd
import folium
from folium.features import DivIcon
from folium.plugins import HeatMap
from folium.map import FeatureGroup, LayerControl


def main():
    # --- Leitura dos dados ---
    df = pd.read_parquet("../data/pontos_coleta_municipios_longo.parquet")

    # --- Pré-processamento ---
    # Remove linhas com dados essenciais ausentes
    dados = df.dropna(subset=["lat", "lon", "pollutant", "value"])

    # Obter o último valor disponível por estação e poluente como proxy
    dados_mais_recentes = (
        dados.sort_values("sample_dt")
        .groupby(["station_name", "lat", "lon", "pollutant"])
        .last()
        .reset_index()
    )

    # Reorganiza para que pol_a e pol_b fiquem em colunas distintas
    dados_pivot = dados_mais_recentes.pivot_table(
        index=["station_name", "lat", "lon"],
        columns="pollutant",
        values="value",
        fill_value=0,
    ).reset_index()

    # --- Criação do mapa base ---
    mapa = folium.Map(location=[dados["lat"].mean(), dados["lon"].mean()], zoom_start=6)

    # --- Camada de barras verticais (mini-grafico) ---
    camada_barras = FeatureGroup(name="Barras (poluentes A e B)")
    ESCALA_BARRA = 5  # Fator visual de escala das barras

    for _, linha in dados_pivot.iterrows():
        valor_a = linha.get("pol_a", 0)
        valor_b = linha.get("pol_b", 0)

        altura_a = min(int(valor_a * ESCALA_BARRA), 40)
        altura_b = min(int(valor_b * ESCALA_BARRA), 40)

        html_barras = f"""
        <div style="display: flex; align-items: flex-end; gap: 4px; width: 30px; height: 45px;">
            <div style="width: 10px; height: {altura_a}px; background-color: #e74c3c;" title="pol_a: {valor_a:.2f}"></div>
            <div style="width: 10px; height: {altura_b}px; background-color: #3498db;" title="pol_b: {valor_b:.2f}"></div>
        </div>
        """

        folium.Marker(
            location=[linha["lat"], linha["lon"]],
            icon=DivIcon(html=html_barras),
            tooltip=f"<b>{linha['station_name']}</b>",
        ).add_to(camada_barras)

    camada_barras.add_to(mapa)

    # --- Heatmap do poluente A ---
    amostras_a = dados[dados["pollutant"] == "pol_a"]
    pontos_a = amostras_a[["lat", "lon", "value"]].values.tolist()

    camada_heatmap_a = FeatureGroup(name="Heatmap Poluente A")
    HeatMap(pontos_a, radius=15, blur=20, max_opacity=0.7).add_to(camada_heatmap_a)
    camada_heatmap_a.add_to(mapa)

    # --- Heatmap do poluente B ---
    amostras_b = dados[dados["pollutant"] == "pol_b"]
    pontos_b = amostras_b[["lat", "lon", "value"]].values.tolist()

    camada_heatmap_b = FeatureGroup(name="Heatmap Poluente B")
    HeatMap(pontos_b, radius=15, blur=20, max_opacity=0.7).add_to(camada_heatmap_b)
    camada_heatmap_b.add_to(mapa)

    # --- Marcadores tradicionais para as estações ---
    camada_marcadores = FeatureGroup(name="Marcadores das Estações")

    for _, linha in dados_pivot.iterrows():
        popup_html = (
            f"<b>Estação:</b> {linha['station_name']}<br>"
            f"<b>Poluente A:</b> {linha.get('pol_a', 0):.2f} mg/L<br>"
            f"<b>Poluente B:</b> {linha.get('pol_b', 0):.2f} mg/L"
        )
        folium.Marker(
            location=[linha["lat"], linha["lon"]],
            popup=popup_html,
            icon=folium.Icon(color="green", icon="flask", prefix="fa"),
        ).add_to(camada_marcadores)

    camada_marcadores.add_to(mapa)

    # --- Controle de camadas ---
    LayerControl(collapsed=False).add_to(mapa)

    # --- Salvar mapa offline ---
    mapa.save("../maps/mapa.html")
    print("Mapa salvo com sucesso em maps/mapa.html")
    return 1


if __name__ == "__main__":
    main()
