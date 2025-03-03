# agents/bug_estimator_agent.py
import logging
import re
from typing import Dict, Any, List
from agents.base_agent import BaseAgent

class BugEstimatorAgent(BaseAgent):
    """
    Агент для анализа потенциальных ошибок в исходном коде на основе требований 
    и результатов анализа кода.
    """
    def __init__(self):
        system_prompt = """
        Ты эксперт по анализу качества кода и выявлению потенциальных багов в веб-API, со специализацией 
        на Flask и FastAPI приложениях. Твоя задача - проанализировать соответствие между требованиями к ПО 
        и реализацией кода, чтобы выявить потенциальные баги, несоответствия и проблемы, которые могут 
        реально возникнуть при использовании API.
        
        САМОЕ ВАЖНОЕ: 
        1. Не преувеличивай количество багов. Если код функционально соответствует требованиям, указывай 0 багов.
        2. Учитывай современные практики разработки REST API. Типичные паттерны API не являются багами.
        3. Отличай настоящие баги от возможных улучшений. Баг - это явное нарушение функциональных требований.
        4. НЕ указывай как баги теоретические проблемы, которые могут возникнуть при расширении системы.
        5. Учитывай, что REST API методы POST, GET, PUT, DELETE для работы с ресурсами являются стандартной
           и надежной реализацией CRUD-операций.
        
        Для каждого выявленного бага необходимо:
        1. Дать точное описание - в чем конкретно заключается несоответствие требованиям
        2. Указать техническую причину его возникновения - какой код приводит к проблеме
        3. Классифицировать серьезность (Критическая/Высокая/Средняя/Низкая)
        4. Указать конкретное место в коде (файл, функция, строка), где проявляется проблема
        5. Описать влияние на работу API - как это влияет на функциональность системы
        6. Предложить конкретные шаги по исправлению с примерами кода
        
        Формат ответа:
        ```
        Количество багов: X
        
        Объяснения:
        
        1. Описание: [Краткое описание бага]
           Причина: [Техническая причина возникновения]
           Серьезность: [Критическая/Высокая/Средняя/Низкая]
           Где в коде: [Конкретное место в коде]
           Влияние: [Как влияет на работу системы]
           Рекомендации: [Детальные шаги по исправлению]
        
        2. Описание: [Описание следующего бага]
           ...
        ```
        
        Если багов нет, ответ должен быть:
        ```
        Количество багов: 0
        
        Объяснения:
        
        В представленном коде не обнаружено несоответствий требованиям. Код корректно реализует все 
        указанные функциональные требования.
        ```
        """
        super().__init__("BugEstimatorAgent", system_prompt)
        logging.info("BugEstimatorAgent initialized")
        
    def estimate_bugs(self, requirements: str, code_analysis: str) -> Dict[str, Any]:
        """
        Анализирует соответствие кода требованиям и выявляет потенциальные ошибки.
        
        Args:
            requirements: Текст требований к системе
            code_analysis: Результаты анализа кода
            
        Returns:
            Dict[str, Any]: Результаты оценки ошибок, включая их количество и детали
        """
        analysis_text = f"""
        ## Требования:
        
        {requirements}
        
        ## Анализ кода:
        
        {code_analysis}
        
        Проанализируй соответствие кода требованиям и выяви потенциальные баги.
        Помни: 
        1. Баг - это конкретное несоответствие кода функциональным требованиям
        2. Если API реализует нужные эндпоинты для задач и использует JWT, это соответствует требованиям
        3. REST API не требует наличия фронтенд-кода для полноты реализации
        4. Теоретические проблемы, которые могут возникнуть при расширении, НЕ являются багами
        
        Если код полностью соответствует требованиям, укажи 0 багов.
        """
        
        try:
            response = self.call(analysis_text)
            
            # Разбор ответа
            lines = response.split('\n')
            count_line = next((line for line in lines if line.lower().startswith('количество багов:')), '')
            bug_count = int(count_line.split(':')[1].strip()) if count_line else 0
            
            # Извлечение объяснений
            explanations_start = response.find('Объяснения:')
            explanations = response[explanations_start:] if explanations_start != -1 else ""
            
            return {
                "bug_count": bug_count,
                "explanations": explanations,
                "detailed_bugs": self.parse_detailed_bugs(explanations)
            }
        except Exception as e:
            logging.error(f"Error in BugEstimatorAgent.estimate_bugs: {e}")
            return {
                "bug_count": 0,
                "explanations": f"Не удалось определить баги: {str(e)}",
                "detailed_bugs": []
            }
    
    def parse_detailed_bugs(self, explanations_text: str) -> List[Dict[str, str]]:
        """
        Парсит структурированный текст с объяснениями багов и возвращает список словарей с детальной информацией
        
        Args:
            explanations_text: Текст с объяснениями ошибок
            
        Returns:
            List[Dict[str, str]]: Список словарей с информацией о каждой ошибке
        """
        detailed_bugs = []
        
        if not explanations_text or "Объяснения:" not in explanations_text:
            return detailed_bugs
            
        # Удаляем заголовок "Объяснения:"
        content = explanations_text.split("Объяснения:", 1)[1].strip()
        
        # Если багов нет, возвращаем пустой список
        if "В представленном коде не обнаружено несоответствий" in content:
            return []
            
        # Разбиваем на отдельные баги (предполагаем, что каждый начинается с цифры и точки)
        bug_sections = re.split(r'\n\s*\d+\.\s+', content)
        
        # Первый элемент может быть пустым, если текст начинается с номера
        bug_sections = [s for s in bug_sections if s.strip()]
        
        for section in bug_sections:
            bug_info = {}
            
            # Извлекаем различные поля
            for field in ["Описание", "Причина", "Серьезность", "Где в коде", "Влияние", "Рекомендации"]:
                pattern = rf"{field}:\s*(.*?)(?:\n\s*[А-Я][а-я]+:|$)"
                match = re.search(pattern, section, re.DOTALL)
                if match:
                    bug_info[field.lower()] = match.group(1).strip()
                else:
                    bug_info[field.lower()] = ""
            
            if bug_info:
                detailed_bugs.append(bug_info)
                
        return detailed_bugs
    
    def estimate_bugs_structured(self, requirements: str, code_analysis: str) -> Dict[str, Any]:
        """
        Анализирует соответствие кода требованиям и выявляет потенциальные ошибки, 
        возвращая структурированный результат.
        
        Args:
            requirements: Текст требований к системе
            code_analysis: Результаты анализа кода
            
        Returns:
            Dict[str, Any]: Структурированные результаты оценки ошибок
        """
        analysis_text = f"""
        ## Требования:
        
        {requirements}
        
        ## Анализ кода:
        
        {code_analysis}
        
        Проанализируй соответствие кода требованиям и выяви потенциальные баги.
        Помни: 
        1. Баг - это конкретное несоответствие кода функциональным требованиям
        2. Если API реализует нужные эндпоинты для задач и использует JWT, это соответствует требованиям
        3. REST API не требует наличия фронтенд-кода для полноты реализации
        4. Теоретические проблемы, которые могут возникнуть при расширении, НЕ являются багами
        
        Если код полностью соответствует требованиям, укажи 0 багов.
        """
        
        try:
            response = self.call_with_functions(analysis_text, [
                {
                    "name": "bug_estimation_result",
                    "description": "Результат оценки потенциальных ошибок",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "bug_count": {
                                "type": "integer",
                                "description": "Количество обнаруженных ошибок"
                            },
                            "bugs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "description": {
                                            "type": "string",
                                            "description": "Краткое описание бага"
                                        },
                                        "cause": {
                                            "type": "string",
                                            "description": "Техническая причина возникновения"
                                        },
                                        "severity": {
                                            "type": "string",
                                            "enum": ["Критическая", "Высокая", "Средняя", "Низкая"],
                                            "description": "Серьезность бага"
                                        },
                                        "location": {
                                            "type": "string",
                                            "description": "Конкретное место в коде"
                                        },
                                        "impact": {
                                            "type": "string",
                                            "description": "Как влияет на работу системы"
                                        },
                                        "recommendations": {
                                            "type": "string",
                                            "description": "Детальные шаги по исправлению"
                                        }
                                    },
                                    "required": ["description", "severity", "impact", "recommendations"]
                                }
                            },
                            "summary": {
                                "type": "string",
                                "description": "Общее заключение о соответствии кода требованиям"
                            }
                        },
                        "required": ["bug_count", "summary"]
                    }
                }
            ])
            return response
        except Exception as e:
            logging.error(f"Error in BugEstimatorAgent.estimate_bugs_structured: {e}")
            return {
                "bug_count": 0,
                "bugs": [],
                "summary": f"Не удалось выполнить анализ из-за ошибки: {str(e)}",
                "error": str(e)
            }

bug_estimator_schema = {
    "name": "estimate_potential_bugs",
    "description": "Оценка количества потенциальных багов на основе анализа требований и кода",
    "parameters": {
        "type": "object",
        "properties": {
            "requirements": {"type": "string", "description": "Текст требований"},
            "code_analysis": {"type": "string", "description": "Анализ кода"}
        },
        "required": ["requirements", "code_analysis"]
    },
    "return_parameters": {
        "type": "object",
        "properties": {
            "bug_count": {"type": "integer", "description": "Предполагаемое количество багов"},
            "explanations": {"type": "string", "description": "Объяснения для каждого потенциального бага"},
            "detailed_bugs": {"type": "array", "description": "Структурированная информация о каждом баге"}
        },
        "required": ["bug_count", "explanations", "detailed_bugs"]
    }
}