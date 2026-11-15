"""Μοντέλο: δυνητική κοόρτη -> alpha -> εκτιμώμενες κατατάξεις, 1976-2026.

Ξεχωρίζει ΠΑΝΤΑ τρία μεγέθη:
  ΡΟΗ      conscripts_modeled - κατατάξεις στο έτος t
  ΑΠΟΘΕΜΑ  serving_modeled    - στρατεύσιμοι υπό τα όπλα στο t
  ΡΟΗ      discharges_modeled - απολύσεις στο t (κατατάξεις μετατοπισμένες)

ΚΑΜΙΑ ΠΡΟΒΛΕΨΗ: το μοντέλο σταματά στο σήμερα (2026). Η δυνητική κοόρτη
βγαίνει εξ ολοκλήρου από πραγματικές, ήδη καταγεγραμμένες γεννήσεις.

Έξοδος: data/processed/model_output.csv
"""
import pathlib

import numpy as np
import pandas as pd
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def potential_cohort(births: pd.DataFrame, weights: dict) -> pd.Series:
    """Σταθμισμένο άθροισμα γεννήσεων αγοριών των ετών t-19 ... t-26.

    Επιστρέφει NaN όπου λείπει έστω ΜΙΑ από τις κοόρτες - καμία συμπλήρωση.
    """
    b = births.set_index("year")["male_births"]
    wsum = sum(weights.values())
    lo, hi = b.index.min(), b.index.max()
    years = range(lo + max(weights), hi + min(weights) + 1)
    out = {}
    for t in years:
        parts = [w * b.get(t - k, np.nan) for k, w in weights.items()]
        out[t] = np.nan if any(pd.isna(p) for p in parts) else sum(parts) / wsum
    return pd.Series(out, name="potential_cohort")


def duration_series(timeline: pd.DataFrame, branch: str,
                    post2021_months: float) -> pd.Series:
    """Πραγματική διάρκεια θητείας (μήνες) ανά έτος για τον δεδομένο κλάδο."""
    t = timeline[(timeline.measure == "actual") & (timeline.branch == branch)].copy()
    t = t.dropna(subset=["duration_months"])
    t["start"] = pd.to_datetime(t.start_date).dt.year
    t["end"] = pd.to_datetime(t.end_date).dt.year
    out = {}
    for _, r in t.sort_values("start").iterrows():
        end = int(r["end"]) if pd.notna(r["end"]) else 2040
        for y in range(int(r["start"]), end + 1):
            out[y] = float(r["duration_months"])
    # Από το 2021 ισχύει το διζωνικό 12/9 -> σταθμισμένη ενεργή διάρκεια
    for y in range(2021, 2041):
        out[y] = post2021_months
    return pd.Series(out, name="duration_months").sort_index()


def main() -> None:
    cfg = load_config()
    weights = {int(k): float(v) for k, v in cfg["cohort"]["weights"].items()}
    end_year = int(cfg["model"]["end_year"])

    births = pd.read_csv(PROC / "births_male.csv")
    obs = pd.read_csv(PROC / "conscripts_observed.csv")
    timeline = pd.read_csv(PROC / "service_timeline.csv")

    cohort = potential_cohort(births, weights)

    # --- alpha: βαθμονόμηση στο μοναδικό παρατηρούμενο σημείο -------------
    enl = obs[(obs.metric == "enlisted") & (obs.type.isin(["official", "reported"]))]
    if len(enl) != 1:
        raise SystemExit(
            f"Το μοντέλο υποθέτει ΕΝΑ σημείο κατατάξεων, βρήκε {len(enl)}.\n"
            "Αν προστέθηκαν νέα, γράψε εδώ κανονική παλινδρόμηση του alpha."
        )
    row = enl.iloc[0]
    # Η τιμή είναι μ.ό. 5ετίας γύρω από το row.year -> ίδιο παράθυρο στην κοόρτη
    win = range(int(row.year) - 2, int(row.year) + 3)
    cohort_win = cohort.reindex(win).mean()
    alpha_hat = float(row.value) / float(cohort_win)

    lo_mult = float(cfg["alpha"]["scenario_low"])
    hi_mult = float(cfg["alpha"]["scenario_high"])

    dur = duration_series(timeline, cfg["service"]["branch_for_derived"],
                          float(cfg["service"]["post2021_effective_months"]))

    years = [y for y in cohort.index if y <= end_year]
    df = pd.DataFrame({"year": years})
    df["potential_cohort"] = df.year.map(cohort).round(0)
    df["alpha"] = np.where(df.year.isin(win), alpha_hat, np.nan)
    df["alpha_used"] = alpha_hat
    # ΠΡΟΣΟΧΗ: εκτός του παραθύρου βαθμονόμησης το alpha ΔΕΝ μετρήθηκε.
    # Τα έτη "extrapolated" είναι αντιπαράδειγμα σταθερού alpha, ΟΧΙ εκτίμηση
    # του τι έγινε/θα γίνει. Στη δεκαετία 1980 (θητεία 21-24 μήνες, ελάχιστη
    # μετανάστευση νέων, λιγότερες απαλλαγές) το alpha ήταν σχεδόν σίγουρα
    # υψηλότερο· η γραμμή για το 1976-2020 υποεκτιμά συστηματικά.
    df["alpha_regime"] = np.where(df.year.isin(win), "calibrated", "extrapolated")
    df["conscripts_modeled"] = (df.potential_cohort * alpha_hat).round(0)
    df["low"] = (df.potential_cohort * alpha_hat * lo_mult).round(0)
    df["high"] = (df.potential_cohort * alpha_hat * hi_mult).round(0)
    df["duration_months"] = df.year.map(dur)
    df["serving_modeled"] = (
        df.conscripts_modeled * df.duration_months / 12.0).round(0)

    # Απολύσεις: οι κατατάξεις του t μετατοπισμένες κατά τη ΤΟΤΕ διάρκεια.
    # Μετατόπιση κατά ceil(μήνες/12) έτη: 9 ή 12 μήνες -> +1 έτος,
    # 14-24 μήνες -> +2 έτη. Είναι προσέγγιση σε ετήσια ανάλυση.
    disch = {}
    for y, n in zip(df.year, df.conscripts_modeled):
        m = dur.get(y)
        if m is None or pd.isna(m):
            continue
        shift = int(np.ceil(m / 12.0))
        if y + shift <= end_year:
            disch[y + shift] = disch.get(y + shift, 0.0) + n
    df["discharges_modeled"] = df.year.map(disch)

    out = PROC / "model_output.csv"
    df.to_csv(out, index=False, encoding="utf-8")

    valid = df.dropna(subset=["potential_cohort"])
    print(f"alpha = {alpha_hat:.4f}  "
          f"({int(row.value):,} / {cohort_win:,.0f} μ.ό. κοόρτης {win.start}-{win.stop-1})")
    print(f"κοόρτη: {int(valid.year.min())}-{int(valid.year.max())}, "
          f"{len(valid)} έτη -> {out.name}")
    for y in (1976, 1985, 1995, 2005, 2015, 2026):
        r = df[df.year == y]
        if r.empty or pd.isna(r.potential_cohort.iloc[0]):
            continue
        r = r.iloc[0]
        print(f"  {y}: κοόρτη {int(r.potential_cohort):>7,} | "
              f"κατατάξεις {int(r.conscripts_modeled):>6,} "
              f"[{int(r.low):,}-{int(r.high):,}] | "
              f"υπηρετούντες {int(r.serving_modeled):>6,}")


if __name__ == "__main__":
    main()
