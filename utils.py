from gigachat_llm import GigaChatLLM
import logging
from typing import Dict, Any, List

logger: logging.Logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, client_id, client_secret):
        self.llm = GigaChatLLM(client_id, client_secret)
        logger.info(f"Инициализирован агент {self.__class__.__name__}")

    def analyze(self, system_prompt, user_input):
        logger.info(f"Начинаем анализ для {self.__class__.__name__}")
        logger.debug(f"System prompt: {system_prompt}")
        logger.debug(f"User input: {user_input[:100]}...")  # Логируем начало текста
        return self.llm.generate_response(
            system_prompt=system_prompt,
            user_message=user_input,
            model="GigaChat-Max"
        )
    
    def call_with_functions(self, user_message: str, functions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Вызов модели с поддержкой пользовательских функций.
        
        :param user_message: Сообщение пользователя
        :param functions: Описание функций в формате JSON Schema
        :return: Ответ API с учетом вызова функций
        """
        logger.info(f"{self.__class__.__name__}: Вызов call_with_functions")
        return self.llm.call_with_functions(user_message, functions)
