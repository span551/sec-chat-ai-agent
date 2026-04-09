## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Hermes Agent |
| LLM | OpenRouter (nvidia/nemotron-3-nano-30b-a3b:free) |
| Sentiment | Groq (llama-3.3-70b-versatile) |
| Twitter scraping | Apify + Scweet fallback |
| Vector DB | FAISS |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| API | Flask |
| Charts | Matplotlib |

## Features

- ✅ SEC Form 4 insider trading data (last 24hrs, top 5 by value)
- ✅ Twitter/X tweet collection via Apify (last 7 days)
- ✅ LLM sentiment analysis (bullish/bearish/neutral) with weighted scoring
- ✅ RAG chatbot — answers only based on collected data
- ✅ 4 chart types (bar, pie, radar, insider trading)
- ✅ Hermes Agent integration with closed learning loop
- ✅ Logging and error handling throughout

## Chunking Strategy

Data is split into 5 chunk types per ticker:
1. **SEC chunk** — insider transaction summary (value, buy/sell counts)
2. **Sentiment chunk** — bullish/bearish/neutral percentages + weighted scores
3. **Bullish tweets chunk** — sample bullish tweets
4. **Bearish tweets chunk** — sample bearish tweets
5. **Comparison chunk** — cross-ticker sentiment comparison

Total: ~13 chunks for 3 tickers → embedded into FAISS vector index.

## Setup

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/sec-chat-ai-agent
cd sec-chat-ai-agent

# Install dependencies
pip install -r requirements.txt

# Set up .env
cp .env.example .env
# Edit .env with your API keys

# Run pipeline
python3 main.py

# Start chatbot
python3 chatbot.py
```

## Environment Variables
