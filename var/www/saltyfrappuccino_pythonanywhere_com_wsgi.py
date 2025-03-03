"""
WSGI файл для запуска FastAPI приложения на PythonAnywhere
"""

import sys
import os

# Путь к директории с приложением
app_path = '/home/SaltyFrappuccino/AI-Mammoth-API'
if app_path not in sys.path:
    sys.path.append(app_path)

# Устанавливаем переменную окружения для доступа к API ключу GigaChat
# Лучше настроить это через Web -> Environment Variables на PythonAnywhere
os.environ.setdefault("GIGACHAT_API_KEY", "ВАШ_API_КЛЮЧ_ЗДЕСЬ")
os.environ.setdefault("GIGACHAT_API_BASE", "https://gigachat.devices.sberbank.ru")

# Импортируем FastAPI приложение из main.py
from main import app

# Используем адаптер для преобразования ASGI в WSGI
import uvicorn.middleware.wsgi
application = uvicorn.middleware.wsgi.WSGIMiddleware(app) 