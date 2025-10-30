"""
scraping.extract
----------------
Utilities to fetch and extract the main textual content from a news article URL.
Designed for use in the populism-news-its pipeline.

Dependencies:
    pip install requests beautifulsoup4 trafilatura tldextract

Notes:
- trafilatura is usually best for news; we fall back to BeautifulSoup if needed.
- We do NOT attempt to bypass hard paywalls.
"""

from __future__ import annotations

import re
import math
import json
import time
from tqdm import tqdm
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

import requests
from bs4 import BeautifulSoup
import trafilatura
import tldextract
from datetime import datetime

from collections import Counter
from functools import reduce

pattern = re.compile(
    r"(Jan(?:uary)?\.?|Feb(?:ruary)?\.?|Mar(?:ch)?\.?|Apr(?:il)?\.?|May\.?|Jun(?:e)?\.?|Jul(?:y)?\.?|Aug(?:ust)?\.?|"
    r"Sep(?:t(?:ember)?)?\.?|Oct(?:ober)?\.?|Nov(?:ember)?\.?|Dec(?:ember)?\.?)\s+(\d{1,2}),\s*(\d{4})"
)


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) sentiment-sampler/1.0"

@dataclass
class Article:
    url: str
    title: Optional[str]
    site: Optional[str]
    published_time: Optional[str]
    text: str
    word_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _clean_spaces(s: str) -> str:
    # Normalize whitespace and strip
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def parse_date_str(month, day, year):
    month = month.strip().replace(".", "").title()
    
    month_map = {
        "Jan": "Jan", "January": "January",
        "Feb": "Feb", "February": "February",
        "Mar": "Mar", "March": "March",
        "Apr": "Apr", "April": "April",
        "May": "May",
        "Jun": "Jun", "June": "June",
        "Jul": "Jul", "July": "July",
        "Aug": "Aug", "August": "August",
        "Sept": "Sep", "Sep": "Sep", "September": "September",
        "Oct": "Oct", "October": "October",
        "Nov": "Nov", "November": "November",
        "Dec": "Dec", "December": "December"
    }

    month = month_map.get(month, month)
    try:
        dt = datetime.strptime(f"{month} {day}, {year}", "%b %d, %Y")
    except ValueError:
        dt = datetime.strptime(f"{month} {day}, {year}", "%B %d, %Y")
    return dt.strftime("%Y-%m-%d")

def _extract_meta(soup: BeautifulSoup, url: str) -> Dict[str, Optional[str]]:
    # Title
    meta_og_title = soup.select_one("meta[property='og:title']")
    title = (meta_og_title.get("content").strip() if meta_og_title and meta_og_title.get("content") else None)
    if not title:
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

    # Site
    meta_site = soup.select_one("meta[property='og:site_name']")
    site = (meta_site.get("content").strip() if meta_site and meta_site.get("content") else None)
    if not site:
        ext = tldextract.extract(url)
        site = ".".join([p for p in [ext.domain, ext.suffix] if p])

    # Published time
    meta_pub = None
    for sel in [
        "meta[property='article:published_time']",
        "meta[name='publishdate']",
        "meta[name='date']",
        "time[datetime]",
        "meta[name='DC.date.issued']",
        "div[class='author']"
    ]:
        tag = soup.select_one(sel)
        if sel != "div[class='author']":
            if tag:
                meta_pub = tag.get("content") or tag.get("datetime")
                if meta_pub:
                    meta_pub = meta_pub.strip()
                    break
        else:
            if tag and tag.text:
                dates = pattern.findall(tag.text)
                parsed_strs = [parse_date_str(m, d, y) for m, d, y in dates]
                if dates:
                    meta_pub = parsed_strs[0]
                    break

    return {"title": title, "site": site, "published_time": meta_pub}


def _filter_paragraphs(paragraphs, min_par_chars: int) -> list[str]:
    out = []
    bad_snippets = [
        "subscribe", "cookie", "accept cookies", "sign up", "newsletter",
        "advertisement", "ad choices", "share this", "follow us", "privacy policy"
    ]
    for p in paragraphs:
        p = p.strip()
        if len(p) < min_par_chars:
            continue
        low = p.lower()
        if any(b in low for b in bad_snippets):
            continue
        out.append(p)
    # Light dedupe while preserving order
    seen = set()
    uniq = []
    for p in out:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


