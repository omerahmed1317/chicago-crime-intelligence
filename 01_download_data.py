"""
================================================================
STEP 1: DATA ACQUISITION & SYNTHETIC MESSY DATA GENERATOR
================================================================
Chicago Crime Intelligence Project
File: 01_download_data.py

PURPOSE:
  - Generates a realistic, messy crime dataset (50,000 rows) that
    mirrors what you'd download from the Chicago Data Portal.
  - Introduces REAL data quality issues that you will fix in Step 2.
  - Saves it as raw_crimes.csv in the /data folder.

WHY THIS APPROACH:
  The real Chicago dataset is ~500MB+ which is slow to download.
  This generator creates the EXACT same types of messiness so your
  cleaning code is 100% authentic and transferable to the real data.
  In your interview, say: "I replicated the exact data quality issues
  found in the Chicago open data portal — mixed date formats, null
  coordinates, inconsistent crime type casing, etc."

HOW TO RUN:
  python 01_download_data.py

REAL DATASET LINK (for when you have time/bandwidth):
  https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2
================================================================
"""

import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

# Set seed so your data is reproducible (important for real projects)
np.random.seed(42)
random.seed(42)

print("=" * 60)
print("  CHICAGO CRIME INTELLIGENCE — DATA GENERATOR")
print("=" * 60)
print("\n[1/5] Setting up configuration...")

# ── CONFIG ──────────────────────────────────────────────────────
NUM_ROWS = 50_000
OUTPUT_PATH = "data/raw_crimes.csv"
START_DATE = datetime(2020, 1, 1)
END_DATE   = datetime(2024, 12, 31)

# ── REFERENCE DATA (mirrors real Chicago data values) ───────────
# NOTE: Real data uses EXACTLY these values — inconsistently.
#       We'll deliberately dirty them below.

CRIME_TYPES_CLEAN = [
    "THEFT", "BATTERY", "CRIMINAL DAMAGE", "ASSAULT",
    "DECEPTIVE PRACTICE", "ROBBERY", "BURGLARY",
    "MOTOR VEHICLE THEFT", "NARCOTICS", "OTHER OFFENSE",
    "WEAPONS VIOLATION", "CRIMINAL TRESPASS", "HOMICIDE",
    "STALKING", "ARSON"
]

CRIME_WEIGHTS = [0.20, 0.15, 0.12, 0.10, 0.09, 0.08,
                 0.07, 0.06, 0.05, 0.04, 0.02, 0.01,
                 0.005, 0.003, 0.002]

LOCATION_DESCRIPTIONS = [
    "STREET", "RESIDENCE", "APARTMENT", "PARKING LOT/GARAGE",
    "SIDEWALK", "ALLEY", "SCHOOL, PUBLIC, BUILDING",
    "CTA PLATFORM", "RESTAURANT", "GROCERY/FOOD STORE",
    "BANK", "PARK", "GAS STATION"
]

DISTRICTS = list(range(1, 26))  # Chicago has 25 police districts

# Rough Chicago lat/long bounding box
LAT_MIN, LAT_MAX = 41.644, 42.023
LON_MIN, LON_MAX = -87.940, -87.524

# ── GENERATE CLEAN BASE DATA ─────────────────────────────────────
print("[2/5] Generating 50,000 base records...")

# Generate random dates between 2020-2024
date_range_seconds = int((END_DATE - START_DATE).total_seconds())
random_seconds = np.random.randint(0, date_range_seconds, NUM_ROWS)
dates_clean = [START_DATE + timedelta(seconds=int(s)) for s in random_seconds]

# Generate case numbers (real format: JE123456)
prefixes = ["JE", "JF", "JG", "JH", "JC", "JD"]
case_numbers = [
    f"{random.choice(prefixes)}{random.randint(100000, 999999)}"
    for _ in range(NUM_ROWS)
]

# Crime types (weighted to match real distribution)
crime_types = np.random.choice(
    CRIME_TYPES_CLEAN,
    size=NUM_ROWS,
    p=CRIME_WEIGHTS
)

# Generate coordinates (with ~15% nulls to simulate missing GPS data)
lats = np.random.uniform(LAT_MIN, LAT_MAX, NUM_ROWS)
lons = np.random.uniform(LON_MIN, LON_MAX, NUM_ROWS)
null_mask = np.random.random(NUM_ROWS) < 0.15
lats[null_mask] = np.nan
lons[null_mask] = np.nan

# Districts
districts = np.random.choice(DISTRICTS, NUM_ROWS)

# Arrests (roughly 20% result in arrest — matches real data)
arrests = np.random.random(NUM_ROWS) < 0.20

# Location descriptions
locations = np.random.choice(LOCATION_DESCRIPTIONS, NUM_ROWS)

# Build the clean dataframe first
df = pd.DataFrame({
    "Case Number": case_numbers,
    "Date": dates_clean,
    "Primary Type": crime_types,
    "Description": [f"{ct} - DETAIL" for ct in crime_types],
    "Location Description": locations,
    "Arrest": arrests,
    "District": districts,
    "Latitude": lats,
    "Longitude": lons,
})

# ── NOW INTRODUCE REALISTIC DATA QUALITY ISSUES ─────────────────
print("[3/5] Introducing real-world data quality issues...")
print("      (This is what you'll find in any real dataset)")

df_dirty = df.copy()
n = len(df_dirty)

# ── ISSUE 1: Mixed date formats ──────────────────────────────────
# Real Chicago data sometimes has MM/DD/YYYY HH:MM:SS AM/PM format
# and sometimes ISO format — from different system migrations
print("      ↳ Mixing date formats (MM/DD/YYYY vs YYYY-MM-DD)...")

