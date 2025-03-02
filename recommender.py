import logging
import json
import re
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("recommender")

class PriorityLevel(Enum):
    """Уровни приоритета для рекомендаций"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1
    
    @classmethod
    def from_string(cls, s: str) -> "PriorityLevel":
        """Преобразует строковое представление в уровень приоритета"""
        s = s.lower()
        if "критичес" in s or "критич" in s:
            return cls.CRITICAL
        elif "высок" in s:
            return cls.HIGH
        elif "средн" in s:
            return cls.MEDIUM
        elif "низк" in s:
            return cls.LOW
        else:
            return cls.INFO

class RecommendationType(Enum):
    """Типы рекомендаций"""
    SECURITY = "Безопасность"
    PERFORMANCE = "Производительность"
    ARCHITECTURE = "Архитектура"
    CODE_QUALITY = "Качество кода"
    TESTS = "Тесты"
    DOCUMENTATION = "Документация"
    REQUIREMENTS = "Требования"
    INTEGRATION = "Интеграция"
    OTHER = "Другое"
    
    @classmethod
    def from_string(cls, s: str) -> "RecommendationType":
        """Преобразует строковое представление в тип рекомендации"""
        s = s.lower()
        if "безопас" in s:
            return cls.SECURITY
        elif "производительн" in s or "performan" in s:
            return cls.PERFORMANCE
        elif "архитектур" in s:
            return cls.ARCHITECTURE
        elif "качеств" in s or "код" in s:
            return cls.CODE_QUALITY
        elif "тест" in s:
            return cls.TESTS
        elif "документац" in s:
            return cls.DOCUMENTATION
        elif "требован" in s:
            return cls.REQUIREMENTS
        elif "интегра" in s:
            return cls.INTEGRATION
        else:
            return cls.OTHER

class Recommendation:
    """Класс, представляющий отдельную рекомендацию"""
    
    def __init__(
        self,
        text: str,
        priority: PriorityLevel = PriorityLevel.MEDIUM,
        recommendation_type: RecommendationType = RecommendationType.OTHER,
        affected_requirements: List[str] = None,
        affected_code: List[str] = None,
        effort_estimate: Optional[str] = None,
        expected_impact: Optional[str] = None
    ):
        self.text = text
        self.priority = priority
        self.recommendation_type = recommendation_type
        self.affected_requirements = affected_requirements or []
        self.affected_code = affected_code or []
        self.effort_estimate = effort_estimate
        self.expected_impact = expected_impact
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует рекомендацию в словарь"""
        return {
            "text": self.text,
            "priority": self.priority.name,
            "priority_level": self.priority.value,
            "type": self.recommendation_type.value,
            "affected_requirements": self.affected_requirements,
            "affected_code": self.affected_code,
            "effort_estimate": self.effort_estimate,
            "expected_impact": self.expected_impact
        }
    
    def to_markdown(self) -> str:
        """Преобразует рекомендацию в формат Markdown"""
        priority_indicators = {
            PriorityLevel.CRITICAL: "🔴",
            PriorityLevel.HIGH: "🟠",
            PriorityLevel.MEDIUM: "🟡",
            PriorityLevel.LOW: "🟢",
            PriorityLevel.INFO: "🔵"
        }
        
        md = [
            f"### {priority_indicators.get(self.priority, '')} {self.recommendation_type.value}: {self.text}",
            f"**Приоритет**: {self.priority.name}",
        ]
        
        if self.affected_requirements:
            md.append(f"**Затрагивает требования**: {', '.join(self.affected_requirements)}")
        
        if self.affected_code:
            md.append(f"**Затрагивает код**: {', '.join(self.affected_code)}")
        
        if self.effort_estimate:
            md.append(f"**Сложность внедрения**: {self.effort_estimate}")
        
        if self.expected_impact:
            md.append(f"**Ожидаемый эффект**: {self.expected_impact}")
        
        return "\n\n".join(md)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recommendation":
        """Создает объект рекомендации из словаря"""
        return cls(
            text=data.get("text", ""),
            priority=PriorityLevel[data.get("priority", "MEDIUM")],
            recommendation_type=RecommendationType.from_string(data.get("type", "Другое")),
            affected_requirements=data.get("affected_requirements", []),
            affected_code=data.get("affected_code", []),
            effort_estimate=data.get("effort_estimate", None),
            expected_impact=data.get("expected_impact", None)
        )