def extract_article_text(
    url: str,
    *,
    min_par_chars: int = 120,
    max_chars: int = 20000,
    timeout: int = 25,
    allow_redirects: bool = True
) -> Article:
    """
    Fetch a URL and return an Article with cleaned main text and metadata.

    Parameters
    ----------
    url : str
        Article URL.
    min_par_chars : int
        Minimum characters per paragraph to keep when falling back to <p>-based extraction.
    max_chars : int
        Safety cap on returned text length.
    timeout : int
        HTTP timeout (seconds).
    allow_redirects : bool
        Whether to follow redirects in the initial GET.

    Returns
    -------
    Article
        Dataclass with url, title, site, published_time, text, word_count.
    """
    # First try trafilatura's downloader/extractor
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if extracted:
            text = _clean_spaces(extracted)
        else:
            text = ""
    else:
        text = ""

    title = site = published_time = None

    # If trafilatura failed or text is too short, fallback to BeautifulSoup
    if not text or len(text) < 400:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout, allow_redirects=allow_redirects)
        resp.raise_for_status()
        html = resp.text

        soup = BeautifulSoup(html, "html.parser")

        # Metadata
        meta = _extract_meta(soup, url)
        title = meta["title"]
        site = meta["site"]
        published_time = meta["published_time"]

        # Remove obvious boilerplate
        for selector in ["script", "style", "noscript", "header", "footer", "nav", "aside", "form", "iframe", "svg", "template"]:
            for tag in soup.select(selector):
                tag.decompose()

        # Gather paragraphs
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all(["p", "h2", "h3", "li"])]
        paragraphs = _filter_paragraphs(paragraphs, min_par_chars=min_par_chars)
        text = _clean_spaces("\n\n".join(paragraphs))

    # Trim
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0]

    # If we still lack metadata and used trafilatura path, attempt minimal meta pass
    if title is None or site is None or published_time is None:
        try:
            # quick lightweight HEAD+GET for meta only (avoid double large downloads)
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout, allow_redirects=False)
            soup = BeautifulSoup(resp.text, "html.parser")
            meta = _extract_meta(soup, url)
            title = title or meta["title"]
            site = site or meta["site"]
            published_time = published_time or meta["published_time"]
        except Exception:
            pass

    # Finalize
    word_count = len(text.split()) if text else 0
    return Article(
        url=url,
        title=title,
        site=site,
        published_time=published_time,
        text=text,
        word_count=word_count
    )

# Convenience: JSON serialization helper
def extract_article_text_json(url: str, **kwargs) -> str:
    art = extract_article_text(url, **kwargs)
    return json.dumps(art.to_dict(), ensure_ascii=False, indent=2)

ksl_articles = [
    "https://www.ksl.com/article/50131978/experts-sound-warning-as-utah-student-vaccination-rates-show-troubling-trend",
    "https://www.ksl.com/article/50391394/childhood-vaccination-rates-fell-in-kindergartners-last-school-year-cdc-data-shows",
    "https://www.ksl.com/article/50359276/new-study-covid-19-vaccines-quickly-lose-effectiveness-in-kids-5-11",
    "https://www.ksl.com/article/50349268/covid-vaccination-during-pregnancy-helps-protect-babies-after-birth-study-says",
    "https://www.ksl.com/article/50353169/public-covid-19-testing-in-utah-isnt-over-heres-where-you-can-get-tested-this-week"
]

deseret_articles = [
    "https://www.deseret.com/utah/2021/6/10/22528258/utah-incentives-for-covid-19-vaccines-lt-gov-henderson-asks-businesses-to-give-time-off-for-vaccines/",
    "https://www.deseret.com/coronavirus/2021/7/15/22577007/fully-vaccinated-delta-variant-hospitalization/",
    "https://www.deseret.com/u-s-world/2021/2/13/22280029/covid-19-vaccine-doses-president-joe-biden/",
    "https://www.deseret.com/u-s-world/2022/1/5/22868328/president-emmanuel-macron-covid-unvaccinated-life-miserable-health-pass/",
    "https://www.deseret.com/opinion/2022/2/3/22916795/utah-legislature-mask-mandate-high-cases-covid-19-trasmission-unvaccinated/"
]

test_urls = ksl_articles + deseret_articles

example_test = {}

# Tokenize and clean words
def tokenize(text):
    tokens = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return set(tokens)

if __name__ == "__main__":

    # Example usage
    
    for url in tqdm(test_urls):
        article = extract_article_text(url)
        example_test[url] = article.text if article.text else ""
        time.sleep(1)  # be nice to servers

    with open("data/example_extracted.json", "w", encoding="utf-8") as f:
        json.dump(example_test, f, indent=2, ensure_ascii=False)

    print(json.dumps(article.to_dict(), ensure_ascii=False, indent=2))