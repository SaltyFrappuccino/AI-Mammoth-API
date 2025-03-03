import os
import json
import logging
import base64
import time
from typing import Dict, List, Optional, Any, Tuple
from gigachat_client import GigaChatClient

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analysis-engine")

class AnalysisEngine:
    """
    Движок анализа требований и кода на базе GigaChat API
    """
    
    def __init__(self, auth_key=None, api_base=None):
        """
        Инициализация движка анализа
        
        Args:
            auth_key: Ключ авторизации для GigaChat API
            api_base: Базовый URL для GigaChat API
        """
        self.auth_key = auth_key
        self.api_base = api_base
        
        # Создаем клиент GigaChat с механизмом повторных попыток
        self.client = GigaChatClient(
            auth_key=auth_key, 
            api_base=api_base,
            max_retries=5,       # 5 повторных попыток
            retry_delay=1.0,     # Начальная задержка 1 секунда
            timeout=60.0         # Таймаут 60 секунд для длительных операций
        )
        
        print(f"INFO: Инициализирован AnalysisEngine")
    
    def analyze_requirements_and_code(
        self, 
        requirements: str, 
        code: str, 
        test_cases: str, 
        documentation: str = "",
        analyze_security: bool = True
    ) -> Dict:
        """
        Анализ требований, кода и тестовых случаев с генерацией отчета
        
        Args:
            requirements: Текст требований
            code: Исходный код
            test_cases: Тестовые случаи
            documentation: Дополнительная документация
            analyze_security: Флаг для анализа безопасности
            
        Returns:
            Dict: Результаты анализа
        """
        logger.info("Начало анализа требований и кода")
        
        # Функции для структурирования ответа GigaChat
        functions = [
            {
                "name": "analyze_compliance",
                "description": "Анализ соответствия кода требованиям и генерация отчета",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "final_report": {
                            "type": "string",
                            "description": "Итоговый отчет об анализе соответствия"
                        },
                        "bugs_count": {
                            "type": "integer",
                            "description": "Количество обнаруженных ошибок"
                        },
                        "bugs_explanations": {
                            "type": "string",
                            "description": "Объяснения по обнаруженным ошибкам"
                        },
                        "detailed_bugs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {
                                        "type": "string",
                                        "description": "Описание ошибки"
                                    },
                                    "severity": {
                                        "type": "string",
                                        "description": "Степень критичности (Critical, High, Medium, Low)"
                                    },
                                    "location": {
                                        "type": "string",
                                        "description": "Расположение ошибки в коде"
                                    },
                                    "cause": {
                                        "type": "string",
                                        "description": "Причина возникновения ошибки"
                                    },
                                    "impact": {
                                        "type": "string",
                                        "description": "Влияние ошибки на систему"
                                    },
                                    "recommendations": {
                                        "type": "string",
                                        "description": "Рекомендации по исправлению"
                                    }
                                }
                            },
                            "description": "Детальное описание найденных ошибок"
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {
                                        "type": "string",
                                        "description": "Текст рекомендации"
                                    },
                                    "priority": {
                                        "type": "string",
                                        "description": "Приоритет (High, Medium, Low)"
                                    },
                                    "priority_level": {
                                        "type": "integer",
                                        "description": "Числовой приоритет (1 - высший)"
                                    },
                                    "type": {
                                        "type": "string",
                                        "description": "Тип рекомендации (Performance, Security, Quality, Best Practice)"
                                    },
                                    "affected_requirements": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Затронутые требования"
                                    },
                                    "affected_code": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Затронутый код"
                                    }
                                }
                            },
                            "description": "Рекомендации по улучшению"
                        }
                    },
                    "required": ["final_report", "bugs_count", "bugs_explanations"]
                }
            }
        ]
        
        # Если нужен анализ безопасности, добавляем дополнительное поле
        if analyze_security:
            functions[0]["parameters"]["properties"]["security_vulnerabilities"] = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Тип уязвимости"
                        },
                        "severity": {
                            "type": "string",
                            "description": "Степень критичности (Critical, High, Medium, Low)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Описание уязвимости"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Путь к файлу с уязвимостью"
                        },
                        "line_number": {
                            "type": "integer",
                            "description": "Номер строки с уязвимостью"
                        },
                        "code_snippet": {
                            "type": "string",
                            "description": "Фрагмент кода с уязвимостью"
                        },
                        "mitigation": {
                            "type": "string",
                            "description": "Рекомендации по устранению уязвимости"
                        },
                        "cwe_id": {
                            "type": "string",
                            "description": "Идентификатор CWE (Common Weakness Enumeration)"
                        }
                    }
                },
                "description": "Обнаруженные уязвимости безопасности"
            }
        
        # Подготовка запроса к GigaChat
        messages = [
            {
                "role": "system",
                "content": "Ты - аналитическая система, которая оценивает соответствие программного кода требованиям. "
                          "Твоя задача - проанализировать требования, код и тестовые сценарии, и определить, "
                          "соответствует ли код требованиям, нет ли в нем ошибок или уязвимостей. "
                          "Генерируй подробный отчет и четкие рекомендации по улучшению."
            },
            {
                "role": "user",
                "content": f"Проанализируй следующие материалы и сформируй отчет:\n\n"
                          f"## ТРЕБОВАНИЯ:\n{requirements}\n\n"
                          f"## КОД:\n{code}\n\n"
                          f"## ТЕСТОВЫЕ СЛУЧАИ:\n{test_cases}\n\n"
                          f"## ДОКУМЕНТАЦИЯ:\n{documentation}\n\n"
                          f"Проведи оценку соответствия кода требованиям, выяви ошибки и дай рекомендации. "
                          f"{'Также проведи анализ безопасности кода.' if analyze_security else ''}"
            }
        ]
        
        try:
            # Выполняем запрос к GigaChat API с функциями
            response = self.client.generate_with_functions(
                messages=messages,
                functions=functions,
                function_call="auto",
                model="GigaChat-Max",  # Используем продвинутую модель для лучшего анализа
            )
            
            # Обрабатываем результат
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                
                # Проверяем, вернул ли GigaChat вызов функции
                if choice.get("finish_reason") == "function_call" and "function_call" in choice.get("message", {}):
                    function_call = choice["message"]["function_call"]
                    if function_call["name"] == "analyze_compliance":
                        try:
                            # Парсим аргументы функции (результаты анализа)
                            analysis_results = json.loads(function_call["arguments"])
                            logger.info("Анализ успешно завершен")
                            return analysis_results
                        except Exception as e:
                            logger.error(f"Ошибка при парсинге результатов анализа: {str(e)}")
                
                # Если модель не вернула функцию, но вернула текст
                if "content" in choice.get("message", {}) and choice["message"]["content"]:
                    # Пытаемся извлечь хоть какую-то информацию из текстового ответа
                    logger.warning("Модель вернула текстовый ответ вместо вызова функции")
                    
                    return {
                        "final_report": choice["message"]["content"],
                        "bugs_count": 0,
                        "bugs_explanations": "Не удалось структурировать анализ ошибок",
                        "detailed_bugs": [],
                        "enhanced_features_available": False,
                        "error_details": {
                            "error": "Ответ модели не содержит структурированных данных",
                            "error_type": "MODEL_RESPONSE_FORMAT",
                            "details": {"raw_response": choice["message"]["content"][:500] + "..."}
                        }
                    }
            
            # Если не получили ожидаемый результат
            logger.error("Неожиданный формат ответа от GigaChat API")
            return {
                "final_report": "Не удалось выполнить анализ",
                "bugs_count": 0,
                "bugs_explanations": "Ошибка при выполнении анализа",
                "enhanced_features_available": False,
                "error_details": {
                    "error": "Неожиданный формат ответа от GigaChat API",
                    "error_type": "API_RESPONSE_FORMAT",
                    "details": {"raw_response": str(response)[:500] + "..."}
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении анализа: {str(e)}")
            return {
                "final_report": "Произошла ошибка при выполнении анализа",
                "bugs_count": 0,
                "bugs_explanations": f"Ошибка: {str(e)}",
                "enhanced_features_available": False,
                "error_details": {
                    "error": str(e),
                    "error_type": "ANALYSIS_ERROR",
                    "stack_trace": str(e)
                }
            }
    
    def generate_visualizations(self, analysis_results: Dict) -> Dict[str, Dict]:
        """
        Генерация визуализаций на основе результатов анализа
        
        Args:
            analysis_results: Результаты анализа
            
        Returns:
            Dict: Словарь с информацией о визуализациях
        """
        logger.info("Генерация визуализаций")
        
        # Заглушка для демонстрационных целей
        # В реальном приложении здесь будет код для создания графиков и диаграмм
        
        visualizations = {}
        
        # Создаем заглушки для визуализаций
        visualizations["requirements_coverage"] = {
            "html_path": "output/visualizations/requirements_coverage.html",
            "img_path": "output/visualizations/requirements_coverage.png"
        }
        
        visualizations["bugs_severity"] = {
            "html_path": "output/visualizations/bugs_severity.html",
            "img_path": "output/visualizations/bugs_severity.png"
        }
        
        return visualizations
    
    def analyze_security(self, code: str) -> List[Dict]:
        """
        Анализ безопасности кода
        
        Args:
            code: Исходный код
            
        Returns:
            List[Dict]: Список обнаруженных уязвимостей
        """
        logger.info("Начало анализа безопасности")
        
        # Функции для структурирования ответа GigaChat
        functions = [
            {
                "name": "security_analysis",
                "description": "Анализ безопасности кода и выявление уязвимостей",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vulnerabilities": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "description": "Тип уязвимости"
                                    },
                                    "severity": {
                                        "type": "string",
                                        "description": "Степень критичности (Critical, High, Medium, Low)"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Описание уязвимости"
                                    },
                                    "line_number": {
                                        "type": "integer",
                                        "description": "Номер строки с уязвимостью"
                                    },
                                    "code_snippet": {
                                        "type": "string",
                                        "description": "Фрагмент кода с уязвимостью"
                                    },
                                    "mitigation": {
                                        "type": "string",
                                        "description": "Рекомендации по устранению уязвимости"
                                    },
                                    "cwe_id": {
                                        "type": "string",
                                        "description": "Идентификатор CWE (Common Weakness Enumeration)"
                                    }
                                }
                            },
                            "description": "Обнаруженные уязвимости безопасности"
                        },
                        "overall_security_score": {
                            "type": "number",
                            "description": "Общая оценка безопасности (0-10)"
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Рекомендации по улучшению безопасности"
                        }
                    },
                    "required": ["vulnerabilities", "overall_security_score"]
                }
            }
        ]
        
        # Подготовка запроса к GigaChat
        messages = [
            {
                "role": "system",
                "content": "Ты - эксперт по анализу безопасности кода. Твоя задача - найти и описать "
                          "все потенциальные уязвимости и проблемы безопасности в предоставленном коде."
            },
            {
                "role": "user",
                "content": f"Выполни анализ безопасности следующего кода и определи уязвимости:\n\n{code}"
            }
        ]
        
        try:
            # Выполняем запрос к GigaChat API с функциями
            response = self.client.generate_with_functions(
                messages=messages,
                functions=functions,
                function_call="auto",
                model="GigaChat-Max",  # Продвинутая модель для лучшего анализа безопасности
            )
            
            # Обрабатываем результат
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                
                # Проверяем, вернул ли GigaChat вызов функции
                if choice.get("finish_reason") == "function_call" and "function_call" in choice.get("message", {}):
                    function_call = choice["message"]["function_call"]
                    if function_call["name"] == "security_analysis":
                        try:
                            # Парсим аргументы функции (результаты анализа безопасности)
                            security_results = json.loads(function_call["arguments"])
                            logger.info("Анализ безопасности успешно завершен")
                            return security_results.get("vulnerabilities", [])
                        except Exception as e:
                            logger.error(f"Ошибка при парсинге результатов анализа безопасности: {str(e)}")
            
            # Если не получили ожидаемый результат
            logger.error("Неожиданный формат ответа от GigaChat API при анализе безопасности")
            return []
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении анализа безопасности: {str(e)}")
            return [] 