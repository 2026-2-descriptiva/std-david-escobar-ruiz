"""Anonimizacion de datos de clientes.

Lee PRE_05_anonimizacion/data/raw.csv y escribe una version anonimizada en
PRE_05_anonimizacion/submission/anonymized.csv.

Estrategia:
  1. Identificadores directos (name, document_id, email, loyalty_card_number)
     se eliminan; cada registro recibe un record_id aleatorio sin relacion
     con los datos originales.
  2. Cuasi-identificadores (age, city, occupation) se generalizan: rangos de
     edad, region y sector ocupacional. Son los atributos presentes en
     data/auxiliary.csv, que permite un ataque de enlace.
  3. Se aplica k-anonimato: se suprimen los registros cuya combinacion de
     cuasi-identificadores aparece menos de K veces.
  4. El atributo sensible annual_spend se redondea y se acota en el
     percentil 99 (top-coding) para ocultar valores extremos.
"""

import os

import numpy as np
import pandas as pd

FOLDER = "PRE_05_anonimizacion"
RAW_FILE = f"{FOLDER}/data/raw.csv"
AUXILIARY_FILE = f"{FOLDER}/data/auxiliary.csv"
OUTPUT_FILE = f"{FOLDER}/submission/anonymized.csv"

K = 5
SEED = 12345

DIRECT_IDENTIFIERS = ["name", "document_id", "email", "loyalty_card_number"]
QUASI_IDENTIFIERS = ["age_range", "region", "occupation_group"]

REGIONS = {
    "Medellín": "Antioquia",
    "Itagüí": "Antioquia",
    "Bello": "Antioquia",
    "Envigado": "Antioquia",
    "Rionegro": "Antioquia",
    "Pereira": "Eje Cafetero",
    "Manizales": "Eje Cafetero",
    "Cartagena": "Caribe",
    "Barranquilla": "Caribe",
    "Bogotá": "Centro-Oriente",
    "Bucaramanga": "Centro-Oriente",
    "Cali": "Pacífico",
}

OCCUPATION_GROUPS = {
    "Comerciante": "Comercio y administración",
    "Administradora": "Comercio y administración",
    "Contadora": "Finanzas y derecho",
    "Analista financiera": "Finanzas y derecho",
    "Abogada": "Finanzas y derecho",
    "Docente": "Educación y salud",
    "Enfermera": "Educación y salud",
    "Médico": "Educación y salud",
    "Ingeniero de sistemas": "Ingeniería, técnica y diseño",
    "Técnico electricista": "Ingeniería, técnica y diseño",
    "Arquitecta": "Ingeniería, técnica y diseño",
    "Diseñadora gráfica": "Ingeniería, técnica y diseño",
}


# Transformaciones
# -----------------------------------------------------------------------------


def generalize_age(age, width=20):
    lower = (age // width) * width
    return f"{lower}-{lower + width - 1}"


def generalize(df):
    df = df.copy()
    df["age_range"] = df["age"].map(generalize_age)
    df["region"] = df["city"].map(REGIONS).fillna("Otra")
    df["occupation_group"] = df["occupation"].map(OCCUPATION_GROUPS).fillna("Otra")
    return df


def mask_spend(series, step=100_000, quantile=0.99):
    cap = series.quantile(quantile)
    masked = series.astype(float).clip(upper=cap)
    return (masked / step).round().astype(int) * step


def enforce_k_anonymity(df, quasi_identifiers=QUASI_IDENTIFIERS, k=K):
    sizes = df.groupby(quasi_identifiers)[quasi_identifiers[0]].transform("size")
    return df[sizes >= k].copy()


def anonymize(raw, k=K, seed=SEED):
    df = generalize(raw)
    df["annual_spend"] = mask_spend(df["annual_spend"])
    df = enforce_k_anonymity(df, k=k)

    # Orden aleatorio e identificador sin relacion con los datos originales
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    df.insert(0, "record_id", np.arange(1, len(df) + 1))

    return df[["record_id"] + QUASI_IDENTIFIERS + ["annual_spend"]]


# Verificacion
# -----------------------------------------------------------------------------


def linkage_attack(anonymized, auxiliary):
    """Cuantos registros anonimizados coinciden con cada persona del archivo
    auxiliar. Un valor de 1 significa reidentificacion."""
    auxiliary = generalize(auxiliary)
    matches = auxiliary.merge(anonymized, on=QUASI_IDENTIFIERS, how="left")
    return matches.groupby("name")["record_id"].count()


def main():
    raw = pd.read_csv(RAW_FILE)
    anonymized = anonymize(raw)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    anonymized.to_csv(OUTPUT_FILE, index=False)

    k_min = anonymized.groupby(QUASI_IDENTIFIERS).size().min()
    print(f"Registros originales: {len(raw)}")
    print(f"Registros publicados: {len(anonymized)}")
    print(f"k minimo alcanzado: {k_min}")

    auxiliary = pd.read_csv(AUXILIARY_FILE)
    candidates = linkage_attack(anonymized, auxiliary)
    print(f"Personas reidentificadas (1 candidato): {(candidates == 1).sum()}")
    print(f"Candidatos minimos por persona: {candidates[candidates > 0].min()}")

    return anonymized


if __name__ == "__main__":
    main()
