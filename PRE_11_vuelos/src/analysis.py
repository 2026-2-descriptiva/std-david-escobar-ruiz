"""Analisis de puntualidad de vuelos nacionales (2006-2008).

Usa data/flights_by_carrier_month.csv.gz (agregado por anio, mes y
aerolinea) y data/flights_by_carrier_day_hour.csv.gz (agregado ademas por dia
de la semana y hora programada de salida). Genera en submission/:

  - overall_kpis.csv: indicadores nacionales del periodo completo
  - monthly_national_kpis.csv: indicadores nacionales por anio y mes
  - seasonality.csv: indicadores por mes del anio (los tres anios juntos)
  - carrier_summary.csv: indicadores y ranking por aerolinea
  - day_hour_delay.csv: tasa de demora por dia de la semana y hora
  - priority_segments.csv: segmentos aerolinea-hora con mas demoras en
    exceso de lo esperado por la tasa nacional de esa hora

Definiciones:
  - cancellation_rate: cancelados / programados
  - delay_rate: demorados 15+ min / operados
  - avg_delay_minutes: minutos de demora positivos / operados
"""

from pathlib import Path

import pandas as pd

FOLDER = Path(__file__).resolve().parents[1]
MONTH_FILE = FOLDER / "data" / "flights_by_carrier_month.csv.gz"
DAY_HOUR_FILE = FOLDER / "data" / "flights_by_carrier_day_hour.csv.gz"
SUBMISSION_DIR = FOLDER / "submission"

COUNT_COLUMNS = [
    "scheduled_flights",
    "cancelled_flights",
    "operated_flights",
    "delayed_departure_15_flights",
    "positive_departure_delay_minutes",
]
MIN_CARRIER_FLIGHTS = 100_000
MIN_SEGMENT_FLIGHTS = 10_000
TOP_N = 15
DAY_NAMES = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}


def add_rates(table):
    table = table.copy()
    table[COUNT_COLUMNS] = table[COUNT_COLUMNS].astype(int)
    table["cancellation_rate"] = (
        table["cancelled_flights"] / table["scheduled_flights"]
    ).round(4)
    table["delay_rate"] = (
        table["delayed_departure_15_flights"] / table["operated_flights"]
    ).round(4)
    table["avg_delay_minutes"] = (
        table["positive_departure_delay_minutes"] / table["operated_flights"]
    ).round(2)
    return table


def aggregate(df, by):
    return add_rates(df.groupby(by, as_index=False)[COUNT_COLUMNS].sum())


def overall_kpis(monthly):
    totals = monthly[COUNT_COLUMNS].sum().to_frame().T
    totals.insert(0, "carriers", monthly["reporting_airline"].nunique())
    totals.insert(0, "period", f"{monthly['year'].min()}-{monthly['year'].max()}")
    return add_rates(totals)


def carrier_summary(monthly):
    table = aggregate(monthly, "reporting_airline")
    table = table[table["operated_flights"] >= MIN_CARRIER_FLIGHTS]
    table = table.sort_values("delay_rate", ascending=False).reset_index(drop=True)
    table["delay_rank"] = range(1, len(table) + 1)
    return table


def day_hour_delay(day_hour):
    table = aggregate(day_hour, ["day_of_week", "scheduled_departure_hour"])
    table.insert(1, "day_name", table["day_of_week"].map(DAY_NAMES))
    return table


def priority_segments(day_hour):
    hourly = aggregate(day_hour, "scheduled_departure_hour")
    national_rate = (
        hourly["delayed_departure_15_flights"] / hourly["operated_flights"]
    ).set_axis(hourly["scheduled_departure_hour"])

    table = aggregate(day_hour, ["reporting_airline", "scheduled_departure_hour"])
    table = table[table["operated_flights"] >= MIN_SEGMENT_FLIGHTS].copy()
    table["national_delay_rate"] = (
        table["scheduled_departure_hour"].map(national_rate).round(4)
    )
    expected = table["operated_flights"] * table["scheduled_departure_hour"].map(
        national_rate
    )
    table["expected_delayed_flights"] = expected.round(1)
    table["excess_delayed_flights"] = (
        table["delayed_departure_15_flights"] - expected
    ).round(1)
    return (
        table.sort_values("excess_delayed_flights", ascending=False)
        .head(TOP_N)
        .reset_index(drop=True)
    )


def main():
    monthly = pd.read_csv(MONTH_FILE)
    day_hour = pd.read_csv(DAY_HOUR_FILE)

    outputs = {
        "overall_kpis.csv": overall_kpis(monthly),
        "monthly_national_kpis.csv": aggregate(monthly, ["year", "month"]),
        "seasonality.csv": aggregate(monthly, "month"),
        "carrier_summary.csv": carrier_summary(monthly),
        "day_hour_delay.csv": day_hour_delay(day_hour),
        "priority_segments.csv": priority_segments(day_hour),
    }

    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        table.to_csv(SUBMISSION_DIR / name, index=False)

    return outputs


if __name__ == "__main__":
    main()
