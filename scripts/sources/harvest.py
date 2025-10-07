import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
import json

class SitemapParser:
    def __init__(self, domains):
        self.domains = domains
        self.url_data = {}

    @staticmethod
    def ksl_sitemap_urls():
        years = [
            (2017, [0,1,2]),
            (2018, [0,1,2]),
            (2019, [0,1,2]),
            (2020, [0]),
            (2021, [0]),
            (2022, [0]),
            (2023, [0,1]),
            (2024, [0]),
        ]
        for y, idxs in years:
            for i in idxs:
                yield f"https://www.ksl.com/news-sitemap-{y}-{i}.xml.gz"

    def fetch_sitemap(self, domain):
        urls = []
        if domain == "deseretnews":
            base = "https://uploads.deseret.com/sitemaps/deseretnews/sitemap-articles-"
            for i in tqdm(range(46), desc=f"Fetching {domain}"):
                sm_url = f"{base}{i}.xml"
                resp = requests.get(sm_url)
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.content)
                urls.extend(
                    loc.text.strip()
                    for loc in root.iter(
                        "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                    )
                )
        elif domain in {"ksl", "ksl.com"}:
            for sm_url in tqdm(self.ksl_sitemap_urls(), desc=f"Fetching {domain}"):
                resp = requests.get(sm_url)
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.content)
                urls.extend(
                    loc.text.strip()
                    for loc in root.iter(
                        "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                    )
                )
        return urls

    def parse(self):
        for domain in self.domains:
            self.url_data[domain] = self.fetch_sitemap(domain)
        return self.url_data

    def export_json(self, filename="data/sitemap_data.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.url_data, f, indent=2, ensure_ascii=False)

# Example usage
if __name__ == "__main__":
    parser = SitemapParser(["deseretnews", "ksl"])
    data = parser.parse()
    print(len(data["deseretnews"]))
    print(data["deseretnews"][:5])
    print(len(data["ksl"]))
    print(data["ksl"][:5])
    parser.export_json("data/sitemaps.json")
