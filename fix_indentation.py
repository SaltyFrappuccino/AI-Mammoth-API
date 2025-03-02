#!/usr/bin/env python3
"""
Скрипт для исправления ошибок с отступами в файле aggregator.py
"""

import re

def fix_indentation(input_file, output_file):
    # Читаем содержимое файла
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем блок с анализом кода (около строки 153)
    code_block_pattern = r'try:\s*\n\s*code_analysis = self\.code_agent\.call\(code_text\)'
    fixed_code_block = 'try:\n                code_analysis = self.code_agent.call(code_text)'
    content = re.sub(code_block_pattern, fixed_code_block, content)
    
    # Исправляем блок с анализом документации (около строки 177)
    doc_block_pattern = r'try:\s*\n\s*doc_analysis = self\.documentation_agent\.call\(documentation_text\)'
    fixed_doc_block = 'try:\n                    doc_analysis = self.documentation_agent.call(documentation_text)'
    content = re.sub(doc_block_pattern, fixed_doc_block, content)
    
    # Записываем исправленное содержимое
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Исправленный файл сохранен в {output_file}")

if __name__ == "__main__":
    fix_indentation('aggregator.py', 'aggregator_fixed.py')
    print("Для применения исправлений запустите:")
    print("1. Сделайте резервную копию оригинала: copy aggregator.py aggregator_backup.py")
    print("2. Замените оригинал исправленным: copy aggregator_fixed.py aggregator.py") 