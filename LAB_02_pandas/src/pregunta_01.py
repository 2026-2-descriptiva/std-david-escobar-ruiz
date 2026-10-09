import pandas as pd


def pregunta_01():
    """
    ¿Cuántos registros tiene la tabla `data/tbl0.tsv`? Retorne la cantidad
    como un número entero.

    Ejemplo del formato de la respuesta:

        40
    """

    tbl0 = pd.read_csv("data/tbl0.tsv", sep="\t")
    return len(tbl0)
