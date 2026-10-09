"""Lectura del archivo de datos con la biblioteca estandar."""

import csv
import gzip

DATA_FILE = "data/data.csv.gz"


def read_records(data_file=DATA_FILE):
    """Retorna una lista de registros con las columnas ya separadas:

    letter (str), value (int), date (str), codes (list[str]),
    metrics (list[tuple[str, int]])
    """
    records = []
    with gzip.open(data_file, "rt", encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if not row:
                continue
            letter, value, date, codes, metrics = row
            records.append(
                {
                    "letter": letter,
                    "value": int(value),
                    "date": date,
                    "codes": codes.split(","),
                    "metrics": [
                        (key, int(number))
                        for key, number in (pair.split(":") for pair in metrics.split(","))
                    ],
                }
            )
    return records
