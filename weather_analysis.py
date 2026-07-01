"""
weather_analysis.py
--------------------
Cleans the Toronto (Environment Canada) hourly weather dataset, derives KPIs,
and produces all aggregations needed for the dashboard.

Input : Weather_Data.csv   (raw hourly weather data)
Output: dashboard_data.json (KPIs + monthly/hourly/seasonal/daily aggregates
                              + condition distribution + correlation matrix)

Usage:
    python weather_analysis.py --input Weather_Data.csv --output dashboard_data.json
"""

import argparse
import json
import re

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# 1. LOAD & CLEAN
# --------------------------------------------------------------------------- #
def load_and_clean(csv_path: str) -> pd.DataFrame:
    """Load the raw CSV, validate quality, and standardize/derive columns."""

    df = pd.read_csv(csv_path)

    # Standardize column names (raw file uses spaces / inconsistent casing)
    df.columns = [
        "DateTime", "Temp_C", "DewPoint_C", "Humidity_pct",
        "WindSpeed_kmh", "Visibility_km", "Pressure_kPa", "Weather",
    ]

    # Parse datetime (source format: M/D/YYYY H:MM)
    df["DateTime"] = pd.to_datetime(df["DateTime"], format="%m/%d/%Y %H:%M")

    # Trim whitespace on the text field
    df["Weather"] = df["Weather"].astype(str).str.strip()

    # ---- Data quality checks (raise if violated -- fail fast on bad data) ----
    assert df.isnull().sum().sum() == 0, "Unexpected nulls found"
    assert df["DateTime"].duplicated().sum() == 0, "Duplicate timestamps found"
    assert df["Humidity_pct"].between(0, 100).all(), "Humidity out of range"
    assert (df["WindSpeed_kmh"] >= 0).all(), "Negative wind speed found"
    assert (df["Visibility_km"] >= 0).all(), "Negative visibility found"

    # Confirm the hourly series is fully continuous (no gaps/missing hours)
    full_range = pd.date_range(df["DateTime"].min(), df["DateTime"].max(), freq="h")
    missing = full_range.difference(df["DateTime"])
    assert len(missing) == 0, f"Missing {len(missing)} timestamps in series"

    # ---- Derived time features ----
    df["Date"] = df["DateTime"].dt.date
    df["Year"] = df["DateTime"].dt.year
    df["Month"] = df["DateTime"].dt.month
    df["MonthName"] = df["DateTime"].dt.strftime("%b")
    df["Hour"] = df["DateTime"].dt.hour
    df["DayOfWeek"] = df["DateTime"].dt.day_name()
    df["Season"] = df["Month"].map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Fall", 10: "Fall", 11: "Fall",
    })

    # ---- Derived comfort / condition features ----
    df["TempDewSpread"] = df["Temp_C"] - df["DewPoint_C"]  # smaller = closer to saturation
    df["PrimaryCondition"] = df["Weather"].apply(_primary_condition)

    precip_keywords = ["Rain", "Snow", "Drizzle", "Freezing", "Thunderstorm", "Pellets"]
    df["IsPrecip"] = df["Weather"].apply(lambda w: any(k in w for k in precip_keywords))
    df["IsFog"] = df["Weather"].str.contains("Fog|Haze", regex=True)
    df["IsClear"] = df["Weather"].str.contains("Clear")

    return df


def _primary_condition(weather: str) -> str:
    """Collapse a compound weather string (e.g. 'Freezing Drizzle,Fog') into
    one representative category for charting."""
    first = re.split(",", weather)[0].strip()
    if "Thunderstorm" in first:
        return "Thunderstorm"
    if "Freezing" in first:
        return "Freezing Precip"
    if "Snow" in first:
        return "Snow"
    if "Rain" in first:
        return "Rain"
    if "Drizzle" in first:
        return "Drizzle"
    if "Fog" in first or "Haze" in first:
        return "Fog/Haze"
    return first  # Clear / Mainly Clear / Cloudy / Mostly Cloudy, etc.


# --------------------------------------------------------------------------- #
# 2. KPIs
# --------------------------------------------------------------------------- #
def compute_kpis(df: pd.DataFrame) -> dict:
    return {
        "avg_temp": round(df["Temp_C"].mean(), 1),
        "max_temp": round(df["Temp_C"].max(), 1),
        "max_temp_date": str(df.loc[df["Temp_C"].idxmax(), "DateTime"]),
        "min_temp": round(df["Temp_C"].min(), 1),
        "min_temp_date": str(df.loc[df["Temp_C"].idxmin(), "DateTime"]),
        "avg_humidity": round(df["Humidity_pct"].mean(), 1),
        "avg_wind": round(df["WindSpeed_kmh"].mean(), 1),
        "max_wind": int(df["WindSpeed_kmh"].max()),
        "avg_pressure": round(df["Pressure_kPa"].mean(), 2),
        "avg_visibility": round(df["Visibility_km"].mean(), 1),
        "pct_precip_hours": round(df["IsPrecip"].mean() * 100, 1),
        "pct_fog_hours": round(df["IsFog"].mean() * 100, 1),
        "pct_clear_hours": round(df["IsClear"].mean() * 100, 1),
        "total_hours": int(len(df)),
        "annual_temp_range": round(df["Temp_C"].max() - df["Temp_C"].min(), 1),
    }


