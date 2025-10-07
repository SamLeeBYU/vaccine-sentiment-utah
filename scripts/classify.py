from __future__ import annotations

from typing import List, Dict, Tuple, Literal, Optional
import re, os

from google import genai
from google.genai import types

from extract import extract_article_text

LABEL_MAP = {
    "A": "POS",
    "B": "NEG",
    "C": "NEUTRAL",
}

models = [
    "gemma-3-4b-it",
    "gemma-3n-e4b-it"
]

class SentimentClassifier:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemma-3-4b-it"):
        self.client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        if not self.client:
            raise RuntimeError("Missing API key: set GEMINI_API_KEY or pass explicitly")
        self.model = model
        self.schema = {"type": "STRING", "enum": ["A", "B", "C"]}
        self.config = types.GenerateContentConfig(temperature=0, response_schema=self.schema)

        self.prompt_template = (
            "You are a stance-classifier.\n"
            "Task: Label the AUTHOR'S rhetoric towards {topic}.\n"
            "Output exactly one letter from {{A,B,C}}.\n"
            "Labels:\n"
            " A = PRO (supports)\n"
            " B = ANTI (opposes)\n"
            " C = NEUTRAL/UNCLEAR\n"
            "Rules:\n"
            "- Judge stance toward the specified topic only.\n\n"
            "=== ARTICLE TEXT START ===\n"
            "{content}\n"
            "=== ARTICLE TEXT END ==="
        )

    def build_prompt(self, topic: str, content: str) -> str:
        return self.prompt_template.format(topic=topic, content=content)

    def classify(self, topic: str, article_text: str) -> Dict[str, str]:
        prompt = self.build_prompt(topic, article_text)
        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self.config,
        )
        output_text = resp.text or ""

        return {
            "label": LABEL_MAP[output_text.strip()]
        }

if __name__ == "__main__":
    # Example usage
    test_url = "https://www.npr.org/sections/shots-health-news/2025/09/19/nx-s1-5545946/cdc-covid-vaccine-acip-recommendations"
    article = extract_article_text(test_url)

    clf = SentimentClassifier(model=models[1])
    result = clf.classify("vaccination", article.text)
    print(result)