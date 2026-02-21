import ollama
from datetime import datetime

# 长期记忆存储（简单版：用文件存 profile）
PROFILE_FILE = "user_profile.txt"

def load_profile():
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "我是 Bingxi，UNC CS 大一学生,非常癫 在尝试和成为交界地的王"

def save_profile(profile):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        f.write(profile)

# 示例：每轮对话后更新 profile（后面升级成自动总结）
def update_profile_from_chat(user_msg, ai_reply):
    current_profile = load_profile()
    new_info = f"\n[{datetime.now()}] 用户说：{user_msg[:50]}... AI 回复：{ai_reply[:50]}..."
    save_profile(current_profile + new_info)
