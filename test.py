import requests
import os

# Установите базовый URL вашего API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")  # Замените на ваш URL

# Пример данных для анализа
data = {
    "requirements": "Система должна обеспечивать авторизацию пользователей",
    "code": "def login(username, password):\n    return username == 'admin' and password == 'password'",
    "test_cases": "def test_login():\n    assert login('admin', 'password') == True",
    "documentation": "Документация по API",
    "analyze_security": True
}

# Отправка POST запроса к /analyze
response = requests.post(f"{API_BASE_URL}/analyze", json=data)

# Проверка статуса ответа
if response.status_code == 200:
    print("Анализ успешно выполнен:")
    print(response.json())
else:
    print(f"Ошибка при выполнении анализа: {response.status_code}")
    print(response.text)