# agents/analysis_evaluator_agent.py
from langchain_core.messages import HumanMessage, SystemMessage
from config import llm


class AnalysisEvaluatorAgent:
    def __init__(self):
        self.system_prompt = (
            "Ты аналитик качества работы ассистента. Оцени итоговый отчёт, составленный на основе данных агентов, "
            "по следующим критериям: соответствие требований, корректность реализации кода, полнота тестирования и точность документации. "
            "Верни краткую оценку с комментариями, насколько точно выполнен анализ. Если обнаружены несоответствия, укажи, что именно следует исправить."
        )

    def call(self, final_report: str) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=final_report)
        ]
        response = llm.invoke(messages, function_call="auto")
        return response.content
