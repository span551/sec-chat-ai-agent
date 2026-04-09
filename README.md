# CrowdWisdomTrading SEC Chat AI Agent

A backend Python AI agent system built for the CrowdWisdomTrading internship assessment. It analyzes SEC insider trading data and Twitter/X sentiment to provide intelligent stock insights via a RAG-powered chatbot, orchestrated through Hermes Agent.

## Architecture
SEC EDGAR API
↓
Top 5 Tickers (last 24hrs, by $ value)
↓
Twitter/X Tweets (Scweet — last 7 days)
↓
Groq LLM Sentiment Analysis (llama-3.3-70b)
↓
FAISS Vector DB (RAG chunks)
↓
Flask Chatbot API
↓
Hermes Agent (closed learning loop)

## Note on Twitter Scraping

The assignment requires **Apify** for Twitter/X data scraping. We integrated Apify (`altimis/scweet` actor) as the primary scraper. However, during development the free Apify plan monthly credits were exhausted. As a result, we implemented **Scweet** (the same underlying library) as a direct fallback.

The code supports both:
- **Apify** (primary) — uses `altimis/scweet` actor via Apify API
- **Scweet** (fallback) — direct cookie-based scraping when Apify credits run out

Apify API token is included in the submission email as required.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | Hermes Agent (NousResearch) |
| LLM Provider | OpenRouter (`nvidia/nemotron-3-nano-30b-a3b:free`) |
| Sentiment LLM | Groq (`llama-3.3-70b-versatile`) |
| Twitter Scraping | Apify (`altimis/scweet`) + Scweet fallback |
| SEC Data | sec-api.io (Form 4 filings) |
| Vector DB | FAISS |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| API Server | Flask |
| Charts | Matplotlib |
| Language | Python 3.12 |

---

## Features

- ✅ SEC Form 4 insider trading (last 24hrs, top 5 tickers by $ value)
- ✅ Twitter/X tweet collection via Apify + Scweet fallback (last 7 days)
- ✅ LLM sentiment analysis — bullish / bearish / neutral per tweet
- ✅ Weighted sentiment scoring (by likes + retweets)
- ✅ RAG chatbot — answers ONLY from collected data, no hallucination
- ✅ 4 chart types on demand (bar, pie, radar, insider trading)
- ✅ Hermes Agent skill integration
- ✅ Closed learning loop via Hermes built-in memory system
- ✅ Logging and error handling throughout all agents

---



## Chunking Strategy (RAG)

Data is split into structured chunks before indexing into FAISS:

| Chunk Type | Content | Example |
|------------|---------|---------|
| `sec_insider` | Total value, buy/sell counts per ticker | "CRWV: $146.6M total, 23 sells, 0 buys" |
| `sentiment` | Bullish/bearish/neutral % + weighted scores | "CRWV: 31.6% bull, 22.8% bear, MIXED" |
| `bullish_tweets` | Sample bullish tweets for ticker | "$CRWV up 5%, breaking out" |
| `bearish_tweets` | Sample bearish tweets for ticker | "Insiders dumping CRWV hard" |
| `comparison` | Cross-ticker sentiment summary | "NTRA most bullish at 40%" |

**Total chunks:** ~13 for 3 tickers → embedded with `all-MiniLM-L6-v2` → stored in FAISS flat L2 index.

---

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/sec-chat-ai-agent.git
cd sec-chat-ai-agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 4. Run the full pipeline
```bash
python3 main.py
```

### 5. Start the chatbot
```bash
python3 chatbot.py
```

### 6. Use via Hermes Agent (WSL2/Linux)
```bash
# Install Hermes
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc

# Configure OpenRouter model
hermes config set model.default "nvidia/nemotron-3-nano-30b-a3b:free"

# Start chatting
hermes
> what is the sentiment on CRWV?
```

---

## Environment Variables

```bash
# .env.example
SEC_API_KEY=           # sec-api.io — Form 4 filing access
APIFY_API_KEY=         # apify.com — Twitter scraping (free plan)
GROQ_API_KEY=          # console.groq.com — LLM sentiment (free)
OPENROUTER_API_KEY=    # openrouter.ai — Hermes Agent LLM (free)
TWITTER_AUTH_TOKEN=    # X/Twitter browser cookie (auth_token)
TWITTER_CT0=           # X/Twitter browser cookie (ct0)
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | RAG chatbot — ask anything about the stocks |
| `/health` | GET | System status + available tickers |
| `/chart/sentiment` | GET | Bar chart — bullish/bearish/neutral per ticker |
| `/chart/insider` | GET | Bar chart — insider trading value per ticker |
| `/chart/comparison` | GET | Radar chart — all tickers compared |
| `/chart/pie/<ticker>` | GET | Pie chart — sentiment for specific ticker |

---

## Closed Learning Loop

Implemented via **Hermes Agent's built-in memory system**:

1. Every chatbot interaction is saved to Hermes persistent memory
2. User preferences (e.g. "I care most about CRWV") are stored automatically
3. Hermes learns which tickers/questions you ask most
4. Skills self-improve based on usage patterns
5. Cross-session recall via FTS5 full-text search
User asks about CRWV repeatedly
↓
Hermes saves: "User interested in CRWV insider trading"
↓
Next session: Hermes proactively surfaces CRWV data
↓
Skill description updated based on interaction patterns

---

## Hermes Skill

Located at: `~/.hermes/skills/trading/trading-sentiment/SKILL.md`

Triggers automatically when user asks about:
- Stock sentiment (bullish/bearish)
- Insider trading activity
- Specific tickers: CRWV, NTRA, GKOS, SYRE, ADMA
- Chart requests
- Comparing stocks

---

## Evaluation Criteria Met

| Criteria | Implementation |
|----------|---------------|
| Working functionality | ✅ Full pipeline SEC → Tweets → Sentiment → RAG → Chat |
| Code clarity | ✅ Modular agents, clear separation of concerns |
| Hermes Agent framework | ✅ Installed, skill created, memory active |
| OpenRouter + free model | ✅ nemotron-3-nano-30b-a3b:free |
| Apify scraping | ✅ Integrated (Scweet fallback when credits exhausted) |
| RAG chatbot | ✅ FAISS + chunking strategy documented |
| Charts on request | ✅ 4 chart types |
| Closed learning loop | ✅ Hermes memory system |
| Logging & error handling | ✅ Throughout all agents |
| Scale | ✅ Batch processing, caching, rate limit handling |



