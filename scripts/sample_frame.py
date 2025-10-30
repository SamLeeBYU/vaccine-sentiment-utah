import json
import re
from pathlib import Path
from typing import Any, Dict, List, Iterable, Optional

import pandas as pd
import time
from tqdm import tqdm
from datetime import datetime

from extract import extract_article_text
from sampleurl import read_annotations, get_dates, filter_urls


DEFAULT_KEY_WORDS = [
    "vaccine", "vaccines", "vaccination", "vaccinations",
    "vaccinated", "vaccinating", "vaccinates",
    "unvaccinated", "unvaccinate", "unvaccinating", "unvaccinates",
    "antivaccine", "anti-vaccine", "anti vaccine",
    "antivax", "anti-vax", "anti vax",
    "antivaxxer", "anti-vaxxer", "anti vaxxer",
    "antivaxxers", "anti-vaxxers", "anti vaxxers",
    "immunization", "immunizations",
    "immunisation", "immunisations",
    "immunize", "immunized", "immunizing",
    "immunise", "immunised", "immunising",
]


class VaccineArticleCollector:
    def __init__(
        self,
        json_in: str,
        json_out: str,
        *,
        start_date: str = "2017-01-01",
        end_date: str = "2024-01-01",
        keywords: Optional[Iterable[str]] = None,
        sleep_sec: float = 0.5,
    ):
        self.json_in = Path(json_in)
        self.json_out = Path(json_out)
        self.start_date = start_date
        self.end_date = end_date

        self.start = datetime.strptime(self.start_date, "%Y-%m-%d")
        self.end = datetime.strptime(self.end_date, "%Y-%m-%d")

        self.sleep_sec = sleep_sec

        kws = list(keywords) if keywords is not None else list(DEFAULT_KEY_WORDS)
        self._kw_pattern = re.compile(r"\b(" + "|".join(map(re.escape, kws)) + r")\b", re.IGNORECASE)

        # URL -> record dict
        self._results: Dict[str, Dict[str, Any]] = {}

    def _domains(self) -> List[str]:
        with self.json_in.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return list(data.keys())

    def _urls_for_domain(self, domain: str) -> List[str]:
        return read_annotations(str(self.json_in), domain)

    def _urls_in_date_range(self, urls: List[str]) -> List[str]:
        df = get_dates(urls)
        if df.empty:
            return []
        df = filter_urls(df, start=self.start_date, end=self.end_date)
        return df["url"].astype(str).tolist()

    def _has_keywords(self, text: str) -> bool:
        if not text:
            return False
        return bool(self._kw_pattern.search(text))

    def _scrape(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            art = extract_article_text(
                url
            )
            text = (getattr(art, "text", "") or "").strip()
            if not text:
                return None

            rec: Dict[str, Any] = {
                "url": getattr(art, "url", url),
                "title": getattr(art, "title", None),
                "site": getattr(art, "site", None),
                "published_time": getattr(art, "published_time", None),
                "text": text,
            }
            return rec
        except Exception:
            return None

    def _process_url(self, url: str):
        if url in self._results:
            return
        rec = self._scrape(url)
        pt = datetime.strptime(rec["published_time"][:10], "%Y-%m-%d") if rec and rec.get("published_time") else None
        if rec and self._has_keywords(rec["text"]) and pt and pt >= self.start and pt <= self.end:
            self._results[url] = rec

    def process(self, domains = None, urlstart = None):
        domains = domains if domains is not None else self._domains()
        for domain in domains:
            urls = self._urls_for_domain(domain)
            if domain == "deseretnews":
                urls = self._urls_in_date_range(urls)
            start = urlstart if urlstart is not None else 0
            urls = urls[start:]
            for url in tqdm(urls, desc=f"Processing {domain}"):
                self._process_url(url)
                if self.sleep_sec:
                    time.sleep(self.sleep_sec)

    def save(self):
        payload = self._results if self._results else {}
        self.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":

    # usage example:
    collector = VaccineArticleCollector(
        json_in="data/sitemaps.json",
        json_out="data/vaccine_articles.json",
        start_date="2017-01-01",
        end_date="2024-01-01",
        keywords=DEFAULT_KEY_WORDS,
    )
    collector.process(domains=['ksl'], urlstart=32912)
    collector.save()
