# -*- coding: utf-8 -*-
import sys
print(sys.executable)
import gradio as gr
import ollama
from datetime import datetime
import threading
import time
import os
import json
import shutil
import psutil
from plyer import notification
from mem0 import Memory

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

ollama.host = "http://127.0.0.1:11434"

# ───── 用户配置 ─────
CONFIG_FILE = "./user_config.json"

def load_or_create_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    print("\n========== 欢迎使用 Private AI Twin ==========")
    name = input("请输入你的名字：").strip() or "user"
    bio = input("简单介绍一下你自己（可跳过）：").strip() or ""
    config_data = {"name": name, "bio": bio}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
    print(f"配置已保存！欢迎，{name}。\n")
    return config_data

user_config = load_or_create_config()
USER_ID = user_config["name"]
USER_BIO = user_config["bio"]

# ───── Mem0 配置 ─────
mem0_config = {
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
            "collection_name": "private_ai_memory",
            "embedding_model_dims": 768,
            "on_disk": True,
            "path": "./qdrant_db"
        }
    }
}

# 启动前杀掉旧进程释放锁
for proc in psutil.process_iter(['pid', 'name']):
    try:
        if 'python' in proc.info['name'].lower() and proc.pid != os.getpid():
            proc.kill()
            print(f"[启动] 关闭旧进程：{proc.pid}")
    except Exception:
        pass
time.sleep(1)

memory = Memory.from_config(mem0_config)

# ───── RAG 配置 ─────
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text", base_url="http://127.0.0.1:11434")
Settings.llm = Ollama(model="qwen3:4b", base_url="http://127.0.0.1:11434")

DOCS_DIR = "./docs"
os.makedirs(DOCS_DIR, exist_ok=True)

rag_index = None
rag_lock = threading.Lock()

def build_rag_index():
    global rag_index
    if not os.listdir(DOCS_DIR):
        return
    print("[RAG] 构建索引中...")
    docs = SimpleDirectoryReader(DOCS_DIR, recursive=True).load_data()
    with rag_lock:
        rag_index = VectorStoreIndex.from_documents(docs)
    print("[RAG] 索引构建完成")

def query_rag(question):
    with rag_lock:
        index = rag_index
    if index is None:
        return ""
    try:
        return str(index.as_query_engine().query(question))
    except Exception:
        return ""

def extract_memory_text(m):
    if isinstance(m, dict):
        return m.get("memory") or m.get("text") or str(m)
    return str(m)

def search_memories(query, limit=5):
    raw = memory.search(query=query, user_id=USER_ID, limit=limit)
    if isinstance(raw, dict):
        return raw.get("results", [])
    return raw if isinstance(raw, list) else []

# ───── 通知 ─────
def send_notification(title, message):
    notification.notify(title=title, message=message, app_name="Private AI Twin", timeout=10)

# ───── 智能提醒 ─────
def reminder_loop():
    print("[提醒] 后台线程已启动")
    reminded_today = False
    last_date = None
    while True:
        now = datetime.now()
        today = now.date()
        if last_date != today:
            reminded_today = False
            last_date = today
        if now.hour >= 20 and not reminded_today:
            recent = search_memories("what did I do today")
            if not recent:
                send_notification("Private AI", f"{USER_ID}，今天还没记录任何事？来聊聊吧。")
                reminded_today = True
        time.sleep(300)

# ───── 每日总结 ─────
def daily_summary():
    print("[总结] 每日总结线程已启动")
    while True:
        now = datetime.now()
        if now.hour == 1 and now.minute < 5:
            memories = search_memories("today", limit=20)
            if memories:
                memory_text = "\n".join([extract_memory_text(m) for m in memories])
                response = ollama.chat(
                    model="qwen3:4b",
                    messages=[
                        {"role": "system", "content": "根据对话记录生成简洁的每日总结，提炼关键事件、情绪、待办，200字以内。"},
                        {"role": "user", "content": f"记录：\n{memory_text}"}
                    ]
                )
                summary = response["message"]["content"]
                memory.add(
                    messages=f"每日总结（{now.date()}）：{summary}",
                    user_id=USER_ID,
                    metadata={"type": "daily_summary", "date": str(now.date())}
                )
            time.sleep(360)
        else:
            time.sleep(60)

