# Scraper for https://utahsonlinelibrary.org/countynews/
# Saves a CSV with columns: county,name,url,source_page
import re
import time
import csv
from urllib.parse import urljoin, urlparse
from distro import name
import requests
from bs4 import BeautifulSoup

BASE = "https://utahsonlinelibrary.org/countynews/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; UtahCountyNewsScraper/1.0; +https://github.com/SamLeeBYU)"
}

def get_soup(url):
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)
    return None

def is_external_news_link(href):
    if not href:
        return False
    href = href.strip()
    if not href.startswith("http"):
        return False
    # Exclude Utah Online Library self-links
    netloc = urlparse(href).netloc.lower()
    if "utahsonlinelibrary.org" in netloc:
        return False
    # Exclude obvious social/share or non-news platforms if desired
    bad_hosts = ["facebook.com", "twitter.com", "x.com", "instagram.com", "youtube.com", "maps.google.", "google.com", "apple.com", "play.google.com"]
    if any(bad in netloc for bad in bad_hosts):
        return False
    return True

def discover_county_pages():
    soup = get_soup(BASE)
    county_links = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        text = a.get_text(strip=True)
        if not href:
            continue
        full = urljoin(BASE, href)
        # Heuristic: county pages are children of /countynews/ and not the base itself
        parsed = urlparse(full)
        if not full.startswith(BASE):
            continue
        # Accept paths like /countynews/{county}/ or /countynews/{county}
        path = parsed.path.rstrip("/")
        base_path = urlparse(BASE).path.rstrip("/")
        # Must have one more path segment than base
        if path == base_path:
            continue
        if not path.startswith(base_path + "/"):
            continue
        # Keep only first-segment children (avoid deeper subpaths like /countynews/{county}/something)
        rel = path[len(base_path) + 1:]
        if "/" in rel:
            continue
        county = rel
        county_links.append((county, full))
    # Deduplicate by county
    dedup = {}
    for county, url in county_links:
        dedup[county] = url
    return sorted(dedup.items())

CITY_RE = re.compile(
    r'^\s*(?P<city>.+?)'                  # city
    r'(?:,\s*(?:Utah|UT)|\s+(?:Utah|UT))' # state (with or without comma)
    r'(?:\s+\d{5}(?:-\d{4})?)?\s*$',      # optional ZIP or ZIP+4
    flags=re.I
)

def clean_city(s: str) -> str:
    m = CITY_RE.match(s.strip().replace(",", ""))
    return m.group('city').strip() if m else s.strip()

def extract_news_links_from_county(county_url):
    soup = get_soup(county_url)
    links = []
    candidates = soup.select(".infeatureboxMain .colBox p a[href]")
    titles = soup.select(".infeatureboxMain .colBox span")
    title_text = [t.get_text(strip=True) for t in titles]

    city_text = soup.select(".infeatureboxMain .colBox p")
    cities_1 = [city.text.split("\n")[3].strip() for city in city_text]
    cities_2 = [city.text.split("\n")[-1].strip() for city in city_text]
    cities = [clean_city(c1) if len(c1) > len(c2) else clean_city(c2) for c1, c2 in zip(cities_1, cities_2)]

    for a in candidates:
        href = a.get("href")
        if len(a.text) > 1 and is_external_news_link(href):
            full = urljoin(county_url, href)
            links.append(full)

    out = [(c, t, u) for c, t, u in zip(cities, title_text, links)]

    return out

def scrape_all():
    rows = []
    counties = discover_county_pages()
    for county, county_url in counties:
        try:
            news_links = extract_news_links_from_county(county_url)
        except Exception as e:
            news_links = []
        for city, name, url in news_links:
            rows.append({
                "county": county.split(".")[0].title().replace("_", " "),
                "city": city,
                "name": name,
                "url": url,
                "source_page": county_url
            })
        time.sleep(0.5)  # be polite
    return rows

if __name__ == "__main__":
    rows = scrape_all()
    out_path = "data/utah_news_sources.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["county", "city", "name", "url", "source_page"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")