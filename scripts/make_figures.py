"""Τα τέσσερα γραφήματα -> figures/*.png

Άξονας x: χρόνος (έτος). Άξονας y: αριθμός (ή μήνες / λόγος).
Παλέτα: οι 3 πρώτες κατηγορικές θέσεις τεκμηριωμένης παλέτας (μπλε,
πορτοκαλί, aqua) + κόκκινο για τα θεσμικά ορόσημα. Η σειρά είναι σταθερή,
ποτέ κυκλική, και κάθε γράφημα με >=2 σειρές έχει υπόμνημα.
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

MARKERS = {"official": "o", "reported": "s", "estimate": "^", "modeled": "D"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.size": 10, "font.family": "DejaVu Sans",
    "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.titlecolor": INK, "savefig.facecolor": SURFACE,
})
THOUS = FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))

CHANGES = [
    (2003, "1/1/2003: ΣΞ 18 -> 12 μήνες"),
    (2009, "6/2009: ΣΞ 12 -> 9"),
    (2021, "ΦΕΚ Β 853/2021: 9 -> 12 (9 στα ακριτικά)"),
    (2026, "Ν.5265/2026: νόμιμη 24 -> 12, 4 ΕΣΣΟ, όλοι στον ΣΞ"),
]


def style(ax, title, sub, ylab):
    ax.set_title(title, fontsize=13, fontweight="bold", loc="left", pad=18)
    ax.annotate(sub, xy=(0, 1.013), xycoords="axes fraction",
                fontsize=8.5, color=INK3, va="bottom")
    ax.set_ylabel(ylab, fontsize=9)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def milestones(ax, y, labels=True):
    for yr, lab in CHANGES:
        ax.axvline(yr, color=RED, lw=1, ls=(0, (4, 3)), alpha=0.55, zorder=1)
        if labels:
            ax.annotate(lab, xy=(yr, y), xytext=(4, 0),
                        textcoords="offset points", fontsize=7.2, color=RED,
                        rotation=90, ha="left", va="top", alpha=0.9)


def fig1(model, obs):
    """Κύριο γράφημα. Το ΣΥΝΟΛΙΚΟ προσωπικό ΕΔ μπαίνει σε ΔΙΚΟ ΤΟΥ πάνελ:
    είναι άλλο μέγεθος και άλλη κλίμακα - ποτέ δεύτερος άξονας y."""
    f, (ax, ax2) = plt.subplots(2, 1, figsize=(13.5, 8.8), sharex=True,
                                gridspec_kw={"height_ratios": [2.9, 1]})
    m = model.dropna(subset=["potential_cohort"])
    cal = m[m.alpha_regime == "calibrated"]
    pre = m[m.year <= cal.year.min()]
    post = m[m.year >= cal.year.max()]

    ax.fill_between(m.year, m.low, m.high, color=ORANGE, alpha=0.16, lw=0,
                    label="εύρος σεναρίου α +/-15%", zorder=2)
    ax.plot(m.year, m.potential_cohort, color=BLUE, lw=2.4, zorder=4,
            label="δυνητική κοόρτη (γεννήσεις αγοριών t-19...t-26, ΕΛΣΤΑΤ)")
    ax.plot(pre.year, pre.conscripts_modeled, color=ORANGE, lw=1.6,
            ls=(0, (5, 3)), zorder=5,
            label="κατατάξεις με ΣΤΑΘΕΡΟ α - αντιπαράδειγμα, ΟΧΙ ιστορική εκτίμηση")
    ax.plot(cal.year, cal.conscripts_modeled, color=ORANGE, lw=3.4, zorder=6,
            label="κατατάξεις, παράθυρο βαθμονόμησης α (2021-2025)")
    ax.plot(post.year, post.conscripts_modeled, color=ORANGE, lw=1.6,
            ls=(0, (5, 3)), zorder=5)
    ax.plot(m.year, m.high_max_recovery, color=ORANGE, lw=1, ls=(0, (1, 2)),
            alpha=0.85, zorder=3,
            label="ακραίο σενάριο: ανάκτηση όλων των απωλειών (+47%)")

    o = obs[(obs.metric == "enlisted") & obs.year.notna()]
    for _, r in o.iterrows():
        ax.scatter(r.year, r.value, s=190, marker=MARKERS.get(r.type, "o"),
                   color=ORANGE, edgecolor=SURFACE, lw=2.4, zorder=8)
        ax.annotate("35.000 κατατάξεις/έτος\n(type=reported, μ.ό. 2021-2025,\n"
                    "στοιχεία ΥΠΕΘΑ Δεκ 2025)",
                    xy=(r.year, r.value), xytext=(-180, -58),
                    textcoords="offset points", fontsize=8.5, color=INK2,
                    arrowprops=dict(arrowstyle="-", color=INK3, lw=0.8))

    peak = m.loc[m[m.year >= 2026].potential_cohort.idxmax()]
    trough = m.loc[m[m.year >= 2026].potential_cohort.idxmin()]
    for r, lab in ((peak, "κορυφή"), (trough, "βυθός")):
        ax.scatter(r.year, r.potential_cohort, s=40, color=BLUE,
                   edgecolor=SURFACE, lw=1.6, zorder=9)
        ax.annotate(f"{lab} {int(r.year)}: {int(r.potential_cohort):,}".replace(",", "."),
                    xy=(r.year, r.potential_cohort), xytext=(0, 12),
                    textcoords="offset points", fontsize=8, color=BLUE,
                    ha="center")

    ax.set_xlim(1974, 2041)
    ax.set_ylim(0, 96000)
    milestones(ax, 94000)
    ax.axvspan(1974, 1976, color=INK3, alpha=0.1, lw=0)
    ax.annotate("1974-1975\nχωρίς δεδομένα\n(η ΕΛΣΤΑΤ δεν δίνει\nγεννήσεις κατά\nφύλο για 1941-1955)",
                xy=(1976.4, 62000), fontsize=7.8, color=INK3)
    style(ax, "Πόσοι άνδρες κατατάσσονται κάθε χρόνο στην Ελλάδα, 1974-2040",
          "Δυνητική κοόρτη από τις γεννήσεις (ΕΛΣΤΑΤ / UN WPP) - ΕΝΑ μόνο "
          "παρατηρούμενο σημείο κατατάξεων - οι γεννήσεις ως το 2025 είναι "
          "γνωστές, άρα η κοόρτη ως το 2044 ΔΕΝ είναι πρόβλεψη",
          "αριθμός ανδρών")
    ax.yaxis.set_major_formatter(THOUS)
    ax.legend(loc="lower left", fontsize=8.2, frameon=True, framealpha=0.96,
              edgecolor=GRID, facecolor=SURFACE)

    tp = obs[obs.metric == "total_personnel"].sort_values("year")
    ax2.plot(tp.year, tp.value, color=AQUA, lw=1.8, marker="^", ms=3.5)
    ax2.set_ylim(0, 230000)
    ax2.yaxis.set_major_formatter(THOUS)
    ax2.set_ylabel("ΣΥΝΟΛΙΚΟ ενεργό\nπροσωπικό ΕΔ", fontsize=9)
    ax2.set_xlabel("έτος", fontsize=9)
    ax2.annotate("World Bank MS.MIL.TOTL.P1 (πηγή IISS). ΑΛΛΟ ΜΕΓΕΘΟΣ: μόνιμοι + ΕΠΟΠ + "
                 "κληρωτοί, απόθεμα - ΟΧΙ κατατάξεις. Ξεχωριστό πάνελ ώστε να μη "
                 "συγκρίνεται οπτικά με λάθος κλίμακα.",
                 xy=(0, 1.04), xycoords="axes fraction", fontsize=8, color=INK3)
    ax2.grid(axis="y", color=GRID, lw=0.8)
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    for yr, _ in CHANGES:
        ax2.axvline(yr, color=RED, lw=1, ls=(0, (4, 3)), alpha=0.55)
    f.tight_layout()
    f.savefig(FIG / "01_katataxeis_1974_2040.png", dpi=170)
    plt.close(f)


def resolve_years(sub, last=2026):
    """year -> μήνες, με «η πιο πρόσφατη εγγραφή κερδίζει».

    Το timeline έχει επικαλυπτόμενες/ανοιχτές περιόδους (π.χ. «21 μήνες από
    το 1985, χωρίς end_date» και «24 μήνες το 1996»). Χωρίς αυτή τη λύση το
    step chart πηδάει μπρος-πίσω και δείχνει αλλαγές που δεν υπήρξαν.
    """
    out = {}
    for _, r in sub.sort_values("start").iterrows():
        end = (pd.to_datetime(r.end_date).year
               if pd.notna(r.end_date) else last)
        for y in range(int(r["start"]), int(end) + 1):
            out[y] = float(r.duration_months)
    s = pd.Series(out).sort_index()
    return s.index.to_list(), s.to_list()


def fig2(timeline):
    f, ax = plt.subplots(figsize=(13.5, 6.0))
    t = timeline[(timeline.measure == "actual")
                 & timeline.duration_months.notna()
                 & timeline.branch.isin(["ΣΞ", "ΠΝ", "ΠΑ"])].copy()
    t["start"] = pd.to_datetime(t.start_date).dt.year
    for branch, color, lw in (("ΣΞ", BLUE, 3.0), ("ΠΝ", ORANGE, 2.0),
                              ("ΠΑ", AQUA, 2.0)):
        b = t[t.branch == branch]
        xs, ys = resolve_years(b)
        ax.step(xs, ys, where="post", color=color, lw=lw,
                label=f"{branch} - πραγματική")
        ax.scatter(b["start"], b.duration_months, s=26, color=color,
                   edgecolor=SURFACE, lw=1.2, zorder=5)

    leg = timeline[timeline.measure == "legal"].copy()
    leg["start"] = pd.to_datetime(leg.start_date).dt.year
    xs, ys = resolve_years(leg)
    ax.step(xs, ys, where="post", color=INK3, lw=2.0, ls=(0, (6, 3)),
            label="ΝΟΜΙΜΗ διάρκεια (Ν.1763/1988 - Ν.3421/2005 - Ν.5265/2026)")

    ax.axvspan(1974, 2000, color=RED, alpha=0.06, lw=0)
    ax.annotate("1974-1999: μόνο δευτερογενείς πηγές, κανένα ΦΕΚ.\n"
                "«24 μήνες ως το 1985» / «21 από το 1985» /\n"
                "«22-24-26 στη δεκαετία 80» / «24 μετά τα Ίμια»\n"
                "- αντιφάσκουν μεταξύ τους. Η γραμμή εδώ είναι\n"
                "η καλύτερη δυνατή ανάγνωση, όχι τεκμηριωμένο γεγονός.",
                xy=(1974.6, 3.0), fontsize=8.2, color=RED, alpha=0.95)
    ax.annotate("Το κενό 24 vs 12 μήνες: η ΝΟΜΙΜΗ\nδιάρκεια δεν άλλαξε ποτέ "
                "ως το 2026·\nάλλαζε μόνο ο χρόνος απόλυσης\nμε υπουργική απόφαση.",
                xy=(2009.5, 22.4), fontsize=8.2, color=INK2)
    ax.set_xlim(1974, 2027)
    ax.set_ylim(0, 26.5)
    style(ax, "Διάρκεια στρατιωτικής θητείας στην Ελλάδα ανά κλάδο",
          "Η ΝΟΜΙΜΗ διάρκεια έμεινε 24 μήνες από το 1988 ως το 2026 - ο "
          "πραγματικός χρόνος οριζόταν χαμηλότερα με υπουργικές αποφάσεις. "
          "Γι' αυτό διαφωνούν οι πηγές.", "μήνες")
    ax.set_xlabel("έτος", fontsize=9)
    ax.legend(loc="lower right", fontsize=8.5, frameon=True,
              facecolor=SURFACE, edgecolor=GRID)
    f.tight_layout()
    f.savefig(FIG / "02_diarkeia_thiteias.png", dpi=170)
    plt.close(f)


def fig3(model):
    f, ax = plt.subplots(figsize=(13.5, 5.8))
    m = model.dropna(subset=["potential_cohort"])
    a = float(m.alpha_used.iloc[0])
    cal = m[m.alpha_regime == "calibrated"]

    ax.fill_between(m.year, a * 0.85, a * 1.15, color=ORANGE, alpha=0.16,
                    lw=0, label="εύρος σεναρίου +/-15%")
    ax.plot(m.year, [a] * len(m), color=ORANGE, lw=1.5, ls=(0, (5, 3)),
            label=f"α που χρησιμοποιεί το μοντέλο = {a:.3f} (σταθερό - ΠΑΡΑΔΟΧΗ)")
    ax.plot(cal.year, cal.alpha, color=ORANGE, lw=3.4, zorder=5,
            label="α ΜΕΤΡΗΜΕΝΟ (2021-2025): 35.000 / 53.360 κοόρτη")
    ax.scatter([2023], [a], s=180, marker=MARKERS["reported"], color=ORANGE,
               edgecolor=SURFACE, lw=2.2, zorder=6)

    a_nl = a * (1 + 16500 / 35000)
    ax.axhline(a_nl, color=AQUA, lw=1.9, ls=(0, (2, 2)),
               label=f"α χωρίς τις ετήσιες απώλειες = {a_nl:.3f} "
                     "(+16.500 ανυπότακτοι / απαλλαγές υγείας)")

    ax.axhline(1.0, color=INK3, lw=1, alpha=0.5)
    ax.annotate("α = 1: θα κατατάσσονταν όλη η δυνητική κοόρτη",
                xy=(1976, 1.0), xytext=(0, 6), textcoords="offset points",
                fontsize=8, color=INK3)
    ax.set_xlim(1974, 2041)
    ax.set_ylim(0, 1.12)
    milestones(ax, 1.1, labels=False)
    style(ax, "Συντελεστής κατάταξης α = κατατάξεις / δυνητική κοόρτη",
          "ΠΡΟΣΟΧΗ: το α μετρήθηκε σε ΕΝΑ σημείο. Η επίπεδη γραμμή είναι "
          "παραδοχή, όχι εύρημα - στη δεκαετία 80 ήταν σχεδόν σίγουρα "
          "υψηλότερο (λιγότερες απαλλαγές, λιγότερη μετανάστευση).", "α")
    ax.set_xlabel("έτος", fontsize=9)
    ax.legend(loc="lower left", fontsize=8.5, frameon=True, facecolor=SURFACE,
              edgecolor=GRID)
    f.tight_layout()
    f.savefig(FIG / "03_syntelestis_katataxis_alpha.png", dpi=170)
    plt.close(f)


def fig4(model):
    f, (ax, ax2) = plt.subplots(2, 1, figsize=(13.5, 8.6), sharex=True,
                                gridspec_kw={"height_ratios": [2.4, 1]})
    m = model.dropna(subset=["serving_modeled"])
    cal_lo = model[model.alpha_regime == "calibrated"].year.min()
    ax.fill_between(m.year, m.low * m.duration_months / 12,
                    m.high * m.duration_months / 12, color=BLUE, alpha=0.15,
                    lw=0, label="εύρος σεναρίου α +/-15%")
    ax.plot(m[m.year <= cal_lo].year, m[m.year <= cal_lo].serving_modeled,
            color=BLUE, lw=1.7, ls=(0, (5, 3)),
            label="υπηρετούντες (ΑΠΟΘΕΜΑ) με ΣΤΑΘΕΡΟ α - αντιπαράδειγμα")
    ax.plot(m[m.year >= cal_lo].year, m[m.year >= cal_lo].serving_modeled,
            color=BLUE, lw=2.8,
            label="υπηρετούντες στρατεύσιμοι (ΑΠΟΘΕΜΑ) = κατατάξεις x μήνες/12")
    d = m.dropna(subset=["discharges_modeled"])
    ax.plot(d.year, d.discharges_modeled, color=ORANGE, lw=1.9,
            label="απολύσεις (ΡΟΗ) = κατατάξεις μετατοπισμένες κατά τη θητεία")

    ax.annotate("Αναφερόμενοι υπηρετούντες 49.176\n"
                "(ΣΞ 41.000 + ΠΝ 4.850 + ΠΑ 3.326).\n"
                "Η πηγή δεν δίνει έτος, άρα δεν σχεδιάζεται.\n"
                "Δεν συμβιβάζεται με 35.000 x 11/12 = 32.000.",
                xy=(1976, 66000), fontsize=8.2, color=AQUA)
    spike = d.loc[d.discharges_modeled.idxmax()]
    ax.annotate("Το 2004 απολύονται ΔΥΟ σειρές μαζί: η σειρά του 2002\n"
                "(14 μήνες) και η σειρά του 2003 (12 μήνες). Δεν είναι\n"
                "σφάλμα - είναι η αριθμητική συνέπεια της μείωσης 18->12,\n"
                "το ίδιο φαινόμενο που περιγράφεται ως «μαζική αποστολή\n"
                "λευκών απολυτηρίων» (ΕΛΙΑΜΕΠ PP 27).",
                xy=(spike.year, spike.discharges_modeled), xytext=(70, -118),
                textcoords="offset points", fontsize=8.2, color=ORANGE,
                arrowprops=dict(arrowstyle="-", color=ORANGE, lw=0.9))
    ax.set_xlim(1974, 2041)
    ax.set_ylim(0, 118000)
    milestones(ax, 115000)
    style(ax, "Εκτιμώμενοι υπηρετούντες και απολύσεις",
          "ΡΟΗ vs ΑΠΟΘΕΜΑ: το απόθεμα πέφτει κατακόρυφα όταν κοντύνει η "
          "θητεία, ακόμη κι όταν οι κατατάξεις μένουν σταθερές.", "άνδρες")
    ax.yaxis.set_major_formatter(THOUS)
    ax.legend(loc="lower right", fontsize=8.5, frameon=True, facecolor=SURFACE,
              edgecolor=GRID)

    ax2.step(m.year, m.duration_months, where="post", color=RED, lw=2)
    ax2.fill_between(m.year, 0, m.duration_months, step="post", color=RED,
                     alpha=0.1, lw=0)
    ax2.set_ylim(0, 26)
    ax2.set_ylabel("μήνες θητείας\n(ΣΞ, πραγματική)", fontsize=9)
    ax2.set_xlabel("έτος", fontsize=9)
    ax2.grid(axis="y", color=GRID, lw=0.8)
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    f.tight_layout()
    f.savefig(FIG / "04_ypiretountes_apolyseis.png", dpi=170)
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
