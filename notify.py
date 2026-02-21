import time
from plyer import notification
from datetime import datetime

def send_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name="Bingxi AI 分身",
        timeout=10
    )

print("AI 分身后台提醒已启动...")

while True:
    now = datetime.now()
    # 简单测试：每隔 30 秒弹一次（实际可以改成每天特定时间）
    if now.second % 10 == 0:
        send_notification(
            "分身提醒",
            "Bingxi，主公，今天想邵强了吗？今天不想邵强，明天就凉凉了～😏"
        )
    time.sleep(1)  # 每秒检查一次