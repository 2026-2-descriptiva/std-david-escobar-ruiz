from .utils import read_records


def pregunta_03():
    """
    Sume los valores de la segunda columna (`value`) para cada letra de la
    primera columna (`letter`). Retorne una lista de tuplas `(letra, suma)`
    ordenada alfabéticamente por la letra.

    Ejemplo del formato de la respuesta:

        [("A", 53), ("B", 36), ("C", 27), ...]
    """

    sums = {}
    for record in read_records():
        sums[record["letter"]] = sums.get(record["letter"], 0) + record["value"]
    return sorted(sums.items())
