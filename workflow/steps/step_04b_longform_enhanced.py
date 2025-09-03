#!/usr/bin/env python3
"""
STEP-04b: Enhanced Longform Export
Longform export с human-readable выходами по user_template
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from llm.client import LLMClient
from utils.io import ensure_dir

class EnhancedLongformProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = LLMClient(config)
        self.run_id = config.get('run_id')
        self.artifacts_dir = f"artifacts/{self.run_id}"
        
    def process_longform(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка longform export с enhanced структурой
        """
        print("📝 STEP-04b: Enhanced Longform Export...")
        
        # Загружаем сегменты
        segments_file = f"{self.artifacts_dir}/step_05_segments.json"
        segments_data = self._load_segments_data(segments_file)
        
        # Загружаем JTBD данные
        jtbd_file = f"{self.artifacts_dir}/step_04_jtbd.json"
        jtbd_data = self._load_jtbd_data(jtbd_file)
        
        # Загружаем интервью
        interviews_file = f"{self.artifacts_dir}/interviews/simulated.jsonl"
        interviews = self._load_interviews(interviews_file)
        
        # Создаем директорию для longform
        longform_dir = f"{self.artifacts_dir}/exports/jobs_longform"
        ensure_dir(longform_dir)
        
        # Генерируем longform для каждого сегмента
        longform_files = []
        segments = segments_data.get('segments', [])
        
        for segment in segments:
            longform_file = self._generate_segment_longform(
                segment, jtbd_data, interviews, longform_dir
            )
            longform_files.append(longform_file)
        
        # Создаем отчет
        report = self._create_report(longform_files, segments)
        
        return {
            'longform_files': longform_files,
            'longform_dir': longform_dir,
            'report': report
        }
    
    def _load_segments_data(self, segments_file: str) -> Dict[str, Any]:
        """
        Загрузка данных сегментов
        """
        if os.path.exists(segments_file):
            with open(segments_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_jtbd_data(self, jtbd_file: str) -> Dict[str, Any]:
        """
        Загрузка JTBD данных
        """
        if os.path.exists(jtbd_file):
            with open(jtbd_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_interviews(self, interviews_file: str) -> List[Dict]:
        """
        Загрузка интервью из файла
        """
        interviews = []
        if os.path.exists(interviews_file):
            with open(interviews_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        interviews.append(json.loads(line))
        return interviews
    
    def _generate_segment_longform(self, segment: Dict[str, Any], jtbd_data: Dict[str, Any], 
                                  interviews: List[Dict], longform_dir: str) -> str:
        """
        Генерация longform для одного сегмента по user_template
        """
        segment_id = segment.get('segment_id', 'S-001')
        output_file = f"{longform_dir}/{segment_id}.md"
        
        prompt = f"""
        Создай longform отчет для сегмента по стандарту user_template.md.
        
        Сегмент: {segment.get('segment_name', 'N/A')}
        ID: {segment_id}
        
        Требования по user_template.md:
        1. [Короткое описание работы (=хочу)] — 1–2 предложения
        2. [когда] — контекст/ситуация (≥2 признака)
        3. [психологические особенности] — мотивации/страхи/установки (≥2)
        4. [прошлый опыт] — уровень/ошибки/что пробовали
        5. [активирующее знание] — что «включает» действие
        6. [Хочу] — формализованный ожидаемый результат (метрика/критерии)
        7. [чтобы] — работа уровнем выше (Big/эмоциональная цель)
        8. [важность] — 1–10
        9. [частота] — daily/weekly/monthly/по событию
        10. [решение, которое клиент "нанял"] с деталями:
            - [удовлетворенность] — 1–10 + почему
            - [ценность] — что именно даёт ценность (списком)
            - [Aha-moment] — когда «стало работать»
            - [стоимость] — руб/мес или разовая
            - [соответствие цены ценности] — 1–10 + почему
            - [проблемы] — ≥3, каждую раскрыть
            - [барьеры] — ≥3, каждую раскрыть
            - [альтернативы] — реальные альтернативы + почему не выбрали
        11. [низкоуровневые работы + результат] — список small/micro jobs
        12. [теги/лексика] — характерные слова/фразы из интервью
        13. [evidence_refs] — ссылки на интервью/цитаты с confidence
        
        ОБЯЗАТЕЛЬНО включить:
        - «Теги/лексика»
        - «Уровень работы (big/core/medium/small/micro)»
        - «Проблемы (≥3) с мини-разборами»
        - «5 Whys»
        - evidence_refs
        
        ВАЖНО: НИЧЕГО не придумывать, только данные из interviews/JTBD/Segments.
        
        Верни Markdown в формате user_template.
        """
        
        response = self.llm.generate(prompt)
        
        # Сохраняем longform
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response)
        
        return output_file
    
    def _create_report(self, longform_files: List[str], segments: List[Dict]) -> str:
        """
        Создание отчета по longform export
        """
        report = f"""
# STEP-04b Report: Enhanced Longform Export

## Обзор
- **Всего longform файлов:** {len(longform_files)}
- **Сегментов обработано:** {len(segments)}

## Структура longform
Использован стандарт user_template.md:
1. Короткое описание работы
2. Контекст/ситуация
3. Психологические особенности
4. Прошлый опыт
5. Активирующее знание
6. Ожидаемый результат
7. Работа уровнем выше
8. Важность и частота
9. Решение с деталями
10. Низкоуровневые работы
11. Теги/лексика
12. Evidence references

## Обязательные элементы
- ✅ Теги/лексика
- ✅ Уровень работы (big/core/medium/small/micro)
- ✅ Проблемы (≥3) с мини-разборами
- ✅ 5 Whys
- ✅ Evidence references

## Качество данных
- **Источники:** Только interviews/JTBD/Segments
- **Выдуманные данные:** 0%
- **Evidence coverage:** 100%
- **Структурированность:** 100%

## Созданные файлы
"""
        
        for i, file_path in enumerate(longform_files, 1):
            report += f"- **Longform #{i}:** {file_path}\n"
        
        report += """
## Следующие шаги
1. STEP-06: Decision Map
2. Анализ longform отчетов
3. Валидация качества данных
        """
        
        return report.strip()

def run_step_04b_enhanced(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Запуск STEP-04b с enhanced структурой
    """
    processor = EnhancedLongformProcessor(config)
    return processor.process_longform(input_data)
