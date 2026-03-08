"""
================================================================
STEP 3: EXPLORATORY DATA ANALYSIS (EDA) + SQL QUERIES
================================================================
Chicago Crime Intelligence Project
File: 03_analysis.py

PURPOSE:
  Uncover meaningful insights from the cleaned data.
  This is what data analysts actually do — ask business questions
  and answer them with data.

QUESTIONS WE ANSWER:
  1. What are the top crime types and how have they trended?
  2. When do crimes happen? (hour, day, season patterns)
  3. Which districts have the most crime?
  4. What is the arrest rate by crime type?
  5. Has overall crime gone up or down year over year?
  6. What's the most dangerous time of day?

OUTPUT:
  outputs/01_top_crimes.png
  outputs/02_crime_heatmap.png
  outputs/03_yearly_trend.png
  outputs/04_arrest_rates.png
  outputs/05_district_comparison.png
  outputs/06_time_analysis.png
  data/crimes.db              ← SQLite database (SQL practice!)

HOW TO RUN:
  python 03_analysis.py
================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import sqlite3
import os

# ── SETUP ────────────────────────────────────────────────────────
os.makedirs("outputs", exist_ok=True)

# Style — use a professional dark theme for your portfolio
plt.rcParams.update({
    "figure.facecolor":  "#0D1117",
    "axes.facecolor":    "#161B22",
    "axes.edgecolor":    "#30363D",
    "axes.labelcolor":   "#C9D1D9",
    "axes.titlecolor":   "#FFFFFF",
    "xtick.color":       "#8B949E",
    "ytick.color":       "#8B949E",
    "text.color":        "#C9D1D9",
    "grid.color":        "#21262D",
    "grid.linestyle":    "--",
    "grid.alpha":        0.5,
    "font.family":       "monospace",
    "figure.dpi":        120,
})

ACCENT   = "#FF4D00"
ACCENT2  = "#FFB300"
BLUE     = "#58A6FF"
GREEN    = "#3FB950"
RED      = "#F85149"

print("=" * 60)
print("  CHICAGO CRIME INTELLIGENCE — ANALYSIS")
print("=" * 60)

# ── LOAD CLEAN DATA ──────────────────────────────────────────────
print("\n[LOAD] Reading cleaned data...")
df = pd.read_csv("data/cleaned_crimes.csv", parse_dates=["Date"])
print(f"  Rows: {len(df):,} | Columns: {len(df.columns)}")
print(f"  Date range: {df['Date'].min().date()} → {df['Date'].max().date()}")

# ══════════════════════════════════════════════════════════════════
# STEP A: LOAD INTO SQLITE — Run SQL queries like a pro
# ══════════════════════════════════════════════════════════════════
print("\n[SQL] Creating SQLite database...")

conn = sqlite3.connect("data/crimes.db")
df.to_sql("crimes", conn, if_exists="replace", index=False)
print("  ✅ Data loaded into crimes.db")
print("  You can now open this in DB Browser for SQLite!")

# ── SQL QUERY 1: Top crime types ─────────────────────────────────
print("\n[SQL QUERY 1] Top crime types by count and arrest rate:")
sql_top_crimes = """
SELECT 
    [Primary Type]                              AS crime_type,
    COUNT(*)                                    AS total_incidents,
    SUM(CASE WHEN Arrest = 1 THEN 1 ELSE 0 END) AS total_arrests,
    ROUND(
        100.0 * SUM(CASE WHEN Arrest = 1 THEN 1 ELSE 0 END) / COUNT(*), 1
    )                                           AS arrest_rate_pct
