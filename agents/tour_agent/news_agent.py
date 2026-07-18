import spacy
from transformers import pipeline

class NewsAgent:
    def __init__(self, mode="live"):
        self.mode = mode
        # Load NLP models
        self.ner_model = spacy.load("en_core_web_sm")
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        self.classifier = pipeline("zero-shot-classification")
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        # Travel-relevant categories
        self.categories = ["event", "alert", "weather", "culture", "transport"]

    def get_news(self, location, date):
        if self.mode == "mock":
            return [
                "Temple festival announced in Trastevere on July 13 at 6 PM",
                "Political rally to block roads near Piazza Venezia tomorrow",
                "Heavy rains expected across Rome this weekend"
            ]
        else:
            # Replace with Google News API or RSS feed integration
            return fetch_local_news_api(location, date)

    def process_news(self, headlines):
        digest = []
        for headline in headlines:
            # Named Entity Recognition
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

    def digest_card(self, location, date):
        headlines = self.get_news(location, date)
        processed = self.process_news(headlines)

        card = "📰 Local News Digest\n"
        for item in processed:
            card += f"- {item['summary']} ({item['category']}, Sentiment: {item['sentiment']})\n"
        return card

