"""Γραφήματα σε στυλ ειδησεογραφικού site (militaire.gr) -> figures/*.png

Σκούρο φόντο, κόκκινο σήμα, τίτλος μέσα στην εικόνα, πηγές στο υποσέλιδο -
ώστε η εικόνα να στέκεται μόνη της σε άρθρο ή σε social.

Παλέτα: #ff2929 / #4486cd / #17a673 πάνω σε #14171b.
Περνάει και τους 5 ελέγχους (lightness band, chroma, CVD all-pairs,
normal-vision floor, contrast) - βλ. README.

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

BG = "#14171b"
RED, BLUE, GREEN = "#ff2929", "#4486cd", "#17a673"
WHITE, GREY, FAINT = "#ffffff", "#9aa3ad", "#2b3138"

FONT = "Segoe UI"
CREDIT = "Γράφημα: ΔΗΜΟΣ  ·  Δεδομένα & κώδικας: github.com/ItsD1m/greek-conscription-data"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "font.family": FONT, "font.size": 12,
    "axes.edgecolor": FAINT, "axes.labelcolor": GREY,
    "xtick.color": GREY, "ytick.color": GREY,
    "xtick.major.size": 0, "ytick.major.size": 0,
})
THOUS = FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))

CHANGES = [(2003, "2003\nθητεία 18→12"), (2009, "2009\n12→9"),
           (2021, "2021\n9→12"), (2026, "2026\nνέος νόμος")]


def card(kicker, headline, deck, source, size=(12.8, 7.2),
         chart=(0.068, 0.145, 0.90, 0.60), credit=CREDIT, left=0.068):
    """Σκελετός κάρτας: κόκκινο kicker, τίτλος, υπότιτλος, υποσέλιδο πηγών."""
    f = plt.figure(figsize=size, dpi=150)

    right = 1 - left
    f.add_artist(plt.Rectangle((left, 0.930), 0.030, 0.0075,
                               transform=f.transFigure, color=RED, lw=0))
    f.text(left, 0.952, kicker.upper(), color=RED, fontsize=11.5,
           fontweight="bold", va="bottom")
    f.text(left, 0.868, headline, color=WHITE, fontsize=26,
           fontweight="bold", va="top")
    f.text(left, 0.800, deck, color=GREY, fontsize=13, va="top",
           linespacing=1.5)

    f.add_artist(plt.Line2D([left, right], [0.082, 0.082],
                            transform=f.transFigure, color=FAINT, lw=1))
    f.text(left, 0.052, source, color=GREY, fontsize=10, va="center")
    f.text(right, 0.052, credit, color=FAINT, fontsize=9, va="center",
           ha="right")

    ax = f.add_axes(chart)
    ax.grid(axis="y", color=FAINT, lw=0.9)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(FAINT)
    ax.tick_params(labelsize=11.5, pad=6)
    return f, ax


def marks(ax, ytop, labels=True):
    for yr, lab in CHANGES:
        ax.axvline(yr, color=GREY, lw=1, ls=(0, (3, 4)), alpha=0.35, zorder=1)
        if labels:
            ax.annotate(lab, xy=(yr, ytop), fontsize=9.5, color=GREY,
                        ha="center", va="bottom", linespacing=1.5)


def big(ax, x, y, text, color, dx=0, dy=16, ha="center"):
    ax.annotate(text, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                fontsize=17, fontweight="bold", color=color, ha=ha)


def fig1(model, obs):
    f, ax = card(
        "Στρατολογία",
        "Ένας στους τρεις λιγότερος",
        "Οι άνδρες σε ηλικία στράτευσης έπεσαν 32% από το 1976. Η πτώση έγινε\n"
        "σχεδόν ολόκληρη μέσα σε μία δεκαετία, το 2003–2012.",
        "Πηγές: ΕΛΣΤΑΤ (γεννήσεις), ΥΠΕΘΑ (κατατάξεις), ΦΕΚ")
    m = model.dropna(subset=["potential_cohort"])

    ax.fill_between(m.year, 0, m.potential_cohort, color=RED, alpha=0.13, lw=0)
    ax.plot(m.year, m.potential_cohort, color=RED, lw=3.4, zorder=5,
            label="Άνδρες σε ηλικία στράτευσης")
    ax.plot(m.year, m.conscripts_modeled, color=BLUE, lw=2.2, ls=(0, (6, 4)),
            zorder=4, label="Εκτίμηση όσων πράγματι κατατάσσονται")

    o = obs[(obs.metric == "enlisted") & obs.year.notna()]
    for _, r in o.iterrows():
        ax.scatter(r.year, r.value, s=190, color=BLUE, edgecolor=BG, lw=3,
                   zorder=8)
        ax.annotate("35.000\nτο μόνο επίσημο νούμερο", xy=(r.year, r.value),
                    xytext=(-14, -58), textcoords="offset points",
                    fontsize=11, color=BLUE, ha="right", linespacing=1.5)

    for yr, ha, dx in ((1976, "left", -4), (2026, "right", 6)):
        v = m.loc[m.year == yr, "potential_cohort"].iloc[0]
        ax.scatter(yr, v, s=70, color=RED, edgecolor=BG, lw=2.5, zorder=9)
        big(ax, yr, v, f"{int(v):,}".replace(",", "."), WHITE, dx, 14, ha)

    marks(ax, 85000)
    ax.set_xlim(1974, 2028)
    ax.set_ylim(0, 99000)
    ax.yaxis.set_major_formatter(THOUS)
    ax.legend(loc="lower left", fontsize=12, frameon=False,
              labelcolor=[RED, BLUE], handlelength=1.8)
    f.savefig(FIG / "01_katataxeis.png")
    plt.close(f)


def resolve_years(sub, last=2026):
    out = {}
    for _, r in sub.sort_values("start").iterrows():
        end = (pd.to_datetime(r.end_date).year
               if pd.notna(r.end_date) else last)
        for y in range(int(r["start"]), int(end) + 1):
            out[y] = float(r.duration_months)
    s = pd.Series(out).sort_index()
    return s.index.to_list(), s.to_list()


def fig2(timeline):
    f, ax = card(
        "Στρατολογία",
        "Από τα δύο χρόνια στους εννέα μήνες",
        "Η θητεία κόπηκε στο μισό μέσα στη δεκαετία του 2000. Το 2021 ανέβηκε\n"
        "ξανά στους 12 μήνες — 9 για όσους υπηρετούν στα σύνορα.",
        "Πηγές: ΦΕΚ Β΄853/2021, ΦΕΚ Β΄5855/2023, Ν.5265/2026, ΕΛΙΑΜΕΠ, Τύπος")
    t = timeline[(timeline.measure == "actual")
                 & timeline.duration_months.notna()
                 & timeline.branch.isin(["ΣΞ", "ΠΝ", "ΠΑ"])].copy()
    t["start"] = pd.to_datetime(t.start_date).dt.year
    for branch, name, color, lw in (("ΣΞ", "Στρατός Ξηράς", RED, 3.6),
                                    ("ΠΝ", "Πολεμικό Ναυτικό", BLUE, 2.2),
                                    ("ΠΑ", "Πολεμική Αεροπορία", GREEN, 2.2)):
        xs, ys = resolve_years(t[t.branch == branch])
        ax.step(xs, ys, where="post", color=color, lw=lw, label=name)

    ax.axvspan(1974, 2000, color=WHITE, alpha=0.028, lw=0)
    ax.annotate("1974–1999\nδεν βρέθηκε επίσημο έγγραφο·\nοι πηγές διαφωνούν",
                xy=(1975.2, 4.6), fontsize=11, color=GREY, linespacing=1.6)
    for x, y, txt, col in ((1978.5, 24, "24 μήνες", WHITE),
                           (2013, 9, "9 μήνες", WHITE),
                           (2023, 12, "12 μήνες", WHITE)):
        ax.annotate(txt, xy=(x, y), xytext=(0, 12 if y > 10 else -26),
                    textcoords="offset points", fontsize=14,
                    fontweight="bold", color=col, ha="center")
    ax.set_xlim(1974, 2028)
    ax.set_ylim(0, 29)
    ax.set_ylabel("μήνες", fontsize=11.5)
    ax.legend(loc="lower left", fontsize=12, frameon=False,
              labelcolor=[RED, BLUE, GREEN], handlelength=1.8, ncol=3,
              columnspacing=2.2)
    f.savefig(FIG / "02_diarkeia_thiteias.png")
    plt.close(f)


def fig3(model):
    f, ax = card(
        "Στρατολογία",
        "Το στράτευμα άδειασε χωρίς να πέσουν οι κατατάξεις",
        "Από το 2003 ως το 2009 οι φαντάροι που υπηρετούσαν ταυτόχρονα έπεσαν\n"
        "41%, ενώ οι κατατάξεις μόλις 21%. Τη διαφορά την έκανε η θητεία.",
        "Πηγές: ΕΛΣΤΑΤ, ΥΠΕΘΑ, ΦΕΚ  ·  εκτίμηση βάσει διάρκειας θητείας")
    m = model.dropna(subset=["serving_modeled"])
    ax.fill_between(m.year, 0, m.serving_modeled, color=RED, alpha=0.13, lw=0)
    ax.plot(m.year, m.serving_modeled, color=RED, lw=3.4,
            label="Υπηρετούν ταυτόχρονα")
    ax.plot(m.year, m.conscripts_modeled, color=BLUE, lw=2.2, ls=(0, (6, 4)),
            label="Κατατάσσονται μέσα στη χρονιά")

    for yr, col, dy in ((1980, WHITE, 16), (2009, WHITE, 18), (2026, WHITE, 16)):
        v = m.loc[m.year == yr, "serving_modeled"].iloc[0]
        ax.scatter(yr, v, s=70, color=RED, edgecolor=BG, lw=2.5, zorder=9)
        big(ax, yr, v, f"{int(v):,}".replace(",", "."), col, 0, dy)

    marks(ax, 108000)
    ax.set_xlim(1974, 2028)
    ax.set_ylim(0, 126000)
    ax.yaxis.set_major_formatter(THOUS)
    ax.legend(loc="center left", bbox_to_anchor=(0.02, 0.14), fontsize=12,
              frameon=False, labelcolor=[RED, BLUE], handlelength=1.8)
    f.savefig(FIG / "03_ypiretountes.png")
    plt.close(f)


def fig4(model):
    """Κάθετη κάρτα για social (1080x1350)."""
    f, ax = card(
        "Στρατολογία",
        "−32%",
        "",
        "ΕΛΣΤΑΤ · ΥΠΕΘΑ",
        size=(7.2, 9.0), chart=(0.11, 0.155, 0.82, 0.40), left=0.10,
        credit="github.com/ItsD1m/greek-conscription-data")
    f.texts[1].set_fontsize(68)
    f.texts[1].set_y(0.885)
    f.text(0.10, 0.760,
           "λιγότεροι άνδρες σε ηλικία\nστράτευσης απ' ό,τι το 1976",
           color=WHITE, fontsize=19, va="top", linespacing=1.5)
    f.text(0.10, 0.645,
           "81.355  →  55.243\nΗ πτώση έγινε σχεδόν όλη το 2003–2012.",
           color=GREY, fontsize=13.5, va="top", linespacing=1.7)

    m = model.dropna(subset=["potential_cohort"])
    ax.fill_between(m.year, 0, m.potential_cohort, color=RED, alpha=0.15, lw=0)
    ax.plot(m.year, m.potential_cohort, color=RED, lw=3.4)
    for yr in (1976, 2026):
        v = m.loc[m.year == yr, "potential_cohort"].iloc[0]
        ax.scatter(yr, v, s=80, color=RED, edgecolor=BG, lw=3, zorder=9)
    ax.set_xlim(1974, 2028)
    ax.set_ylim(0, 96000)
    ax.yaxis.set_major_formatter(THOUS)
    ax.tick_params(labelsize=11)
    f.savefig(FIG / "04_social_vertical.png")
    plt.close(f)


def main() -> None:
    FIG.mkdir(exist_ok=True)
    model = pd.read_csv(PROC / "model_output.csv")
    obs = pd.read_csv(PROC / "conscripts_observed.csv")
    timeline = pd.read_csv(PROC / "service_timeline.csv")
    fig1(model, obs)
    fig2(timeline)
    fig3(model)
    fig4(model)
    for p in sorted(FIG.glob("*.png")):
        print(f"  {p.name}  {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
