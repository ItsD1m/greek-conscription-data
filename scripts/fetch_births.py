"""Γεννήσεις αγοριών στην Ελλάδα ανά έτος.

ΚΥΡΙΑ ΠΗΓΗ: ΕΛΣΤΑΤ, Φυσική Κίνηση Πληθυσμού (SPO03), πίνακας
  «01. Γεννήσεις - Θάνατοι ζώντων κατά φύλο (1932 - 2025)», στήλη «Άρρενες».
  https://www.statistics.gr/el/statistics/-/publication/SPO03/1932
  Το xlsx αποθηκεύεται στο data/raw/ (βλ. RAW_XLSX) ώστε το αποτέλεσμα να
  αναπαράγεται χωρίς δίκτυο.

ΣΥΜΠΛΗΡΩΜΑΤΙΚΗ ΠΗΓΗ (1950-1955): η ΕΛΣΤΑΤ ΔΕΝ δημοσιεύει γεννήσεις κατά φύλο
  για 1939-1955 (πόλεμος/εμφύλιος: τα έτη 1941-1954 λείπουν τελείως, τα 1939,
  1940 και 1955 έχουν «...» στο φύλο). Για να μπορεί η δυνητική κοόρτη να
  ξεκινά νωρίτερα, τα 1950-1955 συμπληρώνονται από UN WPP 2024 ως
  Births x SRB/(100+SRB). Είναι ΠΑΡΑΓΩΓΗ τιμή και η στήλη source το λέει ρητά.
  ΠΡΟΣΟΧΗ: το WPP διορθώνει για υποκαταγραφή, άρα είναι ~4% πάνω από την
  ΕΛΣΤΑΤ στα κοινά έτη (1956: WPP 164.186 vs ΕΛΣΤΑΤ 158.203 σύνολο). Τα
  1948-1949 λείπουν και από το WPP, άρα πλήρης κοόρτη υπάρχει από το 1976.

ΔΙΑΣΤΑΥΡΩΣΗ: Eurostat demo_fasec [geo=EL, sex=M, age=TOTAL] - καλύπτει μόνο
  2007+, άρα δεν μπορεί να είναι η κύρια πηγή για σειρά από το 1950.

Έξοδος: data/processed/births_male.csv (year, male_births, source)
"""
import json
import pathlib
import sys

try:
    import truststore  # ο Avast σπάει το HTTPS της Python - βλ. README
    truststore.inject_into_ssl()
except ImportError:
    pass

import pandas as pd
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

RAW_XLSX = RAW / "elstat_SPO03_births_deaths_by_sex_1932_2025.xlsx"
ELSTAT_PAGE = "https://www.statistics.gr/el/statistics/-/publication/SPO03/1932"
ELSTAT_DOC_ID = 116911
SOURCE = (
    "ΕΛΣΤΑΤ, Φυσική Κίνηση Πληθυσμού (SPO03), πίν. «Γεννήσεις - Θάνατοι ζώντων "
    f"κατά φύλο (1932-2025)», στήλη Άρρενες | {ELSTAT_PAGE}"
)
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_fasec"

WPP_GZ = RAW / "WPP2024_Demographic_Indicators_Medium.csv.gz"
WPP_URL = (
    "https://population.un.org/wpp/assets/Excel%20Files/"
    "1_Indicator%20(Standard)/CSV_FILES/"
    "WPP2024_Demographic_Indicators_Medium.csv.gz"
)
WPP_SOURCE = (
    "UN World Population Prospects 2024, Demographic Indicators (Medium), "
    "Greece (LocID 300) | ΠΑΡΑΓΩΓΗ: male_births = Births*1000*SRB/(100+SRB) | "
    f"{WPP_URL}"
)
WPP_GAP_YEARS = range(1950, 1956)  # η ΕΛΣΤΑΤ δεν δίνει φύλο για 1939-1955


def download_elstat() -> None:
    """Κατεβάζει το xlsx της ΕΛΣΤΑΤ αν δεν υπάρχει ήδη στο data/raw/."""
    if RAW_XLSX.exists():
        print(f"[elstat] υπάρχει: {RAW_XLSX.name}", file=sys.stderr)
        return
    import re
    from html import unescape

    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    page = s.get(ELSTAT_PAGE, timeout=90).text
    m = re.search(rf'href="([^"]*documentID={ELSTAT_DOC_ID}[^"]*)"', page)
    if not m:
        raise SystemExit(
            "Δεν βρέθηκε ο σύνδεσμος του πίνακα στη σελίδα της ΕΛΣΤΑΤ.\n"
            f"Κατέβασέ τον χειροκίνητα από {ELSTAT_PAGE}\n"
            f"(«01. Γεννήσεις - Θάνατοι ζώντων κατά φύλο») και βάλ' τον ως\n"
            f"{RAW_XLSX}"
        )
    r = s.get(unescape(m.group(1)), headers={"Referer": ELSTAT_PAGE}, timeout=120)
    r.raise_for_status()
    RAW_XLSX.write_bytes(r.content)
    print(f"[elstat] {len(r.content)} bytes -> {RAW_XLSX.name}", file=sys.stderr)


