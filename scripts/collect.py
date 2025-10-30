import itertools
import pandas as pd
import json

from sampleurl import plot_articles_by_month

#Read in sampling frame of URLs
def get_sampling_frame(json_files) -> pd.DataFrame:
    merged = {}
    for file in json_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged.update(data)

    records = []
    for url, details in merged.items():
        records.append({
            "url": details.get("url", ""),
            "title": details.get("title", ""),
            "site": details.get("site", ""),
            "published_time": details.get("published_time", ""),
            "text": details.get("text", "")
        })
    df = pd.DataFrame(records)

    #[1188, 1282, 1284, 1287, 1290, 1292, 1295, 1297, 1298]

    #First convert dates like these: '2017-10-03'
    date1 = pd.to_datetime(df['published_time'], format='%Y-%m-%d', errors='coerce')
    #Then convert dates like these: '2017-01-10T22:57:22Z'
    date2 = pd.to_datetime(df['published_time'], format='%Y-%m-%dT%H:%M:%SZ', errors='coerce')
    #and '2021-01-28T22:37:36.059Z'
    date3 = pd.to_datetime(df['published_time'], format='%Y-%m-%dT%H:%M:%S.%fZ', errors='coerce')
    df['date'] = date1.combine_first(date2).combine_first(date3)

    return df

if __name__ == "__main__":
    sampling_frame = get_sampling_frame(["data/vaccine_articles_1.json", "data/vaccine_articles.json"])
    #plot_articles_by_month(sampling_frame)

    sampling_frame.to_csv("data/sampling_frame.csv", index=False)