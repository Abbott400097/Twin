# -*- coding: utf-8 -*-
import sys
print(sys.executable)
import gradio as gr
import ollama
from datetime import datetime
import threading
import time
import os
from plyer import notification
from mem0 import Memory

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

ollama.host = "http://127.0.0.1:11434"

# Mem0 config
config = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "qwen3:4b",
            "ollama_base_url": "http://127.0.0.1:11434",
            "temperature": 0.7,
            "max_tokens": 512
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text",
            "ollama_base_url": "http://127.0.0.1:11434"
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "bingxi_memory",
            "embedding_model_dims": 768,
            "on_disk": True,
            "path": "./qdrant_db"
        }
    }
}
import shutil
import glob

# 启动前自动清理qdrant锁文件
for lock_file in glob.glob("./qdrant_db/**/*.lock", recursive=True):
    try:
        os.remove(lock_file)
        print(f"[启动] 清理锁文件：{lock_file}")
    except Exception:
        pass
memory = Memory.from_config(config)

# RAG config
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text", base_url="http://127.0.0.1:11434")
Settings.llm = Ollama(model="qwen3:4b", base_url="http://127.0.0.1:11434")

DOCS_DIR = "./docs"
os.makedirs(DOCS_DIR, exist_ok=True)

def build_rag_index():
    if not os.listdir(DOCS_DIR):
        return None
    docs = SimpleDirectoryReader(DOCS_DIR, recursive=True).load_data()
    return VectorStoreIndex.from_documents(docs)

rag_index = build_rag_index()

def query_rag(question):
    if rag_index is None:
        return ""
    try:
        result = rag_index.as_query_engine().query(question)
        return str(result)
    except Exception:
        return ""

def extract_memory_text(m):
    if isinstance(m, dict):
        return m.get("memory") or m.get("text") or str(m)
    return str(m)

def send_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name="Bingxi AI",
        timeout=10
    )

def reminder_loop():
    print("reminder started...")
    reminded_today = False
    last_date = None
    while True:
        now = datetime.now()
        today = now.date()
        if last_date != today:
            reminded_today = False
            last_date = today
        if now.hour >= 20 and not reminded_today:
            recent_memories = memory.search(
                query="erhu practice today",
                user_id="bingxi",
                limit=5
            )
            profile_text = "\n".join([extract_memory_text(m) for m in recent_memories])
            if "erhu" not in profile_text.lower():
                send_notification(
                    "reminder",
                    "Bingxi, haven't practiced erhu today?"
                )
                reminded_today = True
        time.sleep(300)

def chat_with_ai(message, history):
    try:
        history = history[-10:]
        memories = memory.search(query=message, user_id="bingxi", limit=5)

        if memories:
            profile = "\n".join([extract_memory_text(m) for m in memories])
        else:
            profile = "I am Bingxi, UNC CS freshman, like erhu, classical Chinese, poker."

        rag_context = query_rag(message)

        system_prompt = f"""你是我（Bingxi）的私人AI分身。
长期记忆：
{profile}

文档知识库（如果有相关内容）：
{rag_context}

规则：
- 禁止胡编，基于事实。
- 简洁有力，150字以内。
- 风格：冷静克制+人文关怀，像自己给自己发消息。
- 身份：UNC CS大一，什么都喜欢。
- 目的：关心我、提醒、规划生活，越聊越懂我。"""

        messages = [{"role": "system", "content": system_prompt}]
        for pair in history:
            if len(pair) == 2:
                messages.append({"role": "user", "content": pair[0]})
                messages.append({"role": "assistant", "content": pair[1]})
        messages.append({"role": "user", "content": message})

        response = ollama.chat(
            model="qwen3:4b",
            messages=messages,
            options={"num_ctx": 2048, "temperature": 0.6, "top_p": 0.9}
        )
        ai_reply = response["message"]["content"]

        ai_reply = response["message"]["content"]

        def save_memory():
            memory.add(
                messages=f"user: {message}\nai: {ai_reply}",
                user_id="bingxi",
                metadata={"timestamp": str(datetime.now())}
            )
        threading.Thread(target=save_memory, daemon=True).start()
        return ai_reply

    except Exception as e:
        return f"error: {str(e)}"

threading.Thread(target=reminder_loop, daemon=True).start()

demo = gr.ChatInterface(
    fn=chat_with_ai,
    title="Bingxi AI",
    description="本地运行，Mem0长期记忆+RAG文档检索，越聊越懂你。把文档扔进docs文件夹即可。",
    examples=["今天状态怎么样？", "帮我规划本周计划", "用文言写首关于UNC的诗"],
    cache_examples=False
)

if __name__ == "__main__":
    demo.launch()
