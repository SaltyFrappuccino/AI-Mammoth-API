import tkinter as tk
from tkinter import scrolledtext, messagebox, Menu, font
import requests
import json
import re
import traceback
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gui")

# Добавляем поддержку Markdown
try:
    from tkhtmlview import HTMLLabel
    MARKDOWN_SUPPORT = True
except ImportError:
    MARKDOWN_SUPPORT = False
    messagebox.showwarning("Предупреждение", "Для корректного отображения Markdown установите библиотеку tkhtmlview: pip install tkhtmlview")

def md_to_html(markdown_text):
    """Преобразует базовый Markdown в HTML"""
    if not MARKDOWN_SUPPORT:
        return markdown_text

    # Заголовки
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', markdown_text, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)

    # Жирный текст
    html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
    
    # Курсив
    html = re.sub(r'\*(.+?)\*', r'<i>\1</i>', html)
    
    # Списки
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    
    # Переносы строк
    html = html.replace('\n\n', '<br><br>')
    
    return html

def create_context_menu(widget):
    """Создает контекстное меню для текстового виджета"""
    context_menu = Menu(widget, tearoff=0)
    context_menu.add_command(label="Копировать всё", command=lambda: copy_all_text(widget))
    context_menu.add_command(label="Вставить", command=lambda: paste_text(widget))
    context_menu.add_separator()
    context_menu.add_command(label="Очистить", command=lambda: clear_text(widget))
    
    # Привязываем появление меню к правой кнопке мыши
    widget.bind("<Button-3>", lambda event: show_context_menu(event, context_menu))
    
    return context_menu

def show_context_menu(event, menu):
    """Отображает контекстное меню в позиции клика правой кнопкой мыши"""
    menu.tk_popup(event.x_root, event.y_root)

def copy_all_text(widget):
    """Копирует весь текст из виджета в буфер обмена"""
    text = widget.get("1.0", tk.END).rstrip()  # rstrip убирает последний перенос строки
    root.clipboard_clear()
    root.clipboard_append(text)
    
def paste_text(widget):
    """Вставляет текст из буфера обмена в текущую позицию курсора"""
    try:
        text = root.clipboard_get()
        widget.insert(tk.INSERT, text)
    except tk.TclError:
        # Буфер обмена пуст или недоступен
        pass
        
def clear_text(widget):
    """Очищает всё содержимое текстового виджета"""
    widget.delete("1.0", tk.END)

def create_labeled_text(master, label_text, initial_text="", height=5):
    frame = tk.Frame(master)
    label = tk.Label(frame, text=label_text)
    label.pack(anchor="w")
    text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=height)
    text.pack(fill="both", expand=True)
    text.insert(tk.END, initial_text) 
    
    # Добавляем контекстное меню
    create_context_menu(text)
    
    frame.pack(fill="both", expand=True, padx=10, pady=5)
    return text

