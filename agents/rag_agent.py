import os
import json
import logging
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)


class RAGAgent:
    def __init__(self):
        self.groq = Groq(api_key="")
        self.model = "llama-3.3-70b-versatile"
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.chunks = []
        self.index = None
        logging.info("RAG Agent initialized")

    # ─────────────────────────────────────────
    # STEP 1: CHUNKING
    # ─────────────────────────────────────────
    def build_chunks(self, sec_data: list, tweets_data: dict, sentiment_data: dict):
        """
        Convert all collected data into searchable chunks.

        Chunking strategy:
        - Chunk 1 per ticker: SEC insider trading summary
        - Chunk 2 per ticker: Sentiment summary
        - Chunk 3 per ticker: Sample bullish tweets
        - Chunk 4 per ticker: Sample bearish tweets
        - Chunk 5: Overall market summary (cross-ticker)
        """
        self.chunks = []

        tickers = list(sentiment_data.keys())

        for ticker in tickers:
            sentiment = sentiment_data.get(ticker, {})
            tweets = tweets_data.get(ticker, [])
            pct = sentiment.get("sentiment_percentages", {})
            counts = sentiment.get("sentiment", {})
            weighted = sentiment.get("weighted_sentiment_percentages", {})
            samples = sentiment.get("sample_tweets", {})

            # ── Chunk 1: SEC insider trading data ──────────
            ticker_txns = [t for t in sec_data if t.get("ticker") == ticker]
            total_value = sum(t.get("value", 0) for t in ticker_txns)
            sells = [t for t in ticker_txns if t.get("tx_code") == "S"]
            buys  = [t for t in ticker_txns if t.get("tx_code") == "P"]
            awards = [t for t in ticker_txns if t.get("tx_code") in ["A", "F", "M"]]

            sec_text = f"""
SEC Insider Trading Data for ${ticker}:
Total insider transaction value: ${total_value:,.2f}
Number of insider sells (S): {len(sells)}
Number of insider purchases (P): {len(buys)}
Number of awards/grants (A/F/M): {len(awards)}
Total transactions: {len(ticker_txns)}
Most recent transactions: {', '.join([f"${t['value']:,.0f} ({t['tx_code']})" for t in ticker_txns[:3]])}
""".strip()

            self.chunks.append({
                "id": f"{ticker}_sec",
                "ticker": ticker,
                "type": "sec_insider",
                "text": sec_text
            })

            # ── Chunk 2: Sentiment summary ──────────────────
            bull_pct = pct.get("bullish", 0)
            bear_pct = pct.get("bearish", 0)
            neu_pct  = pct.get("neutral", 0)
            w_bull   = weighted.get("bullish", 0)
            w_bear   = weighted.get("bearish", 0)

            if bull_pct > bear_pct + 20:
                signal = "BULLISH"
            elif bear_pct > bull_pct + 20:
                signal = "BEARISH"
            else:
                signal = "MIXED"

            sentiment_text = f"""
Sentiment Analysis for ${ticker}:
Overall signal: {signal}
Bullish tweets: {bull_pct}% ({counts.get('bullish', 0)} tweets)
Bearish tweets: {bear_pct}% ({counts.get('bearish', 0)} tweets)
Neutral tweets: {neu_pct}% ({counts.get('neutral', 0)} tweets)
Total tweets analyzed: {sentiment.get('total_tweets_analyzed', 0)}
Weighted bullish (by likes/retweets): {w_bull}%
Weighted bearish (by likes/retweets): {w_bear}%
""".strip()

            self.chunks.append({
                "id": f"{ticker}_sentiment",
                "ticker": ticker,
                "type": "sentiment",
                "text": sentiment_text
            })

            # ── Chunk 3: Bullish tweets ─────────────────────
            bull_tweets = samples.get("bullish", [])
            if bull_tweets:
                bull_text = f"""
Bullish tweets about ${ticker} (last 7 days):
""" + "\n".join(f'- "{t}"' for t in bull_tweets)

                self.chunks.append({
                    "id": f"{ticker}_bullish_tweets",
                    "ticker": ticker,
                    "type": "bullish_tweets",
                    "text": bull_text.strip()
                })

            # ── Chunk 4: Bearish tweets ─────────────────────
            bear_tweets = samples.get("bearish", [])
            if bear_tweets:
                bear_text = f"""
Bearish tweets about ${ticker} (last 7 days):
""" + "\n".join(f'- "{t}"' for t in bear_tweets)

                self.chunks.append({
                    "id": f"{ticker}_bearish_tweets",
                    "ticker": ticker,
                    "type": "bearish_tweets",
                    "text": bear_text.strip()
                })

        # ── Chunk 5: Cross-ticker comparison ───────────────
        comparison_lines = []
        for ticker in tickers:
            s = sentiment_data.get(ticker, {})
            p = s.get("sentiment_percentages", {})
            bull = p.get("bullish", 0)
            bear = p.get("bearish", 0)
            sig  = "BULLISH" if bull > bear + 20 else "BEARISH" if bear > bull + 20 else "MIXED"
            comparison_lines.append(
                f"${ticker}: {sig} — Bullish {bull}%, Bearish {bear}%"
            )

        comparison_text = "Overall Market Sentiment Comparison (Top 5 insider trading tickers):\n" + \
                          "\n".join(comparison_lines)

        self.chunks.append({
            "id": "overall_comparison",
            "ticker": "ALL",
            "type": "comparison",
            "text": comparison_text
        })

        logging.info(f"Built {len(self.chunks)} chunks")
        return self.chunks

    # ─────────────────────────────────────────
    # STEP 2: BUILD VECTOR INDEX (FAISS)
    # ─────────────────────────────────────────
    def build_index(self):
        """Embed all chunks and store in FAISS vector index."""
        texts = [c["text"] for c in self.chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=False)
        embeddings = np.array(embeddings).astype("float32")

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)

        logging.info(f"FAISS index built with {self.index.ntotal} vectors")

    # ─────────────────────────────────────────
    # STEP 3: RETRIEVE RELEVANT CHUNKS
    # ─────────────────────────────────────────
    def retrieve(self, query: str, top_k: int = 4) -> list:
        """Embed the query and find most relevant chunks."""
        query_vec = self.embedder.encode([query]).astype("float32")
        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for idx in indices[0]:
            if idx < len(self.chunks):
                results.append(self.chunks[idx])

        logging.info(f"Retrieved {len(results)} chunks for query: '{query}'")
        return results

    # ─────────────────────────────────────────
    # STEP 4: GENERATE ANSWER USING LLM
    # ─────────────────────────────────────────
    def answer(self, query: str) -> str:
        """Full RAG pipeline: retrieve → prompt → generate."""
        retrieved = self.retrieve(query, top_k=4)

        context = "\n\n---\n\n".join([c["text"] for c in retrieved])

        prompt = f"""You are a financial analyst chatbot. Answer ONLY using the data provided below.
Do NOT use any external knowledge. Do NOT hallucinate.
If the data doesn't contain enough information, say "I don't have enough data to answer that."

=== RETRIEVED DATA ===
{context}
=== END OF DATA ===

User question: {query}

Answer clearly and concisely based strictly on the data above:"""

        response = self.groq.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1,
        )

        return response.choices[0].message.content.strip()

    # ─────────────────────────────────────────
    # SAVE/LOAD CHUNKS
    # ─────────────────────────────────────────
    def save_chunks(self, filepath: str = "data/chunks.json"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(self.chunks, f, indent=2)
        logging.info(f"Chunks saved to {filepath}")
