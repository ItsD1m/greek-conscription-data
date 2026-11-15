"""Χτίζει το conscripts_observed.csv: τα ΠΑΡΑΤΗΡΟΥΜΕΝΑ νούμερα, με πηγή σε κάθε τιμή.

ΤΙΠΟΤΑ δεν υπολογίζεται εδώ και τίποτα δεν συμπληρώνεται - μόνο ό,τι βρέθηκε
τεκμηριωμένο. Η στήλη metric λέει ΤΙ μετρά η τιμή και είναι το κρίσιμο πεδίο:

  enlisted        ροή   - κατατάξεις στρατευσίμων σε ένα ημερολογιακό έτος
  serving         απόθεμα - στρατεύσιμοι που υπηρετούν σε μια στιγμή
  ceiling         απόθεμα - εγκεκριμένη οροφή δύναμης (όχι πραγματική)
  total_personnel απόθεμα - ΣΥΝΟΛΙΚΟ προσωπικό ΕΔ (μόνιμοι+ΕΠΟΠ+κληρωτοί)
  exempted/draft_evaders  - απώλειες στρατευσίμων (πλαίσιο)

type: official | reported | estimate | modeled
"""
import pathlib
import sys

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import pandas as pd
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
ACCESSED = "2026-11-15"

DR = "https://defencereview.gr/protofanis-katastasi-16-500-neoi-ton-chrono"
ES = "http://www.ellinikos-stratos.com/stratologia/thiteia.asp"
ELIAMEP = ("https://www.eliamep.gr/wp-content/uploads/2019/01/"
           "Policy-Paper-No-27-1-convertedFINAL.pdf")
WB_API = ("https://api.worldbank.org/v2/country/GRC/indicator/"
          "MS.MIL.TOTL.P1?format=json&per_page=200")
WB_PAGE = "https://data.worldbank.org/indicator/MS.MIL.TOTL.P1?locations=GR"

