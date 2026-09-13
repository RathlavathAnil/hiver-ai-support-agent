import psycopg2
from seed_db import compute_fallback_embedding, get_connection

conn = get_connection()
cur = conn.cursor()

queries = [
    "my iPhone battery is draining very quickly",
    "my iPhone won't connect to WiFi",
    "my Apple ID is locked",
    "I dropped my iPhone and the screen is broken",
    "the latest iOS update is freezing my phone"
]

for q in queries:
    vec = compute_fallback_embedding(q)
    vec_str = "[" + ",".join(f"{v:.6f}" for v in vec) + "]"

    cur.execute("""
        SELECT c.customer_text, c.agent_reply, c.intent,
               (1.0 - (ce.embedding <=> CAST(%s AS vector))) AS similarity
        FROM conversations c
        JOIN conversation_embeddings ce ON c.id = ce.conversation_id
        WHERE c.brand = 'AppleSupport'
        ORDER BY ce.embedding <=> CAST(%s AS vector)
        LIMIT 3;
    """, (vec_str, vec_str))

    rows = cur.fetchall()
    print(f'Query: "{q}"')
    for r in rows:
        print(f'  Similarity: {r[3]:.4f} | Intent: {r[2]} | Text: "{r[0][:60]}..." | Reply: "{r[1][:60]}..."')
    print("-" * 60)
conn.close()
