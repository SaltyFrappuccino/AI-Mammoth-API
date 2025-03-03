import os
import json
import uuid
import time
import base64
import requests
import logging
import random
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gigachat-client")

class GigaChatClient:
    """
    Клиент для работы с GigaChat API без использования LangChain или GigaChain
    """
    
    def __init__(self, auth_key: str = "", api_base: str = "https://gigachat.devices.sberbank.ru", 
                 max_retries: int = 5, retry_delay: float = 1.0, timeout: float = 30.0):
        """
        Инициализация клиента GigaChat API
        
        Args:
            auth_key: Ключ авторизации (Authorization Key)
            api_base: Базовый URL API (по умолчанию production)
            max_retries: Максимальное количество повторных попыток при ошибках сети
            retry_delay: Начальная задержка между повторными попытками (секунды)
            timeout: Таймаут для HTTP-запросов (секунды)
        """
        self.auth_key = auth_key or "Y2JkYzY3ZTUtMjg2Ny00ODJkLWE1ZTYtYmE4MTliMWZkNjVhOjlhZTRiM2UyLWZhZGUtNDNhMy04MjQ0LWFjNDBhMTQxYzRmYw=="
        if not self.auth_key:
            raise ValueError("Требуется ключ авторизации GigaChat API. Передайте его в конструктор или установите переменную среды GIGACHAT_API_KEY")
        
        self.api_base = api_base
        self.access_token = None
        self.token_expires_at = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
    
    def _make_http_request(self, method: str, url: str, headers: Dict, data=None, json=None) -> requests.Response:
        """
        Выполняет HTTP-запрос с автоматическим повтором при сетевых ошибках
        
        Args:
            method: HTTP метод ('GET', 'POST', etc.)
            url: URL для запроса
            headers: HTTP заголовки
            data: Данные для отправки (form data)
            json: Данные для отправки (json)
            
        Returns:
            requests.Response: Ответ сервера
            
        Raises:
            Exception: В случае исчерпания всех попыток
        """
        attempt = 0
        last_exception = None
        
        while attempt < self.max_retries:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    json=json,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response
                
            except (ConnectionError, Timeout, ConnectionResetError) as e:
                attempt += 1
                last_exception = e
                
                if attempt < self.max_retries:
                    # Экспоненциальная задержка с случайным джиттером
                    delay = self.retry_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    logger.warning(f"Сетевая ошибка: {str(e)}. Повторная попытка {attempt}/{self.max_retries} через {delay:.2f} секунд...")
                    time.sleep(delay)
                    
                    # Попробуем обновить токен при следующей попытке, если это проблема с авторизацией
                    if isinstance(e, HTTPError) and (e.response.status_code == 401 or e.response.status_code == 403):
                        self.access_token = None
                else:
                    logger.error(f"Исчерпаны все попытки подключения. Последняя ошибка: {str(e)}")
            
            except Exception as e:
                # Для других ошибок (не связанных с сетью) немедленно выбрасываем исключение
                logger.error(f"Ошибка при выполнении HTTP-запроса: {str(e)}")
                raise
                
        # Если мы здесь, значит все попытки исчерпаны
        if last_exception:
            raise last_exception
        else:
            raise Exception("Неизвестная ошибка при попытке выполнить HTTP-запрос")
    
    def _get_access_token(self) -> str:
        """
        Получение токена доступа для GigaChat API
        
        Returns:
            str: Токен доступа
        """
        # Проверяем, не истек ли текущий токен
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
            
        # Генерируем новый токен
        rquid = str(uuid.uuid4())
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": rquid,
            "Authorization": f"Basic {self.auth_key}"
        }
        
        try:
            response = self._make_http_request(
                method="POST",
                url=f"{self.api_base.replace('gigachat', 'ngw')}/api/v2/oauth",
                headers=headers,
                data="scope=GIGACHAT_API_PERS"
            )
            
            data = response.json()
            self.access_token = data["access_token"]
            
            # Токен действует 30 минут, но мы установим срок действия на 25 минут для запаса
            expires_at_timestamp = data["expires_at"] / 1000  # Переводим из миллисекунд в секунды
            self.token_expires_at = datetime.fromtimestamp(expires_at_timestamp) - timedelta(minutes=5)
            
            logger.info("Получен новый токен доступа GigaChat API")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Ошибка при получении токена доступа: {str(e)}")
            raise
    
    def chat_completion(self,
                      messages: List[Dict[str, str]], 
                      model: str = "GigaChat-Max", 
                      temperature: float = 0.7,
                      max_tokens: int = 1024,
                      stream: bool = False) -> Dict:
        """
        Генерация текста с помощью GigaChat API
        
        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "Запрос"}]
            model: Модель для генерации текста (GigaChat, GigaChat-Pro)
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе
            stream: Использовать потоковую генерацию
            
        Returns:
            Dict: Ответ от API
        """
        access_token = self._get_access_token()
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            response = self._make_http_request(
                method="POST",
                url=f"{self.api_base}/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка при генерации текста: {str(e)}")
            raise
    
    # Алиас для обратной совместимости
    generate_text = chat_completion
    
    def generate_with_functions(self, 
                               messages: List[Dict[str, str]], 
                               functions: List[Dict],
                               function_call: str = "auto",
                               model: str = "GigaChat-Max",
                               temperature: float = 0.7) -> Dict:
        """
        Генерация текста с использованием функций
        
        Args:
            messages: Список сообщений
            functions: Описание функций в формате JSON Schema
            function_call: Режим вызова функций ("auto", "none" или имя конкретной функции)
            model: Модель для генерации
            temperature: Температура генерации
            
        Returns:
            Dict: Ответ от API
        """
        access_token = self._get_access_token()
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "functions": functions,
            "function_call": function_call
        }
        
        try:
            response = self._make_http_request(
                method="POST",
                url=f"{self.api_base}/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка при генерации с функциями: {str(e)}")
            raise
    
    def create_embeddings(self, texts: List[str], model: str = "Embeddings") -> Dict:
        """
        Создание эмбеддингов для текстов
        
        Args:
            texts: Список текстов для создания эмбеддингов
            model: Модель для создания эмбеддингов
            
        Returns:
            Dict: Ответ от API с эмбеддингами
        """
        access_token = self._get_access_token()
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        payload = {
            "model": model,
            "input": texts
        }
        
        try:
            response = self._make_http_request(
                method="POST",
                url=f"{self.api_base}/api/v1/embeddings",
                headers=headers,
                json=payload
            )
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка при создании эмбеддингов: {str(e)}")
            raise 