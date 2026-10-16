from pathlib import Path

import pandas as pd


def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Una cadena de suministros de oficina vende mucho, pero la gerencia
    sospecha que parte de esas ventas no deja utilidad. El archivo
    `data/superstore_orders.csv.gz` tiene una fila por línea de pedido, con
    el número de pedido (`Order ID`), las ventas (`Sales`), la utilidad
    (`Profit`), el descuento aplicado (`Discount`, como proporción), el
    segmento del cliente (`Customer Segment`) y la categoría del producto
    (`Product Category`). Una utilidad negativa significa que la línea se
    vendió con pérdida.

    Use estas definiciones:

    - Margen (`profit_margin`): utilidad sobre ventas.
    - Línea con pérdida: una línea cuya utilidad es negativa.
    - `loss_line_rate`: la proporción de líneas con pérdida.
    - `lost_profit`: la suma de las pérdidas de las líneas con pérdida,
      escrita como número positivo.
    - Rango de descuento (`discount_band`): `0%` si no hubo descuento,
      `1%-5%` si fue mayor que 0 y hasta 5 %, `6%-10%` si fue mayor que 5 % y
      hasta 10 %, y `más de 10%` en otro caso.

    Genere tres archivos en `submission/`, sin el índice de Pandas y con las
    columnas en el orden indicado:

    1. `profitability_summary.csv`, con una sola fila: `lines` (cantidad de
       líneas), `orders` (pedidos distintos), `sales`, `profit`,
       `profit_margin`, `loss_lines` (cantidad de líneas con pérdida),
       `loss_line_rate` y `lost_profit`.

    2. `discount_summary.csv`, con una fila por rango de descuento, en el
       orden en que se definieron arriba: `discount_band`, `lines`, `sales`,
       `profit`, `profit_margin`, `loss_line_rate` y `lost_profit`.

    3. `priority_segments.csv`, con los cinco segmentos segmento–categoría
       que más utilidad pierden: `Customer Segment`, `Product Category`,
       `lines`, `sales`, `profit`, `profit_margin` y `lost_profit`. Considere
       solamente segmentos con al menos 100 líneas y ordénelos por
       `lost_profit` de mayor a menor.

    La función también debe retornar las tres tablas, en el mismo orden.

    Ejemplo del formato de `discount_summary.csv`:

        discount_band,lines,sales,profit,profit_margin,loss_line_rate,...
        0%,166,170539.05,29472.3789,0.1728,0.488,...
        ...
    """

    df = pd.read_csv(
        "data/superstore_orders.csv.gz",
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )
    df["loss"] = df["Profit"] < 0
    df["lost"] = -df["Profit"].where(df["loss"], 0)


    def summarize(frame):
        sales = frame["Sales"].sum()
        profit = frame["Profit"].sum()
        return pd.Series(
            {
                "lines": len(frame),
                "orders": frame["Order ID"].nunique(),
                "sales": sales,
                "profit": profit,
                "profit_margin": profit / sales,
                "loss_lines": int(frame["loss"].sum()),
                "loss_line_rate": frame["loss"].mean(),
                "lost_profit": frame["lost"].sum(),
            }
        )


    def finish(table):
        table = table.copy()
        for column in ["lines", "orders", "loss_lines"]:
            if column in table:
                table[column] = table[column].astype(int)
        for column in ["sales", "profit", "profit_margin", "loss_line_rate", "lost_profit"]:
            if column in table:
                table[column] = table[column].round(4)
        return table


    # 1. Resumen general
    summary = finish(summarize(df).to_frame().T)

    # 2. Resumen por rango de descuento
    bands = ["0%", "1%-5%", "6%-10%", "más de 10%"]
    df["discount_band"] = pd.cut(
        df["Discount"],
        bins=[float("-inf"), 0, 0.05, 0.10, float("inf")],
        labels=bands,
    )
    discounts = (
        df.groupby("discount_band", observed=False)
        .apply(summarize, include_groups=False)
        .reindex(bands)
        .reset_index()
    )
    discounts = finish(
        discounts[
            [
                "discount_band",
                "lines",
                "sales",
                "profit",
                "profit_margin",
                "loss_line_rate",
                "lost_profit",
            ]
        ]
    )

    # 3. Segmentos segmento-categoria que mas utilidad pierden
    segments = (
        df.groupby(["Customer Segment", "Product Category"])
        .apply(summarize, include_groups=False)
        .reset_index()
    )
    segments = segments[segments["lines"] >= 100]
    segments = segments.sort_values("lost_profit", ascending=False).head(5)
    segments = finish(
        segments[
            [
                "Customer Segment",
                "Product Category",
                "lines",
                "sales",
                "profit",
                "profit_margin",
                "lost_profit",
            ]
        ].reset_index(drop=True)
    )

    submission_dir = Path("submission")
    submission_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(submission_dir / "profitability_summary.csv", index=False)
    discounts.to_csv(submission_dir / "discount_summary.csv", index=False)
    segments.to_csv(submission_dir / "priority_segments.csv", index=False)

    return summary, discounts, segments
