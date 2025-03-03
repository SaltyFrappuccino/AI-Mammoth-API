from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import sys
import os
from datetime import datetime
from analysis_engine import AnalysisEngine
from dotenv import load_dotenv

# Настройка минимального логирования только в stdout
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Инициализация API
app = FastAPI(
    title="API Анализа Кода",
    description="API для анализа исходного кода и соответствия требованиям",
    version="2.0.0"
)

# Настройка CORS для разрешения запросов со всех источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем запросы с любых источников
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все HTTP методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешаем все заголовки
    expose_headers=["Content-Disposition"],  # Позволяет клиентам видеть заголовки для скачивания файлов
)

# Загружаем переменные окружения для доступа к GigaChat API
load_dotenv()

# Инициализация анализатора с явной передачей ключа API
analyzer = AnalysisEngine(
    auth_key=os.getenv("GIGACHAT_API_KEY", ""),
    api_base=os.getenv("GIGACHAT_API_BASE", "https://gigachat.devices.sberbank.ru")
)

class AnalysisRequest(BaseModel):
    requirements: str
    code: str
    test_cases: str
    documentation: str = ""
    analyze_security: bool = True

class BugDetail(BaseModel):
    description: str = ""
    severity: str = ""
    location: str = ""
    cause: str = ""
    impact: str = ""
    recommendations: str = ""

class RecommendationDetail(BaseModel):
    text: str
    priority: str
    priority_level: int
    type: str
    affected_requirements: List[str] = []
    affected_code: List[str] = []
    effort_estimate: Optional[str] = None
    expected_impact: Optional[str] = None

class Visualization(BaseModel):
    html_content: str
    base64_image: Optional[str] = None

class SecurityVulnerabilityDetail(BaseModel):
    type: str
    severity: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    mitigation: Optional[str] = None
    cwe_id: Optional[str] = None

class EnhancedReport(BaseModel):
    report_content: str
    visualizations: Dict[str, Visualization] = {}
    security_report: Optional[str] = None
    recommendations_report: Optional[str] = None

class ErrorDetails(BaseModel):
    error: str
    error_type: str
    details: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    final_report: str
    bugs_count: int
    bugs_explanations: str
    detailed_bugs: List[BugDetail] = []
    enhanced_features_available: bool = False
    recommendations: List[RecommendationDetail] = []
    visualizations: Dict[str, Visualization] = {}
    security_vulnerabilities: List[SecurityVulnerabilityDetail] = []
    enhanced_report: Optional[EnhancedReport] = None
    error_details: Optional[ErrorDetails] = None

