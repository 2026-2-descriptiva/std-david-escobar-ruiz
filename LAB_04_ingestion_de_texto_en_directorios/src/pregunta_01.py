from pathlib import Path

import pandas as pd


def pregunta_01():
    """
    Las frases de este laboratorio no están en una tabla, sino en miles de
    archivos de texto organizados en carpetas. Dentro de `data/` hay dos
    carpetas, `train/` y `test/`, y cada una contiene las carpetas
    `negative/`, `neutral/` y `positive/`. Cada archivo `.txt` contiene una
    frase, y la carpeta donde se encuentra indica su sentimiento.

    Su tarea es construir un dataset para cada división y guardarlo en:

    - `submission/train_dataset.csv`
    - `submission/test_dataset.csv`

    Cada archivo debe tener dos columnas: `phrase`, con el texto de la frase,
    y `target`, con el nombre de la carpeta de sentimiento (`negative`,
    `neutral` o `positive`). Recorra las carpetas y los archivos en orden
    alfabético, de modo que el resultado sea siempre el mismo. No guarde el
    índice de Pandas en el CSV.

    Ejemplo del formato de cada archivo:

        phrase,target
        "The real estate company posted a net loss ...",negative
        ...
        "Cardona slowed her vehicle , turned around ...",neutral
        ...
    """

    data_dir = Path("data")
    submission_dir = Path("submission")
    submission_dir.mkdir(parents=True, exist_ok=True)

    for split in ("train", "test"):
        records = []
        for target_dir in sorted(p for p in (data_dir / split).iterdir() if p.is_dir()):
            for file in sorted(target_dir.glob("*.txt")):
                phrase = file.read_text(encoding="utf-8").strip()
                records.append({"phrase": phrase, "target": target_dir.name})

        df = pd.DataFrame(records, columns=["phrase", "target"])
        df.to_csv(submission_dir / f"{split}_dataset.csv", index=False)
