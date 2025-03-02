@echo off
ECHO "==== Попытка сборки Docker-образа ===="
ECHO.

ECHO "1. Попытка сборки с использованием Alpine Linux (обычно самый быстрый и надежный)"
docker build -t ai-mammoth-api -f Dockerfile.minimal .
IF %ERRORLEVEL% EQU 0 (
    ECHO "Сборка успешна! Запускаем контейнер..."
    docker run -p 8080:8080 --env-file .env ai-mammoth-api
    GOTO :EOF
)

ECHO.
ECHO "2. Попытка сборки с использованием Ubuntu (более стабильные репозитории)"
docker build -t ai-mammoth-api -f Dockerfile.ubuntu .
IF %ERRORLEVEL% EQU 0 (
    ECHO "Сборка успешна! Запускаем контейнер..."
    docker run -p 8080:8080 --env-file .env ai-mammoth-api
    GOTO :EOF
)

ECHO.
ECHO "3. Попытка сборки с использованием базового Debian-образа"
docker build -t ai-mammoth-api -f Dockerfile.alternative .
IF %ERRORLEVEL% EQU 0 (
    ECHO "Сборка успешна! Запускаем контейнер..."
    docker run -p 8080:8080 --env-file .env ai-mammoth-api
    GOTO :EOF
)

ECHO.
ECHO "4. Последняя попытка с использованием модифицированного Dockerfile"
docker build -t ai-mammoth-api .
IF %ERRORLEVEL% EQU 0 (
    ECHO "Сборка успешна! Запускаем контейнер..."
    docker run -p 8080:8080 --env-file .env ai-mammoth-api
    GOTO :EOF
)

ECHO.
ECHO "Все попытки сборки завершились неудачно."
ECHO "Попробуйте запустить приложение без Docker:"
ECHO "1. pip install -r requirements.txt"
ECHO "2. python -m main"
PAUSE 