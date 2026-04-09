import json
import logging
from flask import Flask, request, jsonify
from agents.rag_agent import RAGAgent

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# ── Load data and build RAG on startup ──────────────
logging.info("Loading data...")

with open("data/sentiment.json", encoding="utf-8") as f:
    sentiment_data = json.load(f)

with open("data/tweets.json", encoding="utf-8") as f:
    tweets_data = json.load(f)

with open("data/sec_transactions.json", encoding="utf-8") as f:
    sec_data = json.load(f)

rag = RAGAgent()
rag.build_chunks(sec_data, tweets_data, sentiment_data)
rag.build_index()
rag.save_chunks()

logging.info("RAG chatbot ready!")


# ── Chat endpoint ────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "No query provided"}), 400

    answer = rag.answer(query)
    return jsonify({
        "query": query,
        "answer": answer
    })


# ── Health check ─────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "chunks": len(rag.chunks)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)