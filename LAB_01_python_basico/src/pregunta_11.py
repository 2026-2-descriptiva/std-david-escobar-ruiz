from .utils import read_records


def pregunta_11():
    """
    La cuarta columna (`codes`) contiene letras minúsculas separadas por
    comas. Para cada una de esas letras, sume los valores de la segunda
    columna (`value`) de los registros en los que aparece. Retorne un
    diccionario `{letra: suma}` con las letras en orden alfabético.

    Ejemplo del formato de la respuesta:

        {"a": 122, "b": 49, "c": 91, ...}
    """

    sums = {}
    for record in read_records():
        for code in record["codes"]:
            sums[code] = sums.get(code, 0) + record["value"]
    return dict(sorted(sums.items()))
