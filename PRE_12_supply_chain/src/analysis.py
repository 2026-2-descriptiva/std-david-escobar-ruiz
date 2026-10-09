"""Analisis de desempeno de la cadena de suministro.

Lee data/supply_chain.csv (una fila por linea de pedido) y genera en
submission/:

  - overall_kpis.csv: indicadores generales
  - mode_summary.csv: desempeno por modo de envio
  - freight_by_mode.csv: costos de flete por modo de envio
  - country_summary.csv: desempeno por pais
  - country_mode_summary.csv: desempeno por pais y modo de envio
  - monthly_summary.csv: evolucion mensual (mes de entrega)
  - priority_countries.csv: paises con mayor tasa de entregas tardias
  - priority_segments.csv: segmentos pais-modo con mayor tasa de entregas
    tardias

Definiciones:
  - late: la entrega al cliente ocurrio despues de la fecha programada
  - delay_days: dias entre la fecha programada y la de entrega (si es tarde)
  - freight_cost_usd / weight_kg: solo valores numericos. Los textos como
    "See DN-304 (ID#:10589)" remiten al flete de otra linea y "Freight
    Included in Commodity Cost" no tiene un valor separado; ambos quedan
    como faltantes para no contar dos veces el mismo flete.
  - freight_to_value: flete / valor de las lineas con flete numerico
"""

from pathlib import Path

import pandas as pd

FOLDER = Path(__file__).resolve().parents[1]
DATA_FILE = FOLDER / "data" / "supply_chain.csv"
SUBMISSION_DIR = FOLDER / "submission"

MIN_COUNTRY_LINES = 50
MIN_SEGMENT_LINES = 30
TOP_N = 10


def load_data(data_file=DATA_FILE):
    df = pd.read_csv(data_file)
    df = df.rename(
        columns={
            "Country": "country",
            "Shipment Mode": "shipment_mode",
            "Line Item Value": "line_value",
        }
    )
    df["shipment_mode"] = df["shipment_mode"].fillna("Unknown")

    scheduled = pd.to_datetime(df["Scheduled Delivery Date"], format="%d-%b-%y")
    delivered = pd.to_datetime(df["Delivered to Client Date"], format="%d-%b-%y")
    df["delivery_month"] = delivered.dt.to_period("M").astype(str)
    df["late"] = delivered > scheduled
    df["delay_days"] = (delivered - scheduled).dt.days.where(df["late"])

    df["freight_cost_usd"] = pd.to_numeric(df["Freight Cost (USD)"], errors="coerce")
    df["weight_kg"] = pd.to_numeric(df["Weight (Kilograms)"], errors="coerce")
    return df


def summarize(frame):
    with_freight = frame["freight_cost_usd"].notna()
    freight = frame.loc[with_freight, "freight_cost_usd"].sum()
    value_with_freight = frame.loc[with_freight, "line_value"].sum()
    return pd.Series(
        {
            "lines": len(frame),
            "line_value_usd": round(frame["line_value"].sum(), 2),
            "late_lines": int(frame["late"].sum()),
            "late_rate": round(frame["late"].mean(), 4),
            "on_time_rate": round(1 - frame["late"].mean(), 4),
            "avg_delay_days_when_late": round(frame["delay_days"].mean(), 1),
            "freight_cost_usd": round(freight, 2),
            "freight_to_value": (
                round(freight / value_with_freight, 4) if value_with_freight else None
            ),
        }
    )


def group_summary(df, by):
    table = df.groupby(by).apply(summarize, include_groups=False).reset_index()
    table[["lines", "late_lines"]] = table[["lines", "late_lines"]].astype(int)
    return table


def overall_kpis(df):
    kpis = summarize(df).to_dict()
    kpis["lines"] = int(kpis["lines"])
    kpis["late_lines"] = int(kpis["late_lines"])
    kpis["countries"] = df["country"].nunique()
    kpis["vendors"] = df["Vendor"].nunique()
    kpis["first_delivery_month"] = df["delivery_month"].min()
    kpis["last_delivery_month"] = df["delivery_month"].max()
    return pd.DataFrame([kpis])


def freight_by_mode(df):
    def freight_stats(frame):
        has_freight = frame["freight_cost_usd"].notna()
        has_both = has_freight & frame["weight_kg"].gt(0)
        freight = frame.loc[has_freight, "freight_cost_usd"]
        return pd.Series(
            {
                "lines": len(frame),
                "lines_with_freight": int(has_freight.sum()),
                "total_freight_usd": round(freight.sum(), 2),
                "median_freight_usd": round(freight.median(), 2),
                "freight_per_kg_usd": round(
                    frame.loc[has_both, "freight_cost_usd"].sum()
                    / frame.loc[has_both, "weight_kg"].sum(),
                    2,
                ),
                "freight_to_value": round(
                    freight.sum() / frame.loc[has_freight, "line_value"].sum(), 4
                ),
            }
        )

    table = (
        df.groupby("shipment_mode")
        .apply(freight_stats, include_groups=False)
        .reset_index()
    )
    table[["lines", "lines_with_freight"]] = table[
        ["lines", "lines_with_freight"]
    ].astype(int)
    return table.sort_values("total_freight_usd", ascending=False).reset_index(
        drop=True
    )


def prioritize(table, min_lines, n=TOP_N):
    table = table[table["lines"] >= min_lines]
    return (
        table.sort_values(["late_rate", "late_lines"], ascending=False)
        .head(n)
        .reset_index(drop=True)
    )


def main():
    df = load_data()

    country = group_summary(df, "country").sort_values("lines", ascending=False)
    country_mode = group_summary(df, ["country", "shipment_mode"])

    outputs = {
        "overall_kpis.csv": overall_kpis(df),
        "mode_summary.csv": group_summary(df, "shipment_mode").sort_values(
            "lines", ascending=False
        ),
        "freight_by_mode.csv": freight_by_mode(df),
        "country_summary.csv": country,
        "country_mode_summary.csv": country_mode,
        "monthly_summary.csv": group_summary(df, "delivery_month"),
        "priority_countries.csv": prioritize(country, MIN_COUNTRY_LINES),
        "priority_segments.csv": prioritize(country_mode, MIN_SEGMENT_LINES),
    }

    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        table.to_csv(SUBMISSION_DIR / name, index=False)

    return outputs


if __name__ == "__main__":
    main()