def run_analysis():
    logger.info("Starting analysis")
    requirements = requirements_text.get("1.0", tk.END).strip()
    code = code_text.get("1.0", tk.END).strip()
    test_cases = test_cases_text.get("1.0", tk.END).strip()
    documentation = documentation_text.get("1.0", tk.END).strip()
    
    semantic_db_content = semantic_db_text.get("1.0", tk.END).strip()
    
    # Проверка и обработка семантической базы данных
    try:
        if semantic_db_content:
            semantic_db = json.loads(semantic_db_content)
            # Проверяем, является ли семантическая база словарем сервисов или старым форматом
            if not isinstance(semantic_db, dict) or "documents" in semantic_db:
                # Старый формат, преобразуем в словарь сервисов если это список документов
                if "documents" in semantic_db and isinstance(semantic_db["documents"], list):
                    documents = semantic_db["documents"]
                    # Просто используем список документов как есть
                    pass
                else:
                    # Пустой или неверный формат
                    semantic_db = {"documents": []}
        else:
            # Пустая строка, используем пустой словарь
            semantic_db = {"documents": []}
        
        logger.info(f"Parsed semantic DB with {len(semantic_db)} entries")
    except json.JSONDecodeError as e:
        error_msg = f"Неверный формат JSON для семантической базы: {str(e)}"
        logger.error(error_msg)
        messagebox.showerror("Ошибка", error_msg)
        return

    if not requirements or not code or not test_cases:
        messagebox.showwarning("Предупреждение", "Пожалуйста, заполните все обязательные поля.")
        return

    api_url = "http://localhost:8080/analyze"  

    payload = {
        "requirements": requirements,
        "code": code,
        "test_cases": test_cases,
        "documentation": documentation,
        "semantic_db": semantic_db
    }

    try:
        logger.info(f"Sending request to {api_url}")
        response = requests.post(api_url, json=payload, timeout=300)  # 5-minute timeout
        
        # Log the response status and headers
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # Try to parse as JSON
        try:
            response_data = response.json()
            logger.info("Successfully parsed response as JSON")
            
            # Check for error details in the response
            if "error_details" in response_data and response_data["error_details"]:
                error_details = response_data["error_details"]
                error_type = error_details.get("error_type", "Unknown")
                error_msg = error_details.get("error", "Unknown error")
                stack_trace = error_details.get("stack_trace", "")
                
                logger.error(f"Server returned error: {error_type}: {error_msg}")
                logger.error(f"Server stack trace: {stack_trace}")
                
                # Include error details in the result
                result = response_data.get("final_report", f"Ошибка при анализе: {error_msg}")
                bugs_count = response_data.get("bugs_count", 0)
                bugs_explanations = response_data.get("bugs_explanations", "")
                detailed_bugs = response_data.get("detailed_bugs", [])
                
                # Show error in a dialog
                messagebox.showerror("Ошибка сервера", 
                                    f"Сервер вернул ошибку: {error_type}: {error_msg}\n\n"
                                    "Подробности смотрите в логах.")
            else:
                # Normal response
                result = response_data.get("final_report", "Нет данных в ответе.")
                bugs_count = response_data.get("bugs_count", "N/A")
                bugs_explanations = response_data.get("bugs_explanations", "")
                detailed_bugs = response_data.get("detailed_bugs", [])
        except json.JSONDecodeError:
            # Response is not JSON, use text
            logger.error(f"Failed to parse response as JSON. Raw response: {response.text[:500]}...")
            result = f"Ошибка парсинга ответа от сервера. Текст ответа: {response.text[:1000]}..."
            bugs_count = "N/A"
            bugs_explanations = ""
            detailed_bugs = []
            messagebox.showerror("Ошибка парсинга", "Не удалось распарсить ответ сервера как JSON.")
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Ошибка при отправке запроса: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        if isinstance(e, requests.exceptions.ConnectionError):
            error_msg = f"Не удалось подключиться к серверу: {str(e)}\n\nПроверьте, запущен ли сервер по адресу http://localhost:8080"
        elif isinstance(e, requests.exceptions.Timeout):
            error_msg = "Превышено время ожидания ответа от сервера. Возможно, анализ слишком сложный."
        elif isinstance(e, requests.exceptions.HTTPError):
            if hasattr(e, 'response') and e.response is not None:
                # Try to get more detailed error from response
                try:
                    response_data = e.response.json()
                    if "detail" in response_data:
                        error_msg = f"Ошибка HTTP: {e.response.status_code} - {response_data['detail']}"
                    else:
                        error_msg = f"Ошибка HTTP: {e.response.status_code} - {e.response.reason}"
                except json.JSONDecodeError:
                    # Response is not JSON
                    error_msg = f"Ошибка HTTP: {e.response.status_code} - {e.response.reason}\n\nТекст ответа: {e.response.text[:500]}"
            else:
                error_msg = f"Ошибка HTTP: {str(e)}"
        
        result = f"Ошибка при отправке запроса: {error_msg}"
        bugs_count = "N/A"
        bugs_explanations = ""
        detailed_bugs = []
        
        messagebox.showerror("Ошибка соединения", error_msg)
    except Exception as e:
        error_msg = f"Неизвестная ошибка: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        result = f"Неизвестная ошибка: {error_msg}"
        bugs_count = "N/A"
        bugs_explanations = ""
        detailed_bugs = []
        
        messagebox.showerror("Неизвестная ошибка", error_msg)

    # Создаем окно с результатами
    create_result_window(result, bugs_count, bugs_explanations, detailed_bugs)

