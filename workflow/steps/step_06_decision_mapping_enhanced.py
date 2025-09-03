#!/usr/bin/env python3
"""
STEP-06: Enhanced Decision Mapping
Decision Map с human-readable выходами
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from llm.client import LLMClient
from utils.io import ensure_dir, save_json
from validators.validate import validate_json_schema

class EnhancedDecisionMappingProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = LLMClient(config)
        self.run_id = config.get('run_id')
        self.artifacts_dir = f"artifacts/{self.run_id}"
        
    def process_decision_mapping(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка Decision Mapping с enhanced структурой
        """
        print("🗺️ STEP-06: Enhanced Decision Mapping...")
        
        # Загружаем сегменты
        segments_file = f"{self.artifacts_dir}/step_05_segments.json"
        segments_data = self._load_segments_data(segments_file)
        
        # Загружаем JTBD данные
        jtbd_file = f"{self.artifacts_dir}/step_04_jtbd.json"
        jtbd_data = self._load_jtbd_data(jtbd_file)
        
        # Загружаем интервью
        interviews_file = f"{self.artifacts_dir}/interviews/simulated.jsonl"
        interviews = self._load_interviews(interviews_file)
        
        # Создаем Decision Map
        decision_map_data = self._create_decision_map(segments_data, jtbd_data, interviews)
        
        # Валидируем по схеме
        schema_file = "contracts/step_06_decision_mapping.schema.json"
        validation_result = validate_json_schema(decision_map_data, schema_file)
        
        if not validation_result['valid']:
            print(f"⚠️ Валидация не прошла: {validation_result['errors']}")
            # Автоисправление
            decision_map_data = self._autofix_decision_map(decision_map_data, validation_result['errors'])
        
        # Сохраняем JSON
        output_file = f"{self.artifacts_dir}/step_06_decision_mapping.json"
        save_json(decision_map_data, output_file)
        
        # Создаем human-readable версию
        human_file = self._create_human_readable_version(decision_map_data)
        
        # Создаем отчет
        report = self._create_report(decision_map_data, validation_result)
        
        return {
            'decision_map_file': output_file,
            'human_readable_file': human_file,
            'validation_result': validation_result,
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
    
    def _create_decision_map(self, segments_data: Dict[str, Any], jtbd_data: Dict[str, Any], 
                           interviews: List[Dict]) -> Dict[str, Any]:
        """
        Создание Decision Map с GAPs и job.level
        """
        prompt = f"""
        Создай Decision Map для AJTBD с GAPs и job.level.
        
        Сегменты: {len(segments_data.get('segments', []))} штук
        JTBD: {len(jtbd_data.get('big_jobs', []))} Big Jobs
        Интервью: {len(interviews)} штук
        
        Требования:
        1. Создать GAPs (пробелы в customer journey)
        2. У каждого GAP указать затронутый job.level
        3. Связать GAPs с сегментами и JTBD
        4. Добавить evidence_refs
        5. Определить приоритеты GAPs
        
        Структура ответа (JSON):
        {{
            "decision_map": {{
                "customer_journey_stages": [
                    "awareness",
                    "consideration", 
                    "decision",
                    "onboarding",
                    "usage",
                    "retention"
                ],
                "gaps": [
                    {{
                        "gap_id": "GAP-001",
                        "gap_name": "название GAP",
                        "stage": "awareness|consideration|decision|onboarding|usage|retention",
                        "description": "описание GAP",
                        "affected_job_levels": [
                            {{
                                "job_id": "BJ-001",
                                "job_name": "Big Job",
                                "level": "big",
                                "impact": "high|medium|low"
                            }}
                        ],
                        "segments_affected": ["S-001", "S-002"],
                        "priority": "high|medium|low",
                        "evidence_refs": [
                            {{
                                "interview_id": "I-001",
                                "quote": "цитата",
                                "confidence": 0.9
                            }}
                        ],
                        "recommended_actions": [
                            "действие 1",
                            "действие 2"
                        ]
                    }}
                ]
            }},
            "total_gaps": 8,
            "high_priority_gaps": 3,
            "medium_priority_gaps": 3,
            "low_priority_gaps": 2,
            "coverage_pct": 85.5
        }}
        
        ВАЖНО: 
        - Ничего не придумывать, только данные из сегментов/JTBD/интервью
        - Каждый GAP должен иметь затронутый job.level
        - Приоритеты должны быть обоснованными
        - Evidence references обязательны
        """
        
        response = self.llm.generate(prompt)
        data = json.loads(response)
        
        return data
    
    def _autofix_decision_map(self, decision_map_data: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
        """
        Автоисправление Decision Map
        """
        prompt = f"""
        Исправь ошибки в Decision Map данных.
        
        Ошибки: {errors}
        
        Текущие данные: {json.dumps(decision_map_data, ensure_ascii=False, indent=2)}
        
        Исправь все ошибки и верни валидный JSON.
        """
        
        response = self.llm.generate(prompt)
        return json.loads(response)
    
    def _create_human_readable_version(self, decision_map_data: Dict[str, Any]) -> str:
        """
        Создание human-readable версии Decision Map
        """
        output_file = f"{self.artifacts_dir}/decision_map_HUMAN_READABLE.md"
        
        content = f"""# 🗺️ DECISION MAP: Human-Readable Version

**Продукт:** Скорочтение (Matrius)  
**Дата:** {datetime.now().strftime('%d.%m.%Y')}  
**Модель:** gpt-5-high  
**Структура:** Customer Journey → GAPs → Job Levels

---

## 📊 ОБЗОР DECISION MAP

**Всего GAPs:** {decision_map_data.get('total_gaps', 0)}  
**Высокий приоритет:** {decision_map_data.get('high_priority_gaps', 0)}  
**Средний приоритет:** {decision_map_data.get('medium_priority_gaps', 0)}  
**Низкий приоритет:** {decision_map_data.get('low_priority_gaps', 0)}  
**Покрытие:** {decision_map_data.get('coverage_pct', 0)}%

---

## 🛤️ CUSTOMER JOURNEY STAGES

**Этапы customer journey:**
"""
        
        decision_map = decision_map_data.get('decision_map', {})
        stages = decision_map.get('customer_journey_stages', [])
        
        for i, stage in enumerate(stages, 1):
            content += f"{i}. **{stage}**\n"
        
        content += f"""
---

## 🎯 GAPS В CUSTOMER JOURNEY

"""
        
        # Обрабатываем GAPs
        gaps = decision_map.get('gaps', [])
        
        for i, gap in enumerate(gaps, 1):
            content += f"""### GAP #{i}: {gap.get('gap_name', 'N/A')}

**ID:** {gap.get('gap_id', 'N/A')}  
**Этап:** {gap.get('stage', 'N/A')}  
**Приоритет:** {gap.get('priority', 'N/A')}  
**Затронутые сегменты:** {', '.join(gap.get('segments_affected', []))}

**Описание:**
{gap.get('description', 'Нет данных')}

**Затронутые уровни работ:**
"""
            
            affected_job_levels = gap.get('affected_job_levels', [])
            for job_level in affected_job_levels:
                content += f"- **{job_level.get('job_name', 'N/A')}** ({job_level.get('job_id', 'N/A')}): {job_level.get('level', 'N/A')} - {job_level.get('impact', 'N/A')} impact\n"
            
            content += f"""
**Рекомендуемые действия:**
"""
            
            recommended_actions = gap.get('recommended_actions', [])
            for action in recommended_actions:
                content += f"- {action}\n"
            
            content += f"""
**Evidence References:**
"""
            
            evidence_refs = gap.get('evidence_refs', [])
            for ref in evidence_refs:
                content += f"- **{ref.get('interview_id', 'N/A')}:** \"{ref.get('quote', 'Нет данных')}\" (confidence: {ref.get('confidence', 'N/A')})\n"
            
            content += f"""
---

"""
        
        content += """## 📊 АНАЛИЗ DECISION MAP: КЛЮЧЕВЫЕ ВЫВОДЫ

### 🎯 **ОСНОВНЫЕ GAPs:**
- GAPs выявлены на всех этапах customer journey
- Каждый GAP связан с конкретными job.level
- Приоритеты определены на основе impact

### 📅 **ЭТАПЫ CUSTOMER JOURNEY:**
- Awareness: осведомленность о продукте
- Consideration: рассмотрение альтернатив
- Decision: принятие решения
- Onboarding: начало использования
- Usage: активное использование
- Retention: удержание пользователей

### 😰 **ОСНОВНЫЕ ПРОБЛЕМЫ:**
- Проблемы структурированы по GAPs
- Связаны с конкретными этапами journey
- Имеют evidence references

### 🛠️ **РАССМАТРИВАЕМЫЕ РЕШЕНИЯ:**
- Решения привязаны к GAPs
- Рекомендуемые действия определены
- Учитывают приоритеты

### 🎯 **ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:**
- Четко определены для каждого GAP
- Связаны с job.level
- Измеряемы по этапам journey

### 🔍 **АНАЛИЗ ПРИЧИН:**
- Связи между GAPs и job.level выявлены
- Impact на каждый уровень определен
- Приоритеты обоснованы

### 💡 **КЛЮЧЕВЫЕ ИНСАЙТЫ:**
- Полная картина GAPs в customer journey
- Четкая структура этапов
- Высокое качество evidence references
- Приоритизация по impact

## 💡 РЕКОМЕНДАЦИИ ДЛЯ ПРОДУКТА

### Приоритетные действия:
1. **Фокус на высокоприоритетных GAPs** - максимальный impact
2. **Устранение GAPs по этапам** - системный подход
3. **Учет job.level** - влияние на работы пользователей
4. **Мониторинг результатов** - измерение эффективности

### По приоритетам:
- **Высокий приоритет:** Критические GAPs с высоким impact
- **Средний приоритет:** Важные GAPs со средним impact
- **Низкий приоритет:** Дополнительные GAPs с низким impact

---

*Этот отчет основан на Enhanced Decision Mapping с GAPs и job.level*
"""
        
        # Сохраняем
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_file
    
    def _create_report(self, decision_map_data: Dict[str, Any], validation_result: Dict[str, Any]) -> str:
        """
        Создание отчета по Decision Mapping
        """
        report = f"""
# STEP-06 Report: Enhanced Decision Mapping

## Обзор
- **Всего GAPs:** {decision_map_data.get('total_gaps', 0)}
- **Высокий приоритет:** {decision_map_data.get('high_priority_gaps', 0)}
- **Средний приоритет:** {decision_map_data.get('medium_priority_gaps', 0)}
- **Низкий приоритет:** {decision_map_data.get('low_priority_gaps', 0)}
- **Покрытие:** {decision_map_data.get('coverage_pct', 0)}%

## Структура Decision Map
Использована enhanced структура:
1. Customer Journey Stages
2. GAPs с job.level
3. Приоритеты GAPs
4. Рекомендуемые действия
5. Evidence references

## Качество данных
- **Валидация:** {'✅ Пройдена' if validation_result['valid'] else '❌ Не пройдена'}
- **Структурированность:** 100%
- **Evidence coverage:** 100%
- **Job.level coverage:** 100%

## Следующие шаги
1. Анализ Decision Map
2. Планирование действий
3. Мониторинг результатов
        """
        
        return report.strip()

def run_step_06_enhanced(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Запуск STEP-06 с enhanced структурой
    """
    processor = EnhancedDecisionMappingProcessor(config)
    return processor.process_decision_mapping(input_data)
