import requests

BASE = "http://localhost:5000"

queries = [
    "What are people saying about GKOS and quote some positive tweets?",
]

print(requests.get(f"{BASE}/health").json())
print()

for q in queries:
    print(f"Q: {q}")
    r = requests.post(f"{BASE}/chat", json={"query": q})
    print(f"A: {r.json()['answer']}")
    print("-" * 60)