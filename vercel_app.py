from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-mammoth-api")

app = FastAPI(
    title="AI Mammoth API", 
    description="A lightweight API for code analysis",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ErrorDetails(BaseModel):
    error: str
    error_type: str
    details: Optional[Dict[str, Any]] = None

class AnalysisRequest(BaseModel):
    requirements: str
    code: str
    test_cases: str
    documentation: str = ""
    analyze_security: bool = True

class AnalysisResponse(BaseModel):
    message: str
    request_id: str

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    Endpoint for requesting code analysis.
    In the Vercel deployment, this is a lightweight proxy that returns a request ID.
    The actual processing is done by your full server elsewhere.
    """
    try:
        # Generate a request ID
        request_id = f"req_{os.urandom(4).hex()}"
        
        # In a production environment, you would queue this request
        # to be processed by your full server or send it to a message queue

        return AnalysisResponse(
            message="Analysis request received. Due to Vercel serverless function size limits, the analysis will be processed on a separate server.",
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=ErrorDetails(
                error="Internal server error",
                error_type="SERVER_ERROR",
                details={"message": str(e)}
            ).dict()
        )

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API."""
    return {
        "status": "ok",
        "message": "This is a lightweight version of the AI Mammoth API running on Vercel",
        "version": "2.0.0"
    } 