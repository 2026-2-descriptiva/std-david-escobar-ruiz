from .utils import read_records


def pregunta_05():
    """
    Para cada letra de la primera columna (`letter`), encuentre el valor
    máximo y el valor mínimo de la segunda columna (`value`). Retorne una lista
    de tuplas `(letra, máximo, mínimo)` ordenada alfabéticamente por la letra.

    Ejemplo del formato de la respuesta:

        [("A", 9, 2), ("B", 9, 1), ...]
    """

    values = {}
    for record in read_records():
        values.setdefault(record["letter"], []).append(record["value"])
    return [(letter, max(v), min(v)) for letter, v in sorted(values.items())]
