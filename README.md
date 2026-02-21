# Private AI Twin

A 100% local, privacy-first AI companion that learns who you are over time. No cloud. No data leaving your machine. Ever.

## What it does

- **Long-term memory** — Remembers what you tell it across sessions using Mem0 + Qdrant vector database
- **RAG document search** — Upload your notes, PDFs, and markdown files; the AI can reference them in conversation
- **Proactive reminders** — Runs in the background and sends desktop notifications (e.g. reminds you to practice if you haven't logged it)
- **Daily summaries** — Automatically summarizes your day at 1am and stores it as a memory
- **User profiles** — First-time setup saves your name and bio; fully configurable via the Settings tab

## Stack

| Component | Technology |
|-----------|------------|
| LLM | Ollama (qwen3:4b) |
| Memory | Mem0 + Qdrant (local) |
| RAG | LlamaIndex + nomic-embed-text |
| UI | Gradio |
| Notifications | plyer |

## Requirements

- Windows (tested on Windows 11)
- Python 3.10+
- [Ollama](https://ollama.com) running locally

## Setup

```bash
# 1. Install Ollama and pull required models
ollama pull qwen3:4b
ollama pull nomic-embed-text

# 2. Install dependencies
pip install gradio ollama mem0ai llama-index llama-index-embeddings-ollama llama-index-llms-ollama pymupdf plyer psutil watchdog chromadb

# 3. Run
python b.py
```

First launch will ask for your name and a short bio. This is saved locally to `user_config.json` and never uploaded anywhere.

## Usage

- **Chat tab** — Talk to your AI twin. It retrieves relevant memories and document context automatically.
- **Upload docs** — Drop `.txt`, `.md`, or `.pdf` files into the knowledge base. Hot-reloads automatically.
- **Settings tab** — Update your name or bio. Takes effect on restart.

To view stored memories:
```bash
python check.py
```

## Privacy

All data stays on your machine:
- Conversations → `qdrant_db/`
- Uploaded documents → `docs/`
- User config → `user_config.json`

None of these are tracked by git (see `.gitignore`).

## Roadmap

- [ ] Fix Mem0 memory extraction reliability with local models
- [ ] Voice input/output
- [ ] Mobile access via ngrok
- [ ] Emotion tracking
- [ ] iOS version (MLC-LLM)
