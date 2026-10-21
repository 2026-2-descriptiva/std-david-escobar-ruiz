from pathlib import Path

import pandas as pd


def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Una autoridad aeronáutica publica cada año un ranking de aerolíneas según
    su tasa de demora, y algunas aerolíneas se quejan de que es injusto: las
    demoras se acumulan a lo largo del día, de modo que una aerolínea con
    muchos vuelos en la tarde y la noche parece peor aunque opere igual de
    bien que las demás. Su tarea es construir un ranking que tenga en cuenta
    la mezcla de horarios de cada aerolínea.

    El archivo `data/flights_by_carrier_day_hour.csv.gz` tiene los vuelos
    nacionales entre 2006 y 2008, agregados por año, mes, día de la semana,
    hora programada de salida (`scheduled_departure_hour`) y aerolínea
    (`reporting_airline`). Use las columnas `operated_flights` (vuelos
    operados) y `delayed_departure_15_flights` (vuelos que salieron con 15
    minutos o más de demora).

    Siga estos pasos:

    1. Calcule la tasa nacional de demora de cada hora programada de salida:
       vuelos demorados sobre vuelos operados, con todas las aerolíneas
       juntas.
    2. Para cada aerolínea, calcule las demoras esperadas: en cada hora,
       multiplique sus vuelos operados por la tasa nacional de esa hora, y
       sume sobre todas las horas. Son las demoras que tendría si en cada hora
       se comportara como el promedio nacional.
    3. Divida las demoras observadas entre las esperadas. Un valor mayor que 1
       significa que la aerolínea se demora más de lo que explican sus
       horarios.

    Genere dos archivos en `submission/`, sin el índice de Pandas y con las
    columnas en el orden indicado:

    1. `hourly_delay_rates.csv`, con una fila por hora, de 0 a 23:
       `scheduled_departure_hour`, `operated_flights`,
       `delayed_departure_15_flights` y `delay_rate`.

    2. `carrier_adjusted_delays.csv`, con una fila por aerolínea:
       `reporting_airline`, `operated_flights`,
       `delayed_departure_15_flights`, `delay_rate` (la tasa sin ajustar),
       `expected_delayed_flights`, `observed_to_expected_ratio`, `crude_rank`
       y `adjusted_rank`. Incluya solamente aerolíneas con al menos 100 000
       vuelos operados. `crude_rank` es la posición según `delay_rate` y
       `adjusted_rank` la posición según `observed_to_expected_ratio`; en
       ambos, 1 es la peor aerolínea. Ordene la tabla por `adjusted_rank`.

    Compare los dos rankings: las aerolíneas que cambian de posición son las
    que el ranking sin ajustar juzga mal por sus horarios.

    La función también debe retornar las dos tablas, en el mismo orden.

    Ejemplo del formato de `carrier_adjusted_delays.csv`:

        reporting_airline,operated_flights,...,crude_rank,adjusted_rank
        EV,819223,...,1,1
        ...
    """

    hour = "scheduled_departure_hour"
    airline = "reporting_airline"
    operated = "operated_flights"
    delayed = "delayed_departure_15_flights"

    df = pd.read_csv("data/flights_by_carrier_day_hour.csv.gz")

    # 1. Tasa nacional de demora por hora programada de salida
    hourly = df.groupby(hour, as_index=False)[[operated, delayed]].sum()
    hourly["delay_rate"] = hourly[delayed] / hourly[operated]
    hourly = hourly.sort_values(hour).reset_index(drop=True)

    # 2. Demoras esperadas: vuelos de la aerolinea en cada hora por la tasa
    # nacional de esa hora (estandarizacion indirecta)
    by_carrier_hour = df.groupby([airline, hour], as_index=False)[[operated, delayed]].sum()
    by_carrier_hour = by_carrier_hour.merge(hourly[[hour, "delay_rate"]], on=hour)
    by_carrier_hour["expected_delayed_flights"] = (
        by_carrier_hour[operated] * by_carrier_hour["delay_rate"]
    )

    carriers = by_carrier_hour.groupby(airline, as_index=False)[
        [operated, delayed, "expected_delayed_flights"]
    ].sum()
    carriers = carriers[carriers[operated] >= 100_000].copy()

    # 3. Razon observado / esperado y rankings (1 = peor)
    carriers["delay_rate"] = carriers[delayed] / carriers[operated]
    carriers["observed_to_expected_ratio"] = (
        carriers[delayed] / carriers["expected_delayed_flights"]
    )
    carriers["crude_rank"] = (
        carriers["delay_rate"].rank(ascending=False, method="first").astype(int)
    )
    carriers["adjusted_rank"] = (
        carriers["observed_to_expected_ratio"]
        .rank(ascending=False, method="first")
        .astype(int)
    )
    carriers = carriers.sort_values("adjusted_rank").reset_index(drop=True)

    hourly[[operated, delayed]] = hourly[[operated, delayed]].astype(int)
    carriers[[operated, delayed]] = carriers[[operated, delayed]].astype(int)
    hourly = hourly.round({"delay_rate": 4})
    carriers = carriers.round(
        {
            "delay_rate": 4,
            "expected_delayed_flights": 4,
            "observed_to_expected_ratio": 4,
        }
    )
    carriers = carriers[
        [
            airline,
            operated,
            delayed,
            "delay_rate",
            "expected_delayed_flights",
            "observed_to_expected_ratio",
            "crude_rank",
            "adjusted_rank",
        ]
    ]

    submission_dir = Path("submission")
    submission_dir.mkdir(parents=True, exist_ok=True)
    hourly.to_csv(submission_dir / "hourly_delay_rates.csv", index=False)
    carriers.to_csv(submission_dir / "carrier_adjusted_delays.csv", index=False)

    return hourly, carriers
