from .utils import read_records


def pregunta_04():
    """
    Cuente cuántos registros hay en cada mes, usando la fecha de la tercera
    columna (`date`). Represente el mes como un texto de dos dígitos y retorne
    una lista de tuplas `(mes, cantidad)` ordenada por el mes.

    Ejemplo del formato de la respuesta:

        [("01", 3), ("02", 4), ("03", 2), ...]
    """

    counts = {}
    for record in read_records():
        month = record["date"].split("-")[1]
        counts[month] = counts.get(month, 0) + 1
    return sorted(counts.items())
