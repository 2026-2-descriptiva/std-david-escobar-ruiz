"""Analisis de equidad salarial entre trayectorias tecnica y directiva.

Lee data/salarios.csv (una fila por empleado) y genera en submission/:

  - department_pay_gap.csv: brecha salarial directiva vs tecnica por
    departamento, sin ajustar y ajustada por categoria
  - high_salary_by_career.csv: participacion de cada trayectoria en los
    salarios altos (decil superior), en total y por categoria
  - compensation_recommendations.csv: celdas departamento-categoria donde la
    trayectoria tecnica gana bastante menos que la directiva en la misma
    categoria, con el ajuste sugerido y su costo
  - analysis_conclusions.csv: conclusiones del analisis con su evidencia

Definiciones:
  - Brecha: mediana directiva / mediana tecnica - 1
  - Brecha sin ajustar: compara todos los directivos con todos los tecnicos
    del grupo, aunque esten en categorias distintas
  - Brecha ajustada: promedio de las brechas dentro de cada categoria en la
    que hay empleados de ambas trayectorias, ponderado por la cantidad de
    empleados de la categoria. Separa el efecto de composicion (los
    directivos se concentran en categorias altas) de la diferencia de pago
    entre personas de la misma categoria
  - Salario alto: salario mayor o igual al percentil 90 de toda la empresa
  - Las recomendaciones solo comparan celdas con al menos MIN_GROUP_SIZE
    empleados en cada trayectoria: la mediana de una o dos personas no es
    una referencia confiable
"""

from pathlib import Path

import pandas as pd

FOLDER = Path(__file__).resolve().parents[1]
DATA_FILE = FOLDER / "data" / "salarios.csv"
SUBMISSION_DIR = FOLDER / "submission"

SALARY = "salario_mensual_cop"
TRACK = "trayectoria"
DIRECTIVA = "Directiva"
TECNICA = "Técnica"
HIGH_SALARY_QUANTILE = 0.9
GAP_THRESHOLD = 0.15  # brecha dentro de categoria que amerita revision
TARGET_GAP = 0.10  # brecha objetivo despues del ajuste
MIN_GROUP_SIZE = 3  # empleados minimos por trayectoria para comparar medianas
CATEGORY_ORDER = ["Analista", "Profesional", "Especialista", "Senior", "Principal"]


def load_data(data_file=DATA_FILE):
    df = pd.read_csv(data_file)
    df["categoria"] = pd.Categorical(
        df["categoria"], categories=CATEGORY_ORDER, ordered=True
    )
    return df


def medians_by_track(df, by):
    table = df.pivot_table(
        index=by, columns=TRACK, values=SALARY, aggfunc=["median", "size"], observed=True
    )
    table.columns = [f"{stat}_{track}" for stat, track in table.columns]
    return table


def adjusted_gap(frame):
    """Brecha promedio dentro de categoria, ponderada por empleados."""
    cells = medians_by_track(frame, "categoria").dropna()
    if cells.empty:
        return float("nan")
    gaps = cells[f"median_{DIRECTIVA}"] / cells[f"median_{TECNICA}"] - 1
    weights = cells[f"size_{DIRECTIVA}"] + cells[f"size_{TECNICA}"]
    return (gaps * weights).sum() / weights.sum()


def gap_summary(frame):
    directiva = frame.loc[frame[TRACK] == DIRECTIVA, SALARY]
    tecnica = frame.loc[frame[TRACK] == TECNICA, SALARY]
    return pd.Series(
        {
            "employees": len(frame),
            "directiva_employees": len(directiva),
            "tecnica_employees": len(tecnica),
            "directiva_median_salary": directiva.median(),
            "tecnica_median_salary": tecnica.median(),
            "unadjusted_gap": directiva.median() / tecnica.median() - 1,
            "adjusted_gap": adjusted_gap(frame),
        }
    )


