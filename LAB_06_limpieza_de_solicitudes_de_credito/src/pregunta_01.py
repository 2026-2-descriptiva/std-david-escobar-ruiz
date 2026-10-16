from pathlib import Path

import pandas as pd


def pregunta_01():
    """
    El archivo `data/solicitudes_de_credito.csv.gz` contiene las solicitudes de
    un programa de crédito, pero llegó sucio: tiene una columna de índice que
    no pertenece a los datos, registros duplicados, registros incompletos y
    valores que representan lo mismo escritos de formas distintas en los
    campos de texto, las fechas, el estrato y el monto.

    Su tarea es limpiarlo y guardar el resultado en
    `submission/solicitudes_de_credito.csv`, usando punto y coma (`;`) como
    separador y sin el índice de Pandas.

    El archivo limpio debe cumplir lo siguiente:

    - Contiene solamente las nueve columnas `sexo`, `tipo_de_emprendimiento`,
      `idea_negocio`, `barrio`, `estrato`, `comuna_ciudadano`,
      `fecha_de_beneficio`, `monto_del_credito` y `línea_credito`, en ese
      orden.
    - Los campos de texto están en minúsculas y sus palabras separadas por
      espacios.
    - `estrato` y `monto_del_credito` son números enteros, sin símbolos ni
      separadores de miles.
    - Todas las fechas de `fecha_de_beneficio` usan un mismo formato, por
      ejemplo `AAAA-MM-DD`.
    - No hay registros incompletos. La única excepción es
      `comuna_ciudadano`: sus valores faltantes son parte de los datos
      originales y deben conservarse.
    - No hay registros duplicados.

    Ejemplo del formato del archivo:

        sexo;tipo_de_emprendimiento;idea_negocio;barrio;estrato;...
        femenino;comercio;almacen de ropa en;los cerros el vergel;2;...
        ...
    """

    df = pd.read_csv(
        "data/solicitudes_de_credito.csv.gz", sep=";", index_col=0, encoding="utf-8"
    )

    # Campos de texto: minusculas, guiones como espacios y espacios normalizados
    text_columns = [
        "sexo",
        "tipo_de_emprendimiento",
        "idea_negocio",
        "barrio",
        "línea_credito",
    ]
    for column in text_columns:
        df[column] = (
            df[column]
            .str.lower()
            .str.replace(r"[-_]", " ", regex=True)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

    # Estrato: '02' -> 2
    df["estrato"] = df["estrato"].astype(int)

    # Monto: '$ 7,000,000.00' -> 7000000
    df["monto_del_credito"] = (
        df["monto_del_credito"]
        .astype(str)
        .str.replace(r"\.00$", "", regex=True)
        .str.replace(r"[^0-9]", "", regex=True)
        .astype(int)
    )

    # Fechas en DD/MM/AAAA o AAAA/MM/DD -> AAAA-MM-DD
    dates = pd.to_datetime(df["fecha_de_beneficio"], format="%d/%m/%Y", errors="coerce")
    dates = dates.fillna(
        pd.to_datetime(df["fecha_de_beneficio"], format="%Y/%m/%d", errors="coerce")
    )
    df["fecha_de_beneficio"] = dates.dt.strftime("%Y-%m-%d")

    df["comuna_ciudadano"] = df["comuna_ciudadano"].astype("Int64")

    # Registros incompletos (comuna_ciudadano puede faltar) y duplicados
    required = [column for column in df.columns if column != "comuna_ciudadano"]
    df = df.dropna(subset=required)
    df = df.drop_duplicates()

    output_file = Path("submission/solicitudes_de_credito.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, sep=";", index=False)
