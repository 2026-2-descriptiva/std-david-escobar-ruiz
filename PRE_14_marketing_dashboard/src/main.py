"""Indicadores de desempeno de campanas de marketing digital.

Lee data/campaign_data.csv y genera en submission/:

  - kpis.csv: indicadores generales del periodo
  - campaign_summary.csv: desempeno por campana (plantilla del anuncio)
  - source_summary.csv: desempeno por fuente de trafico
  - daily_summary.csv: desempeno por dia

Los indicadores que son razones se recalculan a partir de los totales de
cada grupo (por ejemplo, ROAS = ingresos totales / gasto total) en lugar de
promediar las razones de cada fila, que daria el mismo peso a un dia con
10 clics que a uno con 1 000.

  - ctr: page_clicks / impressions
  - roas: revenue / ad_spend
  - cpc: ad_spend / paid_clicks
  - rpc: revenue / paid_clicks
  - gross_profit: revenue - ad_spend
  - blocked_click_rate: blocked_clicks / page_clicks
"""

from pathlib import Path

import pandas as pd

FOLDER = Path(__file__).resolve().parents[1]
DATA_FILE = FOLDER / "data" / "campaign_data.csv"
SUBMISSION_DIR = FOLDER / "submission"

TOTAL_COLUMNS = [
    "impressions",
    "page_clicks",
    "paid_clicks",
    "blocked_clicks",
    "revenue",
    "ad_spend",
]


def load_data(data_file=DATA_FILE):
    df = pd.read_csv(data_file, parse_dates=["utc_date"])
    return df.rename(columns={"template_name": "campaign"})


def add_kpis(table):
    table = table.copy()
    table["gross_profit"] = table["revenue"] - table["ad_spend"]
    table["ctr"] = table["page_clicks"] / table["impressions"]
    table["roas"] = table["revenue"] / table["ad_spend"]
    table["cpc"] = table["ad_spend"] / table["paid_clicks"]
    table["rpc"] = table["revenue"] / table["paid_clicks"]
    table["blocked_click_rate"] = table["blocked_clicks"] / table["page_clicks"]
    money = ["revenue", "ad_spend", "gross_profit", "cpc", "rpc"]
    ratios = ["ctr", "roas", "blocked_click_rate"]
    table[money] = table[money].round(2)
    table[ratios] = table[ratios].round(4)
    return table


def summarize(df, by):
    table = df.groupby(by, as_index=False).agg(
        days=("utc_date", "nunique"), **{c: (c, "sum") for c in TOTAL_COLUMNS}
    )
    return add_kpis(table)


def kpis(df):
    totals = {
        "start_date": df["utc_date"].min().date().isoformat(),
        "end_date": df["utc_date"].max().date().isoformat(),
        "days": df["utc_date"].nunique(),
        **{column: df[column].sum() for column in TOTAL_COLUMNS},
    }
    return add_kpis(pd.DataFrame([totals]))


def campaign_summary(df):
    return summarize(df, "campaign").sort_values("gross_profit", ascending=False)


def source_summary(df):
    return summarize(df, "traffic_source").sort_values("gross_profit", ascending=False)


def daily_summary(df):
    table = summarize(df, "utc_date").drop(columns="days")
    table["utc_date"] = table["utc_date"].dt.date
    return table


def main():
    df = load_data()
    outputs = {
        "kpis.csv": kpis(df),
        "campaign_summary.csv": campaign_summary(df),
        "source_summary.csv": source_summary(df),
        "daily_summary.csv": daily_summary(df),
    }

    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        table.to_csv(SUBMISSION_DIR / name, index=False)

    return outputs


if __name__ == "__main__":
    main()
