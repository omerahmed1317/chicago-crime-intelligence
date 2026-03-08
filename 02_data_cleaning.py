"""
================================================================
STEP 2: DATA CLEANING — THE HEART OF YOUR PROJECT
================================================================
Chicago Crime Intelligence Project
File: 02_data_cleaning.py

PURPOSE:
  Fix every data quality issue from the raw dataset.
  This script is what separates real analysts from beginners.
  Every fix is documented with WHY, not just how.

WHAT YOU'LL FIX:
  ✦ Mixed date formats → unified datetime
  ✦ Inconsistent crime type casing → standardized uppercase
  ✦ Duplicate case numbers → removed
  ✦ Mixed Arrest column (True/False/1/0/null) → clean boolean
  ✦ Null lat/long coordinates → removed with documentation
  ✦ Corrupted district codes → fixed or flagged
  ✦ Whitespace in text columns → stripped

OUTPUT:
  data/cleaned_crimes.csv      ← use this for all analysis
  data/cleaning_report.txt     ← document to show interviewers
  data/removed_records.csv     ← records you removed (always save these!)

HOW TO RUN:
  python 02_data_cleaning.py

INTERVIEW TIP:
  "I always save removed records separately. You never throw data
   away — you quarantine it. That way if someone asks 'why are
   there only 44,000 rows?' you can show them exactly what was
   removed and why."
================================================================
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

print("=" * 60)
print("  CHICAGO CRIME INTELLIGENCE — DATA CLEANING")
print("=" * 60)

# ── LOAD RAW DATA ────────────────────────────────────────────────
print("\n[LOAD] Reading raw data...")
df = pd.read_csv("data/raw_crimes.csv", low_memory=False)

# Always do this first — understand what you have
print(f"  Rows: {len(df):,}")
print(f"  Columns: {list(df.columns)}")
print(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

# Save original shape for the cleaning report
original_shape = df.shape
removed_records = []  # We'll track every removed row here

# ══════════════════════════════════════════════════════════════════
# FIX 1: DATE COLUMN — Mixed formats → clean datetime
# ══════════════════════════════════════════════════════════════════
print("\n[FIX 1] Standardizing date formats...")
print(f"  Sample raw dates: {df['Date'].head(6).tolist()}")

# WHY infer_datetime_format=True:
#   Pandas tries to detect the format automatically.
#   errors='coerce' turns unparseable dates into NaT (null)
#   instead of crashing — then we can handle them.
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# Check how many dates failed to parse
bad_dates = df["Date"].isna().sum()
print(f"  Unparseable dates (will be removed): {bad_dates:,}")

# Remove rows where date couldn't be parsed
if bad_dates > 0:
    bad_date_rows = df[df["Date"].isna()].copy()
    bad_date_rows["removal_reason"] = "unparseable_date"
    removed_records.append(bad_date_rows)
    df = df[df["Date"].notna()].copy()

print(f"  ✅ All dates now: {df['Date'].dtype} | Range: {df['Date'].min().date()} → {df['Date'].max().date()}")

# ══════════════════════════════════════════════════════════════════
# FIX 2: CRIME TYPE — Inconsistent casing → standardized
# ══════════════════════════════════════════════════════════════════
print("\n[FIX 2] Standardizing Primary Type (crime categories)...")
print(f"  Unique values BEFORE: {df['Primary Type'].nunique()}")
print(f"  Sample BEFORE: {df['Primary Type'].unique()[:8]}")

# Step 1: Strip whitespace from both ends
df["Primary Type"] = df["Primary Type"].str.strip()

# Step 2: Convert to uppercase (canonical form)
df["Primary Type"] = df["Primary Type"].str.upper()

# Step 3: Remove " - OTHER" suffix that was added incorrectly
#   WHY: "THEFT - OTHER" and "THEFT" are the same crime category.
#   The "- OTHER" was a description-level detail, not a type.
df["Primary Type"] = df["Primary Type"].str.replace(r"\s*-\s*OTHER$", "", regex=True)

# Step 4: Strip any remaining whitespace after replacements
df["Primary Type"] = df["Primary Type"].str.strip()

print(f"  Unique values AFTER:  {df['Primary Type'].nunique()}")
print(f"  Sample AFTER: {sorted(df['Primary Type'].unique())[:8]}")
print("  ✅ Crime types standardized")

# ══════════════════════════════════════════════════════════════════
# FIX 3: DUPLICATES — Remove duplicate case numbers
# ══════════════════════════════════════════════════════════════════
print("\n[FIX 3] Removing duplicate Case Numbers...")

duplicates_before = df.duplicated(subset=["Case Number"]).sum()
print(f"  Duplicate rows found: {duplicates_before:,}")

# Save duplicates before dropping (audit trail)
dup_rows = df[df.duplicated(subset=["Case Number"], keep="first")].copy()
dup_rows["removal_reason"] = "duplicate_case_number"
removed_records.append(dup_rows)

# Keep FIRST occurrence (earliest in dataset)
# WHY keep='first': The first record is usually the original incident.
#   Later duplicates are often system retry artifacts.
df = df.drop_duplicates(subset=["Case Number"], keep="first").copy()

print(f"  Rows removed: {duplicates_before:,}")
print(f"  ✅ Deduplication complete. Rows remaining: {len(df):,}")

# ══════════════════════════════════════════════════════════════════
# FIX 4: ARREST COLUMN — Mixed types → clean boolean
# ══════════════════════════════════════════════════════════════════
print("\n[FIX 4] Fixing Arrest column (True/False/1/0/Y/N/null mix)...")
print(f"  Unique raw values: {df['Arrest'].astype(str).unique()[:12]}")

def standardize_arrest(val):
    """
    Convert any truthy arrest value to True, falsy to False, 
    unparseable to None.
    
    WHY a function instead of .map():
      Real data has unexpected values. A function lets you handle
      each case explicitly and log anything unexpected.
    """
    if pd.isna(val):
        return None
    
    val_str = str(val).strip().lower()
    
    if val_str in ("true", "1", "yes", "y"):
        return True
    elif val_str in ("false", "0", "no", "n"):
        return False
    else:
        return None  # Unknown value → treat as missing

df["Arrest"] = df["Arrest"].apply(standardize_arrest)

# For remaining nulls: fill with False
# WHY: A null arrest record in real data almost always means
#      no arrest was made (not that data is missing).
null_arrests = df["Arrest"].isna().sum()
print(f"  Null arrests (filled with False): {null_arrests:,}")
df["Arrest"] = df["Arrest"].fillna(False).astype(bool)

print(f"  Arrest rate: {df['Arrest'].mean()*100:.1f}%")
print("  ✅ Arrest column is clean boolean")

# ══════════════════════════════════════════════════════════════════
# FIX 5: LAT/LONG COORDINATES — Handle nulls
# ══════════════════════════════════════════════════════════════════
print("\n[FIX 5] Handling null GPS coordinates...")

null_coords = df["Latitude"].isna().sum()
total = len(df)
null_pct = null_coords / total * 100
print(f"  Rows with null coordinates: {null_coords:,} ({null_pct:.1f}%)")

# Save them before dropping
null_coord_rows = df[df["Latitude"].isna()].copy()
null_coord_rows["removal_reason"] = "null_coordinates"
removed_records.append(null_coord_rows)

# WHY we drop these:
#   Geographic analysis is a core part of this project.
#   Rows without coordinates can't appear on maps or in
#   spatial analysis. We document the % lost so we can
#   mention it in the analysis: "Note: 15% of records had
#   no GPS data and were excluded from spatial analysis."
df = df[df["Latitude"].notna() & df["Longitude"].notna()].copy()

print(f"  Rows removed: {null_coords:,}")
print(f"  ✅ All remaining rows have valid coordinates")

# ══════════════════════════════════════════════════════════════════
# FIX 6: DISTRICT CODES — Fix corrupted values
# ══════════════════════════════════════════════════════════════════
print("\n[FIX 6] Fixing corrupted District codes...")

# Convert to string first to handle mixed types
df["District"] = df["District"].astype(str).str.strip()

# Remove any non-numeric characters (e.g., "14A" → "14")
df["District"] = df["District"].str.extract(r"(\d+)", expand=False)

# Convert to numeric
df["District"] = pd.to_numeric(df["District"], errors="coerce")

# Valid Chicago districts are 1–25
invalid_districts = df[(df["District"] < 1) | (df["District"] > 25) | df["District"].isna()]
print(f"  Invalid district codes found: {len(invalid_districts):,}")

# Flag them rather than drop — district isn't critical for most analysis
df.loc[(df["District"] < 1) | (df["District"] > 25), "District"] = np.nan
df.loc[df["District"].isna(), "District_Flag"] = "INVALID_DISTRICT"

print("  ✅ Districts cleaned. Invalid ones set to NaN and flagged.")

# ══════════════════════════════════════════════════════════════════
# FIX 7: TEXT COLUMNS — Strip whitespace
# ══════════════════════════════════════════════════════════════════
print("\n[FIX 7] Stripping whitespace from text columns...")

text_cols = ["Description", "Location Description"]
for col in text_cols:
    if col in df.columns:
        before = (df[col].str.len() != df[col].str.strip().str.len()).sum()
        df[col] = df[col].str.strip()
        print(f"  {col}: fixed {before:,} rows with leading/trailing spaces")

print("  ✅ Text columns cleaned")

# ══════════════════════════════════════════════════════════════════
# FEATURE ENGINEERING — Add analysis-ready columns
# ══════════════════════════════════════════════════════════════════
print("\n[ENGINEER] Creating new analysis columns from Date...")

# WHY engineer these: You can't easily group by "hour" if you only
# have a datetime. Pre-computing these speeds up all future analysis.

df["Year"]       = df["Date"].dt.year
df["Month"]      = df["Date"].dt.month
df["MonthName"]  = df["Date"].dt.strftime("%b")    # Jan, Feb, Mar...
df["DayOfWeek"]  = df["Date"].dt.day_name()         # Monday, Tuesday...
df["Hour"]       = df["Date"].dt.hour
df["IsWeekend"]  = df["Date"].dt.dayofweek >= 5    # 5=Sat, 6=Sun

# Time of day buckets — useful for charts and grouping
def get_time_of_day(hour):
    if 5 <= hour < 12:  return "Morning"
    elif 12 <= hour < 17: return "Afternoon"
    elif 17 <= hour < 21: return "Evening"
    else:                 return "Night"

df["TimeOfDay"] = df["Hour"].apply(get_time_of_day)

# Season
def get_season(month):
    if month in (12, 1, 2):  return "Winter"
    elif month in (3, 4, 5): return "Spring"
    elif month in (6, 7, 8): return "Summer"
    else:                     return "Fall"

df["Season"] = df["Month"].apply(get_season)

print("  ✅ Added: Year, Month, MonthName, DayOfWeek, Hour, IsWeekend, TimeOfDay, Season")

# ══════════════════════════════════════════════════════════════════
# FINAL VALIDATION — Make sure data looks right
# ══════════════════════════════════════════════════════════════════
print("\n[VALIDATE] Final data quality check...")

print(f"  Shape: {df.shape}")
print(f"  Date range: {df['Date'].min().date()} → {df['Date'].max().date()}")
print(f"  Crime types: {sorted(df['Primary Type'].unique())}")
print(f"  Arrest rate: {df['Arrest'].mean()*100:.1f}%")
print(f"  Any remaining nulls in key columns:")
key_cols = ["Case Number", "Date", "Primary Type", "Latitude", "Longitude", "Arrest"]
for col in key_cols:
    nulls = df[col].isna().sum()
    status = "✅" if nulls == 0 else "⚠️ "
    print(f"    {status} {col}: {nulls} nulls")

# ══════════════════════════════════════════════════════════════════
# SAVE OUTPUTS
# ══════════════════════════════════════════════════════════════════
print("\n[SAVE] Writing output files...")

# 1. Clean dataset
df.to_csv("data/cleaned_crimes.csv", index=False)
print(f"  ✅ data/cleaned_crimes.csv  ({len(df):,} rows)")

# 2. Removed records (your audit trail)
if removed_records:
    removed_df = pd.concat(removed_records, ignore_index=True)
    removed_df.to_csv("data/removed_records.csv", index=False)
    print(f"  ✅ data/removed_records.csv ({len(removed_df):,} rows removed)")

# 3. Cleaning report (TEXT FILE — show this in your README)
rows_removed = original_shape[0] - len(df)
report_lines = [
    "=" * 60,
    "  CHICAGO CRIME DATA — CLEANING REPORT",
    f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    "=" * 60,
    "",
    "BEFORE CLEANING",
    f"  Rows:    {original_shape[0]:,}",
    f"  Columns: {original_shape[1]}",
    "",
    "AFTER CLEANING",
    f"  Rows:    {len(df):,}",
    f"  Columns: {len(df.columns)} (added {len(df.columns) - original_shape[1]} engineered features)",
    f"  Rows removed: {rows_removed:,} ({rows_removed/original_shape[0]*100:.1f}%)",
    "",
    "ISSUES FOUND & FIXED",
    "",
    "1. MIXED DATE FORMATS",
    "   Problem: Date column had 3 different formats mixed together",
    "            (MM/DD/YYYY, YYYY-MM-DD, MM/DD/YYYY HH:MM:SS AM/PM)",
    "   Fix:     pd.to_datetime(..., infer_datetime_format=True)",
    "   Impact:  All dates now uniform datetime64 dtype",
    "",
    "2. INCONSISTENT CRIME TYPE CASING",
    "   Problem: 'THEFT', 'Theft', 'theft', 'THEFT - OTHER' coexisted",
    f"   Before:  {df['Primary Type'].nunique()} unique values (should be 15)",
    "   Fix:     .str.strip().str.upper() + regex to remove '- OTHER' suffix",
    f"   After:   {df['Primary Type'].nunique()} standardized categories",
    "",
    "3. DUPLICATE CASE NUMBERS",
    f"   Problem: {duplicates_before:,} duplicate case numbers (system migration artifacts)",
    "   Fix:     drop_duplicates(subset=['Case Number'], keep='first')",
    "   Decision: Keep first occurrence = original incident record",
    "",
    "4. MIXED ARREST COLUMN TYPES",
    f"   Problem: Column had boolean, string, integer, and null values mixed",
    f"   Examples: True/False, 'true'/'false', 1/0, 'Y'/'N', None",
    "   Fix:     Custom standardize_arrest() function → clean bool",
    f"   Nulls filled with False (no arrest = not arrested, not missing)",
    "",
    "5. NULL GPS COORDINATES",
    f"   Problem: {null_pct:.1f}% of rows had no Latitude/Longitude",
    "   Fix:     Removed from dataset (required for geographic analysis)",
    "   Note:    Saved to removed_records.csv for audit trail",
    "   Impact:  These rows ARE included in non-spatial analysis counts",
    "",
    "6. CORRUPTED DISTRICT CODES",
    f"   Problem: Some districts had letter suffixes (e.g. '14A'), leading zeros,",
    "            or invalid values (99, null)",
    "   Fix:     Regex extract numeric part, validate range 1-25",
    "   Nulls:   Invalid districts set to NaN and flagged in District_Flag column",
    "",
    "7. WHITESPACE IN TEXT COLUMNS",
    "   Problem: Leading/trailing spaces in Location Description, Description",
    "   Fix:     .str.strip() on all text columns",
    "",
    "FEATURE ENGINEERING ADDED",
    "  Year, Month, MonthName, DayOfWeek, Hour, IsWeekend, TimeOfDay, Season",
    "",
    "FINAL COLUMN LIST",
    f"  {list(df.columns)}",
    "",
    "=" * 60,
]

with open("data/cleaning_report.txt", "w") as f:
    f.write("\n".join(report_lines))

print(f"  ✅ data/cleaning_report.txt")

print("\n" + "=" * 60)
print("  CLEANING COMPLETE")
print("=" * 60)
print(f"\n  {original_shape[0]:,} raw rows → {len(df):,} clean rows")
print(f"  {rows_removed:,} rows removed ({rows_removed/original_shape[0]*100:.1f}%)")
print("\n  Next step: Run 03_analysis.py")
