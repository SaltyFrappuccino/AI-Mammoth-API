from fastapi import FastAPI, HTTPException, Response, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import random
from aggregator import Aggregator
from semantic_db import SemanticDB
from config import embeddings
import logging
import traceback
import json
import sys
import os
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api.log')
    ]
)
logger = logging.getLogger("analysis-api")

app = FastAPI(
    title="Анализатор Соответствия Требованиям", 
    description="API для анализа требований и кода на их соответствие",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем директории для статических файлов и результатов
os.makedirs("output", exist_ok=True)
os.makedirs("output/visualizations", exist_ok=True)
os.makedirs("output/reports", exist_ok=True)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="output"), name="static")

class AnalysisRequest(BaseModel):
    requirements: str
    code: str
    test_cases: str
    documentation: str = ""
    semantic_db: Dict = {}
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
    html_path: str
    img_path: str
    base64: Optional[str] = None

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
    report_path: str
    visualizations: Dict[str, Visualization] = {}
    security_report: Optional[str] = None
    recommendations_report: Optional[str] = None

class ErrorDetails(BaseModel):
    error: str
    error_type: str
    stack_trace: Optional[str] = None
    module: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    final_report: str
    bugs_count: int
    bugs_explanations: str
    detailed_bugs: List[BugDetail] = []
    # Новые поля для расширенного ответа
    enhanced_features_available: bool = False
    recommendations: List[RecommendationDetail] = []
    visualizations: Dict[str, Visualization] = {}
    security_vulnerabilities: List[SecurityVulnerabilityDetail] = []
    enhanced_report: Optional[EnhancedReport] = None
    error_details: Optional[ErrorDetails] = None

