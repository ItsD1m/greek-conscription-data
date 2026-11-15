"""Τα γραφήματα -> figures/*.png

x = χρόνος (1974 ως σήμερα). y = αριθμός ανδρών (ή μήνες).
Καμία προβολή στο μέλλον.
"""
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"

BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8880"
SURFACE, GRID = "#fcfcfb", "#e8e7e3"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.size": 11, "font.family": "DejaVu Sans",
    "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.titlecolor": INK, "savefig.facecolor": SURFACE,
})
THOUS = FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))

# Οι αλλαγές στη διάρκεια της θητείας
CHANGES = [
    (2003, "2003\n18→12 μήνες"),
    (2009, "2009\n12→9"),
    (2021, "2021\n9→12"),
    (2026, "2026\nνέος νόμος"),
]


def style(ax, title, sub, ylab):
    ax.set_title(title, fontsize=15, fontweight="bold", loc="left", pad=20)
    ax.annotate(sub, xy=(0, 1.015), xycoords="axes fraction",
                fontsize=10, color=INK3, va="bottom")
    ax.set_ylabel(ylab, fontsize=10)
    ax.set_xlabel("έτος", fontsize=10)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def fig1(model, obs):
    """Το κύριο γράφημα: πόσοι άνδρες, κάθε χρόνο, από το 1974 ως σήμερα."""
    f, ax = plt.subplots(figsize=(13, 7))
    m = model.dropna(subset=["potential_cohort"])

    ax.fill_between(m.year, m.low, m.high, color=ORANGE, alpha=0.18, lw=0,
                    zorder=2)
    ax.plot(m.year, m.potential_cohort, color=BLUE, lw=3, zorder=4,
            label="Άνδρες σε ηλικία στράτευσης (από τις γεννήσεις - πραγματικά στοιχεία)")
    ax.plot(m.year, m.conscripts_modeled, color=ORANGE, lw=2.6,
            ls=(0, (6, 3)), zorder=5,
            label="Εκτίμηση κατατάξεων (66% της κοόρτης - εκτίμηση, όχι μέτρηση)")

    o = obs[(obs.metric == "enlisted") & obs.year.notna()]
    for _, r in o.iterrows():
        ax.scatter(r.year, r.value, s=240, marker="o", color=ORANGE,
                   edgecolor=SURFACE, lw=3, zorder=8,
                   label="Το μόνο επίσημο νούμερο: 35.000 κατατάξεις/χρόνο")

    for yr in (1976, 2026):
        v = m.loc[m.year == yr, "potential_cohort"].iloc[0]
        ax.annotate(f"{int(v):,}".replace(",", "."), xy=(yr, v),
                    xytext=(0, 14), textcoords="offset points",
                    fontsize=11.5, color=BLUE, ha="center", fontweight="bold")

    for yr, lab in CHANGES:
        ax.axvline(yr, color=RED, lw=1.2, ls=(0, (4, 3)), alpha=0.5, zorder=1)
        ax.annotate(lab, xy=(yr, 90000), fontsize=9, color=RED, ha="center",
                    va="top", alpha=0.95)

    ax.set_xlim(1974, 2027)
    ax.set_ylim(0, 95000)
    style(ax, "Πόσοι άνδρες κατατάσσονται κάθε χρόνο στην Ελλάδα",
          "1974 - σήμερα. Οι κόκκινες γραμμές είναι οι αλλαγές στη διάρκεια "
          "της θητείας.", "άνδρες")
    ax.yaxis.set_major_formatter(THOUS)
    ax.legend(loc="lower left", fontsize=10.5, frameon=True, framealpha=0.96,
              edgecolor=GRID, facecolor=SURFACE)
    f.tight_layout()
    f.savefig(FIG / "01_katataxeis.png", dpi=170)
    plt.close(f)


def resolve_years(sub, last=2026):
    """year -> μήνες, με «η πιο πρόσφατη εγγραφή κερδίζει»."""
    out = {}
    for _, r in sub.sort_values("start").iterrows():
        end = (pd.to_datetime(r.end_date).year
               if pd.notna(r.end_date) else last)
        for y in range(int(r["start"]), int(end) + 1):
            out[y] = float(r.duration_months)
    s = pd.Series(out).sort_index()
    return s.index.to_list(), s.to_list()


