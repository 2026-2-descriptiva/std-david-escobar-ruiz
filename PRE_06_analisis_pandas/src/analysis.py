"""Analisis de horas y millas registradas por conductor.

Lee drivers.csv y timesheet.csv, calcula el total de horas y millas por
conductor y genera:
  - submission/summary.csv: resumen por conductor
  - submission/top10_drivers.png: los 10 conductores con mas millas
"""

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

FOLDER = "PRE_06_analisis_pandas"
DRIVERS_FILE = f"{FOLDER}/data/drivers.csv"
TIMESHEET_FILE = f"{FOLDER}/data/timesheet.csv"
SUMMARY_FILE = f"{FOLDER}/submission/summary.csv"
PLOT_FILE = f"{FOLDER}/submission/top10_drivers.png"

BAR_COLOR = "#2a78d6"
SURFACE_COLOR = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"


def load_data():
    drivers = pd.read_csv(DRIVERS_FILE)
    timesheet = pd.read_csv(TIMESHEET_FILE)
    return drivers, timesheet


def compute_summary(drivers, timesheet):
    totals = timesheet.groupby("driverId", as_index=False)[
        ["hours-logged", "miles-logged"]
    ].sum()
    summary = pd.merge(
        drivers[["driverId", "name"]], totals, on="driverId", how="inner"
    )
    summary = summary.sort_values("miles-logged", ascending=False)
    return summary.reset_index(drop=True)


def save_summary(summary):
    os.makedirs(os.path.dirname(SUMMARY_FILE), exist_ok=True)
    summary.to_csv(SUMMARY_FILE, index=False)


def plot_top10(summary):
    top10 = summary.nlargest(10, "miles-logged").sort_values("miles-logged")

    fig, ax = plt.subplots(figsize=(8, 5), facecolor=SURFACE_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    bars = ax.barh(top10["name"], top10["miles-logged"], color=BAR_COLOR, height=0.6)
    ax.bar_label(
        bars,
        labels=[f"{v:,.0f}" for v in top10["miles-logged"]],
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
    ax.set_xlim(0, top10["miles-logged"].max() * 1.12)

    fig.tight_layout()
    os.makedirs(os.path.dirname(PLOT_FILE), exist_ok=True)
    fig.savefig(PLOT_FILE, dpi=150, facecolor=SURFACE_COLOR)
    plt.close(fig)


def main():
    drivers, timesheet = load_data()
    summary = compute_summary(drivers, timesheet)
    save_summary(summary)
    plot_top10(summary)
    return summary


if __name__ == "__main__":
    main()
