import os
import json
import time
import logging
import requests
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)


class TwitterAgent:
    def __init__(self):
        self.apify_key = os.getenv("APIFY_API_KEY")
        self.auth_token = os.getenv("TWITTER_AUTH_TOKEN")
        self.client = ApifyClient(self.apify_key)

    def _fetch_via_apify(self, ticker: str, since: str, until: str, limit: int) -> list:
        """Primary: Apify Scweet actor."""
        logging.info(f"[Apify] Fetching tweets for ${ticker}...")
        try:
            run = self.client.actor("altimis/scweet").call(run_input={
                "searchTerms": [f"${ticker} OR #{ticker}"],
                "since": since,
                "until": until,
                "maxItems": limit,
                "lang": "en",
            })
            tweets = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                tweets.append({
                    "ticker":     ticker,
                    "id":         str(item.get("id", "")),
                    "text":       item.get("text") or item.get("full_text", ""),
                    "author":     item.get("username") or item.get("user", {}).get("screen_name"),
                    "created_at": item.get("created_at"),
                    "likes":      item.get("likes", 0),
                    "retweets":   item.get("retweets", 0),
                    "replies":    item.get("replies", 0),
                    "source":     "apify",
                })
            logging.info(f"[Apify] ✅ {len(tweets)} tweets for ${ticker}")
            return tweets
        except Exception as e:
            logging.warning(f"[Apify] Failed for ${ticker}: {e} — falling back to Scweet")
            return []

    def _fetch_via_scweet(self, ticker: str, since: str, until: str, limit: int) -> list:
        """Fallback: local Scweet."""
        logging.info(f"[Scweet] Fetching tweets for ${ticker}...")
        try:
            from Scweet import Scweet
            s = Scweet(auth_token=self.auth_token)
            results = s.search(
                f"${ticker} OR #{ticker}",
                since=since, until=until, limit=limit,
            )
            tweets = []
            for row in results:
                tweets.append({
                    "ticker":     ticker,
                    "text":       row.get("text") or row.get("Tweet", ""),
                    "author":     row.get("username") or row.get("Username"),
                    "created_at": row.get("created_at") or row.get("Timestamp"),
                    "likes":      row.get("nlikes") or row.get("Likes", 0),
                    "retweets":   row.get("nretweets") or row.get("Retweets", 0),
                    "replies":    row.get("nreplies") or row.get("Replies", 0),
                    "source":     "scweet",
                })
            logging.info(f"[Scweet] ✅ {len(tweets)} tweets for ${ticker}")
            return tweets
        except Exception as e:
            logging.error(f"[Scweet] Failed for ${ticker}: {e}")
            return []

    def fetch_tweets_for_tickers(self, tickers: list, days: int = 7, tweets_per_ticker: int = 50) -> dict:
        from datetime import datetime, timedelta, timezone
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        until = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        all_results = {}
        for ticker in tickers:
            # Try Apify first
            tweets = self._fetch_via_apify(ticker, since, until, tweets_per_ticker)

            # Fallback to Scweet if Apify fails or returns 0
            if not tweets:
                tweets = self._fetch_via_scweet(ticker, since, until, tweets_per_ticker)

            all_results[ticker] = tweets
            time.sleep(1)

        return all_results

    def save_to_json(self, data: dict, filepath: str = "data/tweets.json"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Tweets saved to {filepath}")