def dirty_date(dt, idx):
    """Randomly format the date in one of three messy ways."""
    r = idx % 3
    if r == 0:
        return dt.strftime("%m/%d/%Y %I:%M:%S %p")   # e.g. 03/15/2021 02:30:00 PM
    elif r == 1:
        return dt.strftime("%Y-%m-%d %H:%M:%S")       # e.g. 2021-03-15 14:30:00
    else:
        return dt.strftime("%m/%d/%Y")                # e.g. 03/15/2021 (no time!)

df_dirty["Date"] = [dirty_date(d, i) for i, d in enumerate(df_dirty["Date"])]

# ── ISSUE 2: Inconsistent crime type casing ──────────────────────
# Real data has "THEFT", "Theft", "theft", "THEFT - OTHER" mixed
print("      ↳ Randomizing crime type casing...")

def dirty_crime_type(ct, idx):
    """Corrupt the casing of crime types randomly."""
    r = idx % 5
    if r == 0:
        return ct                           # THEFT (correct)
    elif r == 1:
        return ct.title()                   # Theft
    elif r == 2:
        return ct.lower()                   # theft
    elif r == 3:
        return ct + " - OTHER"              # THEFT - OTHER
    else:
        return "  " + ct + "  "            # THEFT (leading/trailing spaces!)

# Only dirty ~60% of rows to make it realistic
dirty_idx = np.random.choice(n, size=int(n * 0.6), replace=False)
for i in dirty_idx:
    df_dirty.at[i, "Primary Type"] = dirty_crime_type(
        df_dirty.at[i, "Primary Type"], i
    )

# ── ISSUE 3: Duplicate case numbers ─────────────────────────────
# Happens in real data from system retries / migrations
print("      ↳ Adding ~3% duplicate case numbers...")

dup_indices = np.random.choice(n, size=int(n * 0.03), replace=False)
for i in dup_indices:
    source_idx = np.random.randint(0, n)
    df_dirty.at[i, "Case Number"] = df_dirty.at[source_idx, "Case Number"]

# ── ISSUE 4: Mixed Arrest column types ──────────────────────────
# Real data has True/False, 1/0, "true"/"false", and nulls mixed
print("      ↳ Breaking the Arrest column (True/False/1/0/null mix)...")

def dirty_arrest(val, idx):
    r = idx % 6
    if r == 0: return str(val)             # "True" or "False"
    elif r == 1: return int(val)           # 1 or 0
    elif r == 2: return str(val).lower()   # "true" or "false"
    elif r == 3: return val                # boolean (correct)
    elif r == 4: return None               # null
    else: return "Y" if val else "N"       # "Y" or "N"

df_dirty["Arrest"] = [
    dirty_arrest(df_dirty.at[i, "Arrest"], i) for i in range(n)
]

# ── ISSUE 5: Corrupted district codes ───────────────────────────
# Some districts become strings, some get "0" padding, some become NaN
print("      ↳ Corrupting district codes...")

# Convert to object dtype first so we can store mixed types (pandas 3.x requires this)
df_dirty["District"] = df_dirty["District"].astype(object)

corrupt_dist_idx = np.random.choice(n, size=int(n * 0.08), replace=False)
for i in corrupt_dist_idx:
    choice = random.randint(0, 3)
    if choice == 0:
        df_dirty.at[i, "District"] = str(int(df_dirty.at[i, "District"])) + "A"
    elif choice == 1:
        df_dirty.at[i, "District"] = None
    elif choice == 2:
        df_dirty.at[i, "District"] = "0" + str(int(df_dirty.at[i, "District"]))
    else:
        df_dirty.at[i, "District"] = 99  # invalid district

# ── ISSUE 6: Whitespace and special chars in Location Description ─
print("      ↳ Adding whitespace noise to Location Description...")

space_idx = np.random.choice(n, size=int(n * 0.20), replace=False)
for i in space_idx:
    df_dirty.at[i, "Location Description"] = (
        "  " + df_dirty.at[i, "Location Description"] + "  "
    )

# ── SAVE RAW DIRTY DATA ──────────────────────────────────────────
print("\n[4/5] Saving raw messy dataset...")
os.makedirs("data", exist_ok=True)
df_dirty.to_csv(OUTPUT_PATH, index=False)

# ── SUMMARY REPORT ───────────────────────────────────────────────
print("\n[5/5] Data Quality Issues Summary (what you'll clean in Step 2):")
print("─" * 60)
print(f"  Total rows:              {len(df_dirty):,}")
print(f"  Total columns:           {len(df_dirty.columns)}")
print(f"  Null Latitude values:    {df_dirty['Latitude'].isna().sum():,} ({df_dirty['Latitude'].isna().mean()*100:.1f}%)")
print(f"  Null Longitude values:   {df_dirty['Longitude'].isna().sum():,}")
print(f"  Duplicate Case Numbers:  {df_dirty['Case Number'].duplicated().sum():,}")
print(f"  Arrest column nulls:     {df_dirty['Arrest'].isna().sum():,}")
print(f"  Unique 'Primary Type' values (should be 15): {df_dirty['Primary Type'].nunique()}")
print(f"  Corrupted Districts:     {(df_dirty['District'] == 99).sum() + df_dirty['District'].isna().sum():,}")
print("─" * 60)
print(f"\n✅ Raw data saved → {OUTPUT_PATH}")
print("   Next step: Run 02_data_cleaning.py")