def parse_elstat() -> pd.DataFrame:
    """Έτος + Άρρενες από το φύλλο της ΕΛΣΤΑΤ (στήλες 0 και 2, χωρίς header)."""
    raw = pd.read_excel(RAW_XLSX, sheet_name=0, header=None)
    df = raw[[0, 2]].copy()
    df.columns = ["year", "male_births"]
    df = df[pd.to_numeric(df["year"], errors="coerce").between(1900, 2100)]
    df["year"] = df["year"].astype(int)
    df["male_births"] = pd.to_numeric(df["male_births"], errors="coerce")
    df = df.dropna(subset=["male_births"])
    df["male_births"] = df["male_births"].astype(int)
    return df.sort_values("year").reset_index(drop=True)


def wpp_gap_fill() -> pd.DataFrame:
    """Γεννήσεις αγοριών 1950-1955 από UN WPP, όπου λείπει η ΕΛΣΤΑΤ."""
    if not WPP_GZ.exists():
        print(f"[wpp] κατέβασμα {WPP_URL}", file=sys.stderr)
        r = requests.get(WPP_URL, timeout=600)
        r.raise_for_status()
        WPP_GZ.write_bytes(r.content)
    d = pd.read_csv(WPP_GZ, compression="gzip", low_memory=False,
                    usecols=["LocID", "Time", "Births", "SRB"])
    d = d[(d.LocID == 300) & (d.Time.isin(WPP_GAP_YEARS))]
    male = (d.Births * 1000.0 * d.SRB / (100.0 + d.SRB)).round().astype(int)
    out = pd.DataFrame({"year": d.Time.astype(int), "male_births": male})
    out["source"] = WPP_SOURCE
    return out.sort_values("year").reset_index(drop=True)


def crosscheck_eurostat(df: pd.DataFrame) -> None:
    """Συγκρίνει ΕΛΣΤΑΤ με Eurostat στα κοινά έτη. Μόνο έλεγχος, όχι πηγή."""
    try:
        r = requests.get(
            EUROSTAT,
            params={"geo": "EL", "sex": "M", "age": "TOTAL", "unit": "NR",
                    "format": "JSON", "lang": "EN"},
            timeout=90,
        )
        r.raise_for_status()
        js = r.json()
    except Exception as exc:  # το cross-check δεν είναι blocking
        print(f"[eurostat] παραλείπεται ({exc})", file=sys.stderr)
        return
    (RAW / "eurostat_demo_fasec_EL_M.json").write_text(
        json.dumps(js, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    idx = js["dimension"]["time"]["category"]["index"]
    euro = {int(y): js["value"].get(str(p)) for y, p in idx.items()}
    el = dict(zip(df["year"], df["male_births"]))
    diffs = [(y, el[y], euro[y]) for y in sorted(set(el) & set(euro)) if euro[y] is not None]
    bad = [(y, a, b) for y, a, b in diffs if a != b]
    print(f"[eurostat] κοινά έτη: {len(diffs)}, διαφορές: {len(bad)}", file=sys.stderr)
    for y, a, b in bad[:10]:
        print(f"           {y}: ΕΛΣΤΑΤ {a} vs Eurostat {b}", file=sys.stderr)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROC.mkdir(parents=True, exist_ok=True)
    download_elstat()
    el = parse_elstat()
    crosscheck_eurostat(el)
    el["source"] = SOURCE

    gap = wpp_gap_fill()
    df = pd.concat([el, gap]).sort_values("year").reset_index(drop=True)
    df = df[df.year >= 1950].reset_index(drop=True)  # το project ξεκινά από το 1950

    out = PROC / "births_male.csv"
    df.to_csv(out, index=False, encoding="utf-8")

    yrs = set(df.year)
    missing = [y for y in range(df.year.min(), df.year.max() + 1) if y not in yrs]
    print(f"{len(df)} έτη: {df.year.min()}-{df.year.max()} -> {out.name}")
    print(f"  κενά (αφήνονται ΚΕΝΑ, χωρίς interpolation): {missing}")
    print(f"  ΕΛΣΤΑΤ: {(df.source == SOURCE).sum()} | UN WPP: {(df.source == WPP_SOURCE).sum()}")
    peak = df.loc[df.male_births.idxmax()]
    print(f"  κορύφωση: {int(peak.year)} = {int(peak.male_births):,}")
    print(f"  {int(df.year.iloc[-1])}: {int(df.male_births.iloc[-1]):,}")


if __name__ == "__main__":
    main()