# --------------------------------------------------------------------------- #
# 3. AGGREGATIONS
# --------------------------------------------------------------------------- #
def compute_monthly(df: pd.DataFrame) -> list:
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly = (
        df.groupby("Month")
        .agg(
            avg_temp=("Temp_C", "mean"),
            max_temp=("Temp_C", "max"),
            min_temp=("Temp_C", "min"),
            avg_humidity=("Humidity_pct", "mean"),
            avg_wind=("WindSpeed_kmh", "mean"),
            avg_pressure=("Pressure_kPa", "mean"),
            avg_visibility=("Visibility_km", "mean"),
            precip_hours=("IsPrecip", "sum"),
            fog_hours=("IsFog", "sum"),
            clear_hours=("IsClear", "sum"),
        )
        .reset_index()
    )
    monthly["MonthName"] = monthly["Month"].apply(lambda m: month_order[m - 1])
    return monthly.round(1).to_dict(orient="records")


def compute_hourly(df: pd.DataFrame) -> list:
    hourly = (
        df.groupby("Hour")
        .agg(
            avg_temp=("Temp_C", "mean"),
            avg_humidity=("Humidity_pct", "mean"),
            avg_wind=("WindSpeed_kmh", "mean"),
        )
        .round(1)
        .reset_index()
    )
    return hourly.to_dict(orient="records")


def compute_seasonal(df: pd.DataFrame) -> list:
    seasonal = (
        df.groupby("Season")
        .agg(
            avg_temp=("Temp_C", "mean"),
            avg_humidity=("Humidity_pct", "mean"),
            avg_wind=("WindSpeed_kmh", "mean"),
            precip_hours=("IsPrecip", "sum"),
        )
        .round(1)
        .reindex(["Winter", "Spring", "Summer", "Fall"])
        .reset_index()
    )
    return seasonal.to_dict(orient="records")


def compute_condition_distribution(df: pd.DataFrame, top_n: int = 8) -> dict:
    counts = df["PrimaryCondition"].value_counts()
    top = counts.head(top_n)
    other_sum = counts.iloc[top_n:].sum()
    dist = {k: int(v) for k, v in top.to_dict().items()}
    if other_sum > 0:
        dist["Other"] = int(other_sum)
    return dist


def compute_daily(df: pd.DataFrame) -> list:
    daily = (
        df.groupby("Date")
        .agg(
            avg_temp=("Temp_C", "mean"),
            max_temp=("Temp_C", "max"),
            min_temp=("Temp_C", "min"),
            avg_humidity=("Humidity_pct", "mean"),
            avg_wind=("WindSpeed_kmh", "mean"),
            avg_pressure=("Pressure_kPa", "mean"),
        )
        .round(1)
        .reset_index()
    )
    daily["Date"] = daily["Date"].astype(str)
    return daily.to_dict(orient="records")


def compute_correlation(df: pd.DataFrame) -> dict:
    cols = ["Temp_C", "DewPoint_C", "Humidity_pct",
            "WindSpeed_kmh", "Visibility_km", "Pressure_kPa"]
    corr = df[cols].corr().round(2)
    return {row: corr.loc[row].round(2).to_dict() for row in corr.index}


# --------------------------------------------------------------------------- #
# 4. PIPELINE
# --------------------------------------------------------------------------- #
def build_dashboard_data(csv_path: str) -> dict:
    df = load_and_clean(csv_path)
    return {
        "kpis": compute_kpis(df),
        "monthly": compute_monthly(df),
        "hourly": compute_hourly(df),
        "seasonal": compute_seasonal(df),
        "condition_distribution": compute_condition_distribution(df),
        "daily": compute_daily(df),
        "correlation": compute_correlation(df),
    }


def main():
    parser = argparse.ArgumentParser(description="Clean weather data and compute dashboard KPIs.")
    parser.add_argument("--input", default="Weather_Data.csv", help="Path to raw weather CSV")
    parser.add_argument("--output", default="dashboard_data.json", help="Path to write aggregated JSON")
    args = parser.parse_args()

    data = build_dashboard_data(args.input)

    with open(args.output, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Wrote aggregated dashboard data to {args.output}")
    print(json.dumps(data["kpis"], indent=2))


if __name__ == "__main__":
    main()
