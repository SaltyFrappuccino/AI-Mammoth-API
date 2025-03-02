# agents/semantic_agent.py
class SemanticAgent:
    def __init__(self, semantic_db):
        self.semantic_db = semantic_db

    def query_service(self, service_name: str) -> str:
        """Get description for a specific service from the semantic database"""
        description = self.semantic_db.query_service(service_name)
        return f"{service_name}: {description}"
    
    def search_knowledge_base(self, query: str, k: int = 3) -> list:
        """Search the semantic database for information related to the query"""
        return self.semantic_db.search(query, k=k)
