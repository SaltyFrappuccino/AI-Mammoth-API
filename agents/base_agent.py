# agents/base_agent.py
from langchain_core.messages import HumanMessage, SystemMessage
from config import llm
import time
import logging
import httpx
import traceback

logger = logging.getLogger("base_agent")

class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    def call(self, input_text: str, max_retries: int = 3) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=input_text)
        ]
        
        # Добавляем механизм повторных попыток с экспоненциальной задержкой
        retries = 0
        last_error = None
        
        while retries <= max_retries:
            try:
                if retries > 0:
                    logger.info(f"{self.name}: Повторная попытка {retries}/{max_retries}")
                    
                response = llm.invoke(messages)
                return response.content
                
            except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                retries += 1
                last_error = e
                
                if retries <= max_retries:
                    # Экспоненциальная задержка: 2^retry * 1 сек (2, 4, 8 секунд)
                    wait_time = 2 ** retries
                    logger.warning(f"{self.name}: Таймаут запроса. Ожидание {wait_time} сек перед повторной попыткой. ({retries}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{self.name}: Превышено количество попыток. Последняя ошибка: {str(e)}")
                    logger.error(traceback.format_exc())
                    # Возвращаем сообщение об ошибке в крайнем случае
                    return f"Ошибка запроса к API после {max_retries} попыток: {str(e)}"
                    
            except Exception as e:
                logger.error(f"{self.name}: Неожиданная ошибка: {str(e)}")
                logger.error(traceback.format_exc())
                return f"Произошла ошибка при обработке запроса: {str(e)}"
