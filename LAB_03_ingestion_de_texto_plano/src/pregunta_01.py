import re

import pandas as pd


def pregunta_01():
    """
    El archivo `data/clusters_report.txt` es un reporte de clústeres de
    palabras clave pensado para ser leído por una persona, no por un programa:
    los encabezados ocupan varias líneas, las columnas están alineadas con
    espacios y la lista de palabras clave de un clúster continúa en las líneas
    siguientes.

    Su tarea es convertir ese reporte en un DataFrame de Pandas con una fila
    por clúster y las columnas:

    - `cluster`: número del clúster, como entero.
    - `cantidad_de_palabras_clave`: como entero.
    - `porcentaje_de_palabras_clave`: como número decimal; por ejemplo, el
      texto `15,9 %` debe quedar como `15.9`.
    - `principales_palabras_clave`: todas las palabras clave del clúster en un
      solo texto, separadas por una coma y un único espacio.

    Retorne el DataFrame.

    Ejemplo del formato de la respuesta (se omite la última columna):

           cluster  cantidad_de_palabras_clave  porcentaje_de_palabras_clave
        0        1                         105                          15.9
        1        2                         102                          15.4
        ...
    """

    with open("data/clusters_report.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Los registros empiezan despues de la linea de guiones
    start = next(i for i, line in enumerate(lines) if line.startswith("---")) + 1

    records = []
    for line in lines[start:]:
        if not line.strip():
            continue
        match = re.match(r"^\s+(\d+)\s+(\d+)\s+([\d,]+)\s*%\s+(.*)$", line)
        if match:
            cluster, count, percent, keywords = match.groups()
            records.append(
                {
                    "cluster": int(cluster),
                    "cantidad_de_palabras_clave": int(count),
                    "porcentaje_de_palabras_clave": float(percent.replace(",", ".")),
                    "principales_palabras_clave": keywords.strip(),
                }
            )
        else:
            # Continuacion de la lista de palabras clave del registro anterior
            records[-1]["principales_palabras_clave"] += " " + line.strip()

    df = pd.DataFrame(records)

    keywords = df["principales_palabras_clave"]
    keywords = keywords.str.replace(r"\s+", " ", regex=True)
    keywords = keywords.str.replace(r"\s*,\s*", ", ", regex=True)
    keywords = keywords.str.strip().str.rstrip(".")
    df["principales_palabras_clave"] = keywords

    return df
