from .utils import read_records


def pregunta_12():
    """
    Para cada letra de la primera columna (`letter`), sume todos los valores
    numéricos de los pares `clave:valor` de la quinta columna (`metrics`).
    Retorne un diccionario `{letra: suma}` con las letras en orden alfabético.

    Ejemplo del formato de la respuesta:

        {"A": 177, "B": 187, "C": 114, ...}
    """

    sums = {}
    for record in read_records():
        total = sum(number for _, number in record["metrics"])
        sums[record["letter"]] = sums.get(record["letter"], 0) + total
    return dict(sorted(sums.items()))