def fig2(timeline):
    f, ax = plt.subplots(figsize=(13, 6))
    t = timeline[(timeline.measure == "actual")
                 & timeline.duration_months.notna()
                 & timeline.branch.isin(["ΣΞ", "ΠΝ", "ΠΑ"])].copy()
    t["start"] = pd.to_datetime(t.start_date).dt.year
    for branch, name, color, lw in (("ΣΞ", "Στρατός Ξηράς", BLUE, 3.2),
                                    ("ΠΝ", "Πολεμικό Ναυτικό", ORANGE, 2.2),
                                    ("ΠΑ", "Πολεμική Αεροπορία", AQUA, 2.2)):
        xs, ys = resolve_years(t[t.branch == branch])
        ax.step(xs, ys, where="post", color=color, lw=lw, label=name)

    ax.axvspan(1974, 2000, color=RED, alpha=0.06, lw=0)
    ax.annotate("1974-1999: δεν βρέθηκε επίσημο έγγραφο.\n"
                "Οι πηγές διαφωνούν μεταξύ τους.",
                xy=(1975, 6.5), fontsize=10, color=RED)
    ax.annotate("24 μήνες", xy=(1978, 24), xytext=(0, 8),
                textcoords="offset points", fontsize=10.5, color=INK2)
    ax.annotate("9 μήνες", xy=(2013, 9), xytext=(0, -22),
                textcoords="offset points", fontsize=10.5, color=INK2)
    ax.set_xlim(1974, 2027)
    ax.set_ylim(0, 27)
    style(ax, "Πόσο κρατούσε η θητεία",
          "Μήνες πραγματικής υπηρεσίας, 1974 - σήμερα.", "μήνες")
    ax.legend(loc="center right", fontsize=10.5, frameon=True,
              facecolor=SURFACE, edgecolor=GRID)
    f.tight_layout()
    f.savefig(FIG / "02_diarkeia_thiteias.png", dpi=170)
    plt.close(f)


def fig3(model):
    """Πόσοι υπηρετούν ταυτόχρονα vs πόσοι μπαίνουν μέσα στη χρονιά."""
    f, ax = plt.subplots(figsize=(13, 6.4))
    m = model.dropna(subset=["serving_modeled"])
    ax.fill_between(m.year, 0, m.serving_modeled, color=BLUE, alpha=0.14, lw=0)
    ax.plot(m.year, m.serving_modeled, color=BLUE, lw=3,
            label="Στρατεύσιμοι που υπηρετούν ταυτόχρονα")
    ax.plot(m.year, m.conscripts_modeled, color=ORANGE, lw=2.2,
            ls=(0, (6, 3)), label="Κατατάξεις μέσα στη χρονιά")

    for yr, lab in CHANGES[:3]:
        ax.axvline(yr, color=RED, lw=1.2, ls=(0, (4, 3)), alpha=0.5, zorder=1)
        ax.annotate(lab, xy=(yr, 113000), fontsize=9, color=RED, ha="center",
                    va="top", alpha=0.95)

    ax.annotate("Όταν κόβεται η θητεία πέφτουν οι υπηρετούντες,\n"
                "ακόμα κι αν κατατάσσονται οι ίδιοι άνθρωποι.",
                xy=(2004.5, 72000), fontsize=10.5, color=INK2)
    ax.set_xlim(1974, 2027)
    ax.set_ylim(0, 120000)
    style(ax, "Πόσοι φαντάροι ήταν μέσα κάθε στιγμή",
          "Δύο διαφορετικά πράγματα: πόσοι μπαίνουν μέσα στη χρονιά, και "
          "πόσοι είναι μέσα ταυτόχρονα.", "άνδρες")
    ax.yaxis.set_major_formatter(THOUS)
    ax.legend(loc="lower right", fontsize=10.5, frameon=True,
              facecolor=SURFACE, edgecolor=GRID)
    f.tight_layout()
    f.savefig(FIG / "03_ypiretountes.png", dpi=170)
    plt.close(f)


def main() -> None:
    FIG.mkdir(exist_ok=True)
    for old in ("01_katataxeis_1974_2040.png",
                "03_syntelestis_katataxis_alpha.png",
                "04_ypiretountes_apolyseis.png"):
        (FIG / old).unlink(missing_ok=True)
    model = pd.read_csv(PROC / "model_output.csv")
    obs = pd.read_csv(PROC / "conscripts_observed.csv")
    timeline = pd.read_csv(PROC / "service_timeline.csv")
    fig1(model, obs)
    fig2(timeline)
    fig3(model)
    for p in sorted(FIG.glob("*.png")):
        print(f"  {p.name}  {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
