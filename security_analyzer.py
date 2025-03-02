import os
import re
import logging
import json
from typing import List, Dict, Any, Tuple, Optional
import traceback

logger = logging.getLogger("security_analyzer")

class SecurityVulnerability:
    """Класс, представляющий уязвимость в безопасности"""
    
    def __init__(
        self, 
        vuln_type: str,
        severity: str,
        description: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
        mitigation: Optional[str] = None,
        cwe_id: Optional[str] = None
    ):
        self.vuln_type = vuln_type
        self.severity = severity
        self.description = description
        self.file_path = file_path
        self.line_number = line_number
        self.code_snippet = code_snippet
        self.mitigation = mitigation
        self.cwe_id = cwe_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует уязвимость в словарь"""
        return {
            "type": self.vuln_type,
            "severity": self.severity,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "mitigation": self.mitigation,
            "cwe_id": self.cwe_id
        }
    
    def to_markdown(self) -> str:
        """Преобразует уязвимость в формат Markdown"""
        severity_indicators = {
            "Критическая": "🔴",
            "Высокая": "🟠",
            "Средняя": "🟡", 
            "Низкая": "🟢"
        }
        
        severity_icon = severity_indicators.get(self.severity, "")
        
        md_lines = [
            f"### {severity_icon} {self.vuln_type}",
            f"**Серьезность**: {self.severity}"
        ]
        
        if self.cwe_id:
            md_lines.append(f"**CWE**: [{self.cwe_id}](https://cwe.mitre.org/data/definitions/{self.cwe_id.replace('CWE-', '')}.html)")
        
        md_lines.append(f"**Описание**: {self.description}")
        
        if self.file_path:
            location = f"{self.file_path}"
            if self.line_number:
                location += f":{self.line_number}"
            md_lines.append(f"**Расположение**: `{location}`")
        
        if self.code_snippet:
            md_lines.append("**Код**:")
            md_lines.append(f"```\n{self.code_snippet}\n```")
        
        if self.mitigation:
            md_lines.append(f"**Рекомендация по устранению**: {self.mitigation}")
        
        return "\n\n".join(md_lines)

class SecurityAnalyzer:
    """Класс для анализа безопасности кода"""
    
    # Словарь с известными шаблонами уязвимостей
    VULNERABILITY_PATTERNS = {
        # SQL Injection
        "SQL Injection": {
            "pattern": r'(?:execute|query|cursor\.execute|db\.query|\.raw)\s*\(\s*(?:f|format|%|\+\s*(?:\w+|\"|\'))\s*.*\)',
            "severity": "Критическая",
            "description": "Потенциальная уязвимость SQL-инъекции. Параметры запроса могут не проходить надлежащую санитизацию.",
            "cwe_id": "CWE-89",
            "mitigation": "Используйте параметризованные запросы или ORM вместо прямой конкатенации строк в SQL-запросах."
        },
        # XSS (Cross-Site Scripting)
        "Cross-Site Scripting (XSS)": {
            "pattern": r'(?:innerHTML|outerHTML|document\.write|eval|setTimeout|setInterval|new\s+Function)\s*\(\s*(?:\w+|\[|\{|\"|\').*\)',
            "severity": "Высокая",
            "description": "Потенциальная уязвимость XSS. Данные могут быть внедрены в веб-страницу без надлежащей проверки.",
            "cwe_id": "CWE-79",
            "mitigation": "Экранируйте вывод данных перед вставкой в HTML или используйте специальные библиотеки для безопасного построения DOM."
        },
        # Command Injection
        "Command Injection": {
            "pattern": r'(?:os\.system|subprocess\.(?:call|Popen|run)|exec|eval|execfile)\s*\(\s*(?:f|format|%|\+\s*(?:\w+|\"|\'))\s*.*\)',
            "severity": "Критическая",
            "description": "Потенциальная уязвимость инъекции команд. Параметры команды могут не проходить надлежащую проверку.",
            "cwe_id": "CWE-78",
            "mitigation": "Избегайте использования системных команд. Если необходимо, используйте список аргументов вместо строки и избегайте shell=True."
        },
        # Insecure Direct Object Reference (IDOR)
        "Insecure Direct Object Reference": {
            "pattern": r'(?:get|find|select|query|retrieve)(?:_by|_with|_for)?(?:_id|_uuid|_key)\s*\(\s*(?:request|params|query|\.get\()\s*.*\)',
            "severity": "Средняя",
            "description": "Потенциальная уязвимость IDOR. Убедитесь, что доступ к объектам проверяется на авторизацию.",
            "cwe_id": "CWE-639",
            "mitigation": "Проверяйте права доступа пользователя на каждый запрашиваемый им объект, не полагаясь только на ID объекта."
        },
        # Hard-coded Credentials
        "Hard-coded Credentials": {
            "pattern": r'(?:password|passwd|pwd|secret|key|token|api[_\-]?key)\s*=\s*[\'\"][^\'\"\n]{5,}[\'\"]',
            "severity": "Высокая",
            "description": "Обнаружены жестко закодированные учетные данные. Это может привести к несанкционированному доступу.",
            "cwe_id": "CWE-798",
            "mitigation": "Храните учетные данные в переменных окружения или в защищенном хранилище, а не в коде."
        },
        # Path Traversal
        "Path Traversal": {
            "pattern": r'(?:open|file|read|write)\s*\(\s*(?:f|format|%|\+\s*(?:\w+|\"|\'))\s*.*\)',
            "severity": "Средняя",
            "description": "Потенциальная уязвимость обхода пути. Параметры пути могут не проходить надлежащую проверку.",
            "cwe_id": "CWE-22",
            "mitigation": "Проверяйте и нормализуйте все пути файлов и ограничивайте доступ к определенным директориям."
        },
        # Insecure Cryptographic Storage
        "Insecure Cryptographic Storage": {
            "pattern": r'(?:md5|sha1)\s*\(',
            "severity": "Средняя",
            "description": "Использование устаревших криптографических алгоритмов (MD5, SHA1).",
            "cwe_id": "CWE-327",
            "mitigation": "Используйте современные алгоритмы хеширования, такие как SHA-256 или Argon2, и правильную схему хеширования паролей."
        },
        # Missing Authentication
        "Missing Authentication": {
            "pattern": r'@(?:app|route|blueprint)\.(?:route|get|post|put|delete|patch)\s*\(\s*[\'\"][^\'\"\n]*[\'\"],\s*(?!auth|login|authenticate)',
            "severity": "Высокая",
            "description": "Потенциальное отсутствие аутентификации в конечной точке API.",
            "cwe_id": "CWE-306",
            "mitigation": "Добавьте механизм аутентификации ко всем конечным точкам, требующим ограничения доступа."
        },
        # Insecure Deserialization
        "Insecure Deserialization": {
            "pattern": r'(?:pickle|marshal|shelve|yaml\.load|json\.loads)\s*\(',
            "severity": "Высокая",
            "description": "Потенциальная небезопасная десериализация. Может привести к выполнению произвольного кода.",
            "cwe_id": "CWE-502",
            "mitigation": "Для YAML используйте yaml.safe_load() вместо yaml.load(). Для pickle/marshal не десериализуйте данные из недоверенных источников."
        },
        # Cross-Site Request Forgery (CSRF)
        "Cross-Site Request Forgery": {
            "pattern": r'@csrf_exempt',
            "severity": "Средняя",
            "description": "Отключение защиты от CSRF может сделать приложение уязвимым для межсайтовой подделки запросов.",
            "cwe_id": "CWE-352",
            "mitigation": "Включите защиту CSRF и используйте токены для защиты от CSRF-атак."
        },
        # Unvalidated Redirects
        "Unvalidated Redirects": {
            "pattern": r'(?:redirect|HttpResponseRedirect)\s*\(\s*(?:request|params|\.get\(|f|format|%|\+\s*(?:\w+|\"|\'))\s*.*\)',
            "severity": "Средняя",
            "description": "Потенциальная уязвимость непроверенных перенаправлений. Целевой URL может не проходить надлежащую проверку.",
            "cwe_id": "CWE-601",
            "mitigation": "Проверяйте все URL-адреса перенаправления и используйте белый список допустимых доменов."
        },
        # JWT Issues
        "Небезопасное использование JWT": {
            "pattern": r'(?:jwt\.encode|jwt\.decode)\s*\(\s*.*,\s*["\'](?!HS256|RS256|ES256)[^"\']*["\']\s*\)',
            "severity": "Средняя",
            "description": "Потенциально небезопасное использование JWT. Убедитесь, что используется надежный алгоритм (HS256, RS256, ES256).",
            "cwe_id": "CWE-327",
            "mitigation": "Используйте сильные алгоритмы для JWT, такие как HS256, RS256 или ES256."
        },
        # API Key Exposure
        "API Key Exposure": {
            "pattern": r'[A-Za-z0-9_]{20,}',
            "severity": "Средняя",
            "description": "Возможное раскрытие API-ключа в коде. Проверьте, не является ли эта строка API-ключом.",
            "cwe_id": "CWE-312",
            "mitigation": "Храните API-ключи в переменных окружения или в защищенном хранилище, а не в коде."
        }
    }
    
    def __init__(self):
        """Инициализирует анализатор безопасности"""
        self.vulnerabilities: List[SecurityVulnerability] = []
    
    def analyze_file(self, file_path: str) -> List[SecurityVulnerability]:
        """
        Анализирует файл на наличие уязвимостей безопасности
        
        Args:
            file_path (str): Путь к анализируемому файлу
            
        Returns:
            List[SecurityVulnerability]: Список обнаруженных уязвимостей
        """
        file_vulnerabilities = []
        
        try:
            # Проверяем существование файла
            if not os.path.isfile(file_path):
                logger.warning(f"Файл не найден: {file_path}")
                return []
            
            # Проверяем расширение файла (анализируем только определенные типы файлов)
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in ['.py', '.js', '.ts', '.jsx', '.tsx', '.php', '.rb', '.java', '.go', '.cs']:
                logger.debug(f"Пропуск файла с неподдерживаемым расширением: {file_path}")
                return []
            
            # Читаем содержимое файла
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Проходим по всем шаблонам уязвимостей
            for vuln_type, vuln_info in self.VULNERABILITY_PATTERNS.items():
                pattern = re.compile(vuln_info["pattern"])
                
                # Ищем совпадения в файле
                for i, line in enumerate(lines):
                    match = pattern.search(line)
                    if match:
                        # Получаем фрагмент кода с контекстом
                        start_line = max(0, i - 2)
                        end_line = min(len(lines) - 1, i + 2)
                        code_snippet = "\n".join([
                            f"{j+1}: {lines[j]}" for j in range(start_line, end_line + 1)
                        ])
                        
                        # Создаем объект уязвимости
                        vulnerability = SecurityVulnerability(
                            vuln_type=vuln_type,
                            severity=vuln_info["severity"],
                            description=vuln_info["description"],
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=code_snippet,
                            mitigation=vuln_info.get("mitigation"),
                            cwe_id=vuln_info.get("cwe_id")
                        )
                        
                        file_vulnerabilities.append(vulnerability)
                        self.vulnerabilities.append(vulnerability)
            
            logger.info(f"Анализ файла {file_path} завершен. Найдено уязвимостей: {len(file_vulnerabilities)}")
            return file_vulnerabilities
            
        except Exception as e:
            logger.error(f"Ошибка при анализе файла {file_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def analyze_directory(self, directory_path: str, exclude_dirs: List[str] = None) -> List[SecurityVulnerability]:
        """
        Рекурсивно анализирует директорию на наличие уязвимостей безопасности
        
        Args:
            directory_path (str): Путь к анализируемой директории
            exclude_dirs (List[str], optional): Список директорий для исключения
            
        Returns:
            List[SecurityVulnerability]: Список обнаруженных уязвимостей
        """
        if exclude_dirs is None:
            exclude_dirs = ['.git', '.venv', 'venv', 'node_modules', '__pycache__', 'dist', 'build']
        
        all_vulnerabilities = []
        
        try:
            for root, dirs, files in os.walk(directory_path):
                # Исключаем директории из обхода
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    file_vulnerabilities = self.analyze_file(file_path)
                    all_vulnerabilities.extend(file_vulnerabilities)
            
            logger.info(f"Анализ директории {directory_path} завершен. Найдено уязвимостей: {len(all_vulnerabilities)}")
            return all_vulnerabilities
            
        except Exception as e:
            logger.error(f"Ошибка при анализе директории {directory_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def get_vulnerability_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку об обнаруженных уязвимостях
        
        Returns:
            Dict[str, Any]: Сводка о уязвимостях
        """
        # Считаем количество уязвимостей по типам
        vuln_by_type = {}
        for vuln in self.vulnerabilities:
            vuln_by_type[vuln.vuln_type] = vuln_by_type.get(vuln.vuln_type, 0) + 1
        
        # Считаем количество уязвимостей по серьезности
        vuln_by_severity = {}
        for vuln in self.vulnerabilities:
            vuln_by_severity[vuln.severity] = vuln_by_severity.get(vuln.severity, 0) + 1
        
        # Считаем количество уязвимостей по файлам
        vuln_by_file = {}
        for vuln in self.vulnerabilities:
            if vuln.file_path:
                vuln_by_file[vuln.file_path] = vuln_by_file.get(vuln.file_path, 0) + 1
        
        return {
            "total_vulnerabilities": len(self.vulnerabilities),
            "by_severity": vuln_by_severity,
            "by_type": vuln_by_type,
            "by_file": vuln_by_file,
            "top_vulnerable_files": sorted(
                vuln_by_file.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5] if vuln_by_file else []
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует результаты анализа в словарь
        
        Returns:
            Dict[str, Any]: Словарь с результатами анализа
        """
        return {
            "vulnerabilities": [vuln.to_dict() for vuln in self.vulnerabilities],
            "summary": self.get_vulnerability_summary()
        }
    
    def to_markdown(self) -> str:
        """
        Генерирует Markdown-отчет о результатах анализа безопасности
        
        Returns:
            str: Markdown-отчет
        """
        if not self.vulnerabilities:
            return "# Анализ безопасности\n\nУязвимостей не обнаружено."
        
        summary = self.get_vulnerability_summary()
        
        sections = ["# Отчет об анализе безопасности\n"]
        
        # Добавляем раздел со сводкой
        sections.append("## Сводка\n")
        sections.append(f"- **Всего уязвимостей**: {summary['total_vulnerabilities']}")
        
        # Добавляем раздел с уязвимостями по серьезности
        severity_order = ["Критическая", "Высокая", "Средняя", "Низкая"]
        if summary.get('by_severity'):
            sections.append("\n### По серьезности\n")
            for severity in severity_order:
                if severity in summary['by_severity']:
                    sections.append(f"- **{severity}**: {summary['by_severity'][severity]}")
        
        # Добавляем раздел с уязвимостями по типам
        if summary.get('by_type'):
            sections.append("\n### По типам уязвимостей\n")
            for vuln_type, count in sorted(summary['by_type'].items(), key=lambda x: x[1], reverse=True):
                sections.append(f"- **{vuln_type}**: {count}")
        
        # Добавляем раздел с наиболее уязвимыми файлами
        if summary.get('top_vulnerable_files'):
            sections.append("\n### Наиболее уязвимые файлы\n")
            for file_path, count in summary['top_vulnerable_files']:
                sections.append(f"- **{file_path}**: {count} уязвимостей")
        
        # Группируем уязвимости по серьезности
        vulnerabilities_by_severity = {}
        for vuln in self.vulnerabilities:
            if vuln.severity not in vulnerabilities_by_severity:
                vulnerabilities_by_severity[vuln.severity] = []
            vulnerabilities_by_severity[vuln.severity].append(vuln)
        
        # Добавляем разделы с уязвимостями по серьезности
        severity_headers = {
            "Критическая": "## 🔴 Критические уязвимости",
            "Высокая": "## 🟠 Высокие уязвимости",
            "Средняя": "## 🟡 Средние уязвимости",
            "Низкая": "## 🟢 Низкие уязвимости"
        }
        
        for severity in severity_order:
            if severity in vulnerabilities_by_severity and vulnerabilities_by_severity[severity]:
                sections.append(f"\n{severity_headers.get(severity, f'## Уязвимости ({severity})')}\n")
                for vuln in vulnerabilities_by_severity[severity]:
                    sections.append(vuln.to_markdown())
                    sections.append("\n---\n")
        
        return "\n".join(sections)
    
    def save_to_file(self, filename: str, format: str = 'json') -> None:
        """
        Сохраняет результаты анализа в файл
        
        Args:
            filename (str): Имя файла для сохранения
            format (str, optional): Формат файла ('json' или 'md')
        """
        try:
            if format.lower() == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
                logger.info(f"Результаты анализа сохранены в файл JSON: {filename}")
            elif format.lower() in ['md', 'markdown']:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.to_markdown())
                logger.info(f"Результаты анализа сохранены в файл Markdown: {filename}")
            else:
                logger.error(f"Неподдерживаемый формат файла: {format}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении результатов анализа в файл {filename}: {str(e)}")
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Пример использования
    logging.basicConfig(level=logging.INFO)
    
    analyzer = SecurityAnalyzer()
    
    # Анализируем файл или директорию
    analyzer.analyze_directory(".")
    
    # Получаем сводку
    summary = analyzer.get_vulnerability_summary()
    print(f"Всего уязвимостей: {summary['total_vulnerabilities']}")
    
    # Сохраняем отчет
    analyzer.save_to_file("security_report.md", format='md')
    analyzer.save_to_file("security_report.json", format='json') 