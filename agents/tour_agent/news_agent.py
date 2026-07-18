import os, time, requests, feedparser, spacy
from transformers import pipeline
from cachetools import TTLCache
from utils.models import News  # your Pydantic schema

SEARCHAPI_ENDPOINT = "https://www.searchapi.io/api/v1/news"

class NewsAgent:
    def __init__(self, mode="online"):
        self.mode = mode
        # Cache: 30 min TTL
        self.cache = TTLCache(maxsize=100, ttl=1800)

        # NLP models
        self.ner_model = spacy.load("en_core_web_sm")
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        self.classifier = pipeline("zero-shot-classification")
        self.sentiment_analyzer = pipeline("sentiment-analysis")

        # Travel-relevant categories
        self.categories = ["event", "alert", "weather", "culture", "transport"]

    # --- Fetchers ---
    def _fetch_searchapi_news(self, query: str):
        api_key = os.getenv("SEARCHAPI_KEY")
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"q": query, "num": 5, "language": "en"}
        resp = requests.get(SEARCHAPI_ENDPOINT, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = []
        for article in data.get("news_results", []):
            parsed = {
                "headline": article.get("title"),
                "source": article.get("source"),
                "date": article.get("date"),
                "summary": article.get("snippet")
            }
            try:
                news = News(**parsed)
                items.append(news.dict())
            except Exception as e:
                print(f"⚠️ SearchAPI parse error: {e!r}")
        return items

    def _fetch_google_rss(self, query: str):
        url = f"https://news.google.com/rss/search?q={query}"
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:5]:
            parsed = {
                "headline": entry.title,
                "source": "Google News",
                "date": getattr(entry, "published", None),
                "summary": getattr(entry, "summary", None)
            }
            try:
                news = News(**parsed)
                items.append(news.dict())
            except Exception as e:
                print(f"⚠️ RSS parse error: {e!r}")
        return items

    # --- Public API ---
    def get_news(self, location, date=None):
        if self.mode == "demo":
            return [
                {"headline": "Temple festival announced in Trastevere on July 13 at 6 PM"},
                {"headline": "Political rally to block roads near Piazza Venezia tomorrow"},
                {"headline": "Heavy rains expected across Rome this weekend"}
            ]

        cache_key = f"{location}:{date}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Primary: SearchAPI.io
        try:
            news_items = self._fetch_searchapi_news(location)
            if news_items:
                self.cache[cache_key] = news_items
                return news_items
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                print("⚠️ SearchAPI rate limit hit, retrying...")
                time.sleep(2)
            else:
                print(f"⚠️ SearchAPI error: {e!r}")

        # Secondary: Google RSS
        try:
            rss_items = self._fetch_google_rss(location)
            if rss_items:
                self.cache[cache_key] = rss_items
                return rss_items
        except Exception as e:
            print(f"⚠️ RSS error: {e!r}")

        # Tertiary: Fallback
        fallback = [{
            "headline": f"Travel update for {location}",
            "source": "Gemini",
            "date": None,
            "summary": "No live feeds available, fallback summary."
        }]
        self.cache[cache_key] = fallback
        return fallback

    def process_news(self, headlines):
        digest = []
        for item in headlines:
            headline = item["headline"]

            # NER
            doc = self.ner_model(headline)
            entities = [(ent.text, ent.label_) for ent in doc.ents]

            # Summarization
            summary = self.summarizer(headline, max_length=30, min_length=10, do_sample=False)[0]['summary_text']

            # Classification
            classification = self.classifier(headline, self.categories)
            category = classification['labels'][0]

            # Sentiment
            sentiment = self.sentiment_analyzer(headline)[0]['label']

            digest.append({
                "headline": headline,
                "summary": summary,
                "entities": entities,
                "category": category,
                "sentiment": sentiment
            })
        return digest

    def digest_card(self, location, date=None):
        headlines = self.get_news(location, date)
        processed = self.process_news(headlines)

        card = "📰 Local News Digest\n"
        for item in processed:
            card += f"- {item['summary']} ({item['category']}, Sentiment: {item['sentiment']})\n"
        return card
