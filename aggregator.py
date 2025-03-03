# aggregator.py
from agents.requirements_agent import RequirementsAgent
from agents.code_agent import CodeAgent
from agents.test_cases_agent import TestCasesAgent
from agents.documentation_agent import DocumentationAgent
from agents.final_report_agent import FinalReportAgent
from agents.bug_estimator_agent import BugEstimatorAgent
from agents.semantic_agent import SemanticAgent
from semantic_db import SemanticDB
from gigachat_client import GigaChatClient
import logging
import traceback
import os
import json

# Подключаем новые модули
try:
    from visualization import VisualizationEngine
    from recommender import RecommendationEngine, Recommendation
    from security_analyzer import SecurityAnalyzer
    
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    logger = logging.getLogger("aggregator")
    logger.warning("Расширенные модули (visualization, recommender, security_analyzer) не найдены. Будет использована базовая функциональность.")
    ENHANCED_FEATURES_AVAILABLE = False

logger = logging.getLogger("aggregator")

class Aggregator:
    """
    Класс для агрегации результатов анализа от различных агентов
    """
    
    def __init__(self, semantic_db=None, gigachat_client=None):
        """
        Инициализация агрегатора
        
        Args:
            semantic_db: Экземпляр SemanticDB для поиска контекста
            gigachat_client: Экземпляр GigaChatClient
        """
        self.semantic_db = semantic_db
        
        # Инициализируем GigaChatClient, если не предоставлен
        if gigachat_client is None:
            from gigachat_client import GigaChatClient
            import os
            
            auth_key = os.getenv("GIGACHAT_API_KEY", "")
            if not auth_key:
                print("WARNING: GIGACHAT_API_KEY не найден в переменных окружения")
                
            gigachat_client = GigaChatClient(auth_key)
        
        self.client = gigachat_client
        
        # Инициализируем агентов
        self.requirements_agent = RequirementsAgent(semantic_db)
        self.code_agent = CodeAgent()
        self.test_cases_agent = TestCasesAgent()
        self.documentation_agent = DocumentationAgent(semantic_db)
        self.final_report_agent = FinalReportAgent()
        self.bug_estimator_agent = BugEstimatorAgent()
        
        # Инициализируем расширенные функции, если доступны
        if ENHANCED_FEATURES_AVAILABLE:
            logger.info("Инициализация расширенных модулей (визуализация, рекомендации, анализ безопасности)")
            self.visualization_engine = VisualizationEngine(output_dir='output/visualizations')
            self.recommendation_engine = RecommendationEngine()
            self.security_analyzer = SecurityAnalyzer()
        
        if semantic_db:
            logger.info("Semantic DB provided, initializing SemanticAgent")
            try:
                self.semantic_agent = SemanticAgent(semantic_db)
            except Exception as e:
                logger.error(f"Error initializing SemanticAgent: {str(e)}")
                logger.error(traceback.format_exc())
                self.semantic_agent = None

    def aggregate(self, requirements_text: str, code_text: str, test_cases_text: str, documentation_text: str,
                  service_descriptions=None, analyze_security=True) -> tuple:
        logger.info("Starting aggregation process")
        
        try:
            # Создаем директорию для результатов, если её нет
            os.makedirs("output", exist_ok=True)
            os.makedirs("output/visualizations", exist_ok=True)
            os.makedirs("output/reports", exist_ok=True)
            
            # If service_descriptions is provided, initialize the semantic database
            if service_descriptions and not self.semantic_db:
                logger.info("Service descriptions provided, initializing semantic DB")
                try:
                    self.semantic_db = SemanticDB(embeddings=self.client, documents=service_descriptions)
                    self.requirements_agent = RequirementsAgent(self.semantic_db)
                    self.semantic_agent = SemanticAgent(self.semantic_db)
                    logger.info("Semantic DB initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize semantic DB: {str(e)}")
                    logger.error(traceback.format_exc())
            
            results = {}
            
            # Анализ безопасности кода, если включен и доступен
            if analyze_security and ENHANCED_FEATURES_AVAILABLE and code_text:
                logger.info("Performing security analysis")
                try:
                    # Сохраняем код во временный файл для анализа
                    temp_code_file = "output/temp_code_for_analysis.py"
                    with open(temp_code_file, 'w', encoding='utf-8') as f:
                        f.write(code_text)
                    
                    # Анализируем файл
                    security_vulnerabilities = self.security_analyzer.analyze_file(temp_code_file)
                    
                    # Получаем результаты
                    if security_vulnerabilities:
                        security_report = self.security_analyzer.to_markdown()
                        security_summary = self.security_analyzer.get_vulnerability_summary()
                        results["security_analysis"] = {
                            "report": security_report,
                            "summary": security_summary,
                            "vulnerabilities": [v.to_dict() for v in security_vulnerabilities]
                        }
                        
                        # Сохраняем отчет в файл
                        self.security_analyzer.save_to_file("output/reports/security_report.md", format='md')
                        self.security_analyzer.save_to_file("output/reports/security_report.json", format='json')
                        
                        logger.info(f"Security analysis completed with {len(security_vulnerabilities)} vulnerabilities found")
                    else:
                        results["security_analysis"] = {
                            "report": "# Анализ безопасности\n\nВ коде не обнаружено потенциальных уязвимостей.",
                            "summary": {"total_vulnerabilities": 0},
                            "vulnerabilities": []
                        }
                        logger.info("Security analysis completed with no vulnerabilities found")
                        
                    # Удаляем временный файл
                    if os.path.exists(temp_code_file):
                        os.remove(temp_code_file)
                        
                except Exception as e:
                    logger.error(f"Error in security analysis: {str(e)}")
                    logger.error(traceback.format_exc())
                    results["security_analysis"] = {
                        "report": f"# Ошибка анализа безопасности\n\nПроизошла ошибка при анализе безопасности: {str(e)}",
                        "summary": {"total_vulnerabilities": 0},
                        "vulnerabilities": []
                    }
            
            # Анализ требований
            logger.info("Calling RequirementsAgent")
            try:
                req_analysis = self.requirements_agent.analyze_requirements(requirements_text)
                results["requirements_analysis"] = req_analysis
                logger.info("RequirementsAgent completed successfully")
            except Exception as e:
                logger.error(f"Error in RequirementsAgent: {str(e)}")
                logger.error(traceback.format_exc())
                # Создаем базовый анализ требований для продолжения работы
                results["requirements_analysis"] = f"Не удалось выполнить анализ требований: {str(e)}\n\nИсходные требования:\n{requirements_text[:1000]}..."
            
            # Анализ кода
            logger.info("Calling CodeAgent")
            try:
                code_analysis = self.code_agent.analyze_code(code_text)
                results["code_analysis"] = code_analysis
                logger.info("CodeAgent completed successfully")
            except Exception as e:
                logger.error(f"Error in CodeAgent: {str(e)}")
                logger.error(traceback.format_exc())
                results["code_analysis"] = f"Не удалось выполнить анализ кода: {str(e)}"
            
            # Анализ тест-кейсов
            logger.info("Calling TestCasesAgent")
            try:
                test_cases_analysis = self.test_cases_agent.analyze_test_cases(test_cases_text, requirements_text)
                results["test_cases_analysis"] = test_cases_analysis
                logger.info("TestCasesAgent completed successfully")
            except Exception as e:
                logger.error(f"Error in TestCasesAgent: {str(e)}")
                logger.error(traceback.format_exc())
                results["test_cases_analysis"] = f"Не удалось выполнить анализ тест-кейсов: {str(e)}"
            
            # Анализ документации, если она предоставлена
            if documentation_text and documentation_text.strip():
                logger.info("Calling DocumentationAgent")
                try:
                    doc_analysis = self.documentation_agent.analyze_documentation(documentation_text, requirements=requirements_text, code=code_text)
                    results["documentation_analysis"] = doc_analysis
                    logger.info("DocumentationAgent completed successfully")
                except Exception as e:
                    logger.error(f"Error in DocumentationAgent: {str(e)}")
                    logger.error(traceback.format_exc())
                    results["documentation_analysis"] = f"Не удалось выполнить анализ документации: {str(e)}"
            else:
                results["documentation_analysis"] = "Документация не предоставлена."
            
            # Оценка соответствия кода требованиям
            logger.info("Evaluating compliance")
            try:
                # Генерируем данные о соответствии кода требованиям через запрос к GigaChat
                prompt = f"""
                Проанализируй соответствие кода требованиям и тестам на основе следующих данных:
                
                ## Анализ требований
                {results.get("requirements_analysis", "")[:2000]}
                
                ## Анализ кода
                {results.get("code_analysis", "")[:2000]}
                
                ## Анализ тестов
                {results.get("test_cases_analysis", "")[:2000]}
                
                Определи и верни следующие метрики:
                1. Процент соответствия кода требованиям (от 0 до 100)
                2. Процент соответствия тестов требованиям (от 0 до 100)
                3. Процент соответствия кода тестам (от 0 до 100)
                4. Подробное объяснение каждой метрики
                
                Верни результат в следующем формате:
                {
                  "code_to_requirements_percentage": X,
                  "tests_to_requirements_percentage": Y,
                  "code_to_tests_percentage": Z,
                  "code_to_requirements_explanation": "Подробное объяснение...",
                  "tests_to_requirements_explanation": "Подробное объяснение...",
                  "code_to_tests_explanation": "Подробное объяснение..."
                }
                """
                
                response = self.client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                result_text = response["choices"][0]["message"]["content"]
                compliance_result = json.loads(result_text)
                
                results["compliance_result"] = compliance_result
                logger.info("Compliance evaluation completed successfully")
            except Exception as e:
                logger.error(f"Error in compliance evaluation: {str(e)}")
                logger.error(traceback.format_exc())
                results["compliance_result"] = {
                    "code_to_requirements_percentage": 0,
                    "tests_to_requirements_percentage": 0,
                    "code_to_tests_percentage": 0,
                    "code_to_requirements_explanation": f"Ошибка оценки: {str(e)}",
                    "tests_to_requirements_explanation": f"Ошибка оценки: {str(e)}",
                    "code_to_tests_explanation": f"Ошибка оценки: {str(e)}"
                }
            
            # Оценка потенциальных багов
            logger.info("Estimating potential bugs")
            try:
                bug_estimation = self.bug_estimator_agent.estimate_bugs(
                    requirements=results.get("requirements_analysis", ""),
                    code_analysis=results.get("code_analysis", "")
                )
                results["bug_estimation"] = bug_estimation
                logger.info("Bug estimation completed successfully")
            except Exception as e:
                logger.error(f"Error in bug estimation: {str(e)}")
                logger.error(traceback.format_exc())
                results["bug_estimation"] = {
                    "bug_count": 0,
                    "explanations": f"Не удалось оценить потенциальные баги: {str(e)}",
                    "detailed_bugs": []
                }
            
            # Если доступны расширенные функции, создаем визуализации и рекомендации
            if ENHANCED_FEATURES_AVAILABLE:
                try:
                    # Генерация визуализаций
                    logger.info("Generating visualizations")
                    charts = self.visualization_engine.generate_all_charts(results)
                    results["visualizations"] = charts
                    
                    # Сохранение визуализаций в файл JSON
                    with open("output/visualizations/charts_data.json", 'w', encoding='utf-8') as f:
                        json.dump({k: {p: v[p] for p in ['html_path', 'img_path']} for k, v in charts.items() if v}, f, ensure_ascii=False, indent=2)
                    
                    logger.info("Visualizations generated successfully")
                except Exception as e:
                    logger.error(f"Error generating visualizations: {str(e)}")
                    logger.error(traceback.format_exc())
                    results["visualizations"] = {}
                
                try:
                    # Анализ рекомендаций из результатов анализа
                    logger.info("Processing recommendations")
                    
                    # Извлекаем рекомендации из результатов анализа
                    rec_sources = [
                        results.get("requirements_analysis", ""),
                        results.get("code_analysis", ""),
                        results.get("test_cases_analysis", ""),
                        results.get("documentation_analysis", "")
                    ]
                    
                    for source in rec_sources:
                        if source and isinstance(source, str) and len(source) > 50:
                            self.recommendation_engine.parse_recommendations_from_text(source)
                    
                    # Если у нас есть данные о безопасности, добавляем рекомендации по ним
                    if "security_analysis" in results and "vulnerabilities" in results["security_analysis"]:
                        for vuln in results["security_analysis"]["vulnerabilities"]:
                            if isinstance(vuln, dict):
                                self.recommendation_engine.add_recommendation(Recommendation(
                                    text=f"Устранить уязвимость: {vuln.get('description', 'Unknown vulnerability')}",
                                    priority=("CRITICAL" if vuln.get("severity") == "Критическая" else
                                             "HIGH" if vuln.get("severity") == "Высокая" else
                                             "MEDIUM" if vuln.get("severity") == "Средняя" else
                                             "LOW"),
                                    recommendation_type="SECURITY",
                                    affected_code=[vuln.get("file_path", "")] if vuln.get("file_path") else [],
                                    mitigation=vuln.get("mitigation", "Исправьте уязвимость согласно рекомендациям.")
                                ))
                    
                    # Генерируем отчет с рекомендациями
                    recommendations_report = self.recommendation_engine.to_markdown()
                    results["recommendations"] = {
                        "report": recommendations_report,
                        "items": [rec.to_dict() for rec in self.recommendation_engine.get_prioritized_recommendations()]
                    }
                    
                    # Сохраняем рекомендации в файлы
                    with open("output/reports/recommendations.md", 'w', encoding='utf-8') as f:
                        f.write(recommendations_report)
                    
                    self.recommendation_engine.save_to_file("output/reports/recommendations.json")
                    
                    logger.info(f"Generated {len(self.recommendation_engine.recommendations)} recommendations")
                except Exception as e:
                    logger.error(f"Error processing recommendations: {str(e)}")
                    logger.error(traceback.format_exc())
                    results["recommendations"] = {
                        "report": f"# Ошибка обработки рекомендаций\n\nПроизошла ошибка при обработке рекомендаций: {str(e)}",
                        "items": []
                    }
            
            # Формирование итогового отчета
            logger.info("Generating final report")
            try:
                # Если у нас есть визуализации, добавляем их в отчет
                visualization_data = None
                if ENHANCED_FEATURES_AVAILABLE and "visualizations" in results and results["visualizations"]:
                    visualization_data = results["visualizations"]
                
                # Генерируем отчет с учетом новых данных
                final_report = self.final_report_agent.generate_report(results)
                
                # Если у нас есть визуализации, но они не были включены, добавляем их в отчет сейчас
                if ENHANCED_FEATURES_AVAILABLE and visualization_data:
                    # Проверяем, есть ли в отчете визуализации
                    if "![" not in final_report and visualization_data:
                        # Добавляем визуализации в конец отчета
                        compliance_chart = visualization_data.get("compliance")
                        requirements_chart = visualization_data.get("requirements")
                        bugs_chart = visualization_data.get("bugs")
                        
                        viz_section = "\n\n## Визуализация результатов анализа\n\n"
                        
                        if compliance_chart:
                            viz_section += "### Соответствие требованиям\n\n"
                            viz_section += f"![Соответствие требованиям]({compliance_chart['img_path']})\n\n"
                        
                        if requirements_chart:
                            viz_section += "### Анализ требований\n\n"
                            viz_section += f"![Анализ требований]({requirements_chart['img_path']})\n\n"
                        
                        if bugs_chart:
                            viz_section += "### Анализ багов\n\n"
                            viz_section += f"![Анализ багов]({bugs_chart['img_path']})\n\n"
                        
                        final_report += viz_section
                
                # Сохраняем итоговый отчет
                with open("output/reports/final_report.md", 'w', encoding='utf-8') as f:
                    f.write(final_report)
                
                logger.info("Final report generated successfully")
            except Exception as e:
                logger.error(f"Error generating final report: {str(e)}")
                logger.error(traceback.format_exc())
                final_report = f"""
                # Ошибка при формировании итогового отчета
                
                Произошла ошибка при формировании итогового отчета: {str(e)}
                
                ## Доступные результаты анализа:
                
                - Анализ требований: {"Выполнен успешно" if "requirements_analysis" in results and "Не удалось" not in results["requirements_analysis"] else "Ошибка"}
                - Анализ кода: {"Выполнен успешно" if "code_analysis" in results and "Не удалось" not in results["code_analysis"] else "Ошибка"}
                - Анализ тест-кейсов: {"Выполнен успешно" if "test_cases_analysis" in results and "Не удалось" not in results["test_cases_analysis"] else "Ошибка"}
                - Анализ документации: {"Выполнен успешно" if "documentation_analysis" in results and "Не удалось" not in results["documentation_analysis"] else "Ошибка"}
                - Оценка соответствия: {"Выполнен успешно" if "compliance_result" in results and isinstance(results["compliance_result"], dict) and "Ошибка" not in results["compliance_result"].get("code_to_requirements_explanation", "") else "Ошибка"}
                - Оценка багов: {"Выполнен успешно" if "bug_estimation" in results and "explanations" in results.get("bug_estimation", {}) and "Не удалось" not in results.get("bug_estimation", {}).get("explanations", "") else "Ошибка"}
                """
            
            # Сохраняем все результаты в JSON
            try:
                # Создаем копию результатов без больших текстовых полей для сохранения
                serializable_results = {}
                for k, v in results.items():
                    if isinstance(v, dict):
                        serializable_results[k] = v.copy()
                    else:
                        # Сокращаем большие текстовые поля
                        if isinstance(v, str) and len(v) > 1000:
                            serializable_results[k] = v[:1000] + "... [truncated]"
                        else:
                            serializable_results[k] = v
                
                # Сохраняем результаты в файл
                with open("output/analysis_results.json", 'w', encoding='utf-8') as f:
                    json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error saving results to JSON: {str(e)}")
            
            return final_report, results.get("bug_estimation", {"bug_count": 0, "explanations": "Не удалось оценить баги", "detailed_bugs": []})
            
        except Exception as e:
            logger.error(f"Error in aggregation process: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Возвращаем базовый отчет с информацией об ошибке
            error_report = f"""
            # Ошибка при анализе
            
            Произошла ошибка при выполнении анализа: {str(e)}
            
            ## Исходные данные для анализа:
            
            - Требования: {len(requirements_text)} символов
            - Код: {len(code_text)} символов
            - Тест-кейсы: {len(test_cases_text)} символов
            - Документация: {len(documentation_text)} символов
            
            Пожалуйста, попробуйте повторить анализ или сократите объем входных данных.
            """
            
            bug_info = {
                "bug_count": 0,
                "explanations": f"Не удалось выполнить анализ из-за ошибки: {str(e)}",
                "detailed_bugs": []
            }
            
            return error_report, bug_info
        
    def format_detailed_bugs(self, detailed_bugs: list) -> str:
        """
        Форматирует список детальной информации о багах в удобочитаемый текст
        """
        if not detailed_bugs:
            return """## Анализ потенциальных багов

В представленном коде не обнаружено несоответствий требованиям. Код корректно реализует все указанные функциональные требования.
"""
            
        formatted_text = """## Анализ потенциальных багов\n\n"""
        for i, bug in enumerate(detailed_bugs, 1):
            formatted_text += f"### Баг #{i}\n\n"
            
            if bug.get("описание"):
                formatted_text += f"**Описание:** {bug.get('описание')}\n\n"
                
            if bug.get("серьезность"):
                formatted_text += f"**Серьезность:** {bug.get('серьезность')}\n\n"
                
            if bug.get("где в коде"):
                formatted_text += f"**Расположение в коде:** {bug.get('где в коде')}\n\n"
                
            if bug.get("причина"):
                formatted_text += f"**Причина возникновения:** {bug.get('причина')}\n\n"
                
            if bug.get("влияние"):
                formatted_text += f"**Влияние на систему:** {bug.get('влияние')}\n\n"
                
            if bug.get("рекомендации"):
                formatted_text += f"**Рекомендации по исправлению:** {bug.get('рекомендации')}\n\n"
                
            formatted_text += "---\n\n"
            
        return formatted_text