# ───── 文件上传 ─────
def upload_file(files):
    if not files:
        return "没有文件"
    for f in files:
        filename = os.path.basename(f.name)
        shutil.copy(f.name, os.path.join(DOCS_DIR, filename))
    threading.Thread(target=build_rag_index, daemon=True).start()
    return f"已上传 {len(files)} 个文件，索引重建中..."

# ───── 聊天 ─────
def chat_with_ai(message, history):
    try:
        history = history[-10:]
        memories = search_memories(message)
        profile = "\n".join([extract_memory_text(m) for m in memories]) if memories else f"用户名：{USER_ID}。{USER_BIO}"
        rag_context = query_rag(message)

        system_prompt = f"""你是{USER_ID}的私人AI分身。
用户信息：{USER_BIO}
长期记忆：
{profile}

文档知识库：
{rag_context}

规则：
- 禁止胡编，基于事实。
- 简洁有力，150字以内。
- 风格：冷静克制+人文关怀，像自己给自己发消息。
- 目的：关心用户、提醒、规划生活，越聊越懂他。"""

        messages = [{"role": "system", "content": system_prompt}]
        for pair in history:
            if len(pair) == 2:
                messages.append({"role": "user", "content": pair[0]})
                messages.append({"role": "assistant", "content": pair[1]})
        messages.append({"role": "user", "content": message})

        response = ollama.chat(
            model="qwen3:4b",
            messages=messages,
            options={"num_ctx": 4096, "temperature": 0.6, "top_p": 0.9}
        )
        ai_reply = response["message"]["content"]

        def save_memory():
            try:
                result = memory.add(
                    messages=f"user: {message}\nai: {ai_reply}",
                    user_id=USER_ID,
                    metadata={"timestamp": str(datetime.now())}
                )
                print(f"[记忆] 存储成功：{result}")
            except Exception as e:
                print(f"[记忆] 存储失败：{e}")

        threading.Thread(target=save_memory, daemon=True).start()
        return ai_reply
    except Exception as e:
        return f"error: {str(e)}"

# ───── 设置 ─────
def save_config(name, bio):
    user_config["name"] = name.strip() or USER_ID
    user_config["bio"] = bio.strip()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(user_config, f, ensure_ascii=False, indent=2)
    return "已保存！重启后生效。"

# ───── 启动后台 ─────
build_rag_index()
threading.Thread(target=reminder_loop, daemon=True).start()
threading.Thread(target=daily_summary, daemon=True).start()

# ───── UI ─────
with gr.Blocks(title="Private AI Twin") as demo:
    gr.Markdown(f"# Private AI Twin\n欢迎回来，**{USER_ID}**。本地运行，长期记忆，越聊越懂你。")
    with gr.Tabs():
        with gr.Tab("聊天"):
            with gr.Row():
                with gr.Column(scale=3):
                    gr.ChatInterface(fn=chat_with_ai, examples=["今天状态怎么样？", "帮我规划本周计划", "总结一下我最近的记忆"])
                with gr.Column(scale=1):
                    gr.Markdown("### 上传文档到知识库")
                    upload = gr.File(label="支持 txt / md / pdf", file_count="multiple", file_types=[".txt", ".md", ".pdf"])
                    upload_btn = gr.Button("上传")
                    upload_status = gr.Textbox(label="状态", interactive=False)
                    upload_btn.click(fn=upload_file, inputs=upload, outputs=upload_status)
        with gr.Tab("设置"):
            gr.Markdown("### 修改个人信息（重启后生效）")
            name_input = gr.Textbox(label="名字", value=USER_ID)
            bio_input = gr.Textbox(label="个人简介", value=USER_BIO, lines=3)
            save_btn = gr.Button("保存")
            save_status = gr.Textbox(label="状态", interactive=False)
            save_btn.click(fn=save_config, inputs=[name_input, bio_input], outputs=save_status)

if __name__ == "__main__":
    demo.launch()
