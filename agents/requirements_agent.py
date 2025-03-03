# agents/requirements_agent.py
from agents.base_agent import BaseAgent
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("requirements-agent")

class RequirementsAgent(BaseAgent):
    """
    Агент для анализа требований
    """
    
    def __init__(self, semantic_db=None):
        """
        Инициализация агента анализа требований
        
        Args:
            semantic_db: Опциональная семантическая база данных
        """
        system_prompt = """Ты эксперт по анализу требований к программному обеспечению. Твоя задача - анализировать 
        предоставленные требования, выделять ключевые функциональности, оценивать полноту и четкость требований,
        а также выявлять любые потенциальные проблемы или противоречия.
        
        При анализе требований обращай внимание на:
        1. Функциональные требования - что система должна делать
        2. Нефункциональные требования - ограничения и качественные характеристики
        3. Технические требования - архитектура, используемые технологии
        4. Потенциальные противоречия, неясности или пробелы в требованиях
        5. Приоритеты требований (если указаны)
        
        Твой ответ должен быть структурированным, содержать систематизированный перечень требований
        и рекомендации по их улучшению или дополнению.
        """
        
        super().__init__(name="RequirementsAnalysisAgent", system_prompt=system_prompt)
        self.semantic_db = semantic_db
        logger.info("Агент анализа требований инициализирован")
    
    def enrich_prompt_with_context(self, prompt: str) -> str:
        """
        Обогащение промпта контекстом из семантической БД, если она доступна
        
        Args:
            prompt: Исходный промпт
            
        Returns:
            str: Обогащенный промпт
        """
        if not self.semantic_db:
            return prompt
            
        context = ""
        try:
            # Запрашиваем результаты из семантической БД, если она доступна
            search_results = self.semantic_db.search(prompt, k=2)
            
            if search_results and len(search_results) > 0:
                context = "\n\nДополнительный контекст:\n"
                for i, result in enumerate(search_results):
                    context += f"\n--- Документ {i+1} ---\n{result.page_content}\n"
                
                logger.info(f"Промпт обогащен контекстом из {len(search_results)} документов")
            else:
                logger.info("Не удалось найти релевантный контекст в семантической БД")
                
        except Exception as e:
            logger.error(f"Ошибка при обогащении промпта: {str(e)}")
            
        return prompt + context
    
    def analyze_requirements(self, requirements: str) -> str:
        """
        Анализ требований
        
        Args:
            requirements: Текст требований для анализа
            
        Returns:
            str: Результат анализа требований
        """
        prompt = f"Проанализируй следующие требования к программному обеспечению и предоставь структурированный анализ:\n\n{requirements}"
        
        # Обогащаем промпт контекстом, если есть семантическая БД
        enriched_prompt = self.enrich_prompt_with_context(prompt)
        
        result = self.call(enriched_prompt)
        return result
    
    def analyze_requirements_structured(self, requirements: str) -> Dict[str, Any]:
        """
        Анализ требований с получением структурированного ответа
        
        Args:
            requirements: Текст требований для анализа
            
        Returns:
            Dict: Структурированный результат анализа требований
        """
        prompt = f"Проанализируй следующие требования к программному обеспечению и предоставь структурированный анализ:\n\n{requirements}"
        
        # Обогащаем промпт контекстом, если есть семантическая БД
        enriched_prompt = self.enrich_prompt_with_context(prompt)
        
        # Определяем функции для структурирования ответа
        functions = [
            {
                "name": "requirements_analysis",
                "description": "Структурированный анализ требований к программному обеспечению",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "functional_requirements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "Идентификатор требования (FR1, FR2, ...)"},
                                    "description": {"type": "string", "description": "Описание функционального требования"},
                                    "priority": {"type": "string", "description": "Приоритет (High, Medium, Low)"},
                                    "clarity": {"type": "string", "description": "Ясность требования (Clear, Ambiguous, Unclear)"}
                                }
                            },
                            "description": "Список функциональных требований"
                        },
                        "non_functional_requirements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "Идентификатор требования (NFR1, NFR2, ...)"},
                                    "description": {"type": "string", "description": "Описание нефункционального требования"},
                                    "type": {"type": "string", "description": "Тип требования (Performance, Security, Usability, ...)"},
                                    "priority": {"type": "string", "description": "Приоритет (High, Medium, Low)"}
                                }
                            },
                            "description": "Список нефункциональных требований"
                        },
                        "issues": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "description": "Тип проблемы (Contradiction, Ambiguity, Missing, ...)"},
                                    "description": {"type": "string", "description": "Описание проблемы"},
                                    "affected_requirements": {"type": "array", "items": {"type": "string"}, "description": "Затронутые требования"}
                                }
                            },
                            "description": "Выявленные проблемы в требованиях"
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Рекомендации по улучшению требований"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Общая оценка качества требований"
                        }
                    },
                    "required": ["functional_requirements", "non_functional_requirements", "issues", "recommendations", "summary"]
                }
            }
        ]
        
        # Вызываем агента с функциями
        response = self.call_with_functions(enriched_prompt, functions)
        
        # Обрабатываем результат
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            if "message" in choice and "function_call" in choice["message"]:
                function_call = choice["message"]["function_call"]
                if function_call["name"] == "requirements_analysis" and "arguments" in function_call:
                    try:
                        import json
                        analysis_results = json.loads(function_call["arguments"])
                        return analysis_results
                    except Exception as e:
                        logger.error(f"Ошибка при обработке результатов анализа требований: {str(e)}")
        
        # Если не удалось получить структурированный результат, возвращаем простой текстовый анализ
        logger.warning("Не удалось получить структурированный анализ требований, возвращаем текстовый результат")
        result = self.analyze_requirements(requirements)
        return {"summary": result}

    def call(self, input_text: str) -> str:
        """
        Переопределенный метод вызова агента с обработкой результата
        
        Args:
            input_text: Входной текст
            
        Returns:
            str: Результат обработки
        """
        result = super().call(input_text)
        
        # Анализируем ответ, чтобы убедиться, что он соответствует ожидаемому формату
        if "Функциональные требования" not in result and "функциональные требования" not in result.lower():
            logger.warning("Результат анализа требований не содержит ожидаемых разделов, пробуем повторный запрос")
            
            # Добавляем явные инструкции по форматированию
            enhanced_prompt = input_text + "\n\nПожалуйста, структурируй свой ответ следующим образом:\n\n" + \
                              "## Функциональные требования\n\n" + \
                              "## Нефункциональные требования\n\n" + \
                              "## Выявленные проблемы\n\n" + \
                              "## Рекомендации\n\n" + \
                              "## Общая оценка\n"
            
            result = super().call(enhanced_prompt)
        
        return result