def create_result_window(result, bugs_count, bugs_explanations, detailed_bugs):
    """Создает окно с результатами анализа"""
    result_window = tk.Toplevel(root)
    result_window.title("Результат анализа")
    result_window.geometry("900x700")
    
    bugs_label = tk.Label(result_window, text=f"Прогнозируемое количество багов: {bugs_count}")
    bugs_label.pack(pady=5)
    
    # Добавляем вкладки для разных вариантов просмотра
    tab_control = tk.Frame(result_window)
    tab_control.pack(fill="both", expand=True, padx=10, pady=5)
    
    tab_buttons_frame = tk.Frame(tab_control)
    tab_buttons_frame.pack(fill="x")
    
    content_frame = tk.Frame(tab_control)
    content_frame.pack(fill="both", expand=True)
    
    # Создаем текстовый виджет для отображения результатов в текстовом формате
    text_result = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD)
    
    # Если есть поддержка HTML для Markdown
    if MARKDOWN_SUPPORT:
        # Создаем HTML-виджет для отображения Markdown
        html_content = md_to_html(result)
        html_result = HTMLLabel(content_frame, html=html_content)
        
        # Функции для переключения между вкладками
        def show_text_view():
            html_result.pack_forget()
            text_result.pack(fill="both", expand=True)
            text_btn.configure(relief=tk.SUNKEN, bg="lightblue")
            html_btn.configure(relief=tk.RAISED, bg="SystemButtonFace")
            
        def show_html_view():
            text_result.pack_forget()
            html_result.pack(fill="both", expand=True)
            html_btn.configure(relief=tk.SUNKEN, bg="lightblue")
            text_btn.configure(relief=tk.RAISED, bg="SystemButtonFace")
            
        # Создаем кнопки для переключения между вкладками
        text_btn = tk.Button(tab_buttons_frame, text="Текстовый вид", command=show_text_view)
        text_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        html_btn = tk.Button(tab_buttons_frame, text="Markdown вид", command=show_html_view)
        html_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # По умолчанию показываем Markdown-вид
        show_html_view()
    else:
        # Если нет поддержки Markdown, показываем только текстовый вид
        text_result.pack(fill="both", expand=True)
    
    # Заполняем текстовое поле результатом
    text_result.insert(tk.END, result)
    
    # Добавляем контекстное меню и к результату тоже
    create_context_menu(text_result)
    
    # Сделаем текст в окне результатов доступным только для чтения
    text_result.configure(state="disabled")
    
    # Добавляем кнопку для сохранения результата в файл
    def save_result():
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(defaultextension=".md", 
                                               filetypes=[("Markdown", "*.md"), ("Текстовый файл", "*.txt"), ("Все файлы", "*.*")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                messagebox.showinfo("Сохранение", f"Результат успешно сохранен в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    save_btn = tk.Button(result_window, text="Сохранить результат", command=save_result)
    save_btn.pack(pady=10)
    
    # Добавляем кнопку для отображения технической информации об ошибке
    if "error" in result.lower() or "ошибка" in result.lower():
        def show_error_details():
            error_window = tk.Toplevel(result_window)
            error_window.title("Технические детали ошибки")
            error_window.geometry("800x600")
            
            error_text = scrolledtext.ScrolledText(error_window, wrap=tk.WORD)
            error_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Добавляем контекстное меню к виджету с деталями ошибки
            create_context_menu(error_text)
            
            # Заполняем информацией о багах и объяснениями
            error_text.insert(tk.END, f"Количество багов: {bugs_count}\n\n")
            error_text.insert(tk.END, f"Объяснения по багам:\n{bugs_explanations}\n\n")
            error_text.insert(tk.END, "Детальная информация о багах:\n")
            
            for i, bug in enumerate(detailed_bugs, 1):
                error_text.insert(tk.END, f"\nБаг #{i}:\n")
                for key, value in bug.items():
                    if value:  # Только непустые значения
                        error_text.insert(tk.END, f"{key}: {value}\n")
            
            # Добавляем содержимое логов
            try:
                with open('gui.log', 'r') as f:
                    log_content = f.read()
                error_text.insert(tk.END, "\n\nСодержимое лога GUI:\n\n")
                error_text.insert(tk.END, log_content)
            except Exception as e:
                error_text.insert(tk.END, f"\n\nНе удалось прочитать лог GUI: {str(e)}")
            
            error_text.configure(state="disabled")
        
        error_btn = tk.Button(result_window, text="Показать технические детали", command=show_error_details)
        error_btn.pack(pady=5)

# Создаем пример JSON для семантической базы
example_semantic_db = '''{
    "AuthService": "Сервис аутентификации пользователей. Поддерживает регистрацию, вход, восстановление пароля и т.д.",
    "PaymentService": "Сервис обработки платежей. Поддерживает различные платежные системы.",
    "NotificationService": "Сервис отправки уведомлений через email, SMS, push и т.д.",
    "StorageService": "Сервис хранения файлов и данных с резервным копированием."
}'''

root = tk.Tk()
root.title("AI-Ассистент для анализа кода")
root.geometry("1000x800")

requirements_text = create_labeled_text(root, "Требования:", "Введите требования здесь...")
code_text = create_labeled_text(root, "Код:", "Вставьте код сюда...")
test_cases_text = create_labeled_text(root, "Тест-кейсы:", "Опишите тест-кейсы...")
documentation_text = create_labeled_text(root, "Документация:", "Добавьте документацию...")
semantic_db_text = create_labeled_text(root, "Семантическая база (JSON - словарь с описаниями сервисов):", example_semantic_db, height=6)

# Добавляем справку по формату семантической базы
help_label = tk.Label(root, text="Формат семантической базы: JSON-словарь, где ключи - названия сервисов, а значения - их описания.", 
                     font=("Arial", 8), fg="gray")
help_label.pack(pady=0)

analyze_button = tk.Button(root, text="Запустить анализ", command=run_analysis)
analyze_button.pack(pady=10)

# Добавление кнопки для просмотра последнего лога при возникновении ошибок
def show_logs():
    log_window = tk.Toplevel(root)
    log_window.title("Журнал событий")
    log_window.geometry("800x600")
    
    log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD)
    log_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Добавляем контекстное меню
    create_context_menu(log_text)
    
    try:
        with open('gui.log', 'r') as f:
            log_content = f.read()
        log_text.insert(tk.END, log_content)
    except Exception as e:
        log_text.insert(tk.END, f"Не удалось прочитать лог: {str(e)}")
    
    # Прокручиваем до конца лога
    log_text.see(tk.END)

# Добавляем кнопку для просмотра логов
logs_button = tk.Button(root, text="Просмотр логов", command=show_logs)
logs_button.pack(pady=5)

# Обработка необработанных исключений
def handle_exception(exc_type, exc_value, exc_traceback):
    """Глобальный обработчик необработанных исключений"""
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    # Показываем диалог с ошибкой
    error_msg = f"{exc_type.__name__}: {exc_value}"
    messagebox.showerror("Необработанная ошибка", 
                        f"Произошла необработанная ошибка:\n\n{error_msg}\n\n"
                        f"Подробности записаны в лог.")

# Регистрируем обработчик необработанных исключений
tk.Tk.report_callback_exception = handle_exception

root.mainloop()