# agents/compliance_evaluator.py
from langchain_core.messages import HumanMessage, SystemMessage
from config import llm


def evaluate_code_compliance(requirements_analysis: str, test_cases_analysis: str, code_analysis: str) -> dict:
    """
    Оценивает процент соответствия между требованиями, кодом и тест-кейсами.
    Возвращает три метрики:
    1. Соответствие кода требованиям
    2. Соответствие тест-кейсов требованиям
    3. Покрытие кода тест-кейсами
    """
    system_prompt = """
    Ты эксперт по анализу качества программного обеспечения. Твоя задача - оценить соответствие
    между тремя компонентами: требованиями к ПО, реализованным кодом, и тест-кейсами.
    
    На основе предоставленных результатов анализа трех компонентов, ты должен:
    1. Оценить процент соответствия кода требованиям (0-100%)
    2. Оценить процент соответствия тест-кейсов требованиям (0-100%)
    3. Оценить процент покрытия кода тест-кейсами (0-100%)
    
    Для каждой метрики укажи обоснование своей оценки.
    
    Выдай результат в формате JSON с ключами:
    - code_to_requirements_compliance: число от 0 до 100
    - tests_to_requirements_compliance: число от 0 до 100
    - code_to_tests_coverage: число от 0 до 100
    - explanation: строка с объяснением оценок
    """
    
    human_prompt = f"""
    Проанализируй следующие результаты анализа компонентов ПО и оцени соответствие между ними.
    
    === АНАЛИЗ ТРЕБОВАНИЙ ===
    {requirements_analysis}
    
    === АНАЛИЗ КОДА ===
    {code_analysis}
    
    === АНАЛИЗ ТЕСТ-КЕЙСОВ ===
    {test_cases_analysis}
    
    Оцени степень соответствия между требованиями, кодом и тест-кейсами.
    Верни результат в формате JSON.
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    try:
        result = llm(messages).content
        # Извлекаем JSON из ответа
        import json
        import re
        
        # Пытаемся найти JSON в ответе
        json_match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        
        # Пытаемся найти фигурные скобки в ответе
        json_match = re.search(r'({.*})', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
            
        # Пытаемся распарсить JSON
        try:
            compliance_data = json.loads(result)
            # Убедимся, что все необходимые ключи присутствуют
            required_keys = [
                'code_to_requirements_compliance', 
                'tests_to_requirements_compliance', 
                'code_to_tests_coverage',
                'explanation'
            ]
            for key in required_keys:
                if key not in compliance_data:
                    compliance_data[key] = 0 if key != 'explanation' else 'Не удалось получить объяснение'
            
            return compliance_data
        except json.JSONDecodeError:
            return {
                'code_to_requirements_compliance': 0,
                'tests_to_requirements_compliance': 0,
                'code_to_tests_coverage': 0,
                'explanation': f'Не удалось распарсить JSON из ответа: {result}'
            }
    except Exception as e:
        return {
            'code_to_requirements_compliance': 0,
            'tests_to_requirements_compliance': 0,
            'code_to_tests_coverage': 0,
            'explanation': f'Ошибка при выполнении: {str(e)}'
        }


def estimate_bug_count(requirements_text: str, code_text: str, test_cases_text: str, 
                      documentation_text: str, compliance_data: dict) -> dict:
    """
    Оценивает количество потенциальных багов в коде на основе анализа всех компонентов.
    """
    system_prompt = """
    Ты эксперт по анализу качества кода и выявлению потенциальных багов в веб-API, со специализацией 
    на Flask и FastAPI приложениях. Твоя задача - проанализировать предоставленный код, требования, 
    тесты и документацию, а затем оценить следующие метрики:
    
    1. Количество потенциальных багов в коде
    2. Серьезность каждого потенциального бага (критический, высокий, средний, низкий)
    3. Общее качество кода по шкале от 1 до 10
    
    Обрати внимание на:
    - Несоответствия между требованиями и реализацией
    - Отсутствие валидации входных данных
    - Проблемы безопасности (SQL-инъекции, XSS, CSRF и т.д.)
    - Отсутствие обработки ошибок
    - Проблемы с аутентификацией и авторизацией
    - Потенциальные утечки памяти или ресурсов
    - Проблемы с конкурентным доступом
    - Неоптимальные алгоритмы
    
    Выдай результат в формате JSON с ключами:
    - estimated_bugs: число
    - bug_list: массив объектов с ключами "description" и "severity"
    - code_quality_score: число от 1 до 10
    - explanation: строка с объяснением оценок
    """
    
    human_prompt = f"""
    Проанализируй предоставленный код, требования, тесты и документацию и оцени количество потенциальных багов.
    
    === ТРЕБОВАНИЯ ===
    {requirements_text[:5000] if len(requirements_text) > 5000 else requirements_text}
    
    === КОД ===
    {code_text[:7000] if len(code_text) > 7000 else code_text}
    
    === ТЕСТЫ ===
    {test_cases_text[:5000] if len(test_cases_text) > 5000 else test_cases_text}
    
    === ДОКУМЕНТАЦИЯ ===
    {documentation_text[:3000] if len(documentation_text) > 3000 else documentation_text}
    
    === МЕТРИКИ СООТВЕТСТВИЯ ===
    Соответствие кода требованиям: {compliance_data.get('code_to_requirements_compliance', 0)}%
    Соответствие тестов требованиям: {compliance_data.get('tests_to_requirements_compliance', 0)}%
    Покрытие кода тестами: {compliance_data.get('code_to_tests_coverage', 0)}%
    
    Оцени количество потенциальных багов и качество кода.
    Верни результат в формате JSON.
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    try:
        result = llm(messages).content
        # Извлекаем JSON из ответа
        import json
        import re
        
        # Пытаемся найти JSON в ответе
        json_match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        
        # Пытаемся найти фигурные скобки в ответе
        json_match = re.search(r'({.*})', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
            
        # Пытаемся распарсить JSON
        try:
            bug_estimation = json.loads(result)
            # Убедимся, что все необходимые ключи присутствуют
            required_keys = [
                'estimated_bugs', 
                'bug_list', 
                'code_quality_score',
                'explanation'
            ]
            for key in required_keys:
                if key not in bug_estimation:
                    if key == 'bug_list':
                        bug_estimation[key] = []
                    elif key == 'explanation':
                        bug_estimation[key] = 'Не удалось получить объяснение'
                    else:
                        bug_estimation[key] = 0
            
            return bug_estimation
        except json.JSONDecodeError:
            return {
                'estimated_bugs': 0,
                'bug_list': [],
                'code_quality_score': 0,
                'explanation': f'Не удалось распарсить JSON из ответа: {result}'
            }
    except Exception as e:
        return {
            'estimated_bugs': 0,
            'bug_list': [],
            'code_quality_score': 0,
            'explanation': f'Ошибка при выполнении: {str(e)}'
        }


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
