"""
================================================================================
FIT2179 DV2 — Pre-filter script
================================================================================

WHAT THIS DOES:
  Reads the big raw CSV/JSON files from data/raw/
  Slices each one down to ONLY what each chart actually needs
  Writes slim, chart-ready files into data/clean/

HOW TO RUN:
  1. Make sure Python 3 is installed.
  2. Open a terminal/command prompt.
  3. Navigate (cd) into your fit2179-dv2 folder.
     Example:  cd ~/Desktop/fit2179-dv2
  4. Install pandas if you don't have it:
        pip install pandas
  5. Run this script:
        python prefilter.py

  After it runs, your data/clean/ folder will be populated with ~10 small files.
  The script prints what it's doing so you can see progress.

  Run it as many times as you want — it just overwrites the outputs.

================================================================================
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths — assume the script is run from inside the fit2179-dv2/ folder
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent.resolve()
RAW = HERE / "data" / "raw"
CLEAN = HERE / "data" / "clean"

CLEAN.mkdir(parents=True, exist_ok=True)

if not RAW.exists():
    sys.exit(f"ERROR: {RAW} does not exist. Put the script in fit2179-dv2/ and the raw files in fit2179-dv2/data/raw/")


def say(msg):
    print(f"  {msg}")


def saved(path, rows=None):
    size_kb = path.stat().st_size / 1024
    extra = f", {rows} rows" if rows is not None else ""
    print(f"  ✓ {path.relative_to(HERE)}  ({size_kb:.1f} KB{extra})")


# ---------------------------------------------------------------------------
# State name lookup — DOSM uses some names that don't match geoBoundaries
# We'll add a 'map_name' column to every state-level output so the Vega-Lite
# `lookup` transform can join cleanly.
# ---------------------------------------------------------------------------
DOSM_TO_MAP = {
    "Johor": "Johor",
    "Kedah": "Kedah",
    "Kelantan": "Kelantan",
    "Melaka": "Malacca",                  # different
    "Negeri Sembilan": "Negeri Sembilan",
    "Pahang": "Pahang",
    "Perak": "Perak",
    "Perlis": "Perlis",
    "Pulau Pinang": "Penang",             # different
    "Sabah": "Sabah",
    "Sarawak": "Sarawak",
    "Selangor": "Selangor",
    "Terengganu": "Terengganu",
    "W.P. Kuala Lumpur": "Kuala Lumpur",  # different
    "W.P. Labuan": "Labuan",              # different
    "W.P. Putrajaya": "Putrajaya",        # different
}


# ===========================================================================
# CHART 1 — "100 Malaysians, then and now"
#   Goal: 3 panels of 100 figures each, sorted by age, coloured above/below
#         today's median age (30.5 from UN WPP 2024).
#   Years: 1970 (DOSM historical), 2024 (DOSM historical), 2040 (UN projection)
# ===========================================================================
print("\n[Chart 1] 100-figures hook — 1970 / 2024 / 2040")

# --- Step 1: Load population data ---
pm_c1 = pd.read_csv(RAW / "population_malaysia.csv")
pm_c1["year"] = pd.to_datetime(pm_c1["date"]).dt.year

# --- Step 2: Build a consistent set of 5-year age bands across years ---
# DOSM bin granularity varies year-to-year; collapse top bins to a single "70+"
def to_band_c1(a):
    if a in ["0-4","5-9","10-14","15-19","20-24","25-29","30-34","35-39","40-44",
             "45-49","50-54","55-59","60-64","65-69"]:
        return a
    if a in ["70-74","75-79","80-84","85+","70+","80+"]:
        return "70+"
    return None

def dosm_year_distribution(year):
    """Get age-band shares for Malaysia in `year` from DOSM."""
    sub = pm_c1[
        (pm_c1["year"] == year)
        & (pm_c1["sex"] == "both")
        & (pm_c1["ethnicity"] == "overall")
    ].copy()
    sub["band"] = sub["age"].apply(to_band_c1)
    sub = sub.dropna(subset=["band"])
    by_band = sub.groupby("band", as_index=False)["population"].sum()
    by_band["share"] = by_band["population"] / by_band["population"].sum()
    return by_band[["band", "share"]]

d_1970 = dosm_year_distribution(1970)
d_2024 = dosm_year_distribution(2024)

# --- Step 3: For 2040, use UN WPP projection (OWID) ---
# OWID gives broad bands only (Under-5s, Under-15s, Under-25s, 25-64, 65+).
# For visual purposes we split broad bands evenly into 5-year sub-bands.
# This is an approximation used ONLY for figure positioning; the headline
# median age (37) is the exact UN-published number.
ag_c1 = pd.read_csv(RAW / "population-by-age-group-with-projections.csv")
for base in ["Total", "Ages 65+", "Ages 25-64", "Under-25s", "Under-15s", "Under-5s"]:
    pc = f"{base} (Projected)"
    if pc in ag_c1.columns:
        ag_c1[base] = ag_c1[base].combine_first(ag_c1[pc])

mal_2040 = ag_c1[(ag_c1["Entity"] == "Malaysia") & (ag_c1["Year"] == 2040)].iloc[0]
t = mal_2040["Total"]
u5, u15, u25 = mal_2040["Under-5s"], mal_2040["Under-15s"], mal_2040["Under-25s"]
a2564, a65 = mal_2040["Ages 25-64"], mal_2040["Ages 65+"]

bin_shares_2040 = {
    "0-4":   u5 / t,
    "5-9":   (u15 - u5) * 0.5 / t,
    "10-14": (u15 - u5) * 0.5 / t,
    "15-19": (u25 - u15) * 0.5 / t,
    "20-24": (u25 - u15) * 0.5 / t,
    "25-29": a2564 * 1/8 / t,
    "30-34": a2564 * 1/8 / t,
    "35-39": a2564 * 1/8 / t,
    "40-44": a2564 * 1/8 / t,
    "45-49": a2564 * 1/8 / t,
    "50-54": a2564 * 1/8 / t,
    "55-59": a2564 * 1/8 / t,
    "60-64": a2564 * 1/8 / t,
    "65-69": a65 * 0.4 / t,
    "70+":   a65 * 0.6 / t,
}
d_2040 = pd.DataFrame([{"band": b, "share": s} for b, s in bin_shares_2040.items()])

# --- Step 4: Allocate each year's shares to 100 figures (largest-remainder method) ---
import numpy as np

def allocate_100(df):
    df = df.copy().sort_values("band").reset_index(drop=True)
    df["raw"] = df["share"] * 100
    df["floor"] = np.floor(df["raw"]).astype(int)
    leftover = 100 - df["floor"].sum()
    df["frac"] = df["raw"] - df["floor"]
    top_idx = df.sort_values("frac", ascending=False).head(leftover).index
    df["count"] = df["floor"]
    df.loc[top_idx, "count"] = df.loc[top_idx, "count"] + 1
    return df[["band", "count"]]

a_1970 = allocate_100(d_1970)
a_2024 = allocate_100(d_2024)
a_2040 = allocate_100(d_2040)

# --- Step 5: Expand each year's allocation into 100 figure rows ---
# Today's median age is 30.5 (from UN WPP 2024, file: median-age.csv).
# We hardcode it here so figure colouring uses a fixed reference across all 3 years.
TODAY_MEDIAN = 30.5
PUBLISHED_MEDIANS = {1970: 16.3, 2024: 30.5, 2040: 36.8}  # source: median-age.csv

BAND_MID = {
    "0-4": 2.5, "5-9": 7.5, "10-14": 12.5, "15-19": 17.5, "20-24": 22.5,
    "25-29": 27.5, "30-34": 32.5, "35-39": 37.5, "40-44": 42.5, "45-49": 47.5,
    "50-54": 52.5, "55-59": 57.5, "60-64": 62.5, "65-69": 67.5, "70+": 75
}

def expand_to_100(alloc, year):
    alloc = alloc.copy()
    alloc["mid"] = alloc["band"].map(BAND_MID)
    alloc = alloc.sort_values("mid")
    rows = []
    idx = 0
    for _, r in alloc.iterrows():
        for _ in range(int(r["count"])):
            rows.append({
                "year": year,
                "figure_idx": idx,
                "age_band": r["band"],
                "age_mid": r["mid"],
                "above_today": int(r["mid"] >= TODAY_MEDIAN),
            })
            idx += 1
    return rows

all_rows = (
    expand_to_100(a_1970, 1970)
    + expand_to_100(a_2024, 2024)
    + expand_to_100(a_2040, 2040)
)
c1_fig = pd.DataFrame(all_rows)

# Add grid positions: 10 columns × 10 rows per panel
c1_fig["col"] = c1_fig["figure_idx"] % 10
c1_fig["row"] = c1_fig["figure_idx"] // 10
c1_fig["median_age"] = c1_fig["year"].map(PUBLISHED_MEDIANS)

out = CLEAN / "01_hundred_figures.csv"
c1_fig.to_csv(out, index=False)
saved(out, len(c1_fig))

# --- Step 6 (legacy): Keep the old median-age slim file too. ---
#   Not used by the active chart, but documents the earlier design.
ma = pd.read_csv(RAW / "median-age.csv")
ma["median_age"] = ma["Median age"].combine_first(ma["Median age (Projected)"])
ma["is_projection"] = ma["Median age"].isna()
countries_c1 = ["Malaysia", "Japan", "France", "Philippines", "Singapore"]
years_c1 = [1970, 2024, 2040]
c1_legacy = ma[ma["Entity"].isin(countries_c1) & ma["Year"].isin(years_c1)][
    ["Entity", "Year", "median_age", "is_projection"]
].rename(columns={"Entity": "country", "Year": "year"})
c1_legacy["median_age"] = c1_legacy["median_age"].round(1)
out = CLEAN / "01_median_age_hook.csv"
c1_legacy.to_csv(out, index=False)
saved(out, len(c1_legacy))


# ===========================================================================
# CHART 2 — population pyramid: Malaysia by age × sex, three years
#   Years: 1980, 2010, 2024
#   Top bins collapsed to "70+" for cross-year comparison (Choice 1)
# ===========================================================================
print("\n[Chart 2] Population pyramid — 1980 / 2010 / 2024")
pm = pd.read_csv(RAW / "population_malaysia.csv")
pm["year"] = pd.to_datetime(pm["date"]).dt.year

# Standard 5-year bins up to 70+, all ethnicities combined, M/F only (not 'both')
keep_ages = ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34",
             "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65-69"]
yrs_c2 = [1980, 2010, 2024]
c2 = pm[
    (pm["year"].isin(yrs_c2))
    & (pm["sex"].isin(["male", "female"]))
    & (pm["ethnicity"] == "overall")
    & (pm["age"] != "overall")
].copy()

# Collapse 70-74 / 75-79 / 80-84 / 85+ / 70+ / 80+ all into a single "70+" row
def bucket(a):
    if a in keep_ages:
        return a
    # treat anything 70+ as one bucket
    return "70+"

c2["age_band"] = c2["age"].apply(bucket)
c2 = (
    c2.groupby(["year", "sex", "age_band"], as_index=False)["population"].sum()
)

# Order age bands for plotting (low→high)
band_order = keep_ages + ["70+"]
c2["age_band_idx"] = c2["age_band"].apply(band_order.index)
c2 = c2.sort_values(["year", "sex", "age_band_idx"]).drop(columns=["age_band_idx"])

# Signed population: females positive, males negative — makes the back-to-back
# pyramid trivial in Vega-Lite (x = signed value, y = age band)
c2["population_signed"] = c2.apply(
    lambda r: r["population"] if r["sex"] == "female" else -r["population"], axis=1
)

# Units: DOSM is in thousands. Convert to absolute people for readability.
c2["population"] = (c2["population"] * 1000).astype(int)
c2["population_signed"] = (c2["population_signed"] * 1000).astype(int)

out = CLEAN / "02_population_pyramid.csv"
c2.to_csv(out, index=False)
saved(out, len(c2))


# ===========================================================================
# CHART 3 — Births vs deaths in Malaysia, national totals per year, 2000–2023
# ===========================================================================
print("\n[Chart 3] National births vs deaths — 2000 onwards")
bs = pd.read_csv(RAW / "birth_state.csv")
ds = pd.read_csv(RAW / "death_state.csv")
bs["year"] = pd.to_datetime(bs["date"]).dt.year
ds["year"] = pd.to_datetime(ds["date"]).dt.year

births = bs.groupby("year", as_index=False)["abs"].sum().rename(columns={"abs": "births"})
deaths = ds.groupby("year", as_index=False)["abs"].sum().rename(columns={"abs": "deaths"})
c3 = births.merge(deaths, on="year")
c3["natural_increase"] = c3["births"] - c3["deaths"]

out = CLEAN / "03_births_vs_deaths.csv"
c3.to_csv(out, index=False)
saved(out, len(c3))


# ===========================================================================
# CHART 4 — TFR slope: by ethnic group, ~2000 vs latest year
#   Note: fertility.csv is national-only and does NOT split by ethnicity at the
#   row level. Ethnic-group TFR isn't published in this file; only ASFR.
#   Pivot: instead show TFR over time as a single line + a slope between 1970
#   and latest, with the 2.1 replacement line.
#   We keep the slope spirit by showing decade snapshots.
# ===========================================================================
print("\n[Chart 4] Total fertility rate trajectory, 1960 → 2023")
fer = pd.read_csv(RAW / "fertility.csv")
fer["year"] = pd.to_datetime(fer["date"]).dt.year
tfr = fer[fer["age_group"] == "tfr"][["year", "fertility_rate"]].copy()
tfr.columns = ["year", "tfr"]
tfr = tfr[tfr["year"] >= 1960]

out = CLEAN / "04_tfr_over_time.csv"
tfr.to_csv(out, index=False)
saved(out, len(tfr))


# ===========================================================================
# CHART 5 — Speed of ageing: years for each country to go from 7% to 14% elderly
# Plus the M49 ↔ ISO code lookup table for the world map join.
# ===========================================================================
print("\n[Chart 5] Speed of ageing — derived per country + M49↔ISO lookup")

ag = pd.read_csv(RAW / "population-by-age-group-with-projections.csv")
# Coalesce historical & projected columns
for base in ["Total", "Ages 65+"]:
    pc = f"{base} (Projected)"
    if pc in ag.columns:
        ag[base] = ag[base].combine_first(ag[pc])
ag["pct_65plus"] = 100 * ag["Ages 65+"] / ag["Total"]

# For each country with an ISO code, find year first reached 7% and 14%
def crossover(grp, threshold):
    s = grp[grp["pct_65plus"] >= threshold]
    return int(s["Year"].min()) if len(s) else None

rows = []
for iso, grp in ag[ag["Code"].notna()].groupby("Code"):
    name = grp["Entity"].iloc[0]
    y7 = crossover(grp, 7)
    y14 = crossover(grp, 14)
    if y7 and y14:
        rows.append({
            "iso_code": iso,
            "country": name,
            "year_reached_7pct": y7,
            "year_reached_14pct": y14,
            "speed_years": y14 - y7,
        })

c5 = pd.DataFrame(rows).sort_values("speed_years")
out = CLEAN / "05_speed_of_ageing.csv"
c5.to_csv(out, index=False)
saved(out, len(c5))

# Now build M49 numeric ↔ ISO 3-letter lookup. The world-110m.json uses M49.
# We embed a minimal lookup focused on countries that *have* speed values, so
# the file stays small. M49 codes are public UN data.
# Source: UN Statistics Division Standard Country or Area Codes (M49)
#         https://unstats.un.org/unsd/methodology/m49/
M49_TO_ISO = {
    4: "AFG", 8: "ALB", 12: "DZA", 20: "AND", 24: "AGO", 28: "ATG", 31: "AZE",
    32: "ARG", 36: "AUS", 40: "AUT", 44: "BHS", 48: "BHR", 50: "BGD", 51: "ARM",
    52: "BRB", 56: "BEL", 60: "BMU", 64: "BTN", 68: "BOL", 70: "BIH", 72: "BWA",
    76: "BRA", 84: "BLZ", 90: "SLB", 92: "VGB", 96: "BRN", 100: "BGR", 104: "MMR",
    108: "BDI", 112: "BLR", 116: "KHM", 120: "CMR", 124: "CAN", 132: "CPV",
    136: "CYM", 140: "CAF", 144: "LKA", 148: "TCD", 152: "CHL", 156: "CHN",
    158: "TWN", 170: "COL", 174: "COM", 178: "COG", 180: "COD", 184: "COK",
    188: "CRI", 191: "HRV", 192: "CUB", 196: "CYP", 203: "CZE", 204: "BEN",
    208: "DNK", 212: "DMA", 214: "DOM", 218: "ECU", 222: "SLV", 226: "GNQ",
    231: "ETH", 232: "ERI", 233: "EST", 234: "FRO", 242: "FJI", 246: "FIN",
    250: "FRA", 254: "GUF", 258: "PYF", 260: "ATF", 262: "DJI", 266: "GAB",
    268: "GEO", 270: "GMB", 275: "PSE", 276: "DEU", 288: "GHA", 292: "GIB",
    296: "KIR", 300: "GRC", 304: "GRL", 308: "GRD", 312: "GLP", 316: "GUM",
    320: "GTM", 324: "GIN", 328: "GUY", 332: "HTI", 336: "VAT", 340: "HND",
    344: "HKG", 348: "HUN", 352: "ISL", 356: "IND", 360: "IDN", 364: "IRN",
    368: "IRQ", 372: "IRL", 376: "ISR", 380: "ITA", 384: "CIV", 388: "JAM",
    392: "JPN", 398: "KAZ", 400: "JOR", 404: "KEN", 408: "PRK", 410: "KOR",
    414: "KWT", 417: "KGZ", 418: "LAO", 422: "LBN", 426: "LSO", 428: "LVA",
    430: "LBR", 434: "LBY", 438: "LIE", 440: "LTU", 442: "LUX", 446: "MAC",
    450: "MDG", 454: "MWI", 458: "MYS", 462: "MDV", 466: "MLI", 470: "MLT",
    478: "MRT", 480: "MUS", 484: "MEX", 492: "MCO", 496: "MNG", 498: "MDA",
    499: "MNE", 504: "MAR", 508: "MOZ", 512: "OMN", 516: "NAM", 520: "NRU",
    524: "NPL", 528: "NLD", 531: "CUW", 533: "ABW", 540: "NCL", 548: "VUT",
    554: "NZL", 558: "NIC", 562: "NER", 566: "NGA", 570: "NIU", 578: "NOR",
    580: "MNP", 583: "FSM", 584: "MHL", 585: "PLW", 586: "PAK", 591: "PAN",
    598: "PNG", 600: "PRY", 604: "PER", 608: "PHL", 616: "POL", 620: "PRT",
    624: "GNB", 626: "TLS", 630: "PRI", 634: "QAT", 642: "ROU", 643: "RUS",
    646: "RWA", 652: "BLM", 654: "SHN", 659: "KNA", 660: "AIA", 662: "LCA",
    663: "MAF", 666: "SPM", 670: "VCT", 674: "SMR", 678: "STP", 682: "SAU",
    686: "SEN", 688: "SRB", 690: "SYC", 694: "SLE", 702: "SGP", 703: "SVK",
    704: "VNM", 705: "SVN", 706: "SOM", 710: "ZAF", 716: "ZWE", 724: "ESP",
    728: "SSD", 729: "SDN", 740: "SUR", 748: "SWZ", 752: "SWE", 756: "CHE",
    760: "SYR", 762: "TJK", 764: "THA", 768: "TGO", 772: "TKL", 776: "TON",
    780: "TTO", 784: "ARE", 788: "TUN", 792: "TUR", 795: "TKM", 796: "TCA",
    798: "TUV", 800: "UGA", 804: "UKR", 807: "MKD", 818: "EGY", 826: "GBR",
    831: "GGY", 832: "JEY", 833: "IMN", 834: "TZA", 840: "USA", 850: "VIR",
    854: "BFA", 858: "URY", 860: "UZB", 862: "VEN", 876: "WLF", 882: "WSM",
    887: "YEM", 894: "ZMB",
}
lookup_df = pd.DataFrame(
    [{"m49": k, "iso_code": v} for k, v in M49_TO_ISO.items()]
)
out = CLEAN / "_m49_to_iso.csv"
lookup_df.to_csv(out, index=False)
saved(out, len(lookup_df))


# ===========================================================================
# CHART 6 — Life expectancy bump chart, 1960 → 2023, Malaysia + 8 comparators
# Compute rank per year too (so the Vega-Lite spec doesn't have to)
# ===========================================================================
print("\n[Chart 6] Life expectancy ranks, ASEAN + East Asia")
le = pd.read_csv(RAW / "life-expectancy.csv")
comparators = ["Malaysia", "Singapore", "Thailand", "Indonesia", "Vietnam",
               "Philippines", "Japan", "South Korea", "China"]
c6 = le[le["Entity"].isin(comparators) & (le["Year"] >= 1960)].copy()
c6 = c6.rename(columns={"Entity": "country", "Year": "year",
                        "Life expectancy": "life_expectancy"})
c6["life_expectancy"] = c6["life_expectancy"].round(1)
# Rank: 1 = highest life expectancy that year
c6["rank"] = c6.groupby("year")["life_expectancy"].rank(method="min", ascending=False).astype(int)
c6 = c6[["country", "year", "life_expectancy", "rank"]].sort_values(["country", "year"])

out = CLEAN / "06_life_expectancy_bump.csv"
c6.to_csv(out, index=False)
saved(out, len(c6))


# ===========================================================================
# CHART 7 — Malaysia state map: % aged 65+ in 2024 (latest)
# ===========================================================================
print("\n[Chart 7] State % over 65, 2024")
ps = pd.read_csv(RAW / "population_state.csv")
ps["year"] = pd.to_datetime(ps["date"]).dt.year
mask = (
    (ps["year"] == 2024)
    & (ps["sex"] == "both")
    & (ps["ethnicity"] == "overall")
)
ps24 = ps[mask].copy()

# Identify which age rows count toward "65+": 65-69, 70+, 70-74, 75-79, 80+, 80-84, 85+
older = ps24[ps24["age"].isin(["65-69", "70+", "70-74", "75-79", "80+", "80-84", "85+"])]
total = ps24[ps24["age"] == "overall"]

agg_older = older.groupby("state", as_index=False)["population"].sum().rename(columns={"population": "pop_65plus"})
agg_total = total.groupby("state", as_index=False)["population"].sum().rename(columns={"population": "pop_total"})

c7 = agg_older.merge(agg_total, on="state")
c7["pct_65plus"] = (100 * c7["pop_65plus"] / c7["pop_total"]).round(2)
c7["pop_65plus"] = c7["pop_65plus"].round(1)
c7["pop_total"] = c7["pop_total"].round(1)
c7["map_name"] = c7["state"].map(DOSM_TO_MAP)

out = CLEAN / "07_state_65plus_2024.csv"
c7.to_csv(out, index=False)
saved(out, len(c7))


# ===========================================================================
# CHART 8 — Slope: % aged 65+ by state, 2000 vs 2024
# ===========================================================================
print("\n[Chart 8] State % over 65 slope, 2000 vs 2024")
mask = (
    (ps["year"].isin([2000, 2024]))
    & (ps["sex"] == "both")
    & (ps["ethnicity"] == "overall")
)
ps_sub = ps[mask].copy()
older = ps_sub[ps_sub["age"].isin(["65-69", "70+", "70-74", "75-79", "80+", "80-84", "85+"])]
total = ps_sub[ps_sub["age"] == "overall"]

agg_older = older.groupby(["state", "year"], as_index=False)["population"].sum().rename(columns={"population": "pop_65plus"})
agg_total = total.groupby(["state", "year"], as_index=False)["population"].sum().rename(columns={"population": "pop_total"})
c8 = agg_older.merge(agg_total, on=["state", "year"])
c8["pct_65plus"] = (100 * c8["pop_65plus"] / c8["pop_total"]).round(2)
c8["map_name"] = c8["state"].map(DOSM_TO_MAP)
c8 = c8[["state", "map_name", "year", "pct_65plus"]]

out = CLEAN / "08_state_slope_2000_2024.csv"
c8.to_csv(out, index=False)
saved(out, len(c8))


# ===========================================================================
# CHART 9 — Malaysia age bands 0-14, 15-64, 65+ over time, 1970-projected 2040
# Historical: from DOSM (population_malaysia.csv, 1970-2025)
# Projection: from population-by-age-group-with-projections.csv, Malaysia, 2026-2040
# ===========================================================================
print("\n[Chart 9] National age-band shares, 1970 → 2040")

# Historical from DOSM
hist = pm[(pm["sex"] == "both") & (pm["ethnicity"] == "overall")].copy()

def band(a):
    if a in ["0-4", "5-9", "10-14"]: return "0-14"
    if a in ["15-19","20-24","25-29","30-34","35-39","40-44","45-49","50-54","55-59","60-64"]: return "15-64"
    if a in ["65-69","70-74","75-79","80-84","85+","70+","80+"]: return "65+"
    return None

hist["band"] = hist["age"].apply(band)
hist_b = hist.dropna(subset=["band"])
hist_b = hist_b.groupby(["year", "band"], as_index=False)["population"].sum()
# Get totals from 'overall' age row to avoid double-count
totals_h = hist[hist["age"] == "overall"].groupby("year", as_index=False)["population"].sum().rename(columns={"population": "total"})
hist_b = hist_b.merge(totals_h, on="year")
hist_b["pct"] = (100 * hist_b["population"] / hist_b["total"]).round(2)
hist_b["source"] = "historical"
hist_b = hist_b[["year", "band", "pct", "source"]]

# Projection from OWID — Malaysia, 2026–2040
proj_mal = ag[ag["Entity"] == "Malaysia"].copy()
# coalesce columns (already done for Total and Ages 65+; do the others too)
for base in ["Ages 25-64", "Under-25s", "Under-15s", "Under-5s"]:
    pc = f"{base} (Projected)"
    if pc in proj_mal.columns:
        proj_mal[base] = proj_mal[base].combine_first(proj_mal[pc])

proj_mal["band_0_14"] = proj_mal["Under-15s"]
proj_mal["band_15_64"] = proj_mal["Total"] - proj_mal["Under-15s"] - proj_mal["Ages 65+"]
proj_mal["band_65plus"] = proj_mal["Ages 65+"]

proj_long = proj_mal[(proj_mal["Year"] >= 2026) & (proj_mal["Year"] <= 2040)].melt(
    id_vars=["Year", "Total"],
    value_vars=["band_0_14", "band_15_64", "band_65plus"],
    var_name="band", value_name="population",
)
proj_long["band"] = proj_long["band"].map({"band_0_14": "0-14", "band_15_64": "15-64", "band_65plus": "65+"})
proj_long["pct"] = (100 * proj_long["population"] / proj_long["Total"]).round(2)
proj_long["source"] = "projection"
proj_long = proj_long.rename(columns={"Year": "year"})[["year", "band", "pct", "source"]]

c9 = pd.concat([hist_b, proj_long]).sort_values(["year", "band"])
out = CLEAN / "09_age_bands_1970_2040.csv"
c9.to_csv(out, index=False)
saved(out, len(c9))


# ===========================================================================
# CHART 10 — Per-state: 65+ count, working-age count, old-age dependency ratio
# Old-age dependency ratio = (65+ count) / (15-64 count) × 100
# ===========================================================================
print("\n[Chart 10] State 65+ count + old-age dependency ratio, 2024")
working = ps24[ps24["age"].isin(
    ["15-19","20-24","25-29","30-34","35-39","40-44","45-49","50-54","55-59","60-64"]
)]
agg_work = working.groupby("state", as_index=False)["population"].sum().rename(columns={"population": "pop_15_64"})
c10 = agg_older.merge(agg_work, on="state")
c10["old_age_dep_ratio"] = (100 * c10["pop_65plus"] / c10["pop_15_64"]).round(2)
c10["map_name"] = c10["state"].map(DOSM_TO_MAP)
# Absolute count (in thousands, so the bubble area scales nicely)
c10["pop_65plus_thousands"] = c10["pop_65plus"].round(1)
c10 = c10[["state", "map_name", "pop_65plus_thousands", "pop_15_64", "old_age_dep_ratio"]]

out = CLEAN / "10_state_bubbles.csv"
c10.to_csv(out, index=False)
saved(out, len(c10))


# ===========================================================================
# Copy small static reference files into clean/ so the page only loads from one place
# ===========================================================================
print("\n[Copy] Map files → clean/")
import shutil
shutil.copy(RAW / "geoBoundaries-MYS-ADM1_simplified.geojson",
            CLEAN / "malaysia-states.geojson")
saved(CLEAN / "malaysia-states.geojson")
shutil.copy(RAW / "world-110m.json", CLEAN / "world-110m.json")
saved(CLEAN / "world-110m.json")

# ===========================================================================
# Summary
# ===========================================================================
print("\n" + "=" * 60)
print("All done.")
total_size = sum(f.stat().st_size for f in CLEAN.iterdir()) / 1024
print(f"data/clean/ now contains {len(list(CLEAN.iterdir()))} files, total ~{total_size:.0f} KB")
print("=" * 60)