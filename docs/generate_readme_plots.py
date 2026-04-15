"""
Generate README visualizations for all laser-polio-zamfara data files.
Run from the repo root:
    python docs/generate_readme_plots.py
Outputs PNG files to docs/figures/.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DATA_DIR = Path(__file__).parent.parent / "laser_polio_zamfara" / "data"
OUT_DIR = Path(__file__).parent / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def shorten(dot_name):
    """Return just the LGA name from a dot_name."""
    return dot_name.split(":")[-1].replace("_", " ").title()


# ---------------------------------------------------------------------------
# 1. Population, CBR, RI/DPT3
# ---------------------------------------------------------------------------
def plot_demographics():
    df = pd.read_csv(DATA_DIR / "compiled_cbr_pop_ri_sia_underwt_africa.csv")
    # Use most recent year per node
    latest = df.sort_values("year").groupby("dot_name").last().reset_index()
    latest["lga"] = latest["dot_name"].apply(shorten)
    latest = latest.sort_values("pop_total", ascending=False)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    axes[0].barh(latest["lga"], latest["pop_total"] / 1e3, color="steelblue")
    axes[0].set_xlabel("Population (thousands)")
    axes[0].set_title("Population by LGA (latest year)")
    axes[0].invert_yaxis()

    axes[1].plot(
        df.groupby("year")["cbr"].mean(), "o-", color="darkorange", linewidth=2
    )
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("CBR (per 1,000)")
    axes[1].set_title("Crude Birth Rate (Zamfara mean)")

    # RI and DPT3 over time for all nodes
    for dn, grp in df.groupby("dot_name"):
        axes[2].plot(grp["year"], grp["ri_eff"], alpha=0.4, color="steelblue", linewidth=1)
    # Highlight mean
    axes[2].plot(
        df.groupby("year")["ri_eff"].mean(), "o-", color="navy", linewidth=2, label="RI mean"
    )
    axes[2].set_ylim(0, 1)
    axes[2].set_xlabel("Year")
    axes[2].set_ylabel("Coverage")
    axes[2].set_title("Routine Immunization coverage")
    axes[2].legend()

    fig.suptitle("Compiled demographics — Zamfara 14 LGAs", fontsize=13, y=1.01)
    fig.tight_layout()
    out = OUT_DIR / "demographics.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# 2. Age pyramid
# ---------------------------------------------------------------------------
def plot_age_pyramid():
    df = pd.read_csv(DATA_DIR / "Nigeria_age_pyramid_2024.csv")
    fig, ax = plt.subplots(figsize=(6, 6))
    y = np.arange(len(df))
    scale = 1e6
    ax.barh(y, -df["M"] / scale, color="steelblue", label="Male")
    ax.barh(y, df["F"] / scale, color="salmon", label="Female")
    ax.set_yticks(y)
    ax.set_yticklabels(df["Age"])
    ax.set_xlabel("Population (millions)")
    ax.set_title("Nigeria age pyramid (2024)")
    ax.legend()
    xlim = max(df["M"].max(), df["F"].max()) / scale * 1.05
    ax.set_xlim(-xlim, xlim)
    ax.axvline(0, color="black", linewidth=0.8)
    fig.tight_layout()
    out = OUT_DIR / "age_pyramid.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# 3. SIA historic schedule
# ---------------------------------------------------------------------------
def plot_sia_schedule():
    df = pd.read_csv(DATA_DIR / "sia_historic_schedule.csv", parse_dates=["date"])
    df["lga"] = df["dot_name"].apply(shorten)
    # Assign a y-position per LGA
    lgas = sorted(df["lga"].unique())
    lga_y = {l: i for i, l in enumerate(lgas)}
    # Color by vaccine type
    vtypes = df["vaccinetype"].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(vtypes)))
    vcolor = {v: c for v, c in zip(vtypes, colors)}

    fig, ax = plt.subplots(figsize=(12, 5))
    for _, row in df.iterrows():
        ax.scatter(
            row["date"],
            lga_y[row["lga"]],
            color=vcolor[row["vaccinetype"]],
            s=18,
            alpha=0.8,
        )
    # Legend for vaccine types
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=vcolor[v],
                      markersize=8, label=v) for v in vtypes]
    ax.legend(handles=handles, title="Vaccine type", bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.set_yticks(list(lga_y.values()))
    ax.set_yticklabels(list(lga_y.keys()), fontsize=7)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.set_xlabel("Year")
    ax.set_title("SIA historic schedule — Zamfara 14 LGAs")
    fig.tight_layout()
    out = OUT_DIR / "sia_schedule.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# 4. Epi data (cases + ES)
# ---------------------------------------------------------------------------
def plot_epi():
    df = pd.read_hdf(DATA_DIR / "epi_africa_20250408.h5", key="epi")
    df["month_start"] = pd.to_datetime(df["month_start"])
    df["lga"] = df["dot_name"].apply(shorten)

    # Aggregate across LGAs for the summary panels
    agg = df.groupby("month_start")[["cases", "es_samples", "es_positives"]].sum().reset_index()
    agg["es_positivity"] = np.where(agg["es_samples"] > 0,
                                    agg["es_positives"] / agg["es_samples"],
                                    np.nan)

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    # Cases
    axes[0].bar(agg["month_start"], agg["cases"], color="firebrick", width=25)
    axes[0].set_ylabel("Case count")
    axes[0].set_title("AFP cases (Zamfara total)")

    # ES samples
    axes[1].bar(agg["month_start"], agg["es_samples"], color="steelblue", width=25, label="Samples")
    axes[1].bar(agg["month_start"], agg["es_positives"], color="darkorange", width=25, label="Positives")
    axes[1].set_ylabel("ES count")
    axes[1].set_title("Environmental surveillance samples & positives")
    axes[1].legend()

    # ES positivity
    axes[2].plot(agg["month_start"], agg["es_positivity"], color="purple", linewidth=1.5)
    axes[2].set_ylim(0, 1)
    axes[2].set_ylabel("ES positivity rate")
    axes[2].set_title("ES positivity rate (synthetic sinusoidal)")
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[2].xaxis.set_major_locator(mdates.YearLocator(2))
    axes[2].set_xlabel("Year")

    fig.suptitle("Synthetic epi data — Zamfara (2010–2025)", fontsize=13)
    fig.tight_layout()
    out = OUT_DIR / "epi_data.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# 5. Initial immunity age profiles
# ---------------------------------------------------------------------------
def plot_init_immunity():
    age_cols = [c for c in pd.read_hdf(
        DATA_DIR / "init_immunity_0.5coverage_january.h5", key="immunity"
    ).columns if c.startswith("immunity_")]
    # Extract age-group labels (months)
    age_labels = [c.replace("immunity_", "").replace("_", "-") for c in age_cols]

    fig, ax = plt.subplots(figsize=(9, 4))
    for fname, label, color in [
        ("init_immunity_0.5coverage_january.h5", "50% coverage", "steelblue"),
        ("init_immunity_0.8coverage_january.h5", "80% coverage", "darkorange"),
    ]:
        df = pd.read_hdf(DATA_DIR / fname, key="immunity")
        # Take median across nodes and years
        vals = df[age_cols].median()
        ax.plot(range(len(age_cols)), vals, "o-", label=label, color=color, linewidth=2)

    ax.set_xticks(range(len(age_cols)))
    ax.set_xticklabels(age_labels, rotation=45, ha="right", fontsize=7)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Age group (months)")
    ax.set_ylabel("Immunity fraction")
    ax.set_title("Initial immunity by age group (synthetic flat profiles)")
    ax.legend()
    fig.tight_layout()
    out = OUT_DIR / "init_immunity.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# 6. Distance matrix heatmap
# ---------------------------------------------------------------------------
def plot_distance_matrix():
    df = pd.read_hdf(DATA_DIR / "distance_matrix_africa_adm2.h5")
    labels = [shorten(c) for c in df.columns]

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(df.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=7)
    plt.colorbar(im, ax=ax, label="Distance (km)")
    ax.set_title("Haversine distance matrix — Zamfara 14 LGAs")
    fig.tight_layout()
    out = OUT_DIR / "distance_matrix.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


if __name__ == "__main__":
    print(f"Data dir: {DATA_DIR}")
    print(f"Output dir: {OUT_DIR}")
    plot_demographics()
    plot_age_pyramid()
    plot_sia_schedule()
    plot_epi()
    plot_init_immunity()
    plot_distance_matrix()
    print("Done.")
