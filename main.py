import json
import os
import logging
from agents.sec_agent import SECAgent
from agents.twitter_agent import TwitterAgent
from agents.sentiment_agent import SentimentAgent

TWEETS_CACHE = "data/tweets.json"


def get_top_tickers(transactions, top_n=5):
    ticker_totals = {}
    for tx in transactions:
        t = tx["ticker"]
        ticker_totals[t] = ticker_totals.get(t, 0) + tx["value"]
    sorted_tickers = sorted(ticker_totals.items(), key=lambda x: x[1], reverse=True)
    return [t for t, _ in sorted_tickers[:top_n]]


def main():
    # ── Step 2: SEC ─────────────────────────────────────────
    sec_agent = SECAgent()
    filings = sec_agent.fetch_last_24h_filings(lookback_days=7)
    transactions = sec_agent.extract_transactions(filings)

    print(f"\nTop 50 transactions by value:\n")
    print(f"{'#':<4} {'Ticker':<8} {'Code':<6} {'Date':<12} {'Shares':>10} {'Price':>10} {'Value':>14}  Security")
    print("-" * 90)
    for i, tx in enumerate(transactions[:50], 1):
        print(
            f"{i:<4} {tx['ticker']:<8} {tx['tx_code']:<6} {tx['date']:<12} "
            f"{tx['shares']:>10,.0f} {tx['price']:>10,.2f} "
            f"${tx['value']:>13,.2f}  {tx['security']}"
        )

    top_tickers = get_top_tickers(transactions, top_n=5)
    print(f"\n🏆 Top 5 tickers by insider trade value: {top_tickers}")

    # ── Save SEC data for RAG ────────────────────────────────
    os.makedirs("data", exist_ok=True)
    with open("data/sec_transactions.json", "w") as f:
        json.dump(transactions, f, indent=2)
    logging.info("SEC transactions saved.")

    # ── Step 3: Tweets (cached) ─────────────────────────────
    if os.path.exists(TWEETS_CACHE):
        print(f"\n📦 Loading cached tweets from {TWEETS_CACHE}...")
        with open(TWEETS_CACHE, "r", encoding="utf-8") as f:
            tweets_data = json.load(f)
    else:
        twitter_agent = TwitterAgent()
        tweets_data = twitter_agent.fetch_tweets_for_tickers(
            tickers=top_tickers, days=7, tweets_per_ticker=50
        )
        twitter_agent.save_to_json(tweets_data, filepath=TWEETS_CACHE)

    print("\n📊 Tweet summary:")
    for ticker, tweets in tweets_data.items():
        print(f"  ${ticker}: {len(tweets)} tweets")

    # ── Step 4: Sentiment ───────────────────────────────────
    print("\n🧠 Running sentiment analysis...\n")
    sentiment_agent = SentimentAgent()
    sentiment_results = sentiment_agent.analyze_all(tweets_data)
    sentiment_agent.save_to_json(sentiment_results, filepath="data/sentiment.json")

    print("\n📈 Sentiment Summary:\n")
    print(f"  {'Ticker':<8} {'Bullish':>10} {'Bearish':>10} {'Neutral':>10}  Signal")
    print("  " + "-" * 55)
    for ticker, result in sentiment_results.items():
        pct = result["sentiment_percentages"]
        bull, bear, neu = pct["bullish"], pct["bearish"], pct["neutral"]
        signal = "🟢 BULLISH" if bull > bear + 20 else "🔴 BEARISH" if bear > bull + 20 else "🟡 MIXED"
        print(f"  {ticker:<8} {bull:>8.1f}%  {bear:>8.1f}%  {neu:>8.1f}%   {signal}")


if __name__ == "__main__":
    main()