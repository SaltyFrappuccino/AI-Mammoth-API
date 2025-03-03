# main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import sys
import os
import asyncio
import requests
import concurrent.futures
from agents import (
    RequirementsAgent,
    DocumentationAgent,
    TestCasesAgent,
    CodeAgent,
    BugAgent,
    ReportAgent
)

# Настраиваем логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Only log to console
    ]
)
logger: logging.Logger = logging.getLogger(__name__)

# Отключаем предупреждения SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic модели ответа
class BugDetail(BaseModel):
    description: str
    severity: str
    location: str
    cause: str
    impact: str
    recommendations: str

class AnalysisResponse(BaseModel):
    final_report: str
    bugs_count: int
    bugs_explanations: str
    detailed_bugs: List[BugDetail] = []
    enhanced_features_available: bool = False
    error_details: Optional[Dict] = None

# Инициализация агентов
client_id = os.getenv("GIGACHAT_CLIENT_ID")
client_secret = os.getenv("GIGACHAT_CLIENT_SECRET")
agents = {
    "requirements": RequirementsAgent(client_id, client_secret),
    "documentation": DocumentationAgent(client_id, client_secret),
    "testcases": TestCasesAgent(client_id, client_secret),
    "code": CodeAgent(client_id, client_secret),
    "bugs": BugAgent(client_id, client_secret),
    "report": ReportAgent(client_id, client_secret)
}

@app.post("/analyze", response_model=AnalysisResponse)
async def perform_analysis(request: dict):
    logger.info("Получен новый запрос на анализ")
    analysis_results = {"detailed_bugs": [], "testcases": "", "requirements": "", "code": "", "documentation": "", "bugs": ""}

    try:
        tc_analysis = agents["testcases"].execute(request.get("testcases", ""))
        analysis_results["detailed_bugs"].extend(tc_analysis.get("bugs", []))
        analysis_results["testcases"] = (tc_analysis['choices'][0]['message']['content'])
        
        req_analysis = agents["requirements"].execute(request.get("requirements", ""))
        analysis_results["detailed_bugs"].extend(req_analysis.get("bugs", []))
        analysis_results["requirements"] = (req_analysis['choices'][0]['message']['content'])

        
        code_analysis = agents["code"].execute(request.get("code", ""))
        analysis_results["detailed_bugs"].extend(code_analysis.get("bugs", []))
        analysis_results["code"] = (code_analysis['choices'][0]['message']['content'])

        doc_analysis = agents["documentation"].execute(request.get("documentation", ""))
        analysis_results["detailed_bugs"].extend(doc_analysis.get("bugs", []))
        analysis_results["documentation"] = (doc_analysis['choices'][0]['message']['content'])
        
        bug_analysis = agents["bugs"].execute(analysis_results)
        analysis_results["bugs"] = (bug_analysis.get("bugs", []))
        # Анализ кода

        
        # Формирование отчета
        final_report = agents["report"].execute(analysis_results)
        
        return AnalysisResponse(
            final_report=final_report['choices'][0]['message']['content'],
            bugs_count=len(analysis_results["detailed_bugs"]),
            bugs_explanations="Обнаружены следующие проблемы",
            detailed_bugs=analysis_results["detailed_bugs"]
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Сетевая ошибка: {str(e)}")
        return AnalysisResponse(
            final_report="Ошибка анализа",
            bugs_count=0,
            bugs_explanations=f"Сетевая ошибка: {str(e)}",
            error_details={"type": "network", "message": str(e)}
        )
    except asyncio.TimeoutError:
        logger.error("Таймаут анализа")
        return AnalysisResponse(
            final_report="Таймаут анализа",
            bugs_count=0,
            bugs_explanations="Превышено время ожидания",
            error_details={"type": "timeout", "message": "60 секунд"}
        )
    except Exception as e:
        logger.error(f"Внутренняя ошибка: {str(e.value)}")
        return AnalysisResponse(
            final_report="Внутренняя ошибка",
            bugs_count=0,
            bugs_explanations=f"Ошибка сервера: {str(e)}",
            error_details={"type": "server", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)