# agents/base_agent.py
import os
import logging
import traceback
from typing import Dict, List, Optional, Any
from gigachat_client import GigaChatClient

logger = logging.getLogger("base-agent")

class BaseAgent:
    """
    Базовый класс для всех агентов, использующих GigaChat API
    """
    
    def __init__(self, name: str, system_prompt: str):
        """
        Инициализация базового агента
        
        Args:
            name: Название агента
            system_prompt: Системный промпт для агента
        """
        self.name = name
        self.system_prompt = system_prompt
        self.client = GigaChatClient(
            auth_key=os.environ.get("GIGACHAT_API_KEY"),
            api_base=os.environ.get("GIGACHAT_API_BASE", "https://gigachat.devices.sberbank.ru")
        )
        logger.info(f"Агент {name} инициализирован")
    
    def call(self, input_text: str, max_retries: int = 3) -> str:
        """
        Вызов агента с заданным текстом
        
        Args:
            input_text: Входной текст для обработки
            max_retries: Максимальное количество попыток при ошибке
            
        Returns:
            str: Результат обработки
        """
        logger.info(f"Вызов агента {self.name}")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": input_text}
        ]
        
        retries = 0
        while retries < max_retries:
            try:
                # Отправляем запрос к GigaChat API
                response = self.client.generate_text(
                    messages=messages,
                    model="GigaChat-Max",  # Используем продвинутую модель
                )
                
                # Извлекаем ответ
                if "choices" in response and len(response["choices"]) > 0:
                    choice = response["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        result = choice["message"]["content"]
                        logger.info(f"Агент {self.name} успешно выполнил запрос")
                        return result
                
                logger.warning(f"Неожиданный формат ответа от GigaChat API: {response}")
                retries += 1
                
            except Exception as e:
                logger.error(f"Ошибка при вызове агента {self.name}: {str(e)}")
                logger.error(traceback.format_exc())
                retries += 1
                
        # Если все попытки исчерпаны, возвращаем сообщение об ошибке
        error_msg = f"Агент {self.name} не смог обработать запрос после {max_retries} попыток."
        logger.error(error_msg)
        return error_msg
    
    def call_with_functions(self, input_text: str, functions: List[Dict], function_call: str = "auto", max_retries: int = 3) -> Dict:
        """
        Вызов агента с использованием функций
        
        Args:
            input_text: Входной текст для обработки
            functions: Список функций в формате GigaChat API
            function_call: Режим вызова функций
            max_retries: Максимальное количество попыток при ошибке
            
        Returns:
            Dict: Результат обработки
        """
        logger.info(f"Вызов агента {self.name} с функциями")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": input_text}
        ]
        
        retries = 0
        while retries < max_retries:
            try:
                # Отправляем запрос к GigaChat API с функциями
                response = self.client.generate_with_functions(
                    messages=messages,
                    functions=functions,
                    function_call=function_call,
                    model="GigaChat-Max",
                )
                
                logger.info(f"Агент {self.name} успешно выполнил запрос с функциями")
                return response
                
            except Exception as e:
                logger.error(f"Ошибка при вызове агента {self.name} с функциями: {str(e)}")
                logger.error(traceback.format_exc())
                retries += 1
                
        # Если все попытки исчерпаны, возвращаем сообщение об ошибке
        error_msg = f"Агент {self.name} не смог обработать запрос с функциями после {max_retries} попыток."
        logger.error(error_msg)
        return {"error": error_msg}
