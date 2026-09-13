import requests
import json

queries = [
    "my iPhone battery is draining very quickly",
    "my iPhone won't connect to WiFi",
    "my Apple ID is locked",
    "I dropped my iPhone and the screen is broken",
    "the latest iOS update is freezing my phone"
]

print("=== MANUAL RETRIEVAL AND END-TO-END PIPELINE AUDIT ===\n")
for q in queries:
    resp = requests.post("http://localhost:8080/api/v1/support", json={"message": q})
    data = resp.json()
    print(f'QUERY: "{q}"')
    print(f'  Classified Intent: {data.get("intent")} (Confidence: {data.get("confidence")})')
    print(f'  Decision:          {data.get("escalation", {}).get("decision")} - {data.get("escalation", {}).get("reason")}')
    print(f'  Generated Reply:   {data.get("reply")}')
    sims = data.get("similarConversations", [])
    print(f'  Retrieved Examples Count: {len(sims)}')
    for i, sim in enumerate(sims):
        cust = sim.get("customerText", "")[:75]
        rep = sim.get("agentReply", "")[:75]
        score = sim.get("similarityScore", 0.0)
        intent = sim.get("intent", "")
        print(f'    [{i+1}] Similarity: {score:.4f} | Intent: {intent}')
        print(f'        Customer: "{cust}..."')
        print(f'        Reply:    "{rep}..."')
    print("-" * 80)
