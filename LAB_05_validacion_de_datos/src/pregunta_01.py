import json
import re
from pathlib import Path

import pandas as pd


def main():
    """
    Antes de limpiar o analizar un conjunto de datos, un analista debe
    documentar qué problemas tiene. En este laboratorio usted no va a limpiar
    `data/ventas.csv.gz`: va a construir un reporte de calidad que deje evidencia
    de sus problemas, tal como están en el archivo.

    Lea `data/ventas.csv.gz` sin modificar sus valores. Para trabajar con los
    encabezados, normalícelos: páselos a minúsculas, elimine los espacios al
    inicio y al final (y cualquier marca BOM) y reemplace los espacios
    internos por `_`. Las columnas requeridas son `supplier_id`, `supplier`,
    `country`, `city`, `purchase_date`, `amount`, `discount`, `weight`,
    `units`, `unit_price` y `contact_email`.

    Escriba el reporte en `submission/data_quality_report.json` con estas
    claves:

    - `row_count`: cantidad de filas de datos.
    - `column_count`: cantidad de columnas.
    - `missing_required_columns`: lista ordenada de columnas requeridas que no
      están en el archivo.
    - `unexpected_columns`: lista ordenada de columnas del archivo que no son
      requeridas.
    - `duplicate_row_count`: cantidad de filas idénticas a una fila anterior.
    - `duplicate_supplier_id_row_count`: cantidad de filas cuyo `supplier_id`
      aparece más de una vez (cuente todas esas filas, no solo las
      repetidas).
    - `missing_value_count_by_column`: diccionario con la cantidad de valores
      faltantes de cada columna. Considere faltantes las celdas vacías y las
      que contienen `N/A`.
    - `invalid_email_count`: cantidad de valores de `contact_email` que no
      tienen la forma `usuario@dominio.extension`.
    - `invalid_unit_count`: cantidad de valores numéricos de `units` que no son
      enteros positivos. Los valores faltantes no se cuentan aquí.
    - `country_values`: lista ordenada de los valores distintos de `country`,
      escritos exactamente como aparecen en el archivo.

    La función también debe retornar el reporte como un diccionario.

    Ejemplo del formato del reporte:

        {
          "row_count": 103,
          "column_count": 11,
          "missing_required_columns": [],
          ...
          "country_values": [" Colombia ", "CO", ...]
        }
    """

    required_columns = [
        "supplier_id",
        "supplier",
        "country",
        "city",
        "purchase_date",
        "amount",
        "discount",
        "weight",
        "units",
        "unit_price",
        "contact_email",
    ]

    # Se leen todos los valores como texto y sin convertir faltantes, para
    # diagnosticar el archivo tal como esta.
    df = pd.read_csv(
        "data/ventas.csv.gz",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
    )
    df.columns = [
        re.sub(r"\s+", "_", column.replace("﻿", "").strip().lower())
        for column in df.columns
    ]

    is_missing = df.apply(lambda column: column.str.strip().isin(["", "N/A"]))

    email_pattern = r"[^@\s]+@[^@\s]+\.[A-Za-z]+"
    emails = df.loc[~is_missing["contact_email"], "contact_email"].str.strip()
    invalid_email_count = int((~emails.str.fullmatch(email_pattern)).sum())

    units = pd.to_numeric(df.loc[~is_missing["units"], "units"], errors="coerce")
    units = units.dropna()
    invalid_unit_count = int(((units <= 0) | (units % 1 != 0)).sum())

    report = {
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "missing_required_columns": sorted(set(required_columns) - set(df.columns)),
        "unexpected_columns": sorted(set(df.columns) - set(required_columns)),
        "duplicate_row_count": int(df.duplicated().sum()),
        "duplicate_supplier_id_row_count": int(
            df["supplier_id"].str.strip().duplicated(keep=False).sum()
        ),
        "missing_value_count_by_column": {
            column: int(count) for column, count in is_missing.sum().items()
        },
        "invalid_email_count": invalid_email_count,
        "invalid_unit_count": invalid_unit_count,
        "country_values": sorted(df["country"].unique().tolist()),
    }

    output_file = Path("submission/data_quality_report.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return report
