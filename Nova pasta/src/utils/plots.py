"""Funções utilitárias para criação de gráficos interativos usando Altair."""

import altair as alt
from utils.data import carrega_locale_altair
import numpy as np

locale = carrega_locale_altair("pt-BR")


def cria_grafico(df):
    chart = (
        alt.Chart(df)
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
                alt.Tooltip("sample_dt:T", title="Data da coleta", format="%d-%m-%Y"),
                alt.Tooltip("value:Q", title="Valor (mg/L)"),
            ],
        )
        .configure(locale=locale)
    ).add_params()
    return chart


def cria_boxplot(df):
    # Verifica se as colunas necessárias existem
    df["value"] = np.round(np.log(df["value"] + 1), 2)
    df["pollutant"] = df["pollutant"].replace({"pol_a": "A", "pol_b": "B"})
    chart = (
        (
            alt.Chart(df)
            .mark_boxplot(size=70, extent=0.5)
            .encode(
                x=alt.X("pollutant:N", title="Poluente"),
                y=alt.Y(
                    "value:Q", title="Valor medido (ln mg/L)", scale=alt.Scale(base=2)
                ),
                color=alt.Color("pollutant:N", legend=None),
            )
        )
        .properties(
            width=500,  # ⬅ aumente conforme necessário
            height=500,
            title="Distribuição dos valores por poluente",
        )
        .configure(locale=locale)
    )
    return chart
