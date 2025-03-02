# agents/documentation_agent.py
from agents.base_agent import BaseAgent

class DocumentationAgent(BaseAgent):
    def __init__(self, semantic_db=None):
        system_prompt = (
            "Ты эксперт по системной документации. Анализируй документацию с использованием базы знаний. "
            "Выдели важные детали и верни структурированный отчет."
        )
        super().__init__("DocumentationAgent", system_prompt)
        self.semantic_db = semantic_db

    def call(self, input_text: str) -> str:
        if self.semantic_db:
            relevant_docs = self.semantic_db.search(input_text, k=3)
            input_text += "\n\nРелевантные документы из базы знаний:\n" + "\n".join(relevant_docs)
        return super().call(input_text)