#!/usr/bin/env python3
"""
Скрипт командной строки для запуска анализа кода на соответствие требованиям
без необходимости использовать API.
"""

import os
import sys
import argparse
import logging
import json
import uuid
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('analyze.log')
    ]
)
logger = logging.getLogger("analyze-cli")

def ensure_directories():
    """Создаёт необходимые директории для работы анализатора"""
    dirs = ["output", "output/visualizations", "output/reports"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def check_files_exist(requirements_path: str, code_path: str, tests_path: Optional[str] = None):
    """Проверяет существование указанных файлов"""
    files_to_check = [
        (requirements_path, "Файл с требованиями"), 
        (code_path, "Файл с кодом")
    ]
    
    if tests_path:
        files_to_check.append((tests_path, "Файл с тестами"))
    
    for file_path, file_desc in files_to_check:
        if not os.path.exists(file_path):
            logger.error(f"{file_desc} не найден: {file_path}")
            return False
    
    return True

def perform_analysis(
    requirements_path: str, 
    code_path: str, 
    tests_path: Optional[str] = None,
    analyze_security: bool = False
):
    """
    Выполняет анализ кода на соответствие требованиям
    
    Args:
        requirements_path: Путь к файлу с требованиями
        code_path: Путь к файлу с кодом
        tests_path: Путь к файлу с тестами (опционально)
        analyze_security: Выполнять ли анализ безопасности
        
    Returns:
        Dict с результатами анализа
    """
    try:
        # Импортируем необходимые модули
        try:
            from aggregator import Aggregator
            from semantic_db import SemanticDB
        except ImportError as e:
            logger.error(f"Не удалось импортировать необходимые модули: {e}")
            sys.exit(1)
        
        # Генерируем уникальный ID для отчета
        report_id = str(uuid.uuid4())
        output_dir = Path(f"output/reports/{report_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Чтение содержимого файлов
        with open(requirements_path, 'r', encoding='utf-8') as f:
            requirements_content = f.read()
        
        with open(code_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        tests_content = None
        if tests_path:
            with open(tests_path, 'r', encoding='utf-8') as f:
                tests_content = f.read()
        
        # Запуск анализа
        logger.info("Инициализация базы знаний...")
        db = SemanticDB()
        
        logger.info("Запуск агрегатора для анализа...")
        aggregator = Aggregator(db=db)
        
        # Выполнение анализа
        start_time = time.time()
        report, bugs_count = aggregator.aggregate(
            requirements=requirements_content,
            code=code_content,
            tests=tests_content,
            analyze_security=analyze_security
        )
        
        analysis_time = time.time() - start_time
        logger.info(f"Анализ завершен за {analysis_time:.2f} секунд")
        
        # Расширяем результаты для CLI
        result = {
            "report_id": report_id,
            "analysis_time": f"{analysis_time:.2f} сек",
            "report": report,
            "bugs_count": bugs_count
        }
        
        # Проверяем наличие визуализаций
        try:
            import visualization
            viz_files = list(Path(f"output/visualizations/{report_id}").glob("*.png"))
            if viz_files:
                logger.info(f"Создано {len(viz_files)} визуализаций")
                result["visualizations"] = [str(f) for f in viz_files]
        except ImportError:
            pass
        
        # Сохраняем отчет в JSON
        report_path = output_dir / "report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Отчет сохранен: {report_path}")
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при анализе: {e}", exc_info=True)
        return {
            "error": str(e),
            "status": "failed"
        }

def display_report_summary(report: Dict[str, Any]):
    """Отображает краткую информацию о результатах анализа"""
    
    if "error" in report:
        print("\n❌ ОШИБКА ПРИ АНАЛИЗЕ:")
        print(f"  {report['error']}")
        return
    
    print("\n✅ АНАЛИЗ ЗАВЕРШЕН")
    print(f"Время выполнения: {report['analysis_time']}")
    print(f"ID отчета: {report['report_id']}")
    print(f"Расчетное количество ошибок: {report['bugs_count']}")
    
    # Печать сводки по соответствию требованиям
    if "requirements_analysis" in report["report"]:
        reqs = report["report"]["requirements_analysis"]
        total = len(reqs)
        fulfilled = sum(1 for r in reqs if r.get("status") == "fulfilled")
        partially = sum(1 for r in reqs if r.get("status") == "partially_fulfilled")
        not_fulfilled = sum(1 for r in reqs if r.get("status") == "not_fulfilled")
        
        print("\n📋 СООТВЕТСТВИЕ ТРЕБОВАНИЯМ:")
        print(f"  Всего требований: {total}")
        print(f"  ✓ Выполнено полностью: {fulfilled} ({fulfilled/total*100:.1f}%)")
        print(f"  ⚠ Выполнено частично: {partially} ({partially/total*100:.1f}%)")
        print(f"  ✗ Не выполнено: {not_fulfilled} ({not_fulfilled/total*100:.1f}%)")
    
    # Печать информации о рекомендациях
    if "recommendations" in report["report"]:
        recs = report["report"]["recommendations"]
        print(f"\n💡 РЕКОМЕНДАЦИИ ({len(recs)}):")
        
        # Проверяем, есть ли приоритеты в рекомендациях
        has_priorities = any("priority" in r for r in recs)
        
        for idx, rec in enumerate(recs[:5], 1):  # Показываем только первые 5
            priority_str = ""
            if has_priorities and "priority" in rec:
                if rec["priority"] == "high":
                    priority_str = "🔴 "
                elif rec["priority"] == "medium":
                    priority_str = "🟡 "
                else:
                    priority_str = "🟢 "
            
            print(f"  {priority_str}{idx}. {rec.get('description', 'Нет описания')}")
        
        if len(recs) > 5:
            print(f"  ... и еще {len(recs) - 5} рекомендаций")
    
    # Печать информации о визуализациях
    if "visualizations" in report:
        viz_files = report["visualizations"]
        print(f"\n📊 ВИЗУАЛИЗАЦИИ ({len(viz_files)}):")
        for viz_file in viz_files:
            print(f"  • {viz_file}")
    
    # Информация о безопасности
    if "security_vulnerabilities" in report["report"]:
        vulns = report["report"]["security_vulnerabilities"]
        print(f"\n🔒 УЯЗВИМОСТИ ({len(vulns)}):")
        for idx, vuln in enumerate(vulns[:3], 1):  # Показываем только первые 3
            severity = vuln.get("severity", "medium")
            severity_icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
            print(f"  {severity_icon} {vuln.get('type', 'Уязвимость')}: {vuln.get('description', 'Нет описания')}")
        
        if len(vulns) > 3:
            print(f"  ... и еще {len(vulns) - 3} уязвимостей")
    
    print("\n📄 Полный отчет сохранен в:")
    print(f"  output/reports/{report['report_id']}/report.json")

def main():
    """Основная функция для запуска анализа из командной строки"""
    parser = argparse.ArgumentParser(
        description="Анализатор соответствия кода требованиям",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('-r', '--requirements', required=True, 
                        help='Путь к файлу с требованиями')
    parser.add_argument('-c', '--code', required=True,
                        help='Путь к файлу с кодом')
    parser.add_argument('-t', '--tests', 
                        help='Путь к файлу с тестами (опционально)')
    parser.add_argument('-s', '--security', action='store_true',
                        help='Выполнить анализ безопасности')
    parser.add_argument('-o', '--output',
                        help='Путь для сохранения отчета (по умолчанию: output/reports/{id}/report.json)')
    parser.add_argument('-j', '--json', action='store_true',
                        help='Вывести результат в JSON формате')
    
    args = parser.parse_args()
    
    # Проверка наличия файлов
    if not check_files_exist(args.requirements, args.code, args.tests):
        sys.exit(1)
    
    # Создание директорий
    ensure_directories()
    
    # Выполнение анализа
    logger.info("Запуск анализа...")
    print("🔍 Выполняется анализ, пожалуйста, подождите...")
    
    result = perform_analysis(
        requirements_path=args.requirements,
        code_path=args.code,
        tests_path=args.tests,
        analyze_security=args.security
    )
    
    # Вывод результатов
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        display_report_summary(result)
        
    # Сохранение в указанный файл, если задан
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"Результаты сохранены в {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 