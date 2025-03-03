# agents/code_agent.py
import logging
from typing import Dict, Any
from .base_agent import BaseAgent

logger = logging.getLogger("code-agent")

class CodeAgent(BaseAgent):
    """
    Агент для анализа исходного кода
    """
    
    def __init__(self):
        """
        Инициализация агента анализа кода
        """
        system_prompt = """Ты эксперт по анализу исходного кода. Твоя задача - тщательно проанализировать 
        предоставленный исходный код, оценивая его качество, структуру, потенциальные ошибки и соответствие 
        лучшим практикам программирования. 
        
        Анализируя код, обращай внимание на:
        1. Качество кода: чистоту, читаемость, следование стилям и конвенциям
        2. Архитектурные решения и структуру
        3. Потенциальные ошибки и баги
        4. Оптимизацию и эффективность
        5. Безопасность кода
        
        Твой ответ должен быть подробным, содержать конкретные ссылки на проблемные или хорошие места в коде и 
        предлагать рекомендации по улучшению.
        """
        
        super().__init__(name="CodeAnalysisAgent", system_prompt=system_prompt)
        logger.info("Агент анализа кода инициализирован")
    
    def analyze_code(self, code: str) -> str:
        """
        Анализ исходного кода
        
        Args:
            code: Исходный код для анализа
            
        Returns:
            str: Результат анализа кода
        """
        prompt = f"Пожалуйста, проанализируй следующий исходный код и предоставь подробный отчет:\n\n```\n{code}\n```"
        
        result = self.call(prompt)
        return result
    
    def analyze_code_structured(self, code: str) -> Dict[str, Any]:
        """
        Анализ исходного кода с получением структурированного ответа
        
        Args:
            code: Исходный код для анализа
            
        Returns:
            Dict: Структурированный результат анализа кода
        """
        prompt = f"Проанализируй следующий исходный код и предоставь подробный структурированный отчет:\n\n```\n{code}\n```"
        
        # Определяем функции для структурирования ответа
        functions = [
            {
                "name": "code_analysis",
                "description": "Структурированный анализ исходного кода",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code_quality": {
                            "type": "object",
                            "properties": {
                                "rating": {"type": "number", "description": "Оценка качества кода от 1 до 10"},
                                "strengths": {"type": "array", "items": {"type": "string"}, "description": "Сильные стороны кода"},
                                "weaknesses": {"type": "array", "items": {"type": "string"}, "description": "Слабые стороны кода"}
                            }
                        },
                        "potential_bugs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string", "description": "Описание потенциального бага"},
                                    "severity": {"type": "string", "description": "Критичность (Critical, High, Medium, Low)"},
                                    "location": {"type": "string", "description": "Место в коде с ошибкой"}
                                }
                            },
                            "description": "Список потенциальных ошибок и багов"
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Рекомендации по улучшению кода"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Общее заключение по коду"
                        }
                    },
                    "required": ["code_quality", "potential_bugs", "recommendations", "summary"]
                }
            }
        ]
        
        # Вызываем агента с функциями
        response = self.call_with_functions(prompt, functions)
        
        # Обрабатываем результат
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            if "message" in choice and "function_call" in choice["message"]:
                function_call = choice["message"]["function_call"]
                if function_call["name"] == "code_analysis" and "arguments" in function_call:
                    try:
                        import json
                        analysis_results = json.loads(function_call["arguments"])
                        return analysis_results
                    except Exception as e:
                        logger.error(f"Ошибка при обработке результатов анализа кода: {str(e)}")
        
        # Если не удалось получить структурированный результат, возвращаем простой текстовый анализ
        logger.warning("Не удалось получить структурированный анализ кода, возвращаем текстовый результат")
        result = self.analyze_code(code)
        return {"summary": result}
