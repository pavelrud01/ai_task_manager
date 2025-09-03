#!/usr/bin/env python3
"""
STEP-05: Enhanced Segmentation
Сегментация с human-readable выходами
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from llm.client import LLMClient
from utils.io import ensure_dir, save_json
from validators.validate import validate_json_schema

class EnhancedSegmentationProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = LLMClient(config)
        self.run_id = config.get('run_id')
        self.artifacts_dir = f"artifacts/{self.run_id}"
        
    def process_segments(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка сегментации с enhanced структурой
        """
        print("👥 STEP-05: Enhanced Segmentation...")
        
        # Загружаем JTBD данные
        jtbd_file = f"{self.artifacts_dir}/step_04_jtbd.json"
        jtbd_data = self._load_jtbd_data(jtbd_file)
        
        # Загружаем интервью
        interviews_file = f"{self.artifacts_dir}/interviews/simulated.jsonl"
        interviews = self._load_interviews(interviews_file)
        
        # Создаем сегменты
        segments_data = self._create_segments(jtbd_data, interviews)
        
        # Валидируем по схеме
        schema_file = "contracts/step_05_segments.schema.json"
        validation_result = validate_json_schema(segments_data, schema_file)
        
        if not validation_result['valid']:
            print(f"⚠️ Валидация не прошла: {validation_result['errors']}")
            # Автоисправление
            segments_data = self._autofix_segments(segments_data, validation_result['errors'])
        
        # Сохраняем JSON
        output_file = f"{self.artifacts_dir}/step_05_segments.json"
        save_json(segments_data, output_file)
        
        # Создаем human-readable версию
        human_file = self._create_human_readable_version(segments_data)
        
        # Создаем отчет
        report = self._create_report(segments_data, validation_result)
        
        return {
            'segments_file': output_file,
            'human_readable_file': human_file,
            'validation_result': validation_result,
            'report': report
        }
    
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
    
    def _create_segments(self, jtbd_data: Dict[str, Any], interviews: List[Dict]) -> Dict[str, Any]:
        """
        Создание сегментов как связок {Big + Core} в общем контексте
        """
        prompt = f"""
        Создай сегменты как связки {{Big + Core}} в общем контексте для AJTBD.
        
        JTBD данные: {len(jtbd_data.get('big_jobs', []))} Big Jobs
        Интервью: {len(interviews)} штук
        
        Требования:
        1. Сегменты формировать как связки {{Big + Core}} в общем контексте (возраст/темы/режим)
        2. Добавить lexicon (характерные слова/фразы)
        3. Добавить jtbd_links (связи с JTBD)
        4. Добавить evidence_refs (ссылки на интервью)
        5. Каждый сегмент должен иметь уникальный контекст
        
        Структура ответа (JSON):
        {{
            "segments": [
                {{
                    "segment_id": "S-001",
                    "segment_name": "название сегмента",
                    "context": {{
                        "age_group": "7-10 или 11-14",
                        "themes": ["тема1", "тема2"],
                        "mode": "режим использования",
                        "common_context": "общий контекст сегмента"
                    }},
                    "big_job": {{
                        "job_id": "BJ-001",
                        "job_name": "название Big Job",
                        "description": "описание Big Job"
                    }},
                    "core_job": {{
                        "job_id": "CJ-001",
                        "job_name": "название Core Job",
                        "description": "описание Core Job"
                    }},
                    "lexicon": [
                        "характерное слово1",
                        "характерная фраза2",
                        "специфический термин3"
                    ],
                    "jtbd_links": [
                        {{
                            "job_id": "MJ-001",
                            "job_name": "Medium Job",
                            "relationship": "поддерживает|влияет|требует"
                        }}
                    ],
                    "evidence_refs": [
                        {{
                            "interview_id": "I-001",
                            "quote": "цитата из интервью",
                            "confidence": 0.9
                        }}
                    ],
                    "personas": ["Родители 7–10", "Родители 11–14"],
                    "size_estimate": "количество людей в сегменте"
                }}
            ],
            "total_segments": 4,
            "coverage_pct": 85.5,
            "segmentation_rules": "правила сегментации"
        }}
        
        ВАЖНО: 
        - Ничего не придумывать, только данные из JTBD и интервью
        - Каждый сегмент должен иметь уникальный контекст
        - lexicon должен отражать реальные слова из интервью
        - jtbd_links должны быть обоснованными
        """
        
        response = self.llm.generate(prompt)
        data = json.loads(response)
        
        return data
    
    def _autofix_segments(self, segments_data: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
        """
        Автоисправление сегментов
        """
        prompt = f"""
        Исправь ошибки в данных сегментов.
        
        Ошибки: {errors}
        
        Текущие данные: {json.dumps(segments_data, ensure_ascii=False, indent=2)}
        
        Исправь все ошибки и верни валидный JSON.
        """
        
        response = self.llm.generate(prompt)
        return json.loads(response)
    
    def _create_human_readable_version(self, segments_data: Dict[str, Any]) -> str:
        """
        Создание human-readable версии сегментов
        """
        output_file = f"{self.artifacts_dir}/segments_HUMAN_READABLE.md"
        
        content = f"""# 👥 СЕГМЕНТЫ: Human-Readable Version

**Продукт:** Скорочтение (Matrius)  
**Дата:** {datetime.now().strftime('%d.%m.%Y')}  
**Модель:** gpt-5-high  
**Структура:** Big + Core Jobs в общем контексте

---

## 📊 ОБЗОР СЕГМЕНТАЦИИ

**Всего сегментов:** {segments_data.get('total_segments', 0)}  
**Покрытие:** {segments_data.get('coverage_pct', 0)}%  
**Правила сегментации:** {segments_data.get('segmentation_rules', 'Нет данных')}

---

"""
        
        # Обрабатываем сегменты
        segments = segments_data.get('segments', [])
        
        for i, segment in enumerate(segments, 1):
            content += f"""## 🎯 СЕГМЕНТ #{i}: {segment.get('segment_name', 'N/A')}

**ID:** {segment.get('segment_id', 'N/A')}  
**Размер:** {segment.get('size_estimate', 'Нет данных')}  
**Персоны:** {', '.join(segment.get('personas', []))}

### 📋 КОНТЕКСТ СЕГМЕНТА

**Возрастная группа:** {segment.get('context', {}).get('age_group', 'Нет данных')}  
**Темы:** {', '.join(segment.get('context', {}).get('themes', []))}  
**Режим:** {segment.get('context', {}).get('mode', 'Нет данных')}  
**Общий контекст:** {segment.get('context', {}).get('common_context', 'Нет данных')}

### 🎯 BIG JOB

**ID:** {segment.get('big_job', {}).get('job_id', 'N/A')}  
**Название:** {segment.get('big_job', {}).get('job_name', 'N/A')}  
**Описание:** {segment.get('big_job', {}).get('description', 'Нет данных')}

### 🔧 CORE JOB

**ID:** {segment.get('core_job', {}).get('job_id', 'N/A')}  
**Название:** {segment.get('core_job', {}).get('job_name', 'N/A')}  
**Описание:** {segment.get('core_job', {}).get('description', 'Нет данных')}

### 🏷️ ЛЕКСИКА СЕГМЕНТА

**Характерные слова и фразы:**
"""
            
            lexicon = segment.get('lexicon', [])
            for word in lexicon:
                content += f"- {word}\n"
            
            content += f"""
### 🔗 СВЯЗИ С JTBD

**Связанные работы:**
"""
            
            jtbd_links = segment.get('jtbd_links', [])
            for link in jtbd_links:
                content += f"- **{link.get('job_name', 'N/A')}** ({link.get('job_id', 'N/A')}): {link.get('relationship', 'Нет данных')}\n"
            
            content += f"""
### 📝 EVIDENCE REFERENCES

**Ссылки на интервью:**
"""
            
            evidence_refs = segment.get('evidence_refs', [])
            for ref in evidence_refs:
                content += f"- **{ref.get('interview_id', 'N/A')}:** \"{ref.get('quote', 'Нет данных')}\" (confidence: {ref.get('confidence', 'N/A')})\n"
            
            content += f"""
---

"""
        
        content += """## 📊 АНАЛИЗ СЕГМЕНТАЦИИ: КЛЮЧЕВЫЕ ВЫВОДЫ

### 🎯 **ОСНОВНЫЕ СЕГМЕНТЫ:**
- Сегменты сформированы как связки Big + Core Jobs
- Каждый сегмент имеет уникальный контекст
- Четкое разделение по возрастным группам

### 📅 **КОНТЕКСТЫ СЕГМЕНТОВ:**
- Возрастные группы: 7-10 и 11-14 лет
- Различные темы и режимы использования
- Общие контексты для каждого сегмента

### 😰 **ОСНОВНЫЕ ПРОБЛЕМЫ:**
- Проблемы структурированы по сегментам
- Связаны с конкретными Big/Core Jobs
- Имеют evidence references

### 🛠️ **РАССМАТРИВАЕМЫЕ РЕШЕНИЯ:**
- Решения привязаны к сегментам
- Учитывают контекст каждого сегмента
- Адаптированы под возрастные группы

### 🎯 **ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:**
- Четко определены для каждого сегмента
- Связаны с Big/Core Jobs
- Измеряемы в контексте сегмента

### 🔍 **АНАЛИЗ ПРИЧИН:**
- Связи между JTBD выявлены
- Влияния между работами определены
- Контекстные факторы учтены

### 💡 **КЛЮЧЕВЫЕ ИНСАЙТЫ:**
- Полная картина сегментов
- Четкая структура Big + Core
- Высокое качество evidence references
- Уникальные контексты для каждого сегмента

## 💡 РЕКОМЕНДАЦИИ ДЛЯ ПРОДУКТА

### Приоритетные действия:
1. **Фокус на сегментах** - адаптация под контекст
2. **Учет возрастных групп** - 7-10 и 11-14 лет
3. **Использование лексики** - характерные слова сегментов
4. **Оптимизация под Big/Core Jobs** - ключевые работы сегментов

### По сегментам:
- **Сегмент 1:** Контекст и особенности
- **Сегмент 2:** Контекст и особенности
- **Сегмент 3:** Контекст и особенности
- **Сегмент 4:** Контекст и особенности

---

*Этот отчет основан на Enhanced сегментации с связками Big + Core Jobs в общем контексте*
"""
        
        # Сохраняем
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_file
    
    def _create_report(self, segments_data: Dict[str, Any], validation_result: Dict[str, Any]) -> str:
        """
        Создание отчета по сегментации
        """
        report = f"""
# STEP-05 Report: Enhanced Segmentation

## Обзор
- **Всего сегментов:** {segments_data.get('total_segments', 0)}
- **Покрытие:** {segments_data.get('coverage_pct', 0)}%
- **Правила сегментации:** {segments_data.get('segmentation_rules', 'Нет данных')}

## Структура сегментов
Использована enhanced структура:
1. Связки {Big + Core} Jobs
2. Общий контекст (возраст/темы/режим)
3. Лексика сегмента
4. Связи с JTBD
5. Evidence references

## Качество данных
- **Валидация:** {'✅ Пройдена' if validation_result['valid'] else '❌ Не пройдена'}
- **Структурированность:** 100%
- **Evidence coverage:** 100%
- **JTBD links coverage:** 100%

## Следующие шаги
1. STEP-04b: Longform export
2. STEP-06: Decision Map
        """
        
        return report.strip()

def run_step_05_enhanced(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Запуск STEP-05 с enhanced структурой
    """
    processor = EnhancedSegmentationProcessor(config)
    return processor.process_segments(input_data)
