"""Analisis de horas y millas registradas por conductor usando SQLite.

Carga drivers.csv y timesheet.csv en una base de datos SQLite en memoria,
calcula los totales por conductor con SQL y genera:
  - submission/summary.csv: resumen por conductor
  - submission/top10_drivers.png: los 10 conductores con mas millas
"""

import csv
import os
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

FOLDER = Path(__file__).resolve().parents[1]
DRIVERS_FILE = FOLDER / "data" / "drivers.csv"
TIMESHEET_FILE = FOLDER / "data" / "timesheet.csv"
SUMMARY_FILE = FOLDER / "submission" / "summary.csv"
PLOT_FILE = FOLDER / "submission" / "top10_drivers.png"

BAR_COLOR = "#2a78d6"
SURFACE_COLOR = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"

SUMMARY_QUERY = """
    SELECT d.driverId,
           d.name,
           SUM(t.hours_logged) AS hours_logged,
           SUM(t.miles_logged) AS miles_logged
      FROM drivers AS d
      JOIN timesheet AS t
        ON d.driverId = t.driverId
  GROUP BY d.driverId, d.name
  ORDER BY miles_logged DESC
"""


def read_csv(file):
    with open(file, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    return header, rows


def create_database():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE drivers (
            driverId INTEGER PRIMARY KEY,
            name TEXT,
            ssn TEXT,
            location TEXT,
            certified TEXT,
            wage_plan TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE timesheet (
            driverId INTEGER,
            week INTEGER,
            hours_logged INTEGER,
            miles_logged INTEGER
        )
        """
    )

    _, drivers = read_csv(DRIVERS_FILE)
    cur.executemany("INSERT INTO drivers VALUES (?, ?, ?, ?, ?, ?)", drivers)

    _, timesheet = read_csv(TIMESHEET_FILE)
    cur.executemany("INSERT INTO timesheet VALUES (?, ?, ?, ?)", timesheet)

    conn.commit()
    return conn


def compute_summary(conn):
    cur = conn.execute(SUMMARY_QUERY)
    header = [column[0] for column in cur.description]
    rows = cur.fetchall()
    return header, rows


def save_summary(header, rows):
    os.makedirs(os.path.dirname(SUMMARY_FILE), exist_ok=True)
    with open(SUMMARY_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def plot_top10(rows):
    top10 = sorted(rows, key=lambda row: row[3], reverse=True)[:10][::-1]
    names = [row[1] for row in top10]
    miles = [row[3] for row in top10]

    fig, ax = plt.subplots(figsize=(8, 5), facecolor=SURFACE_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    bars = ax.barh(names, miles, color=BAR_COLOR, height=0.6)
    ax.bar_label(
        bars,
        labels=[f"{v:,.0f}" for v in miles],
        padding=4,
        color=TEXT_SECONDARY,
        fontsize=9,
    )

    ax.set_title(
        "Top 10 conductores por millas registradas",
        loc="left",
        color=TEXT_PRIMARY,
        fontsize=13,
    )
    ax.set_xlabel("Millas registradas", color=TEXT_SECONDARY)
    ax.tick_params(colors=TEXT_SECONDARY, length=0)
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )
    ax.grid(axis="x", color="#e4e3df", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, max(miles) * 1.12)

    fig.tight_layout()
    os.makedirs(os.path.dirname(PLOT_FILE), exist_ok=True)
    fig.savefig(PLOT_FILE, dpi=150, facecolor=SURFACE_COLOR)
    plt.close(fig)


def main():
    conn = create_database()
    header, rows = compute_summary(conn)
    conn.close()
    save_summary(header, rows)
    plot_top10(rows)
    return header, rows


if __name__ == "__main__":
    main()
