import json
import numpy as np
import pandas as pd
import re
import matplotlib.pyplot as plt

def read_annotations(json_file: str, domain: str):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data[domain]

def get_dates(urls):
    s = pd.Series(urls, dtype="string")
    pat = r'https?://[^/]+/(?:[^/]+/)*?(?P<y>\d{4})/(?P<m>\d{1,2})/(?P<d>\d{1,2})(?:/|$)'
    m = s.str.extract(pat)
    m.columns = ["year", "month", "day"]

    mask = m.isna().any(axis=1)

    #Merge m[~mask] with s[~mask]
    dates = pd.to_datetime(m[~mask].astype(int), errors="coerce")
    return pd.DataFrame({
        "url": s[~mask].reset_index(drop=True),
        "date": dates.reset_index(drop=True)
    })

def filter_urls(df, start="2017-01-01", end="2025-01-01"):
    mask = (df["date"] >= pd.to_datetime(start)) & (df["date"] <= pd.to_datetime(end))
    return df.loc[mask].sort_values("date").reset_index(drop=True)

def plot_articles_by_month(df):
    monthly_counts = (
        df.dropna(subset=["date"])
          .groupby(df["date"].dt.to_period("M"))
          .size()
          .to_timestamp()
    )
    plt.figure(figsize=(10,4))
    plt.plot(monthly_counts.index, monthly_counts.values, marker="o")
    plt.title("Articles by Month")
    plt.xlabel("Month")
    plt.ylabel("Count")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    urls = read_annotations("data/sitemaps.json", "deseretnews")
    print(f"Read {len(urls)} URLs")
    data = filter_urls(get_dates(urls))
    print(data.head())