# --- ΚΑΤΑΤΑΞΕΙΣ (ροή) -------------------------------------------------------
# Το ΜΟΝΟ νούμερο κατατάξεων που βρέθηκε δημόσια τεκμηριωμένο.
ROWS = [
    dict(
        year=2023, value=35000, metric="enlisted", type="reported",
        source_url=DR, accessed=ACCESSED,
        notes=("ΜΕΣΟΣ ΟΡΟΣ 5ετίας ~2021-2025, ΟΧΙ μέτρηση του 2023. Το έτος "
               "2023 μπαίνει ως μέσο της περιόδου. Αυτολεξεί: «Με μέσο όρο "
               "καταταχθέντων ανά έτος 35.000 την τελευταία πενταετία». "
               "Στοιχεία ΥΠΕΘΑ, όπως παρουσιάστηκαν στη συζήτηση του "
               "Ν.5265/2026 στη Διαρκή Επιτροπή Εθνικής Άμυνας (Δεκ 2025). "
               "Ο αριθμός είναι στρογγυλεμένος."),
    ),
    # --- ΥΠΗΡΕΤΟΥΝΤΕΣ (απόθεμα) -------------------------------------------
    dict(
        year=None, value=41000, metric="serving", type="reported",
        source_url=ES, accessed=ACCESSED,
        notes=("Στρατεύσιμοι που υπηρετούν στον ΣΞ. ΕΤΟΣ ΑΓΝΩΣΤΟ - η σελίδα "
               "περιγράφει το καθεστώς 2021+ (9/12 μήνες) αλλά δεν "
               "χρονολογεί τον πίνακα. ΠΡΟΣΟΧΗ: 41.000+4.850+3.326=49.176 "
               "δεν συμβιβάζεται με 35.000 κατατάξεις x ~11,5/12 μήνες "
               "(~33.500). Πιθανόν οροφή ή παλαιότερο έτος."),
    ),
    dict(year=None, value=4850, metric="serving", type="reported",
         source_url=ES, accessed=ACCESSED,
         notes="Στρατεύσιμοι Πολεμικού Ναυτικού. ΕΤΟΣ ΑΓΝΩΣΤΟ."),
    dict(year=None, value=3326, metric="serving", type="reported",
         source_url=ES, accessed=ACCESSED,
         notes="Στρατεύσιμοι Πολεμικής Αεροπορίας. ΕΤΟΣ ΑΓΝΩΣΤΟ."),
    # --- ΟΡΟΦΕΣ ΔΥΝΑΜΗΣ (απόθεμα, όχι πραγματική επάνδρωση) ---------------
    dict(year=2002, value=126000, metric="ceiling", type="reported",
         source_url=ELIAMEP, accessed=ACCESSED,
         notes=("Οροφή Στρατού Ξηράς πριν τη μείωση της θητείας στο 12μηνο. "
                "ELIAMEP PP 27 σ.13. Οροφή, ΟΧΙ πραγματική δύναμη: το ίδιο "
                "κείμενο αναφέρει επάνδρωση 25-30% στο Δ' Σώμα Στρατού.")),
    dict(year=2003, value=93000, metric="ceiling", type="reported",
         source_url=ELIAMEP, accessed=ACCESSED,
         notes="Οροφή ΣΞ μετά τη μείωση στο 12μηνο (1/1/2003). ELIAMEP σ.13."),
    dict(year=2008, value=103000, metric="ceiling", type="reported",
         source_url=ELIAMEP, accessed=ACCESSED,
         notes=("Αυξημένη οροφή ΕΔ αναγνωρισμένη από ΚΥΣΕΑ (από 93.000). "
                "ELIAMEP σ.14, υποσημ. 20.")),
    # --- ΑΠΩΛΕΙΕΣ ΣΤΡΑΤΕΥΣΙΜΩΝ (πλαίσιο για το alpha) ---------------------
    dict(year=2023, value=16500, metric="annual_loss", type="reported",
         source_url=DR, accessed=ACCESSED,
         notes=("Στρατεύσιμοι/έτος που χάνονται από ανυποταξία κατοίκων "
                "εξωτερικού + απαλλαγές υγείας, μέσος όρος 5ετίας ~2021-2025. "
                "Στοιχεία ΥΠΕΘΑ. Ερμηνεία: ~32% των 35.000 καταταχθέντων. "
                "Είναι ο βασικός λόγος που το alpha δεν είναι 1.")),
    dict(year=2023, value=46000, metric="exempted_health_5y", type="reported",
         source_url=DR, accessed=ACCESSED,
         notes=("Απαλλαχθέντες για λόγους υγείας, ΣΥΝΟΛΟ 5ετίας ~2021-2025 "
                "(το 75% για ψυχικά νοσήματα). Στοιχεία ΥΠΕΘΑ.")),
    dict(year=2023, value=36000, metric="draft_evaders_5y", type="reported",
         source_url=DR, accessed=ACCESSED,
         notes=("Ανυπότακτοι, ΣΥΝΟΛΟ 5ετίας ~2021-2025, από τους οποίους "
                "22.000 κάτοικοι εξωτερικού. Στοιχεία ΥΠΕΘΑ.")),
]

COLS = ["year", "value", "metric", "type", "source_url", "accessed", "notes"]


def world_bank_context() -> list[dict]:
    """ΣΥΝΟΛΙΚΟ προσωπικό ΕΔ - πλαίσιο μόνο, ΔΕΝ είναι κατατάξεις."""
    try:
        r = requests.get(WB_API, timeout=90)
        r.raise_for_status()
        payload = r.json()[1]
    except Exception as exc:
        print(f"[worldbank] παραλείπεται ({exc})", file=sys.stderr)
        return []
    out = []
    for rec in payload:
        if rec["value"] is None:
            continue
        out.append(dict(
            year=int(rec["date"]), value=int(rec["value"]),
            metric="total_personnel", type="estimate",
            source_url=WB_PAGE, accessed=ACCESSED,
            notes=("World Bank MS.MIL.TOTL.P1 (πηγή: IISS Military Balance). "
                   "ΣΥΝΟΛΙΚΟ ενεργό προσωπικό ΕΔ: μόνιμοι + ΕΠΟΠ + κληρωτοί. "
                   "ΔΕΝ είναι κατατάξεις και ΔΕΝ είναι υπηρετούντες "
                   "στρατεύσιμοι. Μόνο ως πλαίσιο."),
        ))
    print(f"[worldbank] {len(out)} έτη", file=sys.stderr)
    return out


def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(ROWS + world_bank_context(), columns=COLS)
    df = df.sort_values(["metric", "year"], na_position="last")
    df["year"] = df["year"].astype("Int64")
    out = PROC / "conscripts_observed.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    print(f"{len(df)} γραμμές -> {out.name}")
    print(df.groupby(["metric", "type"]).size().to_string())


if __name__ == "__main__":
    main()
