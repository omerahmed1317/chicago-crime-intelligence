"""
================================================================
STEP 4: INTERACTIVE DASH DASHBOARD
================================================================
Chicago Crime Intelligence Project
File: 04_dashboard.py

PURPOSE:
  Build a professional, interactive web dashboard using Plotly Dash.
  This creates a real URL you can deploy and put on your resume.

FEATURES:
  ✦ KPI cards (total crimes, arrest rate, peak hour, top district)
  ✦ Tab 1 — Overview: top crimes bar chart + yearly trend
  ✦ Tab 2 — Time Patterns: heatmap + hourly line chart
  ✦ Tab 3 — Geographic: scatter map of crime locations
  ✦ Tab 4 — Deep Dive: filter by crime type, see arrest breakdown
  ✦ Dropdown filters for Year and Crime Type
  ✦ Dark professional theme

HOW TO RUN:
  python 04_dashboard.py
  Then open: http://127.0.0.1:8050

TO DEPLOY (free, takes 5 minutes):
  1. Create account at render.com
  2. Push this project to GitHub
  3. New Web Service → connect repo → build command: pip install -r requirements.txt
  4. Start command: python 04_dashboard.py
  → You'll get a real https://your-app.onrender.com URL!

INTERVIEW TIP:
  Pull up the live URL during the interview on your phone or laptop.
  "Here's the deployed version — I can filter by year, crime type..."
================================================================
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import os

# ── LOAD DATA ────────────────────────────────────────────────────
print("Loading cleaned data...")
df = pd.read_csv("data/cleaned_crimes.csv", parse_dates=["Date"])
print(f"  {len(df):,} rows loaded")

# ── THEME CONFIG ─────────────────────────────────────────────────
BG_DARK    = "#0D1117"
BG_CARD    = "#161B22"
BG_CARD2   = "#1C2128"
BORDER     = "#30363D"
TEXT_PRIMARY   = "#FFFFFF"
TEXT_SECONDARY = "#8B949E"
ACCENT     = "#FF4D00"
ACCENT2    = "#FFB300"
BLUE       = "#58A6FF"
GREEN      = "#3FB950"
RED = "#F85149"

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG_CARD,
        font=dict(color=TEXT_SECONDARY, family="monospace"),
        title=dict(font=dict(color=TEXT_PRIMARY, size=14)),
        xaxis=dict(gridcolor="#21262D", linecolor=BORDER, tickfont=dict(color=TEXT_SECONDARY)),
        yaxis=dict(gridcolor="#21262D", linecolor=BORDER, tickfont=dict(color=TEXT_SECONDARY)),
        legend=dict(bgcolor=BG_CARD2, bordercolor=BORDER, borderwidth=1,
                    font=dict(color=TEXT_SECONDARY)),
        margin=dict(l=40, r=20, t=50, b=40),
    )
)

# ── PRECOMPUTE DATA ───────────────────────────────────────────────
years = sorted(df["Year"].unique())
crime_types = sorted(df["Primary Type"].unique())

# ── BUILD APP ─────────────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    title="Chicago Crime Intelligence"
)

# ── HELPER: KPI CARD ─────────────────────────────────────────────
def kpi_card(title, value, subtitle, color=ACCENT, icon="◈"):
    return html.Div(
        style={
            "background": BG_CARD,
            "border": f"1px solid {BORDER}",
            "borderTop": f"3px solid {color}",
            "borderRadius": "8px",
            "padding": "18px 20px",
            "flex": "1",
            "minWidth": "160px",
        },
        children=[
            html.Div(icon, style={"fontSize": "20px", "color": color, "marginBottom": "8px"}),
            html.Div(value, style={
                "fontSize": "28px", "fontWeight": "900",
                "color": color, "fontFamily": "monospace", "lineHeight": "1"
            }),
            html.Div(title, style={
                "fontSize": "11px", "letterSpacing": "0.15em",
                "color": TEXT_SECONDARY, "marginTop": "6px", "textTransform": "uppercase"
            }),
            html.Div(subtitle, style={"fontSize": "11px", "color": TEXT_SECONDARY, "marginTop": "3px"}),
        ]
    )

# ── LAYOUT ───────────────────────────────────────────────────────
app.layout = html.Div(
    style={"background": BG_DARK, "minHeight": "100vh", "fontFamily": "monospace"},
    children=[

        # ── HEADER ──────────────────────────────────────────────
        html.Div(
            style={
                "background": BG_CARD,
                "borderBottom": f"1px solid {BORDER}",
                "padding": "16px 32px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "flexWrap": "wrap",
                "gap": "12px",
            },
            children=[
                html.Div([
                    html.Div("CHICAGO CRIME INTELLIGENCE DASHBOARD",
                             style={"fontSize": "18px", "fontWeight": "900",
                                    "color": TEXT_PRIMARY, "letterSpacing": "0.05em"}),
                    html.Div("Real-time crime analysis · 2020–2024 · 50,000+ incidents",
                             style={"fontSize": "11px", "color": TEXT_SECONDARY, "marginTop": "3px"}),
                ]),
                html.Div(
                    style={"display": "flex", "gap": "12px", "alignItems": "center"},
                    children=[
                        html.Div("YEAR:", style={"fontSize": "11px", "color": TEXT_SECONDARY}),
                        dcc.Dropdown(
                            id="year-filter",
                            options=[{"label": "All Years", "value": "all"}] +
                                    [{"label": str(y), "value": y} for y in years],
                            value="all",
                            clearable=False,
                            style={"width": "130px", "fontFamily": "monospace", "fontSize": "12px"},
                        ),
                        html.Div("CRIME TYPE:", style={"fontSize": "11px", "color": TEXT_SECONDARY}),
                        dcc.Dropdown(
                            id="crime-filter",
                            options=[{"label": "All Types", "value": "all"}] +
                                    [{"label": c.title(), "value": c} for c in crime_types],
                            value="all",
                            clearable=False,
                            style={"width": "200px", "fontFamily": "monospace", "fontSize": "12px"},
                        ),
                    ]
                )
            ]
        ),

        # ── KPI CARDS ────────────────────────────────────────────
        html.Div(id="kpi-row", style={
            "display": "flex", "gap": "16px",
            "padding": "20px 32px 0", "flexWrap": "wrap"
        }),

        # ── TABS ─────────────────────────────────────────────────
        html.Div(
            style={"padding": "20px 32px"},
            children=[
                dcc.Tabs(
                    id="tabs",
                    value="overview",
                    style={"borderBottom": f"1px solid {BORDER}"},
                    colors={"border": BORDER, "primary": ACCENT, "background": BG_CARD},
                    children=[
                        dcc.Tab(label="📊 Overview",    value="overview"),
                        dcc.Tab(label="⏰ Time Patterns", value="time"),
                        dcc.Tab(label="🗺️ Geographic",  value="geo"),
                        dcc.Tab(label="🔍 Deep Dive",   value="deepdive"),
                    ]
                ),
                html.Div(id="tab-content", style={"marginTop": "20px"}),
            ]
        ),

        # ── FOOTER ──────────────────────────────────────────────
        html.Div(
            "Chicago Crime Intelligence Dashboard · Built with Python + Plotly Dash · "
            "Data: Chicago Open Data Portal",
            style={
                "textAlign": "center", "padding": "20px",
                "color": TEXT_SECONDARY, "fontSize": "11px",
                "borderTop": f"1px solid {BORDER}"
            }
        )
    ]
)

# ── CALLBACKS ─────────────────────────────────────────────────────

def filter_df(year, crime):
    """Apply global filters to the dataframe."""
    filtered = df.copy()
    if year != "all":
        filtered = filtered[filtered["Year"] == int(year)]
    if crime != "all":
        filtered = filtered[filtered["Primary Type"] == crime]
    return filtered


@callback(Output("kpi-row", "children"), [Input("year-filter", "value"), Input("crime-filter", "value")])
def update_kpis(year, crime):
    d = filter_df(year, crime)
    total = len(d)
    arrest_rate = f"{d['Arrest'].mean()*100:.1f}%"
    peak_hour_val = d.groupby("Hour").size().idxmax() if total > 0 else 0
    peak_hour_str = f"{peak_hour_val}:00"
    top_crime = d["Primary Type"].value_counts().index[0].title() if total > 0 else "—"
    top_district = (
        int(d.dropna(subset=["District"])["District"].value_counts().index[0])
        if total > 0 and d["District"].notna().any() else "—"
    )

    return [
        kpi_card("Total Incidents",  f"{total:,}",          "Cleaned & verified",  ACCENT,  "◈"),
        kpi_card("Arrest Rate",      arrest_rate,           "% resulting in arrest", ACCENT2, "⚖"),
        kpi_card("Peak Crime Hour",  peak_hour_str,         "Most active hour",    BLUE,    "⏰"),
        kpi_card("Top Crime Type",   top_crime[:12],        "Most frequent",       GREEN,   "📋"),
        kpi_card("Hottest District", f"Dist {top_district}", "Most incidents",      "#F85149","📍"),
    ]


@callback(Output("tab-content", "children"), [Input("tabs", "value"), Input("year-filter", "value"), Input("crime-filter", "value")])
def update_tabs(tab, year, crime):
    d = filter_df(year, crime)

    # ── TAB 1: OVERVIEW ────────────────────────────────────────
    if tab == "overview":
        top_crimes = (
            d.groupby("Primary Type").size()
            .reset_index(name="count")
            .sort_values("count", ascending=True)
            .tail(12)
        )
        fig_bar = go.Figure(go.Bar(
            x=top_crimes["count"],
            y=top_crimes["Primary Type"].str.title(),
            orientation="h",
            marker=dict(
                color=top_crimes["count"],
                colorscale=[[0, BLUE], [0.7, ACCENT2], [1, ACCENT]],
                showscale=False,
            ),
            text=[f"{v:,}" for v in top_crimes["count"]],
            textposition="outside",
            textfont=dict(size=10, color=TEXT_SECONDARY),
        ))
        fig_bar.update_layout(
            **PLOTLY_TEMPLATE["layout"],
            title="Crime Incidents by Type",
            height=420,
            xaxis_title="Number of Incidents",
        )

        yoy = d.groupby("Year").size().reset_index(name="count")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=yoy["Year"], y=yoy["count"],
            marker_color=[ACCENT if y == yoy["Year"].max() else BLUE for y in yoy["Year"]],
            name="Crimes",
            text=[f"{v:,}" for v in yoy["count"]],
            textposition="outside",
        ))
        fig_trend.update_layout(
            **PLOTLY_TEMPLATE["layout"],
            title="Total Crimes per Year",
            height=320,
            xaxis=dict(**PLOTLY_TEMPLATE["layout"]["xaxis"], tickmode="array", tickvals=list(yoy["Year"])),
        )

        return html.Div([
            html.Div([
                dcc.Graph(figure=fig_bar, config={"displayModeBar": False}),
            ], style={"background": BG_CARD, "borderRadius": "8px",
                      "border": f"1px solid {BORDER}", "padding": "8px", "marginBottom": "16px"}),
            html.Div([
                dcc.Graph(figure=fig_trend, config={"displayModeBar": False}),
            ], style={"background": BG_CARD, "borderRadius": "8px", "border": f"1px solid {BORDER}", "padding": "8px"}),
        ])

    # ── TAB 2: TIME PATTERNS ─────────────────────────────────
    elif tab == "time":
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        pivot = d.groupby(["DayOfWeek", "Hour"]).size().unstack(fill_value=0).reindex(day_order)

        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values,
            x=list(range(24)),
            y=day_order,
            colorscale=[[0, BG_CARD], [0.3, BLUE], [0.7, ACCENT2], [1, ACCENT]],
            hovertemplate="Day: %{y}<br>Hour: %{x}:00<br>Crimes: %{z}<extra></extra>",
        ))
        fig_heat.update_layout(
            **PLOTLY_TEMPLATE["layout"],
            title="Crime Frequency: Hour × Day of Week",
            height=320,
            xaxis_title="Hour of Day",
        )

        hourly = d.groupby("Hour").size().reset_index(name="count")
        fig_hourly = go.Figure()
        fig_hourly.add_trace(go.Scatter(
            x=hourly["Hour"], y=hourly["count"],
            mode="lines+markers",
            line=dict(color=ACCENT, width=2.5),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor=f"rgba(255,77,0,0.1)",
            name="Crimes",
        ))
        fig_hourly.update_layout(
            **PLOTLY_TEMPLATE["layout"],
            title="Crimes by Hour of Day",
            height=280,
            xaxis=dict(**PLOTLY_TEMPLATE["layout"]["xaxis"],
                       tickmode="array", tickvals=list(range(0, 24, 2))),
        )

        return html.Div([
            html.Div(dcc.Graph(figure=fig_heat, config={"displayModeBar": False}),
                     style={"background": BG_CARD, "borderRadius": "8px",
                            "border": f"1px solid {BORDER}", "padding": "8px", "marginBottom": "16px"}),
            html.Div(dcc.Graph(figure=fig_hourly, config={"displayModeBar": False}),
                     style={"background": BG_CARD, "borderRadius": "8px", "border": f"1px solid {BORDER}", "padding": "8px"}),
        ])

    # ── TAB 3: GEOGRAPHIC ────────────────────────────────────
    elif tab == "geo":
        geo = d.dropna(subset=["Latitude", "Longitude"])
        # Sample for performance (maps slow down with too many points)
        sample_size = min(8000, len(geo))
        geo_sample = geo.sample(n=sample_size, random_state=42)

        fig_map = px.scatter_mapbox(
            geo_sample,
            lat="Latitude", lon="Longitude",
            color="Primary Type",
            hover_data={"Date": True, "Location Description": True,
                        "Arrest": True, "Latitude": False, "Longitude": False},
            zoom=10,
            center={"lat": 41.83, "lon": -87.73},
            opacity=0.5,
            title=f"Crime Locations (sample of {sample_size:,} incidents)",
        )
        fig_map.update_layout(
            mapbox_style="carto-darkmatter",
            paper_bgcolor=BG_CARD,
            font=dict(color=TEXT_SECONDARY),
            title=dict(font=dict(color=TEXT_PRIMARY)),
            height=550,
            margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(bgcolor=BG_CARD2, bordercolor=BORDER),
        )

        return html.Div(
            dcc.Graph(figure=fig_map, config={"displayModeBar": False}),
            style={"background": BG_CARD, "borderRadius": "8px",
                   "border": f"1px solid {BORDER}", "padding": "8px"}
        )

    # ── TAB 4: DEEP DIVE ─────────────────────────────────────
    elif tab == "deepdive":
        # Arrest rate by crime type
        arrest_by_type = (
            d.groupby("Primary Type")["Arrest"]
            .agg(["sum", "count"])
            .rename(columns={"sum": "arrests", "count": "total"})
        )
        arrest_by_type["rate"] = arrest_by_type["arrests"] / arrest_by_type["total"] * 100
        arrest_by_type = arrest_by_type.sort_values("rate", ascending=True).reset_index()

        colors = [RED if r < 15 else ACCENT2 if r < 30 else GREEN
                  for r in arrest_by_type["rate"]]
        

        fig_arrest = go.Figure(go.Bar(
            x=arrest_by_type["rate"],
            y=arrest_by_type["Primary Type"].str.title(),
            orientation="h",
            marker_color=colors,
            text=[f"{r:.1f}%" for r in arrest_by_type["rate"]],
            textposition="outside",
            textfont=dict(size=9),
        ))
        fig_arrest.add_vline(
            x=arrest_by_type["rate"].mean(),
            line_dash="dash", line_color=TEXT_SECONDARY, line_width=1,
            annotation_text=f"Avg {arrest_by_type['rate'].mean():.1f}%",
            annotation_font_color=TEXT_SECONDARY,
        )
        fig_arrest.update_layout(
            **PLOTLY_TEMPLATE["layout"],
            title="Arrest Rate by Crime Type (%)",
            height=420,
            xaxis_title="Arrest Rate (%)",
            xaxis_range=[0, arrest_by_type["rate"].max() * 1.3],
        )

        # Location description breakdown
        top_locations = (
            d["Location Description"].value_counts()
            .head(10).reset_index()
            .rename(columns={"index": "location", "Location Description": "count"})
        )
        # Handle both old and new pandas column naming
        if "Location Description" in top_locations.columns and "count" not in top_locations.columns:
            top_locations.columns = ["location", "count"]
        elif top_locations.columns[0] != "location":
            top_locations.columns = ["location", "count"]

        fig_loc = go.Figure(go.Bar(
            x=top_locations.iloc[:, 1],
            y=top_locations.iloc[:, 0],
            orientation="h",
            marker_color=BLUE,
        ))
        fig_loc.update_layout(
            **PLOTLY_TEMPLATE["layout"],
            title="Top Crime Locations",
            height=320,
        )

        return html.Div([
            html.Div(dcc.Graph(figure=fig_arrest, config={"displayModeBar": False}),
                     style={"background": BG_CARD, "borderRadius": "8px",
                            "border": f"1px solid {BORDER}", "padding": "8px", "marginBottom": "16px"}),
            html.Div(dcc.Graph(figure=fig_loc, config={"displayModeBar": False}),
                     style={"background": BG_CARD, "borderRadius": "8px", "border": f"1px solid {BORDER}", "padding": "8px"}),
        ])

    return html.Div("Select a tab", style={"color": TEXT_SECONDARY})


# ── RUN ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  STARTING CHICAGO CRIME INTELLIGENCE DASHBOARD")
    print("=" * 60)
    print("\n  Open in browser: http://127.0.0.1:8050")
    print("  Press Ctrl+C to stop\n")
    app.run(debug=True, host="0.0.0.0", port=8050)
