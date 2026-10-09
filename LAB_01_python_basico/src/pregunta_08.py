from .utils import read_records


def pregunta_08():
    """
    Repita la pregunta 7, pero ahora cada lista de letras debe contener cada
    letra una sola vez y estar ordenada alfabéticamente. Retorne una lista de
    tuplas `(valor, letras)` ordenada por el valor.

    Ejemplo del formato de la respuesta:

        [(0, ["C"]), (1, ["B", "E"]), (2, ["A", "E"]), ...]
    """

    letters = {}
    for record in read_records():
        letters.setdefault(record["value"], set()).add(record["letter"])
    return [(value, sorted(v)) for value, v in sorted(letters.items())]