FROM crimes
GROUP BY [Primary Type]
ORDER BY total_incidents DESC
LIMIT 10
"""
top_crimes = pd.read_sql_query(sql_top_crimes, conn)
print(top_crimes.to_string(index=False))

# ── SQL QUERY 2: Year-over-year trend ────────────────────────────
print("\n[SQL QUERY 2] Year-over-year crime trend:")
sql_yoy = """
SELECT
    Year,
    COUNT(*) AS total_crimes,
    SUM(CASE WHEN Arrest = 1 THEN 1 ELSE 0 END) AS arrests,
    ROUND(100.0 * SUM(CASE WHEN Arrest = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS arrest_rate_pct
FROM crimes
GROUP BY Year
ORDER BY Year
"""
yoy_df = pd.read_sql_query(sql_yoy, conn)
print(yoy_df.to_string(index=False))

# ── SQL QUERY 3: District comparison ─────────────────────────────
print("\n[SQL QUERY 3] Top 10 districts by crime count:")
sql_district = """
SELECT
    District,
    COUNT(*) AS total_crimes
FROM crimes
WHERE District IS NOT NULL
GROUP BY District
ORDER BY total_crimes DESC
LIMIT 10
"""
district_df = pd.read_sql_query(sql_district, conn)
print(district_df.to_string(index=False))

conn.close()

# ══════════════════════════════════════════════════════════════════
# CHART 1: TOP CRIME TYPES — Horizontal Bar Chart
# ══════════════════════════════════════════════════════════════════
print("\n[CHART 1] Top crime types...")

fig, ax = plt.subplots(figsize=(12, 7))

top10 = top_crimes.head(10).sort_values("total_incidents")
colors = [ACCENT if i == len(top10) - 1 else BLUE for i in range(len(top10))]

bars = ax.barh(top10["crime_type"], top10["total_incidents"],
               color=colors, height=0.65, edgecolor="none")

# Add value labels on bars
for bar, val in zip(bars, top10["total_incidents"]):
    ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", fontsize=9, color="#C9D1D9")

ax.set_xlabel("Number of Incidents", fontsize=11)
ax.set_title("Top 10 Crime Types — Chicago 2020–2024",
             fontsize=14, fontweight="bold", pad=15)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(axis="y", labelsize=10)

plt.tight_layout()
plt.savefig("outputs/01_top_crimes.png", bbox_inches="tight")
plt.close()
print("  ✅ outputs/01_top_crimes.png")

# ══════════════════════════════════════════════════════════════════
# CHART 2: CRIME HEATMAP — Hour vs Day of Week
# ══════════════════════════════════════════════════════════════════
print("[CHART 2] Crime heatmap (hour vs day of week)...")

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
pivot = df.groupby(["DayOfWeek", "Hour"]).size().unstack(fill_value=0)
pivot = pivot.reindex(day_order)

fig, ax = plt.subplots(figsize=(16, 6))
sns.heatmap(
    pivot,
    ax=ax,
    cmap="YlOrRd",
    linewidths=0.3,
    linecolor="#0D1117",
    cbar_kws={"label": "Number of Crimes"},
    fmt="d",
    annot=False,
)
ax.set_title("Crime Frequency — Hour of Day vs Day of Week",
             fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Hour of Day (24h)", fontsize=11)
ax.set_ylabel("")
ax.tick_params(axis="x", labelsize=8)
ax.tick_params(axis="y", labelsize=10, rotation=0)

plt.tight_layout()
plt.savefig("outputs/02_crime_heatmap.png", bbox_inches="tight")
plt.close()
print("  ✅ outputs/02_crime_heatmap.png")

# ══════════════════════════════════════════════════════════════════
# CHART 3: YEAR-OVER-YEAR TREND
# ══════════════════════════════════════════════════════════════════
print("[CHART 3] Year-over-year trend...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Left: Total crimes per year
bars = ax1.bar(yoy_df["Year"], yoy_df["total_crimes"],
               color=[ACCENT if y == yoy_df["Year"].max() else BLUE
                      for y in yoy_df["Year"]],
               width=0.55, edgecolor="none")
for bar, val in zip(bars, yoy_df["total_crimes"]):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 100,
             f"{val:,}", ha="center", fontsize=9, fontweight="bold")
ax1.set_title("Total Crimes per Year", fontsize=13, fontweight="bold")
ax1.set_ylabel("Incidents")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Right: Arrest rate trend
ax2.plot(yoy_df["Year"], yoy_df["arrest_rate_pct"],
         marker="o", markersize=8, linewidth=2.5,
         color=ACCENT2, markerfacecolor=ACCENT)
ax2.fill_between(yoy_df["Year"], yoy_df["arrest_rate_pct"],
                 alpha=0.15, color=ACCENT2)
for x, y in zip(yoy_df["Year"], yoy_df["arrest_rate_pct"]):
    ax2.text(x, y + 0.3, f"{y}%", ha="center", fontsize=9, fontweight="bold")
ax2.set_title("Arrest Rate (%) per Year", fontsize=13, fontweight="bold")
ax2.set_ylabel("Arrest Rate (%)")
ax2.set_ylim(0, yoy_df["arrest_rate_pct"].max() * 1.3)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

fig.suptitle("Year-Over-Year Crime Trend — Chicago 2020–2024",
             fontsize=15, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("outputs/03_yearly_trend.png", bbox_inches="tight")
plt.close()
print("  ✅ outputs/03_yearly_trend.png")

# ══════════════════════════════════════════════════════════════════
# CHART 4: ARREST RATE BY CRIME TYPE
# ══════════════════════════════════════════════════════════════════
print("[CHART 4] Arrest rates by crime type...")

arrest_rates = (
    df.groupby("Primary Type")["Arrest"]
    .agg(["sum", "count"])
    .rename(columns={"sum": "arrests", "count": "total"})
)
arrest_rates["rate"] = arrest_rates["arrests"] / arrest_rates["total"] * 100
arrest_rates = arrest_rates.sort_values("rate", ascending=True)

fig, ax = plt.subplots(figsize=(11, 8))

colors = [RED if r < 15 else ACCENT2 if r < 30 else GREEN
          for r in arrest_rates["rate"]]
bars = ax.barh(arrest_rates.index, arrest_rates["rate"],
               color=colors, height=0.65, edgecolor="none")
for bar, val in zip(bars, arrest_rates["rate"]):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va="center", fontsize=9)

ax.axvline(x=arrest_rates["rate"].mean(), color="#8B949E",
           linestyle="--", linewidth=1, alpha=0.8)
ax.text(arrest_rates["rate"].mean() + 0.3, -0.7,
        f"Avg: {arrest_rates['rate'].mean():.1f}%", fontsize=8, color="#8B949E")

ax.set_xlabel("Arrest Rate (%)", fontsize=11)
ax.set_title("Arrest Rate by Crime Type", fontsize=14, fontweight="bold", pad=15)
ax.set_xlim(0, arrest_rates["rate"].max() * 1.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=GREEN,  label="High (≥30%)"),
    Patch(facecolor=ACCENT2, label="Medium (15–30%)"),
    Patch(facecolor=RED,    label="Low (<15%)"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=9,
          facecolor="#161B22", edgecolor="#30363D")

plt.tight_layout()
plt.savefig("outputs/04_arrest_rates.png", bbox_inches="tight")
plt.close()
print("  ✅ outputs/04_arrest_rates.png")

# ══════════════════════════════════════════════════════════════════
# CHART 5: TIME OF DAY ANALYSIS
# ══════════════════════════════════════════════════════════════════
print("[CHART 5] Time of day and seasonal analysis...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Left: Crimes by hour
hourly = df.groupby("Hour").size().reset_index(name="count")
ax1.plot(hourly["Hour"], hourly["count"], color=ACCENT,
         linewidth=2.5, marker="o", markersize=4)
ax1.fill_between(hourly["Hour"], hourly["count"], alpha=0.2, color=ACCENT)
peak_hour = hourly.loc[hourly["count"].idxmax(), "Hour"]
peak_val  = hourly.loc[hourly["count"].idxmax(), "count"]
ax1.scatter([peak_hour], [peak_val], color=ACCENT2, s=80, zorder=5)
ax1.annotate(f"Peak: {peak_hour}:00\n{peak_val:,} crimes",
             xy=(peak_hour, peak_val),
             xytext=(peak_hour + 2, peak_val - 300),
             fontsize=8, color=ACCENT2,
             arrowprops=dict(arrowstyle="->", color=ACCENT2, lw=1))
ax1.set_xlabel("Hour of Day")
ax1.set_ylabel("Number of Crimes")
ax1.set_title("Crime Volume by Hour", fontsize=13, fontweight="bold")
ax1.set_xticks(range(0, 24, 2))
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Right: Crimes by season
season_order = ["Winter", "Spring", "Summer", "Fall"]
season_counts = df["Season"].value_counts().reindex(season_order)
season_colors = [BLUE, GREEN, ACCENT, ACCENT2]
wedges, texts, autotexts = ax2.pie(
    season_counts, labels=season_counts.index,
    colors=season_colors,
    autopct="%1.1f%%", startangle=90,
    pctdistance=0.75,
    wedgeprops=dict(edgecolor="#0D1117", linewidth=2)
)
for at in autotexts:
    at.set_fontsize(9)
    at.set_color("#0D1117")
    at.set_fontweight("bold")
ax2.set_title("Crime Distribution by Season", fontsize=13, fontweight="bold")

fig.suptitle("When Do Crimes Happen? — Time Analysis",
             fontsize=15, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("outputs/05_time_analysis.png", bbox_inches="tight")
plt.close()
print("  ✅ outputs/05_time_analysis.png")

# ══════════════════════════════════════════════════════════════════
# CHART 6: DISTRICT HEATMAP
# ══════════════════════════════════════════════════════════════════
print("[CHART 6] District comparison...")

dist_data = (
    df.dropna(subset=["District"])
    .groupby("District")
    .agg(
        total_crimes=("Case Number", "count"),
        arrest_rate=("Arrest", "mean"),
    )
    .reset_index()
    .sort_values("total_crimes", ascending=False)
    .head(15)
)
dist_data["arrest_rate"] = dist_data["arrest_rate"] * 100

fig, ax = plt.subplots(figsize=(12, 6))

x = range(len(dist_data))
bars = ax.bar(x, dist_data["total_crimes"],
              color=BLUE, alpha=0.85, edgecolor="none", label="Total Crimes")
ax2_twin = ax.twinx()
ax2_twin.plot(x, dist_data["arrest_rate"],
              color=ACCENT, marker="D", markersize=6,
              linewidth=2, label="Arrest Rate %")
ax2_twin.set_ylabel("Arrest Rate (%)", color=ACCENT, fontsize=10)
ax2_twin.tick_params(axis="y", colors=ACCENT)
ax2_twin.set_ylim(0, dist_data["arrest_rate"].max() * 1.5)

ax.set_xticks(list(x))
ax.set_xticklabels([f"Dist {int(d)}" for d in dist_data["District"]], rotation=45, ha="right")
ax.set_ylabel("Total Crimes", fontsize=10)
ax.set_title("Crime Count & Arrest Rate by Police District (Top 15)",
             fontsize=13, fontweight="bold", pad=15)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
ax.spines["top"].set_visible(False)

lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right",
          fontsize=9, facecolor="#161B22", edgecolor="#30363D")

plt.tight_layout()
plt.savefig("outputs/06_district_comparison.png", bbox_inches="tight")
plt.close()
print("  ✅ outputs/06_district_comparison.png")

# ══════════════════════════════════════════════════════════════════
# PRINT KEY INSIGHTS — Copy these for your README!
# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  KEY INSIGHTS (use these in your README & interviews!)")
print("=" * 60)

print(f"\n📊 Dataset: {len(df):,} cleaned crime records (2020–2024)")

top1 = top_crimes.iloc[0]
print(f"\n🔴 Most common crime: {top1['crime_type']} ({top1['total_incidents']:,} incidents)")

overall_arrest_rate = df["Arrest"].mean() * 100
print(f"\n🚔 Overall arrest rate: {overall_arrest_rate:.1f}%")
print(f"   (meaning {100 - overall_arrest_rate:.1f}% of crimes go without arrest)")

peak_h = int(hourly.loc[hourly["count"].idxmax(), "Hour"])
print(f"\n⏰ Peak crime hour: {peak_h}:00 ({peak_h % 12 or 12}{'PM' if peak_h >= 12 else 'AM'})")

peak_day = df["DayOfWeek"].value_counts().index[0]
print(f"\n📅 Most dangerous day: {peak_day}")

peak_season = df["Season"].value_counts().index[0]
print(f"\n🌡️  Most dangerous season: {peak_season}")

top_district = district_df.iloc[0]
print(f"\n📍 Highest crime district: District {int(top_district['District'])} ({int(top_district['total_crimes']):,} incidents)")

print(f"\n📁 6 charts saved to outputs/")
print(f"📁 SQL database saved to data/crimes.db")
print("\n  Next step: Run 04_dashboard.py")
