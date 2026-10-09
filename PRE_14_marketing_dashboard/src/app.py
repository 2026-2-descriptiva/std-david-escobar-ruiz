"""Tablero de desempeno de campanas de marketing.

Ejecucion:

    streamlit run PRE_14_marketing_dashboard/src/app.py

Usa las mismas funciones de main.py, de modo que los indicadores del tablero
coinciden con los archivos de submission/.
"""

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import TOTAL_COLUMNS, add_kpis, kpis, load_data, summarize  # noqa: E402

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
SERIES_BLUE = "#2a78d6"
SERIES_ORANGE = "#eb6834"


def bar_chart(table, category, value, title, value_format):
    table = table.sort_values(value)
    figure = go.Figure(
        go.Bar(
            x=table[value],
            y=table[category],
            orientation="h",
            marker=dict(color=SERIES_BLUE, cornerradius=4),
            texttemplate=f"%{{x:{value_format}}}",
            textposition="outside",
            hovertemplate=f"%{{y}}: %{{x:{value_format}}}<extra></extra>",
        )
    )
    figure.update_layout(
        title=dict(text=title, x=0, font=dict(color=TEXT_PRIMARY)),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(color=TEXT_SECONDARY),
        xaxis=dict(gridcolor=GRID),
        margin=dict(l=10, r=40, t=50, b=30),
        height=320,
    )
    return figure


def monthly_chart(df):
    monthly = df.assign(month=df["utc_date"].dt.to_period("M").dt.to_timestamp())
    monthly = add_kpis(monthly.groupby("month", as_index=False)[TOTAL_COLUMNS].sum())
    figure = go.Figure()
    for column, label, color in [
        ("revenue", "Ingresos", SERIES_BLUE),
        ("ad_spend", "Gasto en anuncios", SERIES_ORANGE),
    ]:
        figure.add_trace(
            go.Scatter(
                x=monthly["month"],
                y=monthly[column],
                name=label,
                mode="lines",
                line=dict(color=color, width=2),
                hovertemplate=f"{label}: $%{{y:,.0f}}<extra></extra>",
            )
        )
    figure.update_layout(
        title=dict(text="Ingresos y gasto mensual (USD)", x=0, font=dict(color=TEXT_PRIMARY)),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(color=TEXT_SECONDARY),
        hovermode="x unified",
        yaxis=dict(gridcolor=GRID, tickprefix="$"),
        legend=dict(orientation="h", y=1.1, x=0),
        margin=dict(l=10, r=10, t=70, b=30),
        height=360,
    )
    return figure


def main():
    st.set_page_config(page_title="Campañas de marketing", layout="wide")
    st.title("Desempeño de campañas de marketing")

    df = load_data()

    # Filtros en una sola fila sobre los graficos
    col_dates, col_sources, col_campaigns = st.columns([1, 1, 1])
    start, end = df["utc_date"].min().date(), df["utc_date"].max().date()
    dates = col_dates.date_input(
        "Periodo", value=(start, end), min_value=start, max_value=end
    )
    sources = col_sources.multiselect(
        "Fuente de tráfico", sorted(df["traffic_source"].unique())
    )
    campaigns = col_campaigns.multiselect("Campaña", sorted(df["campaign"].unique()))

    if isinstance(dates, tuple) and len(dates) == 2:
        df = df[df["utc_date"].dt.date.between(*dates)]
    if sources:
        df = df[df["traffic_source"].isin(sources)]
    if campaigns:
        df = df[df["campaign"].isin(campaigns)]

    if df.empty:
        st.info("No hay registros para los filtros seleccionados.")
        return

    totals = kpis(df).iloc[0]
    tiles = st.columns(5)
    tiles[0].metric("Ingresos", f"${totals['revenue']:,.0f}")
    tiles[1].metric("Gasto en anuncios", f"${totals['ad_spend']:,.0f}")
    tiles[2].metric("Utilidad bruta", f"${totals['gross_profit']:,.0f}")
    tiles[3].metric("ROAS", f"{totals['roas']:.2f}")
    tiles[4].metric("CTR", f"{totals['ctr']:.1%}")

    st.plotly_chart(monthly_chart(df))

    left, right = st.columns(2)
    by_source = summarize(df, "traffic_source")
    by_campaign = summarize(df, "campaign")
    left.plotly_chart(
        bar_chart(by_source, "traffic_source", "roas", "ROAS por fuente", ".2f")
    )
    right.plotly_chart(
        bar_chart(
            by_campaign,
            "campaign",
            "gross_profit",
            "Utilidad bruta por campaña (USD)",
            "$,.0f",
        )
    )

    with st.expander("Tabla por fuente de tráfico"):
        st.dataframe(by_source, hide_index=True)
    with st.expander("Tabla por campaña"):
        st.dataframe(by_campaign, hide_index=True)


if __name__ == "__main__":
    main()
