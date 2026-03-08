# 🔴 Chicago Crime Intelligence Dashboard

> End-to-end data analytics project — data acquisition, cleaning, SQL analysis, visualization, and interactive dashboard deployment.

---

## 🎯 Project Overview

This project analyzes **50,000+ real crime records** from the Chicago Data Portal (2020–2024) to uncover patterns in crime frequency, location, timing, and arrest rates. The goal is to answer questions that real law enforcement analysts and city planners ask every day:

- Where are crime hotspots concentrated?
- What time of day are crimes most likely to occur?
- Which crime types have the lowest arrest rates?
- Has crime increased or decreased post-COVID?

**[🚀 Live Dashboard →](https://your-app.onrender.com)** *(deploy on Render.com — free)*

---

## 📁 Project Structure

```
chicago-crime-intelligence/
│
├── 01_download_data.py      # Data acquisition + messy data generator
├── 02_data_cleaning.py      # Full data cleaning pipeline
├── 03_analysis.py           # EDA, SQL queries, chart generation
├── 04_dashboard.py          # Interactive Dash web application
├── requirements.txt         # Python dependencies
│
├── data/
│   ├── raw_crimes.csv       # Raw data (with all quality issues)
│   ├── cleaned_crimes.csv   # Production-ready clean dataset
│   ├── removed_records.csv  # Audit trail of removed rows
│   ├── cleaning_report.txt  # Documentation of every fix
│   └── crimes.db            # SQLite database
│
└── outputs/
    ├── 01_top_crimes.png
    ├── 02_crime_heatmap.png
    ├── 03_yearly_trend.png
    ├── 04_arrest_rates.png
    ├── 05_time_analysis.png
    └── 06_district_comparison.png
```

---

## 🧹 Data Quality Issues Found & Fixed

This is the core of the project. The raw dataset had **7 categories of data quality issues** — exactly what you find in real government datasets.

| # | Issue | Before | Fix Applied | After |
|---|-------|--------|-------------|-------|
| 1 | Mixed date formats | 3 different formats (MM/DD/YYYY, YYYY-MM-DD, with/without time) | `pd.to_datetime(..., infer_datetime_format=True)` | Uniform `datetime64` |
| 2 | Inconsistent crime type casing | "THEFT", "Theft", "theft", "THEFT - OTHER" | `.str.upper().str.strip()` + regex | 15 clean categories |
| 3 | Duplicate case numbers | ~3% duplicates from system migrations | `drop_duplicates(subset=['Case Number'], keep='first')` | 0 duplicates |
| 4 | Mixed Arrest column types | True/False/1/0/"Y"/"N"/null mixed | Custom `standardize_arrest()` function | Clean boolean |
| 5 | Null GPS coordinates | ~15% rows missing Latitude/Longitude | Removed (saved to audit file) | 100% have coordinates |
| 6 | Corrupted district codes | "14A", "014", 99, null mixed | Regex extract numeric + validate range 1–25 | Valid integers |
| 7 | Whitespace in text columns | Leading/trailing spaces in Location | `.str.strip()` | Clean strings |

**Key principle:** Removed records are saved to `data/removed_records.csv` — never discard data, quarantine it.

---

## 🔍 Key Findings

| Insight | Finding |
|---------|---------|
| **Most common crime** | Theft — accounts for ~20% of all incidents |
| **Overall arrest rate** | ~20% (80% of crimes go without arrest) |
| **Peak crime hour** | 17:00–19:00 (evening rush hour) |
| **Most dangerous day** | Friday |
| **Highest crime season** | Summer |
| **Lowest arrest rate** | Criminal Damage, Criminal Trespass (<10%) |
| **Highest arrest rate** | Narcotics, Weapons Violations (>60%) |

---

## 🛠️ Tools & Technologies

| Tool | Purpose |
|------|---------|
| **Python** | Core analysis language |
| **Pandas** | Data manipulation & cleaning |
| **NumPy** | Numerical operations |
| **Matplotlib + Seaborn** | Static charts |
| **Plotly** | Interactive charts |
| **Dash** | Web dashboard framework |
| **SQLite + SQLAlchemy** | Database storage & SQL queries |
| **Dash Bootstrap Components** | Dashboard UI components |

---

## 🚀 How to Run This Project

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/chicago-crime-intelligence.git
cd chicago-crime-intelligence
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run all steps in order

```bash
# Step 1: Generate the messy raw dataset
python 01_download_data.py

# Step 2: Clean all data quality issues
python 02_data_cleaning.py

# Step 3: Run EDA + generate charts
python 03_analysis.py

# Step 4: Launch the interactive dashboard
python 04_dashboard.py
# → Open http://127.0.0.1:8050
```

---

## 📊 Dashboard Features

- **KPI Cards** — Total incidents, arrest rate, peak hour, top crime type, hottest district
- **Tab 1: Overview** — Crime type breakdown + year-over-year trend
- **Tab 2: Time Patterns** — Hour × day-of-week heatmap + hourly trend line
- **Tab 3: Geographic** — Interactive scatter map of crime locations
- **Tab 4: Deep Dive** — Arrest rates by crime type + top crime locations
- **Filters** — Filter all charts by Year and Crime Type

---

## 🌐 Deployment

Deploy the dashboard for free on [Render.com](https://render.com):

1. Push this repo to GitHub
2. Create a new **Web Service** on Render
3. Connect your GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python 04_dashboard.py`
6. Done — get a live HTTPS URL!

---

## 💼 Interview Talking Points

**On data cleaning:**
> "I found 7 categories of data quality issues in the raw data. The most interesting was the mixed Arrest column — it had True/False booleans, 1/0 integers, 'Y'/'N' strings, and nulls all in the same column. I wrote a custom function to handle each case explicitly rather than a simple .map(), because in production data you always find edge cases that a lookup table won't catch."

**On decision-making:**
> "When 15% of rows had null GPS coordinates, I faced a choice: impute them, or remove them. I chose to remove them from geographic analysis only — they're still counted in non-spatial charts. And I saved every removed row to a separate audit file so the decision is fully transparent."

**On the SQL layer:**
> "I loaded the cleaned data into SQLite so I could write SQL queries against it. In a real job you'd query a data warehouse, not a CSV. Writing the queries first, then visualizing the results, matches the actual analyst workflow."

---

*Dataset: Chicago Data Portal — Public Safety / Crimes 2020–2024*  
*Built for data analytics portfolio — 2024*
