from __future__ import annotations

import code
from typing import List, Dict, Tuple, Literal, Optional
import re, os, time

import pandas as pd
import json

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from tqdm import tqdm

from extract import extract_article_text
from prompts import get_prompts

models = [
    "gemma-3-4b-it",
    "gemma-3n-e4b-it"
]

with open("gemma-api-key.txt", "r") as f:
    API_KEY = f.read().strip()

class SentimentClassifier:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemma-3-4b-it", prompts: str = "health vs. economy"):
        self.client = genai.Client(api_key=api_key)
        if not self.client:
            raise RuntimeError("Missing API key: set GEMINI_API_KEY or pass explicitly")
        self.model = model
        self.schema = {"type": "STRING", "enum": ["A", "B", "C", "D"]}
        self.config = types.GenerateContentConfig(temperature=0, response_schema=self.schema)

        self.prompt_templates = get_prompts(prompts)

    def build_prompt(self, topic: str, content: str, prompt_num: int) -> str:
        return self.prompt_templates[prompt_num].format(topic=topic, content=content)

    def classify(self, topic: str, article_text: str, prompt_num: int) -> Dict[str, str]:
        prompt = self.build_prompt(topic, article_text, prompt_num)

        output_text = ""
        while not output_text.strip():
            try:
                output_text = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self.config,
                ).text
            except ClientError as e:
                retry_delay = e.details['error']['details'][-1]['retryDelay']
                print("retryDelay =", retry_delay)
                if retry_delay and retry_delay.endswith("s"):
                    time.sleep(float(retry_delay[:-1]))
                continue

        return self.extract_label(output_text)

    @staticmethod
    def extract_label(output_text):
        output_text = output_text.strip()
        if not output_text:
            print(f"Unexpected output: '{output_text}'")
            return {"label": None}

        match = re.search(r"\b[A-D]\b", output_text)
        label = match.group(0) if match else None
        return {"label": label}

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

if __name__ == "__main__":

    sample = pd.read_csv("data/main_sample.csv")

    sentiment_data = {
        "model": [],
        "stanceA": [],
        "stanceB": [],
        "stanceC": [],
        "stanceD": []
    }

    clf = SentimentClassifier(model=models[1], api_key=API_KEY)
    for i in tqdm(range(len(sample["url"])), desc="Classifying articles"):
        test_url = sample.loc[i, "url"]
        article_text = sample.loc[sample['url'] == test_url, 'text'].iat[0] #extract_article_text(test_url)
        stances = []
        for prompt_num in range(len(clf.prompt_templates)):
            result = clf.classify("vaccination", article_text, prompt_num=prompt_num)
            stances.append(result["label"])
            time.sleep(3)

        sentiment_data["stanceA"].append(stances.count("A"))
        sentiment_data["stanceB"].append(stances.count("B"))
        sentiment_data["stanceC"].append(stances.count("C"))
        sentiment_data["stanceD"].append(stances.count("D"))

        sentiment_data["model"].append(models[1])

    sentiment_data = pd.DataFrame(sentiment_data)
    sentiment_data = pd.concat([sample, sentiment_data], axis=1)
    print(sentiment_data.head())

    sentiment_data.to_csv("data/sentiment_classification_main.csv", index=False)