# agents/documentation_agent.py
import logging
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent

class DocumentationAgent(BaseAgent):
    """
    Агент для анализа документации, который оценивает полноту, ясность и соответствие 
    документации требованиям и исходному коду.
    """
    def __init__(self, semantic_db=None):
        system_prompt = """
        Ты эксперт по технической документации. Твоя задача - анализировать предоставленную документацию
        на полноту, ясность, соответствие спецификациям и требованиям.
        
        При анализе документации учитывай следующие моменты:
        1. Полнота - охватывает ли документация все аспекты системы, API, компоненты и функции
        2. Ясность - насколько понятно и структурировано представлена информация
        3. Соответствие - соответствует ли документация реальному коду и требованиям
        4. Целевая аудитория - учтены ли потребности разных пользователей (разработчики, администраторы, конечные пользователи)
        5. Примеры и инструкции - содержит ли документация достаточно примеров использования и пошаговых инструкций
        
        Ты должен предоставить четкую оценку по каждому аспекту и рекомендации по улучшению.
        """
        super().__init__("DocumentationAgent", system_prompt)
        self.semantic_db = semantic_db
        logging.info("DocumentationAgent initialized")

    def enrich_prompt_with_context(self, prompt: str) -> str:
        """
        Обогащает запрос контекстом из семантической базы данных, если она доступна.
        
        Args:
            prompt: Исходный запрос
            
        Returns:
            str: Обогащенный контекстом запрос
        """
        if self.semantic_db:
            try:
                relevant_docs = self.semantic_db.search(prompt, k=3)
                prompt += "\n\nРелевантные документы из базы знаний:\n" + "\n".join(relevant_docs)
            except Exception as e:
                logging.error(f"Error enriching prompt with semantic DB: {e}")
        return prompt

    def analyze_documentation(self, documentation: str, requirements: str = "", code: str = "") -> str:
        """
        Анализирует предоставленную документацию и оценивает ее качество.
        
        Args:
            documentation: Текст документации для анализа
            requirements: Требования к системе (опционально)
            code: Исходный код системы (опционально)
            
        Returns:
            str: Подробный анализ документации
        """
        prompt = f"""
        Проанализируй следующую документацию:
        
        ```
        {documentation}
        ```
        
        """
        
        if requirements:
            prompt += f"""
            Требования к системе:
            
            ```
            {requirements}
            ```
            
            Оцени, насколько документация соответствует этим требованиям.
            """
            
        if code:
            prompt += f"""
            Исходный код системы:
            
            ```
            {code}
            ```
            
            Оцени, насколько документация соответствует предоставленному коду.
            """
            
        prompt = self.enrich_prompt_with_context(prompt)
            
        try:
            response = self.call(prompt)
            return response
        except Exception as e:
            logging.error(f"Error in DocumentationAgent.analyze_documentation: {e}")
            return f"Произошла ошибка при анализе документации: {str(e)}"
    
    def analyze_documentation_structured(self, documentation: str, requirements: str = "", code: str = "") -> Dict[str, Any]:
        """
        Анализирует предоставленную документацию и возвращает структурированный результат.
        
        Args:
            documentation: Текст документации для анализа
            requirements: Требования к системе (опционально)
            code: Исходный код системы (опционально)
            
        Returns:
            Dict[str, Any]: Структурированный анализ в формате JSON
        """
        prompt = f"""
        Проанализируй следующую документацию:
        
        ```
        {documentation}
        ```
        
        """
        
        if requirements:
            prompt += f"""
            Требования к системе:
            
            ```
            {requirements}
            ```
            
            Оцени, насколько документация соответствует этим требованиям.
            """
            
        if code:
            prompt += f"""
            Исходный код системы:
            
            ```
            {code}
            ```
            
            Оцени, насколько документация соответствует предоставленному коду.
            """
        
        prompt += """
        Представь результат анализа в следующем JSON формате:
        
        ```json
        {
            "overall_assessment": "Общая оценка документации в 1-2 предложениях",
            "completeness": {
                "score": 8.5,
                "comments": "Комментарий о полноте документации",
                "missing_elements": ["Элемент 1", "Элемент 2"]
            },
            "clarity": {
                "score": 7.0,
                "comments": "Комментарий о ясности документации",
                "unclear_sections": ["Раздел 1", "Раздел 2"]
            },
            "compliance": {
                "with_requirements": {
                    "score": 9.0,
                    "comments": "Комментарий о соответствии требованиям"
                },
                "with_code": {
                    "score": 6.5,
                    "comments": "Комментарий о соответствии коду"
                }
            },
            "target_audience": {
                "developers": {
                    "score": 8.0,
                    "comments": "Комментарий о документации для разработчиков"
                },
                "users": {
                    "score": 7.0,
                    "comments": "Комментарий о документации для пользователей"
                },
                "administrators": {
                    "score": 6.0,
                    "comments": "Комментарий о документации для администраторов"
                }
            },
            "examples_instructions": {
                "score": 7.5,
                "comments": "Комментарий о примерах и инструкциях"
            },
            "recommendations": [
                "Рекомендация 1",
                "Рекомендация 2"
            ]
        }
        ```
        
        Для всех score, используй значения от 0 до 10, где 10 - наилучшая оценка.
        """
        
        prompt = self.enrich_prompt_with_context(prompt)
            
        try:
            response = self.call_with_functions(prompt, [
                {
                    "name": "documentation_analysis_result",
                    "description": "Результат анализа документации",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "overall_assessment": {
                                "type": "string",
                                "description": "Общая оценка документации"
                            },
                            "completeness": {
                                "type": "object",
                                "properties": {
                                    "score": {"type": "number", "minimum": 0, "maximum": 10},
                                    "comments": {"type": "string"},
                                    "missing_elements": {"type": "array", "items": {"type": "string"}}
                                }
                            },
                            "clarity": {
                                "type": "object",
                                "properties": {
                                    "score": {"type": "number", "minimum": 0, "maximum": 10},
                                    "comments": {"type": "string"},
                                    "unclear_sections": {"type": "array", "items": {"type": "string"}}
                                }
                            },
                            "compliance": {
                                "type": "object",
                                "properties": {
                                    "with_requirements": {
                                        "type": "object",
                                        "properties": {
                                            "score": {"type": "number", "minimum": 0, "maximum": 10},
                                            "comments": {"type": "string"}
                                        }
                                    },
                                    "with_code": {
                                        "type": "object",
                                        "properties": {
                                            "score": {"type": "number", "minimum": 0, "maximum": 10},
                                            "comments": {"type": "string"}
                                        }
                                    }
                                }
                            },
                            "target_audience": {
                                "type": "object",
                                "properties": {
                                    "developers": {
                                        "type": "object",
                                        "properties": {
                                            "score": {"type": "number", "minimum": 0, "maximum": 10},
                                            "comments": {"type": "string"}
                                        }
                                    },
                                    "users": {
                                        "type": "object",
                                        "properties": {
                                            "score": {"type": "number", "minimum": 0, "maximum": 10},
                                            "comments": {"type": "string"}
                                        }
                                    },
                                    "administrators": {
                                        "type": "object",
                                        "properties": {
                                            "score": {"type": "number", "minimum": 0, "maximum": 10},
                                            "comments": {"type": "string"}
                                        }
                                    }
                                }
                            },
                            "examples_instructions": {
                                "type": "object",
                                "properties": {
                                    "score": {"type": "number", "minimum": 0, "maximum": 10},
                                    "comments": {"type": "string"}
                                }
                            },
                            "recommendations": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["overall_assessment", "completeness", "clarity", "recommendations"]
                    }
                }
            ])
            return response
        except Exception as e:
            logging.error(f"Error in DocumentationAgent.analyze_documentation_structured: {e}")
            return {
                "error": str(e),
                "overall_assessment": "Произошла ошибка при анализе документации"
            }