def department_pay_gap(df):
    table = (
        df.groupby(["gerencia", "departamento"])
        .apply(gap_summary, include_groups=False)
        .reset_index()
    )
    total = gap_summary(df)
    total["gerencia"] = "Total"
    total["departamento"] = "Total empresa"
    table = pd.concat([table, total.to_frame().T], ignore_index=True)
    table["composition_effect"] = table["unadjusted_gap"] - table["adjusted_gap"]
    return finish(table)


def high_salary_by_career(df):
    threshold = df[SALARY].quantile(HIGH_SALARY_QUANTILE)
    df = df.assign(high_salary=df[SALARY] >= threshold)

    def stats(frame):
        return pd.Series(
            {
                "employees": len(frame),
                "high_salary_employees": int(frame["high_salary"].sum()),
                "high_salary_rate": frame["high_salary"].mean(),
                "median_salary": frame[SALARY].median(),
                "mean_technical_experience_years": frame[
                    "experiencia_tecnica_anios"
                ].mean(),
            }
        )

    by_track = df.groupby(TRACK).apply(stats, include_groups=False).reset_index()
    by_track.insert(1, "categoria", "Total")
    by_cell = (
        df.groupby([TRACK, "categoria"], observed=True)
        .apply(stats, include_groups=False)
        .reset_index()
    )
    by_cell["categoria"] = by_cell["categoria"].astype(str)
    table = pd.concat([by_track, by_cell], ignore_index=True)
    table["share_of_high_salaries"] = (
        table["high_salary_employees"] / df["high_salary"].sum()
    )
    table.insert(2, "high_salary_threshold", threshold)
    return finish(table)


def compensation_recommendations(df):
    cells = medians_by_track(df, ["departamento", "categoria"]).dropna().reset_index()
    cells["categoria"] = cells["categoria"].astype(str)
    cells = cells[
        (cells[f"size_{DIRECTIVA}"] >= MIN_GROUP_SIZE)
        & (cells[f"size_{TECNICA}"] >= MIN_GROUP_SIZE)
    ].copy()
    cells["gap"] = cells[f"median_{DIRECTIVA}"] / cells[f"median_{TECNICA}"] - 1
    cells = cells[cells["gap"] > GAP_THRESHOLD].copy()

    cells["target_tecnica_median_salary"] = cells[f"median_{DIRECTIVA}"] / (
        1 + TARGET_GAP
    )
    cells["suggested_raise_pct"] = (
        cells["target_tecnica_median_salary"] / cells[f"median_{TECNICA}"] - 1
    )
    cells["estimated_monthly_cost_cop"] = (
        cells["target_tecnica_median_salary"] - cells[f"median_{TECNICA}"]
    ) * cells[f"size_{TECNICA}"]
    cells["recommendation"] = cells.apply(
        lambda row: (
            f"Revisar el salario de los {int(row[f'size_{TECNICA}'])} empleados "
            f"técnicos de {row['categoria']} en {row['departamento']}: los "
            f"directivos de su misma categoría ganan {row['gap']:.0%} más; "
            f"subir su mediana {row['suggested_raise_pct']:.0%} deja la brecha "
            f"en {TARGET_GAP:.0%}."
        ),
        axis=1,
    )
    cells = cells.rename(
        columns={
            f"size_{DIRECTIVA}": "directiva_employees",
            f"size_{TECNICA}": "tecnica_employees",
            f"median_{DIRECTIVA}": "directiva_median_salary",
            f"median_{TECNICA}": "tecnica_median_salary",
        }
    )
    cells = cells.sort_values("gap", ascending=False).reset_index(drop=True)
    cells.insert(0, "priority", range(1, len(cells) + 1))
    columns = [
        "priority",
        "departamento",
        "categoria",
        "directiva_employees",
        "tecnica_employees",
        "directiva_median_salary",
        "tecnica_median_salary",
        "gap",
        "target_tecnica_median_salary",
        "suggested_raise_pct",
        "estimated_monthly_cost_cop",
        "recommendation",
    ]
    return finish(cells[columns])


