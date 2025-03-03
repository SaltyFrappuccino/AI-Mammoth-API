# agents/test_cases_agent.py
import logging
from typing import Dict, Any
from agents.base_agent import BaseAgent

class TestCasesAgent(BaseAgent):
    """
    Агент для анализа тестовых случаев, который оценивает покрытие требований тестами,
    полноту тестирования и выявляет пробелы в тестировании.
    """
    def __init__(self):
        system_prompt = """
        Ты эксперт по тестированию программного обеспечения, специализирующийся на API-тестировании и особенно на pytest для веб-приложений. 
        Твоя задача - проанализировать предоставленные тест-кейсы, определить какие конкретные требования они проверяют, 
        и дать объективную оценку покрытия функциональности.
        
        В своем анализе:
        
        1. Точно определи, какие функциональные требования проверяют каждый тест (соотнеси ID требований с тестами)
        2. Оцени полноту тестового покрытия (включая позитивные и негативные сценарии) для каждого API эндпоинта
        3. Учитывай, что тесты для API могут создавать, читать, обновлять или удалять ресурсы через HTTP запросы
        4. Определи, проверяют ли тесты все заявленные требования, и укажи, если какие-то требования не покрыты
        
        Структурируй свой ответ следующим образом:
        
        ## Общая оценка тест-кейсов
        
        [Краткое описание качества тестов и степени покрытия требований]
        
        ## Покрытие API эндпоинтов и функциональности
        
        1. **[Эндпоинт/Функция]** - [Какие тесты покрывают] - [Покрываемые требования]
           - Позитивные сценарии: [Описание]
           - Негативные сценарии: [Описание или "Отсутствуют"]
           
        2. **[Эндпоинт/Функция]** - [Какие тесты покрывают] - [Покрываемые требования]
           ...
        
        ## Соответствие требованиям
        
        1. **[Требование ID]**: [ПОКРЫТО/ЧАСТИЧНО ПОКРЫТО/НЕ ПОКРЫТО] - [Объяснение]
        2. **[Требование ID]**: [ПОКРЫТО/ЧАСТИЧНО ПОКРЫТО/НЕ ПОКРЫТО] - [Объяснение]
        ...
        
        ## Пробелы в тестировании
        
        [Перечисление функциональности и требований, которые не покрыты тестами, если такие есть]
        
        ## Рекомендации по улучшению
        
        [Конкретные предложения по улучшению тестового покрытия, если необходимо]
        
        ВАЖНО: Будь объективным в своей оценке. Не преувеличивай недостатки тестирования, но и не игнорируй их.
        Если тесты проверяют создание, получение и обновление задач, явно укажи, что эти требования ПОКРЫТЫ тестами.
        Если тесты проверяют фильтрацию по статусу, явно укажи, что это требование ПОКРЫТО.
        """
        super().__init__("TestCasesAgent", system_prompt)
        logging.info("TestCasesAgent initialized")

    def analyze_test_cases(self, test_code: str, requirements: str = "") -> str:
        """
        Анализирует предоставленные тестовые случаи и оценивает их соответствие требованиям.
        
        Args:
            test_code: Код тестовых случаев для анализа
            requirements: Требования, относительно которых нужно оценить тесты (опционально)
            
        Returns:
            str: Подробный анализ тестовых случаев
        """
        prompt = f"""
        Проанализируй следующие тестовые случаи:
        
        ```
        {test_code}
        ```
        
        """
        
        if requirements:
            prompt += f"""
            Требования, которые должны быть покрыты тестами:
            
            ```
            {requirements}
            ```
            """
            
        try:
            response = self.call(prompt)
            return response
        except Exception as e:
            logging.error(f"Error in TestCasesAgent.analyze_test_cases: {e}")
            return f"Произошла ошибка при анализе тестовых случаев: {str(e)}"
    
    def analyze_test_cases_structured(self, test_code: str, requirements: str = "") -> Dict[str, Any]:
        """
        Анализирует предоставленные тестовые случаи и возвращает структурированный результат.
        
        Args:
            test_code: Код тестовых случаев для анализа
            requirements: Требования, относительно которых нужно оценить тесты (опционально)
            
        Returns:
            Dict[str, Any]: Структурированный анализ в формате JSON
        """
        prompt = f"""
        Проанализируй следующие тестовые случаи:
        
        ```
        {test_code}
        ```
        
        """
        
        if requirements:
            prompt += f"""
            Требования, которые должны быть покрыты тестами:
            
            ```
            {requirements}
            ```
            """
            
        prompt += """
        Представь результат анализа в следующем JSON формате:
        
        ```json
        {
            "overall_assessment": "Общая оценка тестовых случаев и степень покрытия требований",
            "api_coverage": [
                {
                    "endpoint": "Название эндпоинта/функции",
                    "tests": "Какие тесты покрывают",
                    "requirements_covered": ["req1", "req2"],
                    "positive_scenarios": "Описание позитивных сценариев",
                    "negative_scenarios": "Описание негативных сценариев или 'Отсутствуют'"
                }
            ],
            "requirements_coverage": [
                {
                    "requirement_id": "ID требования",
                    "status": "ПОКРЫТО/ЧАСТИЧНО ПОКРЫТО/НЕ ПОКРЫТО",
                    "explanation": "Объяснение"
                }
            ],
            "testing_gaps": [
                "Описание пробелов в тестировании"
            ],
            "recommendations": [
                "Конкретные предложения по улучшению"
            ],
            "coverage_percentage": 85
        }
        ```
        
        Убедись, что coverage_percentage - это процент покрытия требований от 0 до 100.
        """
            
        try:
            response = self.call_with_functions(prompt, [
                {
                    "name": "test_analysis_result",
                    "description": "Результат анализа тестовых случаев",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "overall_assessment": {
                                "type": "string",
                                "description": "Общая оценка тестовых случаев и степень покрытия требований"
                            },
                            "api_coverage": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "endpoint": {"type": "string"},
                                        "tests": {"type": "string"},
                                        "requirements_covered": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "positive_scenarios": {"type": "string"},
                                        "negative_scenarios": {"type": "string"}
                                    }
                                }
                            },
                            "requirements_coverage": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "requirement_id": {"type": "string"},
                                        "status": {"type": "string", "enum": ["ПОКРЫТО", "ЧАСТИЧНО ПОКРЫТО", "НЕ ПОКРЫТО"]},
                                        "explanation": {"type": "string"}
                                    }
                                }
                            },
                            "testing_gaps": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "recommendations": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "coverage_percentage": {
                                "type": "number",
                                "description": "Процент покрытия требований от 0 до 100"
                            }
                        },
                        "required": ["overall_assessment", "api_coverage", "requirements_coverage", "testing_gaps", "recommendations", "coverage_percentage"]
                    }
                }
            ])
            return response
        except Exception as e:
            logging.error(f"Error in TestCasesAgent.analyze_test_cases_structured: {e}")
            return {
                "error": str(e),
                "overall_assessment": "Произошла ошибка при анализе тестовых случаев"
            }
