import os
import json
import time
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

BATCH_SIZE = 5        # 5 tweets per API call
DELAY_SECONDS = 2     # Groq is generous but let's be polite


class SentimentAgent:
    def __init__(self):
        
        self.api_key = os.getenv("GROQ_API_KEY") or 
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # free, fast, very capable
        logging.info(f"Using Groq model: {self.model}")

    def _classify_batch(self, tweets: list, ticker: str) -> list:
        """
        Classify a batch of tweets in ONE API call.
        Returns list of labels matching input order.
        """
        numbered = "\n".join(
            f'{i+1}. "{t.get("text", "")[:200]}"'
            for i, t in enumerate(tweets)
        )

        prompt = f"""You are a financial sentiment classifier for stock ${ticker}.

Classify each tweet's sentiment. Reply with ONLY a numbered list, one word per line.
Use only: bullish, bearish, or neutral.

- bullish = positive outlook, buying, moon, calls, breakout, upside, good news
- bearish = negative outlook, selling, dump, puts, downside, crash, bad news  
- neutral = no clear direction, just news, question, unrelated

Tweets:
{numbered}

Reply format (exactly like this, nothing else):
1. bullish
2. bearish
3. neutral"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=BATCH_SIZE * 6,
                temperature=0,
            )

            content = response.choices[0].message.content
            if not content:
                logging.warning("Groq returned empty content")
                return ["neutral"] * len(tweets)

            # Parse numbered response
            lines = content.strip().split("\n")
            labels = []
            for line in lines:
                line = line.strip().lower()
                # skip empty lines or lines without sentiment words
                if not line:
                    continue
                if "bullish" in line:
                    labels.append("bullish")
                elif "bearish" in line:
                    labels.append("bearish")
                elif "neutral" in line:
                    labels.append("neutral")

            # Pad with neutral if response was shorter than batch
            while len(labels) < len(tweets):
                labels.append("neutral")

            return labels[:len(tweets)]

        except Exception as e:
            logging.warning(f"Groq batch call failed: {e}")
            return ["neutral"] * len(tweets)

    def _compute_weighted_sentiment(self, classified_tweets: list) -> dict:
        """
        Weighted sentiment: tweets with more likes/retweets count more.
        """
        counts = {"bullish": 0, "bearish": 0, "neutral": 0}
        weighted = {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0}

        for tweet in classified_tweets:
            label = tweet["sentiment"]
            counts[label] += 1
            # Weight = likes + (retweets * 2) + 1 base
            weight = tweet.get("likes", 0) + (tweet.get("retweets", 0) * 2) + 1
            weighted[label] += weight

        total_count = sum(counts.values()) or 1
        total_weight = sum(weighted.values()) or 1

        return {
            "counts": counts,
            "percentages": {
                k: round((v / total_count) * 100, 1)
                for k, v in counts.items()
            },
            "weighted_percentages": {
                k: round((v / total_weight) * 100, 1)
                for k, v in weighted.items()
            }
        }

    def analyze_ticker(self, ticker: str, tweets: list) -> dict:
        """Classify all tweets for a ticker and return aggregated sentiment."""
        logging.info(f"Analyzing sentiment for ${ticker} ({len(tweets)} tweets)...")

        # Filter empty tweets
        valid_tweets = [t for t in tweets if t.get("text", "").strip()]
        classified_tweets = []

        # Process in batches
        for i in range(0, len(valid_tweets), BATCH_SIZE):
            batch = valid_tweets[i:i + BATCH_SIZE]
            labels = self._classify_batch(batch, ticker)

            for tweet, label in zip(batch, labels):
                classified_tweets.append({**tweet, "sentiment": label})

            processed = min(i + BATCH_SIZE, len(valid_tweets))
            logging.info(f"  ${ticker}: {processed}/{len(valid_tweets)} classified...")

            time.sleep(DELAY_SECONDS)

        sentiment_summary = self._compute_weighted_sentiment(classified_tweets)

        # Top 3 sample tweets per sentiment for chatbot context
        samples = {"bullish": [], "bearish": [], "neutral": []}
        for tweet in classified_tweets:
            label = tweet["sentiment"]
            if len(samples[label]) < 3:
                samples[label].append(tweet.get("text", ""))

        logging.info(
            f"  ✅ ${ticker} done — "
            f"Bullish: {sentiment_summary['percentages']['bullish']}% | "
            f"Bearish: {sentiment_summary['percentages']['bearish']}% | "
            f"Neutral: {sentiment_summary['percentages']['neutral']}%"
        )

        return {
            "ticker":                         ticker,
            "total_tweets_analyzed":          len(classified_tweets),
            "sentiment":                      sentiment_summary["counts"],
            "sentiment_percentages":          sentiment_summary["percentages"],
            "weighted_sentiment_percentages": sentiment_summary["weighted_percentages"],
            "sample_tweets":                  samples,
            "all_classified_tweets":          classified_tweets,
        }

    def analyze_all(self, tweets_data: dict) -> dict:
        """Run sentiment analysis on all tickers."""
        results = {}
        for ticker, tweets in tweets_data.items():
            if not tweets:
                logging.warning(f"No tweets for ${ticker}, skipping.")
                continue
            results[ticker] = self.analyze_ticker(ticker, tweets)
        return results

    def save_to_json(self, data: dict, filepath: str = "data/sentiment.json"):
        """Save sentiment results to JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Sentiment results saved to {filepath}")