def analysis_conclusions(pay_gap, high_salary, recommendations):
    total = pay_gap.loc[pay_gap["departamento"] == "Total empresa"].iloc[0]
    departments = pay_gap[pay_gap["departamento"] != "Total empresa"]
    widest = departments.loc[departments["adjusted_gap"].idxmax()]
    narrowest = departments.loc[departments["adjusted_gap"].idxmin()]
    totals = high_salary[high_salary["categoria"] == "Total"].set_index(TRACK)

    conclusions = [
        (
            "Brecha sin ajustar",
            f"La mediana salarial de la trayectoria directiva es "
            f"{total['unadjusted_gap']:.0%} mayor que la de la técnica.",
            f"{total['directiva_median_salary']:,.0f} vs "
            f"{total['tecnica_median_salary']:,.0f} COP",
        ),
        (
            "Efecto de composición",
            "Gran parte de esa diferencia se explica porque los directivos se "
            "concentran en las categorías más altas; dentro de una misma "
            f"categoría la brecha promedio es {total['adjusted_gap']:.0%}.",
            f"Efecto de composición: {total['composition_effect'] * 100:.0f} "
            "puntos porcentuales",
        ),
        (
            "Brecha que persiste",
            "Aun comparando personas de la misma categoría, los técnicos ganan "
            "menos; la diferencia no se explica solo por el nivel del cargo.",
            f"Brecha ajustada: {total['adjusted_gap']:.0%}",
        ),
        (
            "Departamentos",
            f"La brecha ajustada más alta está en {widest['departamento']} "
            f"({widest['adjusted_gap']:.0%}) y la más baja en "
            f"{narrowest['departamento']} ({narrowest['adjusted_gap']:.0%}).",
            "department_pay_gap.csv",
        ),
        (
            "Salarios altos",
            f"La trayectoria directiva tiene "
            f"{totals.loc[DIRECTIVA, 'share_of_high_salaries']:.0%} de los "
            f"salarios del decil superior con solo "
            f"{totals.loc[DIRECTIVA, 'employees'] / totals['employees'].sum():.0%} "
            f"de los empleados.",
            f"Umbral del decil superior: "
            f"{totals.loc[DIRECTIVA, 'high_salary_threshold']:,.0f} COP",
        ),
        (
            "Recomendación",
            f"Revisar {len(recommendations)} combinaciones departamento-categoría "
            f"con brecha mayor a {GAP_THRESHOLD:.0%}; llevarlas a "
            f"{TARGET_GAP:.0%} cuesta cerca de "
            f"{recommendations['estimated_monthly_cost_cop'].sum():,.0f} COP al mes.",
            "compensation_recommendations.csv",
        ),
    ]
    table = pd.DataFrame(conclusions, columns=["topic", "conclusion", "evidence"])
    table.insert(0, "finding", range(1, len(table) + 1))
    return table


def finish(table):
    table = table.copy()
    for column in table.columns:
        if column.endswith("employees"):
            table[column] = table[column].astype(int)
        elif column.endswith(("_salary", "_cop", "_threshold")):
            table[column] = table[column].astype(float).round(0)
        elif table[column].dtype.kind == "f":
            table[column] = table[column].round(4)
    return table


def main():
    df = load_data()

    pay_gap = department_pay_gap(df)
    high_salary = high_salary_by_career(df)
    recommendations = compensation_recommendations(df)
    conclusions = analysis_conclusions(pay_gap, high_salary, recommendations)

    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    pay_gap.to_csv(SUBMISSION_DIR / "department_pay_gap.csv", index=False)
    high_salary.to_csv(SUBMISSION_DIR / "high_salary_by_career.csv", index=False)
    recommendations.to_csv(
        SUBMISSION_DIR / "compensation_recommendations.csv", index=False
    )
    conclusions.to_csv(SUBMISSION_DIR / "analysis_conclusions.csv", index=False)

    return pay_gap, high_salary, recommendations, conclusions


if __name__ == "__main__":
    main()