def perform_analysis(requirements: str, code: str, test_cases: str, documentation: str, semantic_db: Dict, analyze_security: bool = True) -> tuple:
    logger.info("Starting analysis process")
    
    try:
        # Check if semantic_db is dictionary format or old format with "documents" key
        if isinstance(semantic_db, dict) and "documents" not in semantic_db:
            logger.info(f"Using new semantic_db format with {len(semantic_db)} services")
            documents = semantic_db  # New format: dictionary of services
        else:
            logger.info("Using old semantic_db format with documents list")
            documents = semantic_db.get("documents", [])
        
        logger.info(f"Initializing SemanticDB with {len(documents)} documents")
        semantic_db_instance = SemanticDB(embeddings=embeddings, documents=documents)
        
        logger.info("Initializing Aggregator")
        aggregator = Aggregator(semantic_db=semantic_db_instance)
        
        logger.info("Calling aggregator.aggregate method")
        final_report, bug_estimation = aggregator.aggregate(
            requirements_text=requirements,
            code_text=code,
            test_cases_text=test_cases,
            documentation_text=documentation,
            analyze_security=analyze_security
        )
        logger.info("Analysis completed successfully")
        return final_report, bug_estimation, aggregator
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    logger.info("Received analysis request")
    
    try:
        # Log the request data (sizes only for privacy)
        logger.info(f"Request data sizes: requirements={len(request.requirements)}, " +
                   f"code={len(request.code)}, test_cases={len(request.test_cases)}, " +
                   f"documentation={len(request.documentation)}, " +
                   f"semantic_db={len(json.dumps(request.semantic_db))}")
        
        # Проверяем, доступны ли расширенные функции
        try:
            from visualization import VisualizationEngine
            from recommender import RecommendationEngine
            from security_analyzer import SecurityAnalyzer
            enhanced_features_available = True
            logger.info("Enhanced features are available")
        except ImportError:
            enhanced_features_available = False
            logger.warning("Enhanced features are not available")
        
        final_report, bug_estimation, aggregator = perform_analysis(
            requirements=request.requirements,
            code=request.code,
            test_cases=request.test_cases,
            documentation=request.documentation,
            semantic_db=request.semantic_db,
            analyze_security=request.analyze_security
        )
        
        # Преобразуем детальную информацию о багах в нужный формат
        detailed_bugs = []
        for bug in bug_estimation.get("detailed_bugs", []):
            detailed_bugs.append(BugDetail(
                description=bug.get("описание", ""),
                severity=bug.get("серьезность", ""),
                location=bug.get("где в коде", ""),
                cause=bug.get("причина", ""),
                impact=bug.get("влияние", ""),
                recommendations=bug.get("рекомендации", "")
            ))
        
        # Расширенный ответ с новыми функциями
        enhanced_report = None
        recommendations = []
        visualizations = {}
        security_vulnerabilities = []
        
        if enhanced_features_available:
            # Получаем визуализации, если они есть
            if hasattr(aggregator, 'visualization_engine') and os.path.exists("output/visualizations/charts_data.json"):
                try:
                    with open("output/visualizations/charts_data.json", 'r', encoding='utf-8') as f:
                        charts_data = json.load(f)
                    
                    for chart_type, chart_paths in charts_data.items():
                        if chart_paths.get('img_path') and os.path.exists(chart_paths['img_path']):
                            visualizations[chart_type] = Visualization(
                                html_path=chart_paths.get('html_path', ''),
                                img_path=chart_paths.get('img_path', '')
                            )
                except Exception as e:
                    logger.error(f"Error loading visualizations: {str(e)}")
            
            # Получаем рекомендации, если они есть
            if hasattr(aggregator, 'recommendation_engine') and os.path.exists("output/reports/recommendations.json"):
                try:
                    with open("output/reports/recommendations.json", 'r', encoding='utf-8') as f:
                        recs_data = json.load(f)
                    
                    for rec_data in recs_data.get('recommendations', []):
                        recommendations.append(RecommendationDetail(
                            text=rec_data.get('text', ''),
                            priority=rec_data.get('priority', 'MEDIUM'),
                            priority_level=rec_data.get('priority_level', 3),
                            type=rec_data.get('type', 'Другое'),
                            affected_requirements=rec_data.get('affected_requirements', []),
                            affected_code=rec_data.get('affected_code', []),
                            effort_estimate=rec_data.get('effort_estimate'),
                            expected_impact=rec_data.get('expected_impact')
                        ))
                except Exception as e:
                    logger.error(f"Error loading recommendations: {str(e)}")
            
            # Получаем уязвимости безопасности, если они есть
            if hasattr(aggregator, 'security_analyzer') and os.path.exists("output/reports/security_report.json"):
                try:
                    with open("output/reports/security_report.json", 'r', encoding='utf-8') as f:
                        security_data = json.load(f)
                    
                    for vuln_data in security_data.get('vulnerabilities', []):
                        security_vulnerabilities.append(SecurityVulnerabilityDetail(
                            type=vuln_data.get('type', ''),
                            severity=vuln_data.get('severity', ''),
                            description=vuln_data.get('description', ''),
                            file_path=vuln_data.get('file_path'),
                            line_number=vuln_data.get('line_number'),
                            code_snippet=vuln_data.get('code_snippet'),
                            mitigation=vuln_data.get('mitigation'),
                            cwe_id=vuln_data.get('cwe_id')
                        ))
                except Exception as e:
                    logger.error(f"Error loading security vulnerabilities: {str(e)}")
            
            # Формируем объект с информацией о путях к отчетам
            if os.path.exists("output/reports/final_report.md"):
                enhanced_report = EnhancedReport(
                    report_path="/static/reports/final_report.md",
                    visualizations=visualizations
                )
                
                if os.path.exists("output/reports/security_report.md"):
                    enhanced_report.security_report = "/static/reports/security_report.md"
                
                if os.path.exists("output/reports/recommendations.md"):
                    enhanced_report.recommendations_report = "/static/reports/recommendations.md"
        
        logger.info("Returning successful response")
        return {
            "final_report": final_report, 
            "bugs_count": bug_estimation["bug_count"],
            "bugs_explanations": bug_estimation["explanations"],
            "detailed_bugs": detailed_bugs,
            "enhanced_features_available": enhanced_features_available,
            "recommendations": recommendations,
            "visualizations": visualizations,
            "security_vulnerabilities": security_vulnerabilities,
            "enhanced_report": enhanced_report
        }
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Error during analysis: {error_type}: {error_msg}")
        logger.error(stack_trace)
        
        # Create detailed error response
        error_details = ErrorDetails(
            error=error_msg,
            error_type=error_type,
            stack_trace=stack_trace,
            module=e.__class__.__module__,
            details={"location": "analyze_endpoint"}
        )
        
        return {
            "final_report": f"Ошибка при анализе: {error_msg}",
            "bugs_count": 0,
            "bugs_explanations": f"Не удалось выполнить анализ из-за ошибки: {error_msg}",
            "detailed_bugs": [],
            "enhanced_features_available": False,
            "recommendations": [],
            "visualizations": {},
            "security_vulnerabilities": [],
            "error_details": error_details
        }

@app.get("/reports/{report_name}")
async def get_report(report_name: str):
    """Получает отчет по имени."""
    if ".." in report_name or "/" in report_name:
        raise HTTPException(status_code=400, detail="Invalid report name")
    
    report_path = f"output/reports/{report_name}"
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(report_path)

@app.get("/visualizations/{image_name}")
async def get_visualization(image_name: str):
    """Получает изображение визуализации по имени."""
    if ".." in image_name or "/" in image_name:
        raise HTTPException(status_code=400, detail="Invalid image name")
    
    image_path = f"output/visualizations/{image_name}"
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(image_path)

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API."""
    try:
        # Проверяем наличие расширенных функций
        try:
            from visualization import VisualizationEngine
            from recommender import RecommendationEngine
            from security_analyzer import SecurityAnalyzer
            enhanced_features = True
        except ImportError:
            enhanced_features = False
        
        return {
            "status": "ok",
            "enhanced_features_available": enhanced_features,
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server")
    uvicorn.run(app, host="0.0.0.0", port=8080)
    