def perform_analysis(requirements: str, code: str, test_cases: str, documentation: str, analyze_security: bool = True) -> Dict:
    """
    Выполняет анализ требований и кода, используя движок анализа на базе GigaChat API
    """
    print(f"INFO: Запуск анализа с использованием GigaChat API")
    
    try:
        # Выполняем основной анализ
        analysis_results = analyzer.analyze_requirements_and_code(
            requirements=requirements,
            code=code,
            test_cases=test_cases,
            documentation=documentation,
            analyze_security=analyze_security
        )
        
        # Преобразуем результаты для соответствия модели данных API
        # Не используем файловую систему для хранения отчетов и визуализаций
        if "visualizations" in analysis_results:
            for key, visual in analysis_results["visualizations"].items():
                # Заменяем путь к файлу на прямое содержимое
                if isinstance(visual, dict) and "html_path" in visual:
                    # Вместо сохранения в файл, просто храним HTML содержимое
                    visual["html_content"] = visual.get("html_content", "Visualization content")
                    visual["base64_image"] = visual.get("base64", "")
                    # Удаляем ссылки на файлы
                    if "html_path" in visual:
                        del visual["html_path"]
                    if "img_path" in visual:
                        del visual["img_path"]
                    if "base64" in visual:
                        del visual["base64"]
        
        # Если есть enhanced_report, преобразуем его тоже
        if "enhanced_report" in analysis_results and analysis_results["enhanced_report"]:
            # Преобразуем отчет в содержимое, а не путь
            if "report_path" in analysis_results["enhanced_report"]:
                analysis_results["enhanced_report"]["report_content"] = analysis_results["enhanced_report"].get("report_content", 
                                                                    "Enhanced report content")
                del analysis_results["enhanced_report"]["report_path"]
            
            # Преобразуем визуализации внутри enhanced_report
            if "visualizations" in analysis_results["enhanced_report"]:
                for key, visual in analysis_results["enhanced_report"]["visualizations"].items():
                    if isinstance(visual, dict) and "html_path" in visual:
                        visual["html_content"] = visual.get("html_content", "Visualization content")
                        visual["base64_image"] = visual.get("base64", "")
                        # Удаляем ссылки на файлы
                        if "html_path" in visual:
                            del visual["html_path"]
                        if "img_path" in visual:
                            del visual["img_path"]
                        if "base64" in visual:
                            del visual["base64"]
                            
        return analysis_results
    
    except Exception as e:
        print(f"ERROR: Ошибка при выполнении анализа: {str(e)}")
        
        return {
            "final_report": "Произошла ошибка при выполнении анализа",
            "bugs_count": 0,
            "bugs_explanations": f"Ошибка: {str(e)}",
            "detailed_bugs": [],
            "enhanced_features_available": False,
            "error_details": {
                "error": str(e),
                "error_type": "ANALYSIS_ERROR"
            }
        }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    Анализирует требования и код на соответствие, используя GigaChat API
    """
    try:
        print(f"INFO: Получен запрос на анализ")
        
        # Выполняем анализ
        analysis_results = perform_analysis(
            requirements=request.requirements,
            code=request.code,
            test_cases=request.test_cases,
            documentation=request.documentation,
            analyze_security=request.analyze_security
        )
        
        print(f"INFO: Анализ успешно выполнен")
        
        # Возвращаем результаты анализа
        return analysis_results
    
    except Exception as e:
        print(f"ERROR: Ошибка при обработке запроса: {str(e)}")
        
        # Возвращаем ошибку
        return JSONResponse(
            status_code=500,
            content={
                "final_report": "Произошла ошибка при обработке запроса",
                "bugs_count": 0,
                "bugs_explanations": f"Ошибка: {str(e)}",
                "detailed_bugs": [],
                "enhanced_features_available": False,
                "error_details": {
                    "error": str(e),
                    "error_type": "SERVER_ERROR"
                }
            }
        )

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API."""
    try:
        # Проверяем доступность GigaChat API
        from gigachat_client import GigaChatClient
        
        if not os.getenv("GIGACHAT_API_KEY", ""):
            print(f"WARNING: GIGACHAT_API_KEY не найден в переменных окружения")
            is_gigachat_available = False
        else:
            # Создаем клиент с увеличенным числом повторных попыток и таймаутами
            client = GigaChatClient(
                auth_key=os.getenv("GIGACHAT_API_KEY", ""),
                max_retries=3,      # 3 попытки
                retry_delay=0.5,    # Начальная задержка 0.5 секунд
                timeout=10.0        # Таймаут 10 секунд
            )
            
            # Простой запрос для проверки доступности API
            try:
                # Используем меньшее количество токенов для быстрого ответа
                response = client.chat_completion(
                    messages=[{"role": "user", "content": "Привет"}],
                    max_tokens=5,
                    temperature=0.1  # Низкая температура для детерминированного ответа
                )
                is_gigachat_available = bool(response and response.get("choices"))
                print(f"INFO: GigaChat API доступен и отвечает на запросы")
            except Exception as e:
                print(f"ERROR: Ошибка при проверке доступности GigaChat API: {str(e)}")
                is_gigachat_available = False
    except Exception as e:
        print(f"ERROR: Ошибка при проверке доступности GigaChat API: {str(e)}")
        is_gigachat_available = False
    
    return {
        "status": "ok",
        "api_version": "2.0.0",
        "gigachat_api_available": is_gigachat_available,
        "server_time": datetime.now().isoformat(),
        "environment": "serverless" if os.environ.get("VERCEL") else "development"
    }

if __name__ == "__main__":
    import uvicorn
    print(f"INFO: Запуск приложения")
    uvicorn.run(app, host="0.0.0.0", port=8080)
    