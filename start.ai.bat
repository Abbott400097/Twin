@echo off
title Bingxi AI 分身启动器

echo 正在启动 Ollama 服务...
start /min "" "C:\Users\34967\AppData\Local\Programs\Ollama\ollama.exe" serve --keep-alive -1

timeout /t 10 /nobreak >nul

echo Ollama 服务已启动，正在加载模型预热...
start /min "" cmd /c "ollama run qwen3:4b \"预热完成，随时待命\" & exit"

timeout /t 15 /nobreak >nul

echo 启动主程序（聊天 + 提醒）...
cd /d "D:\来 迎接我\Twin"
py main_with_notify.py

pause