# config.py
import os

class Config:
    """
    Класс для конфигурации приложения
    """
    
    # GigaChat API
    GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY", "")
    GIGACHAT_API_BASE = os.getenv("GIGACHAT_API_BASE", "https://gigachat.devices.sberbank.ru")
    AUTH_URL = os.getenv("AUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
    GIGA_URL = os.getenv("GIGA_URL", "https://gigachat.devices.sberbank.ru/api/v1")
    MODEL_TYPE = os.getenv("MODEL_TYPE", "GigaChat-Max")
    
    # Настройки сервера
    PORT = int(os.getenv("PORT", "8080"))
    
    # Настройки логирования
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Настройки анализа
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Настройки безопасности
    ANALYZE_SECURITY = os.getenv("ANALYZE_SECURITY", "True").lower() in ["true", "1", "yes"]
    
    # Пути к файлам
    REPORTS_DIR = os.getenv("REPORTS_DIR", "output/reports")
    VISUALIZATIONS_DIR = os.getenv("VISUALIZATIONS_DIR", "output/visualizations")

config = Config()