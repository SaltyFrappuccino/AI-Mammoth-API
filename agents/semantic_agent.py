# agents/semantic_agent.py
import logging
from typing import List, Optional
from agents.base_agent import BaseAgent

class SemanticAgent(BaseAgent):
    """
    Агент для работы с семантической базой данных. 
    Позволяет искать информацию по запросу и получать описания сервисов.
    """
    def __init__(self, semantic_db):
        """
        Инициализирует агента для работы с семантической базой данных.
        
        Args:
            semantic_db: Экземпляр SemanticDB для поиска информации
        """
        system_prompt = """
        Ты агент, который помогает находить информацию в базе знаний и отвечать на вопросы.
        Ты должен использовать предоставленную контекстную информацию для формирования ответов.
        Если информации недостаточно, ты должен честно признать, что не знаешь ответа.
        """
        super().__init__("SemanticAgent", system_prompt)
        self.semantic_db = semantic_db
        logging.info("SemanticAgent initialized")

    def query_service(self, service_name: str) -> str:
        """
        Получает описание конкретного сервиса из семантической базы данных.
        
        Args:
            service_name: Название сервиса
            
        Returns:
            str: Описание сервиса
        """
        logging.info(f"Querying service: {service_name}")
        try:
            description = self.semantic_db.query_service(service_name)
            return f"{service_name}: {description}"
        except Exception as e:
            logging.error(f"Error in query_service for {service_name}: {e}")
            return f"Не удалось получить информацию о сервисе {service_name}: {str(e)}"
    
    def search_knowledge_base(self, query: str, k: int = 3) -> List[str]:
        """
        Ищет в семантической базе данных информацию по запросу.
        
        Args:
            query: Текст запроса
            k: Количество результатов для возврата
            
        Returns:
            List[str]: Список найденных документов
        """
        logging.info(f"Searching knowledge base for: {query}, k={k}")
        try:
            results = self.semantic_db.search(query, k=k)
            return results
        except Exception as e:
            logging.error(f"Error in search_knowledge_base for query '{query}': {e}")
            return [f"Ошибка при поиске: {str(e)}"]
    
    def answer_question(self, question: str) -> str:
        """
        Отвечает на вопрос, используя информацию из семантической базы данных.
        
        Args:
            question: Вопрос пользователя
            
        Returns:
            str: Ответ на вопрос
        """
        logging.info(f"Answering question: {question}")
        try:
            # Ищем релевантную информацию в базе знаний
            context_docs = self.search_knowledge_base(question)
            
            if not context_docs:
                return "Я не нашел информацию по вашему вопросу в базе знаний."
            
            # Формируем запрос с контекстом
            prompt = f"""
            Вопрос: {question}
            
            Контекстная информация из базы знаний:
            
            {"".join([f"---\n{doc}\n---\n" for doc in context_docs])}
            
            На основе предоставленной информации, ответь на вопрос пользователя.
            Если в контексте недостаточно информации, честно признай, что не знаешь ответа.
            """
            
            response = self.call(prompt)
            return response
        except Exception as e:
            logging.error(f"Error in answer_question for '{question}': {e}")
            return f"Произошла ошибка при попытке ответить на ваш вопрос: {str(e)}"
    
    def analyze_with_context(self, text: str, context_query: str, max_context_docs: int = 3) -> str:
        """
        Анализирует текст с учетом контекста из базы знаний.
        
        Args:
            text: Текст для анализа
            context_query: Запрос для поиска контекста
            max_context_docs: Максимальное количество документов контекста
            
        Returns:
            str: Результат анализа
        """
        logging.info(f"Analyzing text with context query: {context_query}")
        try:
            # Получаем контекст
            context_docs = self.search_knowledge_base(context_query, k=max_context_docs)
            
            # Формируем запрос с контекстом и текстом
            prompt = f"""
            Проанализируй следующий текст:
            
            ```
            {text}
            ```
            
            Контекстная информация для анализа:
            
            {"".join([f"---\n{doc}\n---\n" for doc in context_docs])}
            
            Представь подробный анализ текста с учетом предоставленного контекста.
            Укажи, насколько текст соответствует информации из контекста, выдели основные
            моменты и предложи рекомендации по улучшению.
            """
            
            response = self.call(prompt)
            return response
        except Exception as e:
            logging.error(f"Error in analyze_with_context: {e}")
            return f"Произошла ошибка при анализе текста: {str(e)}"
