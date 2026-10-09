from .utils import read_records


def pregunta_09():
    """
    Cuente cuántas veces aparece cada clave en la quinta columna (`metrics`)
    de todo el archivo. Retorne un diccionario `{clave: cantidad}` con las
    claves en orden alfabético.

    Ejemplo del formato de la respuesta:

        {"aaa": 13, "bbb": 16, "ccc": 23, ...}
    """

    counts = {}
    for record in read_records():
        for key, _ in record["metrics"]:
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))
