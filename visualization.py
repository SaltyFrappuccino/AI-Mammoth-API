import os
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots
import base64
import json
import io
import logging
import traceback

logger = logging.getLogger("visualization")

class VisualizationEngine:
    """
    Класс для создания визуализаций результатов анализа соответствия требованиям.
    Генерирует графики и диаграммы для наглядного представления результатов.
    """
    
    def __init__(self, output_dir='visualizations'):
        """
        Инициализирует движок визуализации
        
        Args:
            output_dir (str): Директория для сохранения визуализаций
        """
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
    def generate_compliance_chart(self, compliance_data):
        """
        Создает круговую диаграмму соответствия требованиям
        
        Args:
            compliance_data (dict): Данные о соответствии требованиям
            
        Returns:
            dict: Пути к сохраненным файлам и данные base64 для встраивания
        """
        try:
            code_to_req = compliance_data.get('code_to_requirements_percentage', 0)
            tests_to_req = compliance_data.get('tests_to_requirements_percentage', 0)
            code_to_tests = compliance_data.get('code_to_tests_percentage', 0)
            
            # Создаем круговую диаграмму
            fig = make_subplots(
                rows=1, cols=3,
                specs=[[{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]],
                subplot_titles=["Код → Требования", "Тесты → Требования", "Код → Тесты"]
            )
            
            # Добавляем данные
            colors = ['#2ecc71', '#f39c12']  # Зеленый для соответствия, оранжевый для несоответствия
            
            # Код к требованиям
            fig.add_trace(go.Pie(
                labels=["Соответствует", "Не соответствует"],
                values=[code_to_req, 100-code_to_req],
                marker_colors=colors,
                name="Код → Требования",
                hole=0.7,
                textinfo='percent',
                hoverinfo='label+percent',
            ), 1, 1)
            
            # Тесты к требованиям
            fig.add_trace(go.Pie(
                labels=["Соответствует", "Не соответствует"],
                values=[tests_to_req, 100-tests_to_req],
                marker_colors=colors,
                name="Тесты → Требования",
                hole=0.7,
                textinfo='percent',
                hoverinfo='label+percent',
            ), 1, 2)
            
            # Код к тестам
            fig.add_trace(go.Pie(
                labels=["Соответствует", "Не соответствует"],
                values=[code_to_tests, 100-code_to_tests],
                marker_colors=colors,
                name="Код → Тесты",
                hole=0.7,
                textinfo='percent',
                hoverinfo='label+percent',
            ), 1, 3)
            
            # Добавляем аннотации с процентами в центре
            fig.add_annotation(
                text=f"{code_to_req}%",
                x=0.16, y=0.5,
                font_size=24,
                showarrow=False
            )
            
            fig.add_annotation(
                text=f"{tests_to_req}%",
                x=0.5, y=0.5,
                font_size=24,
                showarrow=False
            )
            
            fig.add_annotation(
                text=f"{code_to_tests}%",
                x=0.84, y=0.5,
                font_size=24,
                showarrow=False
            )
            
            # Настраиваем внешний вид
            fig.update_layout(
                title_text="Соответствие требованиям",
                height=400,
                width=900,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20),
            )
            
            # Сохраняем как HTML и PNG
            html_path = os.path.join(self.output_dir, 'compliance_chart.html')
            img_path = os.path.join(self.output_dir, 'compliance_chart.png')
            
            fig.write_html(html_path)
            fig.write_image(img_path, scale=2)
            
            # Подготавливаем base64 для встраивания в отчет
            img_bytes = io.BytesIO()
            fig.write_image(img_bytes, format='png', scale=2)
            img_bytes.seek(0)
            img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
            
            return {
                'html_path': html_path,
                'img_path': img_path,
                'base64': img_base64
            }
            
        except Exception as e:
            logger.error(f"Ошибка при создании диаграммы соответствия: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def generate_requirements_coverage_chart(self, requirements_analysis_text):
        """
        Создает диаграмму распределения требований по типам и приоритетам
        
        Args:
            requirements_analysis_text (str): Текст анализа требований
            
        Returns:
            dict: Пути к сохраненным файлам и данные base64 для встраивания
        """
        try:
            # Парсим требования из текста анализа
            req_counts = {
                'Функциональные': 0,
                'Нефункциональные': 0,
                'Интеграционные': 0,
                'Безопасность': 0
            }
            
            priority_counts = {
                'Критический': 0,
                'Высокий': 0,
                'Средний': 0,
                'Низкий': 0
            }
            
            # Простой парсер для извлечения информации из текста
            for line in requirements_analysis_text.split('\n'):
                line = line.strip()
                
                # Поиск общего количества требований по категориям
                if "Функциональных:" in line:
                    try:
                        req_counts['Функциональные'] = int(line.split(':')[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                
                elif "Нефункциональных:" in line:
                    try:
                        req_counts['Нефункциональные'] = int(line.split(':')[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                
                elif "Интеграционных:" in line:
                    try:
                        req_counts['Интеграционные'] = int(line.split(':')[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                
                elif "Безопасности:" in line:
                    try:
                        req_counts['Безопасность'] = int(line.split(':')[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                
                # Подсчет приоритетов
                elif "**Приоритет**:" in line:
                    priority = line.split('**Приоритет**:')[1].strip()
                    if priority in priority_counts:
                        priority_counts[priority] += 1
                    elif "Критический" in priority:
                        priority_counts['Критический'] += 1
                    elif "Высокий" in priority:
                        priority_counts['Высокий'] += 1
                    elif "Средний" in priority:
                        priority_counts['Средний'] += 1
                    elif "Низкий" in priority:
                        priority_counts['Низкий'] += 1
            
            # Создаем подграфики
            fig = make_subplots(
                rows=1, cols=2,
                specs=[[{"type": "pie"}, {"type": "pie"}]],
                subplot_titles=["Типы требований", "Приоритеты требований"]
            )
            
            # Данные для типов требований
            labels_types = list(req_counts.keys())
            values_types = list(req_counts.values())
            
            # Данные для приоритетов
            labels_priorities = list(priority_counts.keys())
            values_priorities = list(priority_counts.values())
            
            # Цвета для типов требований
            colors_types = ['#3498db', '#1abc9c', '#9b59b6', '#e74c3c']
            
            # Цвета для приоритетов
            colors_priorities = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71']
            
            # Добавляем график типов требований
            fig.add_trace(
                go.Pie(
                    labels=labels_types,
                    values=values_types,
                    textinfo='label+percent',
                    marker_colors=colors_types,
                    hole=0.3
                ),
                row=1, col=1
            )
            
            # Добавляем график приоритетов
            fig.add_trace(
                go.Pie(
                    labels=labels_priorities,
                    values=values_priorities,
                    textinfo='label+percent',
                    marker_colors=colors_priorities,
                    hole=0.3
                ),
                row=1, col=2
            )
            
            # Настраиваем внешний вид
            fig.update_layout(
                title_text="Анализ требований",
                height=400,
                width=900,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=50),
            )
            
            # Сохраняем как HTML и PNG
            html_path = os.path.join(self.output_dir, 'requirements_chart.html')
            img_path = os.path.join(self.output_dir, 'requirements_chart.png')
            
            fig.write_html(html_path)
            fig.write_image(img_path, scale=2)
            
            # Подготавливаем base64 для встраивания в отчет
            img_bytes = io.BytesIO()
            fig.write_image(img_bytes, format='png', scale=2)
            img_bytes.seek(0)
            img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
            
            return {
                'html_path': html_path,
                'img_path': img_path,
                'base64': img_base64
            }
            
        except Exception as e:
            logger.error(f"Ошибка при создании диаграммы типов требований: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def generate_bugs_chart(self, bug_data):
        """
        Создает диаграмму для визуализации выявленных багов
        
        Args:
            bug_data (dict): Данные о багах
            
        Returns:
            dict: Пути к сохраненным файлам и данные base64 для встраивания
        """
        try:
            bug_count = bug_data.get('bug_count', 0)
            detailed_bugs = bug_data.get('detailed_bugs', [])
            
            # Если нет подробностей о багах, создаем простую визуализацию
            if bug_count == 0 or not detailed_bugs:
                # Создаем простую диаграмму количества багов
                fig = go.Figure()
                
                fig.add_trace(go.Indicator(
                    mode="number+gauge+delta",
                    title={"text": "Количество выявленных багов"},
                    value=bug_count,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 10]},
                        'bar': {'color': "#e74c3c" if bug_count > 0 else "#2ecc71"},
                        'steps': [
                            {'range': [0, 3], 'color': "#2ecc71"},
                            {'range': [3, 7], 'color': "#f39c12"},
                            {'range': [7, 10], 'color': "#e74c3c"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': bug_count
                        }
                    }
                ))
                
                # Настраиваем внешний вид
                fig.update_layout(
                    title_text="Количество потенциальных багов",
                    height=400,
                    width=600,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=60, b=20),
                )
            else:
                # Создаем более подробную диаграмму с классификацией багов
                severity_counts = {
                    'Критическая': 0,
                    'Высокая': 0,
                    'Средняя': 0,
                    'Низкая': 0
                }
                
                # Подсчитываем количество багов по серьезности
                for bug in detailed_bugs:
                    severity = bug.get('severity', '')
                    if 'критич' in severity.lower():
                        severity_counts['Критическая'] += 1
                    elif 'высок' in severity.lower():
                        severity_counts['Высокая'] += 1
                    elif 'средн' in severity.lower():
                        severity_counts['Средняя'] += 1
                    elif 'низк' in severity.lower():
                        severity_counts['Низкая'] += 1
                
                # Создаем подграфики
                fig = make_subplots(
                    rows=1, cols=2,
                    specs=[[{"type": "indicator"}, {"type": "pie"}]],
                    subplot_titles=["Количество багов", "Серьезность багов"]
                )
                
                # Добавляем индикатор количества багов
                fig.add_trace(
                    go.Indicator(
                        mode="number+gauge",
                        title={"text": "Количество багов"},
                        value=bug_count,
                        gauge={
                            'axis': {'range': [None, 10]},
                            'bar': {'color': "#e74c3c" if bug_count > 0 else "#2ecc71"},
                            'steps': [
                                {'range': [0, 3], 'color': "#2ecc71"},
                                {'range': [3, 7], 'color': "#f39c12"},
                                {'range': [7, 10], 'color': "#e74c3c"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': bug_count
                            }
                        }
                    ),
                    row=1, col=1
                )
                
                # Данные для круговой диаграммы серьезности
                labels_severity = list(severity_counts.keys())
                values_severity = list(severity_counts.values())
                
                # Цвета для серьезности багов
                colors_severity = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71']
                
                # Добавляем круговую диаграмму серьезности
                fig.add_trace(
                    go.Pie(
                        labels=labels_severity,
                        values=values_severity,
                        textinfo='label+percent',
                        marker_colors=colors_severity,
                        hole=0.3
                    ),
                    row=1, col=2
                )
                
                # Настраиваем внешний вид
                fig.update_layout(
                    title_text="Анализ потенциальных багов",
                    height=400,
                    width=900,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=60, b=60),
                )
            
            # Сохраняем как HTML и PNG
            html_path = os.path.join(self.output_dir, 'bugs_chart.html')
            img_path = os.path.join(self.output_dir, 'bugs_chart.png')
            
            fig.write_html(html_path)
            fig.write_image(img_path, scale=2)
            
            # Подготавливаем base64 для встраивания в отчет
            img_bytes = io.BytesIO()
            fig.write_image(img_bytes, format='png', scale=2)
            img_bytes.seek(0)
            img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
            
            return {
                'html_path': html_path,
                'img_path': img_path,
                'base64': img_base64
            }
            
        except Exception as e:
            logger.error(f"Ошибка при создании диаграммы багов: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def generate_all_charts(self, analysis_data):
        """
        Создает все диаграммы на основе данных анализа
        
        Args:
            analysis_data (dict): Данные анализа
            
        Returns:
            dict: Словарь с данными всех диаграмм
        """
        charts = {}
        
        # Диаграмма соответствия требованиям
        if 'compliance_result' in analysis_data:
            charts['compliance'] = self.generate_compliance_chart(analysis_data['compliance_result'])
        
        # Диаграмма анализа требований
        if 'requirements_analysis' in analysis_data:
            charts['requirements'] = self.generate_requirements_coverage_chart(analysis_data['requirements_analysis'])
        
        # Диаграмма багов
        if 'bug_estimation' in analysis_data:
            charts['bugs'] = self.generate_bugs_chart(analysis_data['bug_estimation'])
        
        return charts 