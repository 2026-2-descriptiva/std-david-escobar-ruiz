from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

SURFACE_COLOR = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
SEQUENTIAL_BLUES = LinearSegmentedColormap.from_list(
    "sequential_blues", ["#cde2fb", "#86b6ef", "#2a78d6", "#184f95", "#0d366b"]
)


def plot_heatmap(matrix, output_file):
    """Mapa de calor de retencion; las celdas NaN (periodos aun no
    observables) se dejan vacias en lugar de pintarse como 0 %."""
    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=SURFACE_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    values = np.ma.masked_invalid(matrix.to_numpy(dtype=float))
    image = ax.imshow(values, cmap=SEQUENTIAL_BLUES, vmin=0, vmax=1, aspect="auto")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iat[i, j]
            if pd.isna(value):
                continue
            ax.text(
                j,
                i,
                f"{value:.0%}",
                ha="center",
                va="center",
                fontsize=9,
                color="white" if value >= 0.5 else TEXT_PRIMARY,
            )

    ax.set_xticks(range(matrix.shape[1]), labels=matrix.columns)
    ax.set_yticks(range(matrix.shape[0]), labels=matrix.index)
    ax.set_xlabel("Meses desde la primera compra", color=TEXT_SECONDARY)
    ax.set_ylabel("Cohorte (mes de la primera compra)", color=TEXT_SECONDARY)
    ax.set_title(
        "Retención de clientes por cohorte",
        loc="left",
        color=TEXT_PRIMARY,
        fontsize=13,
    )
    ax.tick_params(colors=TEXT_SECONDARY, length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Separadores de 2 px entre celdas
    ax.set_xticks(np.arange(-0.5, matrix.shape[1]), minor=True)
    ax.set_yticks(np.arange(-0.5, matrix.shape[0]), minor=True)
    ax.grid(which="minor", color=SURFACE_COLOR, linewidth=2)
    ax.tick_params(which="minor", length=0)

    colorbar = fig.colorbar(image, ax=ax, format=lambda x, _: f"{x:.0%}")
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(colors=TEXT_SECONDARY, length=0)

    fig.tight_layout()
    fig.savefig(output_file, dpi=150, facecolor=SURFACE_COLOR)
    plt.close(fig)


def build_cohort_analysis() -> pd.DataFrame:
    """
    Una tienda quiere saber si sus clientes vuelven a comprar después de su
    primera compra. Para responder, agrupe a los clientes en cohortes según
    el mes de su primera compra y mida, mes a mes, qué proporción de cada
    cohorte vuelve a comprar. Use `data/sales.csv.gz`, que tiene una fila por
    orden con su cliente (`CustomerID`) y su fecha (`OrderDate`).

    Use estas definiciones:

    - `cohort_month`: el mes de la primera compra del cliente, escrito como
      `AAAA-MM`.
    - `period_index`: los meses transcurridos desde `cohort_month`; es 0 en el
      mes de la primera compra, 1 en el mes siguiente, y así sucesivamente.
    - `active_customers`: la cantidad de clientes distintos de la cohorte que
      compraron en ese período.
    - `cohort_size`: la cantidad de clientes de la cohorte, es decir, sus
      clientes activos en el período 0.
    - `retention_rate`: `active_customers` sobre `cohort_size`.

    Genere dos archivos en `submission/`:

    1. `cohort_retention.csv`, sin el índice de Pandas, con las columnas
       `cohort_month`, `period_index`, `active_customers`, `cohort_size` y
       `retention_rate`, y una fila por cada combinación cohorte–período
       observada, ordenadas por cohorte y período.

    2. `cohort_retention_heatmap.png`, un mapa de calor de `retention_rate`
       con una fila por cohorte (eje vertical) y una columna por período
       (eje horizontal). Muestre los valores como porcentajes. Los períodos
       que todavía no se pueden observar para una cohorte no significan
       retención cero: déjelos vacíos en el mapa.

    La función también debe retornar la tabla de retención.

    Ejemplo del formato de `cohort_retention.csv`:

        cohort_month,period_index,active_customers,cohort_size,retention_rate
        2022-01,0,100,100,1.0
        2022-01,1,26,100,0.26
        ...
    """

    sales = pd.read_csv("data/sales.csv.gz", parse_dates=["OrderDate"])
    sales["order_month"] = sales["OrderDate"].dt.to_period("M")

    # Cohorte: mes de la primera compra del cliente
    first_month = sales.groupby("CustomerID")["order_month"].min().rename("cohort")
    sales = sales.join(first_month, on="CustomerID")
    sales["period_index"] = (sales["order_month"] - sales["cohort"]).apply(
        lambda offset: offset.n
    )

    retention = (
        sales.groupby(["cohort", "period_index"])["CustomerID"]
        .nunique()
        .rename("active_customers")
        .reset_index()
    )
    cohort_size = retention.loc[retention["period_index"] == 0].set_index("cohort")[
        "active_customers"
    ]
    retention["cohort_size"] = retention["cohort"].map(cohort_size)
    retention["retention_rate"] = (
        retention["active_customers"] / retention["cohort_size"]
    ).round(4)
    retention["cohort_month"] = retention["cohort"].astype(str)
    retention = (
        retention.sort_values(["cohort_month", "period_index"])[
            [
                "cohort_month",
                "period_index",
                "active_customers",
                "cohort_size",
                "retention_rate",
            ]
        ]
        .reset_index(drop=True)
    )

    submission_dir = Path("submission")
    submission_dir.mkdir(parents=True, exist_ok=True)
    retention.to_csv(submission_dir / "cohort_retention.csv", index=False)

    # Mapa de calor: los periodos no observados quedan como NaN (celda vacia)
    matrix = retention.pivot(
        index="cohort_month", columns="period_index", values="retention_rate"
    )
    plot_heatmap(matrix, submission_dir / "cohort_retention_heatmap.png")

    return retention
