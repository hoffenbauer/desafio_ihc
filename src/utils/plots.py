import altair as alt
from utils.utils import carrega_locale_altair

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
