import csv
import json
import os

OUTPUT_FOLDER = "PRE_03_csv2json/temp"


def convert_csv_2_json(csv_file, output_folder=OUTPUT_FOLDER):
    """Convierte un archivo CSV a una lista de objetos JSON.

    El archivo de salida tiene el mismo nombre del CSV con extension .json
    y se guarda en output_folder.
    """
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        data = list(csv.DictReader(f))

    os.makedirs(output_folder, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    json_file = os.path.join(output_folder, f"{base_name}.json")

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return json_file


if __name__ == "__main__":
    convert_csv_2_json("PRE_03_csv2json/data/drivers.csv")
