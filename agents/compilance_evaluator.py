# agents/compliance_evaluator.py
from langchain_core.messages import HumanMessage, SystemMessage
from config import llm


def evaluate_code_compliance(requirements_analysis: str, test_cases_analysis: str, code_analysis: str) -> dict:
    """
    Оценивает процент соответствия между требованиями, кодом и тест-кейсами.
    Возвращает три метрики:
    1. Соответствие кода требованиям
    2. Соответствие тест-кейсов требованиям  
    3. Соответствие кода тест-кейсам
    
    Также возвращает качественную оценку для каждой метрики.
    """
    system_prompt = """
    Ты эксперт по оценке качества и соответствия программного кода с глубоким пониманием веб-API, REST API,
    и современных практик бэкенд-разработки. Твоя задача - провести детальный анализ соответствия между 
    требованиями к ПО, реализацией в коде и тестовыми сценариями.
    
    Необходимо вернуть три отдельные метрики (процентные значения от 0 до 100):
    
    1. code_to_requirements_percentage: Насколько полно код реализует требования
       - Учитывай, что RESTful API могут полностью реализовывать требования без пользовательского интерфейса
       - Если код содержит эндпоинты для создания, чтения, обновления и удаления ресурсов (CRUD), 
         это может полностью удовлетворять соответствующим требованиям
       - Если требуется JWT-аутентификация и код ее реализует, считай это полным соответствием
       
    2. tests_to_requirements_percentage: Насколько полно тесты покрывают требования
       - Автоматизированные тесты API (например, с использованием pytest) являются валидными
       - Если тесты проверяют корректность выполнения операций API, считай это покрытием требования
       
    3. code_to_tests_percentage: Насколько код соответствует тестам
    
    Для каждой метрики необходимо дать краткое текстовое пояснение.
    
    Твой ответ должен быть в формате:
    
    code_to_requirements_percentage: X%
    code_to_requirements_explanation: краткое пояснение
    
    tests_to_requirements_percentage: Y%
    tests_to_requirements_explanation: краткое пояснение
    
    code_to_tests_percentage: Z%
    code_to_tests_explanation: краткое пояснение
    
    Где X, Y, Z - числа от 0 до 100.
    
    ВАЖНО: 
    1. Не усредняй и не упрощай анализ. Если код полностью реализует все требования, 
       соответствующая метрика должна быть 100%.
    2. Понимай, что серверное API на Flask или FastAPI является полноценной реализацией серверной части,
       и если оно реализует требования к API, это засчитывается как полное соответствие.
    3. Используй фактические данные из анализа кода и тестов. Если код реализует JWT-аутентификацию,
       создание, чтение, обновление и поиск задач, и это требовалось - это значит полное соответствие требованиям.
    4. Учитывай, что REST API методы POST, GET, PUT, DELETE для работы с ресурсами являются стандартной
       и полноценной реализацией CRUD-операций.
    """

    analysis_text = (
            "Анализ требований:\n" + requirements_analysis + "\n\n" +
            "Анализ тест-кейсов:\n" + test_cases_analysis + "\n\n" +
            "Анализ кода:\n" + code_analysis + "\n\n" +
            "На основе этого анализа, оцени три метрики соответствия указанные в инструкции. "
            "Подробно объясни свою оценку для каждой метрики."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=analysis_text)
    ]

    response = llm.invoke(messages, function_call="none")
    result_text = response.content.strip()
    
    # Извлечение процентных значений и пояснений
    results = {}
    
    try:
        # Соответствие кода требованиям
        if "code_to_requirements_percentage:" in result_text:
            code_req_text = result_text.split("code_to_requirements_percentage:")[1].split("\n")[0].strip()
            results["code_to_requirements_percentage"] = int(''.join(filter(str.isdigit, code_req_text)))
        else:
            results["code_to_requirements_percentage"] = 0
            
        # Соответствие тестов требованиям
        if "tests_to_requirements_percentage:" in result_text:
            tests_req_text = result_text.split("tests_to_requirements_percentage:")[1].split("\n")[0].strip()
            results["tests_to_requirements_percentage"] = int(''.join(filter(str.isdigit, tests_req_text)))
        else:
            results["tests_to_requirements_percentage"] = 0
            
        # Соответствие кода тестам
        if "code_to_tests_percentage:" in result_text:
            code_tests_text = result_text.split("code_to_tests_percentage:")[1].split("\n")[0].strip()
            results["code_to_tests_percentage"] = int(''.join(filter(str.isdigit, code_tests_text)))
        else:
            results["code_to_tests_percentage"] = 0
            
        # Пояснения
        if "code_to_requirements_explanation:" in result_text:
            results["code_to_requirements_explanation"] = result_text.split("code_to_requirements_explanation:")[1].split("\n\n")[0].strip()
            
        if "tests_to_requirements_explanation:" in result_text:
            results["tests_to_requirements_explanation"] = result_text.split("tests_to_requirements_explanation:")[1].split("\n\n")[0].strip()
            
        if "code_to_tests_explanation:" in result_text:
            results["code_to_tests_explanation"] = result_text.split("code_to_tests_explanation:")[1].split("\n\n")[0].strip()
            
    except Exception as e:
        # В случае ошибки разбора вернем значения по умолчанию
        results = {
            "code_to_requirements_percentage": 0,
            "tests_to_requirements_percentage": 0,
            "code_to_tests_percentage": 0,
            "code_to_requirements_explanation": f"Ошибка анализа: {str(e)}",
            "tests_to_requirements_explanation": f"Ошибка анализа: {str(e)}",
            "code_to_tests_explanation": f"Ошибка анализа: {str(e)}"
        }
    
    return results


evaluate_code_compliance_schema = {
    "name": "evaluate_code_compliance",
    "description": "Оценивает процент соответствия между кодом, требованиями и тест-кейсами.",
    "parameters": {
        "type": "object",
        "properties": {
            "requirements_analysis": {
                "type": "string",
                "description": "Анализ требований."
            },
            "test_cases_analysis": {
                "type": "string",
                "description": "Анализ тест-кейсов."
            },
            "code_analysis": {
                "type": "string",
                "description": "Анализ кода."
            }
        },
        "required": [
            "requirements_analysis",
            "test_cases_analysis",
            "code_analysis"
        ]
    },
    "return_parameters": {
        "type": "object",
        "properties": {
            "code_to_requirements_percentage": {
                "type": "number",
                "description": "Процент соответствия кода требованиям (от 0 до 100)."
            },
            "tests_to_requirements_percentage": {
                "type": "number",
                "description": "Процент соответствия тестов требованиям (от 0 до 100)."
            },
            "code_to_tests_percentage": {
                "type": "number",
                "description": "Процент соответствия кода тестам (от 0 до 100)."
            },
            "code_to_requirements_explanation": {
                "type": "string",
                "description": "Пояснение к оценке соответствия кода требованиям."
            },
            "tests_to_requirements_explanation": {
                "type": "string", 
                "description": "Пояснение к оценке соответствия тестов требованиям."
            },
            "code_to_tests_explanation": {
                "type": "string",
                "description": "Пояснение к оценке соответствия кода тестам."
            }
        },
        "required": [
            "code_to_requirements_percentage",
            "tests_to_requirements_percentage", 
            "code_to_tests_percentage"
        ]
    }
}