class RecommendationEngine:
    """Движок для генерации и управления рекомендациями"""
    
    def __init__(self):
        self.recommendations: List[Recommendation] = []
    
    def add_recommendation(self, recommendation: Recommendation) -> None:
        """Добавляет рекомендацию в список"""
        self.recommendations.append(recommendation)
    
    def parse_recommendations_from_text(self, text: str) -> List[Recommendation]:
        """Парсит рекомендации из текстового отчета"""
        recommendations = []
        
        # Ищем разделы с рекомендациями в отчете
        recommendation_patterns = [
            r"(?:Рекомендации:|Рекомендуется:|Рекомендация:)[ \t]*\n*(.*?)(?=\n\n|\n*$)",
            r"(?:Рекомендуемые действия:|Необходимо:|Следует:)[ \t]*\n*(.*?)(?=\n\n|\n*$)"
        ]
        
        found_recommendations = []
        for pattern in recommendation_patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                recommendation_text = match.group(1).strip()
                if recommendation_text and len(recommendation_text) > 10:
                    found_recommendations.append(recommendation_text)
        
        # Если не нашли рекомендации по паттернам, ищем в списке с дефисами
        if not found_recommendations:
            bullet_points = re.findall(r"(?<=\n)[-*]\s*(.*?)(?=\n[-*]|\n\n|\n*$)", text, re.DOTALL)
            for point in bullet_points:
                if len(point.strip()) > 15 and ("рекоменд" in point.lower() or "следует" in point.lower() or "необходимо" in point.lower()):
                    found_recommendations.append(point.strip())
        
        # Создаем объекты рекомендаций
        for rec_text in found_recommendations:
            # Определяем приоритет на основе текста
            priority = PriorityLevel.MEDIUM
            if re.search(r"критич|срочн|немедленн|уязвим", rec_text.lower()):
                priority = PriorityLevel.CRITICAL
            elif re.search(r"важн|высок|существенн", rec_text.lower()):
                priority = PriorityLevel.HIGH
            elif re.search(r"незначительн|мелк|низк", rec_text.lower()):
                priority = PriorityLevel.LOW
            
            # Определяем тип рекомендации на основе текста
            rec_type = RecommendationType.OTHER
            if re.search(r"безопасн|уязвим|атак|защит", rec_text.lower()):
                rec_type = RecommendationType.SECURITY
            elif re.search(r"производительн|скорост|быстр|оптимиз", rec_text.lower()):
                rec_type = RecommendationType.PERFORMANCE
            elif re.search(r"архитектур|структур|дизайн|паттерн", rec_text.lower()):
                rec_type = RecommendationType.ARCHITECTURE
            elif re.search(r"код|рефакторинг|читаем|понятн", rec_text.lower()):
                rec_type = RecommendationType.CODE_QUALITY
            elif re.search(r"тест|покрыт|unit|интеграцион", rec_text.lower()):
                rec_type = RecommendationType.TESTS
            elif re.search(r"документ|коммент|описан", rec_text.lower()):
                rec_type = RecommendationType.DOCUMENTATION
            elif re.search(r"требован|REQ-|спецификац", rec_text.lower()):
                rec_type = RecommendationType.REQUIREMENTS
            elif re.search(r"интегр|API|внешн|сервис", rec_text.lower()):
                rec_type = RecommendationType.INTEGRATION
            
            # Ищем затронутые требования
            affected_reqs = re.findall(r"REQ-\d+", rec_text)
            
            # Ищем затронутый код
            affected_code = []
            code_patterns = [r"(?:файл(?:е|ах)?|модул(?:е|ях)?|класс(?:е|ах)?|метод(?:е|ах)?)[ \t]*[\"']([^\"']+)[\"']", 
                            r"(?:файл(?:е|ах)?|модул(?:е|ях)?|класс(?:е|ах)?|метод(?:е|ах)?)[ \t]*`([^`]+)`"]
            for pattern in code_patterns:
                code_matches = re.finditer(pattern, rec_text)
                for match in code_matches:
                    affected_code.append(match.group(1))
            
            recommendation = Recommendation(
                text=rec_text,
                priority=priority,
                recommendation_type=rec_type,
                affected_requirements=affected_reqs,
                affected_code=affected_code
            )
            recommendations.append(recommendation)
        
        self.recommendations.extend(recommendations)
        return recommendations
    
    def get_prioritized_recommendations(self) -> List[Recommendation]:
        """Возвращает отсортированные по приоритету рекомендации"""
        return sorted(self.recommendations, key=lambda x: x.priority.value, reverse=True)
    
    def get_recommendations_by_type(self, recommendation_type: RecommendationType) -> List[Recommendation]:
        """Возвращает рекомендации определенного типа"""
        return [r for r in self.recommendations if r.recommendation_type == recommendation_type]
    
    def get_recommendations_for_requirement(self, requirement_id: str) -> List[Recommendation]:
        """Возвращает рекомендации для конкретного требования"""
        return [r for r in self.recommendations if requirement_id in r.affected_requirements]
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует все рекомендации в словарь"""
        return {
            "recommendations": [r.to_dict() for r in self.recommendations],
        }
    
    def to_markdown(self) -> str:
        """Генерирует Markdown-отчет с рекомендациями"""
        if not self.recommendations:
            return "## Рекомендации\n\nРекомендации отсутствуют."
        
        prioritized = self.get_prioritized_recommendations()
        
        sections = ["# Рекомендации по улучшению\n"]
        
        # Добавляем раздел с критическими рекомендациями
        critical = [r for r in prioritized if r.priority == PriorityLevel.CRITICAL]
        if critical:
            sections.append("## 🔴 Критические рекомендации\n")
            for rec in critical:
                sections.append(rec.to_markdown())
                sections.append("---\n")
        
        # Добавляем раздел с высокоприоритетными рекомендациями
        high = [r for r in prioritized if r.priority == PriorityLevel.HIGH]
        if high:
            sections.append("## 🟠 Важные рекомендации\n")
            for rec in high:
                sections.append(rec.to_markdown())
                sections.append("---\n")
        
        # Добавляем раздел со среднеприоритетными рекомендациями
        medium = [r for r in prioritized if r.priority == PriorityLevel.MEDIUM]
        if medium:
            sections.append("## 🟡 Рекомендации среднего приоритета\n")
            for rec in medium:
                sections.append(rec.to_markdown())
                sections.append("---\n")
        
        # Добавляем раздел с низкоприоритетными рекомендациями
        low = [r for r in prioritized if r.priority == PriorityLevel.LOW]
        if low:
            sections.append("## 🟢 Рекомендации низкого приоритета\n")
            for rec in low:
                sections.append(rec.to_markdown())
                sections.append("---\n")
        
        # Добавляем раздел с информационными рекомендациями
        info = [r for r in prioritized if r.priority == PriorityLevel.INFO]
        if info:
            sections.append("## 🔵 Информационные рекомендации\n")
            for rec in info:
                sections.append(rec.to_markdown())
                sections.append("---\n")
        
        # Добавляем сводную статистику
        sections.append("## Сводная статистика\n\n")
        sections.append(f"- **Всего рекомендаций**: {len(self.recommendations)}")
        sections.append(f"- **Критических**: {len(critical)}")
        sections.append(f"- **Важных**: {len(high)}")
        sections.append(f"- **Средних**: {len(medium)}")
        sections.append(f"- **Низких**: {len(low)}")
        sections.append(f"- **Информационных**: {len(info)}")
        
        # Статистика по типам
        sections.append("\n### Рекомендации по типам\n\n")
        type_counts = {}
        for rec in self.recommendations:
            rec_type = rec.recommendation_type.value
            type_counts[rec_type] = type_counts.get(rec_type, 0) + 1
        
        for rec_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            sections.append(f"- **{rec_type}**: {count}")
        
        return "\n\n".join(sections)
    
    def save_to_file(self, filename: str) -> None:
        """Сохраняет рекомендации в JSON-файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"Рекомендации сохранены в файл: {filename}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении рекомендаций в файл: {str(e)}")
    
    @classmethod
    def load_from_file(cls, filename: str) -> "RecommendationEngine":
        """Загружает рекомендации из JSON-файла"""
        engine = cls()
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                recs = data.get('recommendations', [])
                for rec_data in recs:
                    recommendation = Recommendation.from_dict(rec_data)
                    engine.add_recommendation(recommendation)
            logger.info(f"Рекомендации загружены из файла: {filename}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке рекомендаций из файла: {str(e)}")
        
        return engine

