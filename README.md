# CrowdWisdomTrading SEC Chat AI Agent

A backend Python AI agent system built for the CrowdWisdomTrading internship assessment.
The system analyzes SEC insider trading data and Twitter/X sentiment to generate actionable insights via a RAG-powered chatbot, orchestrated through Hermes Agent.

---

## 🚀 Architecture

SEC EDGAR (Form 4 filings, last 24h)
↓
Top 5 Tickers (by total insider transaction value)
↓
Twitter/X Tweets (Apify + Scweet fallback, last 7 days)
↓
LLM Sentiment Analysis (bullish / bearish / neutral)
↓
FAISS Vector Database (RAG chunking + embeddings)
↓
Chatbot (RAG-based, answers strictly from data)
↓
Hermes Agent (closed learning loop + memory)

---

## 🧠 Key Features

* SEC insider trading analysis (last 24 hours)
* Top 5 tickers by transaction value (deduplicated)
* Twitter/X sentiment analysis (last 7 days)
* Weighted sentiment scoring (likes + engagement)
* RAG chatbot (FAISS + semantic search)
* AI Reply Planner (generates actionable trading tweets/replies)
* Charts generation on demand (sentiment + insider activity)
* Hermes Agent integration with persistent memory
* Logging and robust error handling across all agents

---

## 🔁 Reply Planner (Important Requirement)

The system generates **actionable X/Twitter replies** based on sentiment and insider activity.

### Example

**Q:** What should I post about CRWV?

**A:**
"Despite heavy insider selling in $CRWV, sentiment remains mixed.
Traders should wait for confirmation before entering positions."

---

## 🐦 Twitter Scraping (Apify Requirement)

Apify is fully integrated as required in the assignment.

To ensure reliability during development, a fallback mechanism was implemented:

* **Apify (primary)** — used via Apify API (token required)
* **Scweet (fallback)** — used when API limits are reached

Both implementations are included in the codebase.
Apify API token is provided in the submission email as required.

---

## 🧩 Tech Stack

| Component          | Technology                                       |
| ------------------ | ------------------------------------------------ |
| Agent Framework    | Hermes Agent (NousResearch)                      |
| LLM Provider       | OpenRouter (nvidia/nemotron-3-nano-30b-a3b:free) |
| Sentiment Analysis | Groq (llama-3.3-70b)                             |
| Twitter Scraping   | Apify + Scweet                                   |
| SEC Data           | sec-api (Form 4 filings)                         |
| Vector DB          | FAISS                                            |
| Embeddings         | sentence-transformers/all-MiniLM-L6-v2           |
| Charts             | Matplotlib                                       |
| Language           | Python 3.12                                      |

---

## 🧠 RAG Chunking Strategy

Data is structured into semantic chunks before indexing:

| Chunk Type     | Description                                |
| -------------- | ------------------------------------------ |
| sec_insider    | Insider buy/sell totals + value per ticker |
| sentiment      | Bullish / bearish / neutral distribution   |
| bullish_tweets | Representative bullish tweets              |
| bearish_tweets | Representative bearish tweets              |
| comparison     | Cross-ticker sentiment insights            |

* ~13 chunks generated per run
* Embedded using MiniLM
* Stored in FAISS (L2 index)

---

## ⚙️ Setup

### 1. Clone repository

```
git clone https://github.com/span551/sec-chat-ai-agent.git
cd sec-chat-ai-agent
```

---

### 2. Install dependencies

```
pip install -r requirements.txt
```

---


---

### 3. Run full pipeline

```
python3 main.py
```

---

### 4. Run chatbot

```
python3 chatbot.py
```

---

## 💬 Sample Queries

* What is the sentiment on CRWV?
* Compare GKOS and NTRA
* Which stock is most risky?
* Tell me about insider trading activity on CRWV
* What should I post about NTRA?

---

## 📊 Sample Output

**Q:** Which stock is most risky?

**A:**
CRWV appears most risky due to significant insider selling ($146M total)
combined with mixed sentiment, indicating uncertainty in market direction.

---

## 🔁 Closed Learning Loop (Hermes)

Implemented using Hermes Agent’s built-in memory:

* Stores past queries and responses
* Learns user preferences over time
* Improves response relevance across sessions
* Uses persistent memory with full-text search

---

## 🧠 Hermes Skill

Integrated as a custom skill:

* Detects stock-related queries
* Routes to RAG chatbot automatically
* Supports sentiment, insider analysis, and comparisons

---

## ✅ Evaluation Criteria Coverage

| Requirement              | Status                         |
| ------------------------ | ------------------------------ |
| Working functionality    | ✅ End-to-end pipeline          |
| Code clarity             | ✅ Modular agent-based design   |
| Hermes Agent             | ✅ Integrated with memory       |
| OpenRouter               | ✅ Free model used              |
| Apify scraping           | ✅ Implemented (with fallback)  |
| RAG chatbot              | ✅ FAISS + chunking             |
| Charts                   | ✅ Generated on demand          |
| Closed learning loop     | ✅ Hermes memory                |
| Logging & error handling | ✅ Implemented                  |
| Scale considerations     | ✅ Efficient chunking + caching |

---

## 📌 Notes

* The system strictly answers based on collected data (no hallucination)
* Designed for modular scalability (agents can be extended easily)
* Built with production-like structure and logging

---

## 📬 Submission

Includes:

* GitHub repository (this project)
* Apify API token (shared via email)
* Sample outputs (included above)

---
