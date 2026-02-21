# -*- coding: utf-8 -*-
import json
from mem0 import Memory

with open("./user_config.json", "r", encoding="utf-8") as f:
    user_config = json.load(f)
USER_ID = user_config["name"]

config = {
    "llm": {"provider": "ollama", "config": {"model": "qwen3:4b", "ollama_base_url": "http://127.0.0.1:11434"}},
    "embedder": {"provider": "ollama", "config": {"model": "nomic-embed-text", "ollama_base_url": "http://127.0.0.1:11434"}},
    "vector_store": {"provider": "qdrant", "config": {"collection_name": "private_ai_memory", "embedding_model_dims": 768, "on_disk": True, "path": "./qdrant_db"}}
}

memory = Memory.from_config(config)
raw = memory.search(query="everything", user_id=USER_ID, limit=20)
results = raw.get("results", []) if isinstance(raw, dict) else raw

print(f"用户：{USER_ID}，共 {len(results)} 条记忆\n")
for m in results:
    if isinstance(m, dict):
        print("-", m.get("memory") or m.get("text") or str(m))
    else:
        print("-", m)
