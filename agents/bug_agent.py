from utils import BaseAgent

class BugAgent(BaseAgent):
    SYSTEM_PROMPT = """
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
        
        Если багов нет, ответ должен быть:
        ```
        Количество багов: 0
        
        Объяснения:
        
        В представленном коде не обнаружено несоответствий требованиям. Код корректно реализует все 
        указанные функциональные требования.
        ```
        """
    
    def execute(self, analysis_results):
        summary = "\n".join([
            f"Требования: {analysis_results['requirements']}",
            f"Документация: {analysis_results['documentation']}",
            f"Код: {analysis_results['code']}"
        ])
        return self.call_with_functions(summary, [
            {
                "name": "bug_analysis_result",
                "description": "Результат анализа потенциальных багов в коде",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "bug_count": {"type": "integer", "description": "Количество обнаруженных ошибок"},
                        "bugs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string", "description": "Краткое описание бага"},
                                    "cause": {"type": "string", "description": "Техническая причина возникновения"},
                                    "severity": {"type": "string", "enum": ["Критическая", "Высокая", "Средняя", "Низкая"], "description": "Серьезность бага"},
                                    "location": {"type": "string", "description": "Конкретное место в коде"},
                                    "impact": {"type": "string", "description": "Как влияет на работу системы"},
                                    "recommendations": {"type": "string", "description": "Детальные шаги по исправлению"}
                                },
                                "required": ["description", "severity", "impact", "recommendations"]
                            }
                        }
                    },
                    "required": ["bug_count", "bugs"]
                }
            }
        ])
