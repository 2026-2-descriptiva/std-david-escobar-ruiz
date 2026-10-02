"""Analisis descriptivo de ventas minoristas.

Lee data/sales.csv (una fila por orden) y genera en submission/:

  - kpi_summary.csv: indicadores generales del periodo
  - monthly_sales.csv: evolucion mensual
  - category_summary.csv: desempeno por categoria
  - payment_summary.csv: desempeno por medio de pago
  - day_type_summary.csv: dias entre semana vs fin de semana
  - top_customers.csv: 10 clientes con mayores ventas netas
  - top_products.csv: 10 productos con mayores ventas netas
  - return_risk.csv: tasa de devolucion por categoria y canal
  - priority_segments.csv: segmentos categoria-canal-pago que mas venta
    pierden por devoluciones (con un volumen minimo de ordenes)

Definiciones:
  - gross_sales: suma de TotalAmount de todas las ordenes
  - returned_sales: TotalAmount de las ordenes devueltas
  - net_sales: gross_sales - returned_sales
  - return_rate: proporcion de ordenes devueltas
"""

from pathlib import Path

import pandas as pd

FOLDER = Path(__file__).resolve().parents[1]
DATA_FILE = FOLDER / "data" / "sales.csv"
SUBMISSION_DIR = FOLDER / "submission"

TOP_N = 10
MIN_SEGMENT_ORDERS = 20


def load_data(data_file=DATA_FILE):
    df = pd.read_csv(data_file, parse_dates=["OrderDate"])
    df["returned_sales"] = df["TotalAmount"].where(df["IsReturned"] == 1, 0.0)
    df["net_sales"] = df["TotalAmount"] - df["returned_sales"]
    df["month"] = df["OrderDate"].dt.to_period("M").astype(str)
    df["day_type"] = df["OrderDate"].dt.dayofweek.map(
        lambda d: "weekend" if d >= 5 else "weekday"
    )
    return df


def summarize(frame):
    gross = frame["TotalAmount"].sum()
    return pd.Series(
        {
            "orders": len(frame),
            "units": int(frame["Quantity"].sum()),
            "gross_sales": round(gross, 2),
            "returned_sales": round(frame["returned_sales"].sum(), 2),
            "net_sales": round(frame["net_sales"].sum(), 2),
            "return_rate": round(frame["IsReturned"].mean(), 4),
            "avg_order_value": round(gross / len(frame), 2),
        }
    )


def group_summary(df, by):
    table = df.groupby(by).apply(summarize, include_groups=False).reset_index()
    table[["orders", "units"]] = table[["orders", "units"]].astype(int)
    return table


def kpi_summary(df):
    kpis = summarize(df).to_dict()
    kpis["orders"] = int(kpis["orders"])
    kpis["units"] = int(kpis["units"])
    kpis["customers"] = df["CustomerID"].nunique()
    kpis["products"] = df["ProductID"].nunique()
    kpis["start_date"] = df["OrderDate"].min().date().isoformat()
    kpis["end_date"] = df["OrderDate"].max().date().isoformat()
    return pd.DataFrame([kpis])


def with_share(table):
    table = table.sort_values("net_sales", ascending=False).reset_index(drop=True)
    table["net_sales_share"] = (table["net_sales"] / table["net_sales"].sum()).round(4)
    return table


def top_by_net_sales(df, by, n=TOP_N):
    table = group_summary(df, by)
    return table.nlargest(n, "net_sales").reset_index(drop=True)


def return_risk(df):
    table = group_summary(df, ["Category", "SalesChannel"])
    return table.sort_values("return_rate", ascending=False).reset_index(drop=True)


def priority_segments(df, min_orders=MIN_SEGMENT_ORDERS, n=TOP_N):
    table = group_summary(df, ["Category", "SalesChannel", "PaymentMethod"])
    table = table[table["orders"] >= min_orders]
    return (
        table.sort_values("returned_sales", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )


def main():
    df = load_data()

    outputs = {
        "kpi_summary.csv": kpi_summary(df),
        "monthly_sales.csv": group_summary(df, "month"),
        "category_summary.csv": with_share(group_summary(df, "Category")),
        "payment_summary.csv": with_share(group_summary(df, "PaymentMethod")),
        "day_type_summary.csv": with_share(group_summary(df, "day_type")),
        "top_customers.csv": top_by_net_sales(df, "CustomerID"),
        "top_products.csv": top_by_net_sales(df, ["ProductID", "Category"]),
        "return_risk.csv": return_risk(df),
        "priority_segments.csv": priority_segments(df),
    }

    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        table.to_csv(SUBMISSION_DIR / name, index=False)

    return outputs


if __name__ == "__main__":
    main()
