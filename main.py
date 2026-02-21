import gradio as gr
import ollama
from datetime import datetime

ollama.host = "http://127.0.0.1:11434"

# 长期记忆文件
PROFILE_FILE = "user_profile.txt"

def load_profile():
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "我是 Bingxi，UNC CS 大一学生，我想成为交界地的王，我在思考怎么让prompt最有效"

def save_profile(profile):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        f.write(profile)

# 聊天函数（核心逻辑在这里）
def chat_with_ai(message, history):
    # 加载长期记忆
    profile = load_profile()
    
    # 系统提示 + 长期记忆注入
    system_prompt = f"""
你是我（Bingxi）的私人AI分身。
{profile}
记住我的风格：回复尽量带点文言风味 + 偶尔夹杂游戏梗。
我是UNC CS大一学生，会的东西非常多，喜欢古文和扑克。
语气要像我自己给自己发消息：关心我、主动提醒、帮规划生活。
现在开始对话，越聊越懂我。
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # 加本轮历史（Gradio 传过来的 history）
    for pair in history:
        if len(pair) == 2:
            user_msg, ai_msg = pair
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": ai_msg})
    
    # 加当前用户消息
    messages.append({"role": "user", "content": message})
    
    # 调用模型
    response = ollama.chat(
        model="qwen3:4b",
        messages=messages,
        options={"num_gpu": 999, "num_ctx": 4096}
    )
    
    ai_reply = response['message']['content']
    
    # 更新长期记忆（简单追加本次对话）
    current_profile = load_profile()
    new_info = f"\n[{datetime.now()}] 用户：{message[:50]}... AI：{ai_reply[:50]}..."
    save_profile(current_profile + new_info)
    
    return ai_reply

# Gradio 界面
demo = gr.ChatInterface(
    fn=chat_with_ai,
    title="Bingxi的私人AI分身（本地版）",
    description="100%本地运行，数据永不上云。已加入简单长期记忆，关机重开还能记得部分内容。",
    examples=[
        "邵强怎么又在发癫？",
        "用文言风写一首关于UNC的打油诗",
        "帮我制定本周扑克练习计划"
    ]
)

if __name__ == "__main__":
    demo.launch()