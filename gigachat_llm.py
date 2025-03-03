import requests
import base64
import uuid
import time
from typing import Dict, Any, Optional, List

class GigaChatLLM:
    """
    Класс для работы с GigaChat LLM API.
    Обеспечивает автоматическое получение/обновление токена и генерацию ответов.
    """
    
    def __init__(
        self, 
        auth_key: str, 
        scope: str = "GIGACHAT_API_PERS"
    ):
        """
        Инициализация клиента.
        
        :param client_id: Идентификатор клиента (из личного кабинета)
        :param client_secret: Секретный ключ клиента
        :param scope: Область доступа (по умолчанию для физических лиц)
        """
        self.auth_key = auth_key
        self.scope = scope
        self.access_token: Optional[str] = None
        self.expires_at: int = 0

    def _get_access_token(self) -> None:
        """Получение нового токена доступа через OAuth2"""
        rq_uid = str(uuid.uuid4())
        
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

        payload='scope=GIGACHAT_API_PERS'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': rq_uid,
            'Authorization': 'Basic Y2JkYzY3ZTUtMjg2Ny00ODJkLWE1ZTYtYmE4MTliMWZkNjVhOjlhZTRiM2UyLWZhZGUtNDNhMy04MjQ0LWFjNDBhMTQxYzRmYw=='
        }
        
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)

        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.expires_at = token_data["expires_at"]

    def _is_token_expired(self) -> bool:
        """Проверка срока действия токена"""
        return int(time.time() * 1000) >= self.expires_at

    def _ensure_token_valid(self) -> None:
        """Обновление токена при необходимости"""
        if not self.access_token or self._is_token_expired():
            self._get_access_token()

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        model: str = "GigaChat",
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Генерация ответа от модели
        
        :param system_prompt: Системный промт (задает поведение модели)
        :param user_message: Вопрос пользователя
        :param model: Название модели (GigaChat, GigaChat-Pro и т.д.)
        :param temperature: Температура выборки (0-2)
        :param top_p: Порог вероятности для nucleus sampling
        :param max_tokens: Максимальное количество токенов в ответе
        :param stream: Включить потоковую передачу
        :return: Ответ API в формате JSON
        """
        self._ensure_token_valid()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Client-ID": self.auth_key,
            "X-Request-ID": str(uuid.uuid4()),
            "X-Session-ID": str(uuid.uuid4())
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        response = requests.post(
            "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
            headers=headers,
            json=data,
            verify=False
        )
        response.raise_for_status()
        return response.json()
    
    def call_with_functions(self, user_message: str, functions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Генерация ответа с возможностью вызова функций.
        
        :param user_message: Сообщение пользователя
        :param functions: Описание функций в формате JSON Schema
        :return: Ответ API с учетом вызова функций
        """
        self._ensure_token_valid()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Client-ID": self.auth_key,
            "X-Request-ID": str(uuid.uuid4()),
            "X-Session-ID": str(uuid.uuid4())
        }
        
        data = {
            "model": "GigaChat-Pro",
            "messages": [{"role": "user", "content": user_message}],
            "functions": functions,
            "function_call": "auto"
        }
        
        response = requests.post(
            "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
            headers=headers,
            json=data,
            verify=False
        )
        response.raise_for_status()
        return response.json()
