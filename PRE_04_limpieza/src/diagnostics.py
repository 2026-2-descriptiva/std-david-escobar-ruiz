"""Diagnostico de calidad de datos del archivo de ventas (crudo o limpio)."""

import sys

import pandas as pd

FOLDER = "PRE_04_limpieza"
INPUT_FILE = f"{FOLDER}/data/ventas.csv"


def diagnostics(df):
    print(f"Filas: {df.shape[0]}  Columnas: {df.shape[1]}")
    print(f"Filas duplicadas: {df.duplicated().sum()}")
    print()

    for column in df.columns:
        series = df[column]
        print(f"== {column!r}")
        print(f"   tipo: {series.dtype}")
        print(f"   faltantes: {series.isna().sum()}")
        print(f"   valores unicos: {series.nunique()}")
        print(f"   ejemplos: {series.dropna().unique()[:8].tolist()}")
        print()


def main(input_file=INPUT_FILE):
    df = pd.read_csv(input_file, dtype=str, encoding="utf-8-sig")
    diagnostics(df)


if __name__ == "__main__":
    main(*sys.argv[1:])
