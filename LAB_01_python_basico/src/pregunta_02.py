from .utils import read_records


def pregunta_02():
    """
    Cuente cuántos registros hay para cada letra de la primera columna
    (`letter`). Retorne una lista de tuplas `(letra, cantidad)` ordenada
    alfabéticamente por la letra.

    Ejemplo del formato de la respuesta:

        [("A", 8), ("B", 7), ("C", 5), ...]
    """

    counts = {}
    for record in read_records():
        counts[record["letter"]] = counts.get(record["letter"], 0) + 1
    return sorted(counts.items())