if __name__ == "__main__":
    # Пример использования
    logging.basicConfig(level=logging.INFO)
    
    # Создаем движок рекомендаций
    engine = RecommendationEngine()
    
    # Добавляем несколько рекомендаций
    engine.add_recommendation(Recommendation(
        text="Внедрить механизм аутентификации для API",
        priority=PriorityLevel.CRITICAL,
        recommendation_type=RecommendationType.SECURITY,
        affected_requirements=["REQ-1", "REQ-5"],
        affected_code=["api/routes.py", "auth/middleware.py"],
        effort_estimate="Средняя",
        expected_impact="Значительное повышение безопасности системы"
    ))
    
    engine.add_recommendation(Recommendation(
        text="Добавить кэширование для часто запрашиваемых данных",
        priority=PriorityLevel.HIGH,
        recommendation_type=RecommendationType.PERFORMANCE,
        affected_requirements=["REQ-3"],
        affected_code=["data/repository.py"],
        effort_estimate="Низкая",
        expected_impact="Повышение производительности на ~30%"
    ))
    
    engine.add_recommendation(Recommendation(
        text="Улучшить документацию методов API",
        priority=PriorityLevel.MEDIUM,
        recommendation_type=RecommendationType.DOCUMENTATION,
        affected_requirements=["REQ-10"],
        affected_code=["api/routes.py"],
        effort_estimate="Низкая",
        expected_impact="Улучшение понимания API для разработчиков"
    ))
    
    # Получаем приоритизированные рекомендации
    prioritized = engine.get_prioritized_recommendations()
    for rec in prioritized:
        print(f"[{rec.priority.name}] {rec.recommendation_type.value}: {rec.text}")
    
    # Сохраняем в файл
    engine.save_to_file("recommendations_example.json")
    
    # Генерируем Markdown
    markdown = engine.to_markdown()
    with open("recommendations_example.md", 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print("\nРекомендации сохранены в файлы recommendations_example.json и recommendations_example.md") 