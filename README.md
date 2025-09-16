# Populism in U.S. News: Interrupted Time Series Analysis

This project investigates how **populism-related discourse** in U.S. digital news changed before and after the onset of COVID-19.  
We combine **news article sampling**, **large language model (LLM) stance classification**, and **interrupted time series (ITS)** methods to quantify both the prevalence and sentiment of populism in news coverage.

## Project Goals
- Construct a representative sample of U.S. news articles (2018–2025) from major national and local outlets.
- Use an instruction-tuned LLM (OpenAI) to classify stance toward populism (pro, anti, neutral).
- Estimate time-trend shifts with nonparametric interrupted time series models, focusing on March 11, 2020 (WHO pandemic declaration).

## Repository Structure
- `scraping/` – code for collecting and cleaning article text from URLs.
- `analysis/` – time-series models, exploratory notebooks.
- `data/` – sampled URLs, intermediate datasets (gitignored if large/private).
- `README.md` – project overview (this file).

## Getting Started
1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/populism-news-its.git
   cd populism-news-its
   ```
2. Install dependencies (Python 3.10+ recommended):
   ```bash
   pip install -r requirements.txt
   ```
3. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

## Next Steps
- Implement pipeline to extract main text from news articles (`scraping/`).
- Build stance classification wrapper using OpenAI Chat API with logprobs.
- Develop interrupted time series models for aggregated weekly data.

## License
MIT License (see `LICENSE` file).
