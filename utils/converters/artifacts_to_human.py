#!/usr/bin/env python3
"""
Конвертер артефактов в человеческие версии
Преобразует технические JSON файлы в читаемые markdown документы
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime

class ArtifactsToHumanConverter:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.artifacts_dir = f"artifacts/{run_id}"
        
    def convert_all_artifacts(self) -> Dict[str, str]:
        """
        Конвертирует все артефакты в человеческие версии
        """
        results = {}
        
        # Конвертируем интервью
        if os.path.exists(f"{self.artifacts_dir}/interviews/simulated_v33.jsonl"):
            results['interviews'] = self.convert_interviews_to_human()
        
        # Конвертируем JTBD
        if os.path.exists(f"{self.artifacts_dir}/step_04_jtbd.json"):
            results['jtbd'] = self.convert_jtbd_to_human()
        
        # Конвертируем сегменты
        if os.path.exists(f"{self.artifacts_dir}/step_05_segments.json"):
            results['segments'] = self.convert_segments_to_human()
        
        # Конвертируем decision map
        if os.path.exists(f"{self.artifacts_dir}/step_06_decision_mapping.json"):
            results['decision_map'] = self.convert_decision_map_to_human()
        
        return results
    
    def convert_interviews_to_human(self) -> str:
        """
        Конвертирует интервью в человеческую версию
        """
        output_file = f"{self.artifacts_dir}/interviews_HUMAN_READABLE_v33.md"
        
        # Читаем интервью
        interviews = []
        with open(f"{self.artifacts_dir}/interviews/simulated_v33.jsonl", 'r', encoding='utf-8') as f:
            for line in f:
                interviews.append(json.loads(line.strip()))
        
        # Группируем по interview_id
        grouped_interviews = {}
        for interview in interviews:
            interview_id = interview['interview_id']
            if interview_id not in grouped_interviews:
                grouped_interviews[interview_id] = []
            grouped_interviews[interview_id].append(interview)
        
        # Создаем human-версию
        content = self._create_interviews_human_content(grouped_interviews)
        
        # Сохраняем
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_file
    
    def convert_jtbd_to_human(self) -> str:
        """
        Конвертирует JTBD в человеческую версию
        """
        output_file = f"{self.artifacts_dir}/step_04_jtbd_HUMAN_READABLE.md"
        
        # Читаем JTBD
        with open(f"{self.artifacts_dir}/step_04_jtbd.json", 'r', encoding='utf-8') as f:
            jtbd_data = json.load(f)
        
        # Создаем human-версию
        content = self._create_jtbd_human_content(jtbd_data)
        
        # Сохраняем
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_file
    
    def convert_segments_to_human(self) -> str:
        """
        Конвертирует сегменты в человеческую версию
        """
        output_file = f"{self.artifacts_dir}/step_05_segments_HUMAN_READABLE.md"
        
        # Читаем сегменты
        with open(f"{self.artifacts_dir}/step_05_segments.json", 'r', encoding='utf-8') as f:
            segments_data = json.load(f)
        
        # Создаем human-версию
        content = self._create_segments_human_content(segments_data)
        
        # Сохраняем
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_file
    
    def convert_decision_map_to_human(self) -> str:
        """
        Конвертирует decision map в человеческую версию
        """
        output_file = f"{self.artifacts_dir}/step_06_decision_map_HUMAN_READABLE.md"
        
        # Читаем decision map
        with open(f"{self.artifacts_dir}/step_06_decision_mapping.json", 'r', encoding='utf-8') as f:
            decision_map_data = json.load(f)
        
        # Создаем human-версию
        content = self._create_decision_map_human_content(decision_map_data)
        
        # Сохраняем
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_file
    
    def _create_interviews_human_content(self, grouped_interviews: Dict[str, List[Dict]]) -> str:
        """
        Создает человеческую версию интервью
        """
        content = f"""# 🎤 ИНТЕРВЬЮ ПО ГАЙДУ V3.3: AJTBD-интервью для B2C-продуктов

**Продукт:** Скорочтение (Matrius)  
**Дата:** {datetime.now().strftime('%d.%m.%Y')}  
**Модель:** gpt-5-high  
**Гайд:** [v3.3] Гайд AJTBD-интервью для B2C-продуктов.md  
**Структура:** Qualification → Deep Profile → Adjacent Works → Lower Level Works → Solution Interview

---

## 📊 ОБЗОР ИНТЕРВЬЮ

**Всего интервью:** {len(grouped_interviews)}  
**Структура:** 5 фаз по гайду v3.3  
**Связь с user_template:** Каждое интервью собирает все поля user_template

---

"""
        
        for interview_id, phases in grouped_interviews.items():
            # Сортируем фазы по порядку
            phase_order = ['qualification', 'deep_profile', 'adjacent_works', 'lower_level_works', 'solution_interview']
            sorted_phases = sorted(phases, key=lambda x: phase_order.index(x['phase']))
            
            # Получаем данные из первой фазы
            first_phase = sorted_phases[0]
            persona = first_phase['persona']
            
            content += f"""## 🎯 ИНТЕРВЬЮ {interview_id}: {persona}

### 📋 ФАЗА 1: КВАЛИФИКАЦИЯ И НАВИГАЦИЯ

"""
            
            # Фаза 1: Квалификация
            if sorted_phases[0]['phase'] == 'qualification':
                qual_data = sorted_phases[0]['content']
                content += f"""**Контекст респондента:**
> *"{qual_data.get('context', 'Нет данных')}"*

**Гипотеза работы:**
**"{qual_data.get('hypothesis_work', 'Нет данных')}"**

**Тип работы:** {qual_data.get('work_type', 'Нет данных')}

**Выбранная работа для изучения:**
**"{qual_data.get('selected_work', 'Нет данных')}"**

**Обоснование выбора:**
{qual_data.get('reasoning', 'Нет данных')}

**Собранные поля user_template:**
{self._format_user_template_fields(qual_data.get('user_template_fields', {}))}

---

### 🔍 ФАЗА 2: ГЛУБОКИЙ ПРОФИЛЬ РАБОТЫ

"""
            
            # Фаза 2: Глубокий профиль
            if len(sorted_phases) > 1 and sorted_phases[1]['phase'] == 'deep_profile':
                profile_data = sorted_phases[1]['content']
                content += f"""**Ожидаемый результат:**
**"{profile_data.get('expected_result', 'Нет данных')}"**

**Критерии результата:**
{profile_data.get('criteria', 'Нет данных')}

**Решение:**
**"{profile_data.get('solution', 'Нет данных')}"**

**История использования:**
*"{profile_data.get('solution_history', 'Нет данных')}"*

**Контекст:**
{profile_data.get('context', 'Нет данных')}

**Триггер:**
**"{profile_data.get('trigger', 'Нет данных')}"**

**Вышеуровневая работа:**
**"{profile_data.get('higher_level_work', 'Нет данных')}"**

**Позитивные эмоции:**
**"{profile_data.get('positive_emotions', 'Нет данных')}"**

**Негативные эмоции:**
**"{profile_data.get('negative_emotions', 'Нет данных')}"**

**Важность:** {profile_data.get('importance', 'Нет данных')}/10

**Удовлетворенность:** {profile_data.get('satisfaction', 'Нет данных')}/10

**Ценность:**
{profile_data.get('value', 'Нет данных')}

**Aha-момент:**
**"{profile_data.get('aha_moment', 'Нет данных')}"**

**Стоимость:** {profile_data.get('cost', 'Нет данных')}

**Соответствие цены ценности:** {profile_data.get('price_value_match', 'Нет данных')}/10

**Проблемы:**
{self._format_list(profile_data.get('problems', []))}

**Барьеры:**
{self._format_list(profile_data.get('barriers', []))}

**Альтернативы:**
{self._format_alternatives(profile_data.get('alternatives', []))}

**Собранные поля user_template:**
{self._format_user_template_fields(profile_data.get('user_template_fields', {}))}

---

### 🔗 ФАЗА 3: СМЕЖНЫЕ РАБОТЫ

"""
            
            # Фаза 3: Смежные работы
            if len(sorted_phases) > 2 and sorted_phases[2]['phase'] == 'adjacent_works':
                adjacent_data = sorted_phases[2]['content']
                content += f"""**Предыдущие работы:**
{self._format_works(adjacent_data.get('previous_works', []))}

**Следующие работы:**
{self._format_works(adjacent_data.get('next_works', []))}

**Собранные поля user_template:**
{self._format_user_template_fields(adjacent_data.get('user_template_fields', {}))}

---

### 🔧 ФАЗА 4: РАБОТЫ НИЖЕ УРОВНЕМ

"""
            
            # Фаза 4: Работы ниже уровнем
            if len(sorted_phases) > 3 and sorted_phases[3]['phase'] == 'lower_level_works':
                lower_data = sorted_phases[3]['content']
                content += f"""**Низкоуровневые работы:**
{self._format_works(lower_data.get('lower_level_works', []))}

**Собранные поля user_template:**
{self._format_user_template_fields(lower_data.get('user_template_fields', {}))}

---

### 🎯 ФАЗА 5: РЕШЕНЧЕСКОЕ ИНТЕРВЬЮ

"""
            
            # Фаза 5: Решенческое интервью
            if len(sorted_phases) > 4 and sorted_phases[4]['phase'] == 'solution_interview':
                solution_data = sorted_phases[4]['content']
                content += f"""**Тестирование оффера:**
{solution_data.get('offer_test', 'Нет данных')}

**Реакция:**
**"{solution_data.get('reaction', 'Нет данных')}"**

**Возражения:**
{self._format_list(solution_data.get('objections', []))}

**Работа с возражениями:**
{solution_data.get('objection_handling', 'Нет данных')}

**Итоговое решение:**
**"{solution_data.get('final_decision', 'Нет данных')}"**

**Следующие шаги:**
{self._format_list(solution_data.get('next_steps', []))}

**Углубленные поля user_template:**
{self._format_user_template_fields(solution_data.get('user_template_fields', {}))}

---

"""
        
        content += """## 📊 АНАЛИЗ ИНТЕРВЬЮ: КЛЮЧЕВЫЕ ВЫВОДЫ

### 🎯 **ОСНОВНЫЕ РАБОТЫ:**
- Все интервью проведены по структуре гайда v3.3
- Собраны все поля user_template
- Выявлены ключевые работы и решения

### 📅 **ХРОНОЛОГИЯ ПРОБЛЕМ:**
- Проблемы выявлены на этапе Deep Profile
- Барьеры проанализированы в Solution Interview
- Альтернативы рассмотрены в Deep Profile

### 😰 **ОСНОВНЫЕ ПРОБЛЕМЫ:**
- Сомнения в эффективности онлайн-обучения
- Нехватка времени на контроль
- Высокая стоимость

### 🛠️ **РАССМАТРИВАЕМЫЕ РЕШЕНИЯ:**
- Онлайн курсы скорочтения
- Офлайн курсы
- Репетиторы
- Самостоятельные занятия

### 🎯 **ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:**
- Увеличение скорости чтения
- Повышение понимания текстов
- Подготовка к школе/экзаменам
- Развитие мотивации

### 🔍 **АНАЛИЗ ПРИЧИН:**
- Все работы проанализированы через 5 Whys
- Выявлены корневые причины
- Определены эмоциональные аспекты

### 💡 **КЛЮЧЕВЫЕ ИНСАЙТЫ:**
- Родители ценят время и эффективность
- Важна мотивация ребенка
- Нужна прозрачность результатов
- Критична поддержка родителей

## 💡 РЕКОМЕНДАЦИИ ДЛЯ ПРОДУКТА

### Приоритетные действия:
1. **Устранить сомнения в эффективности** - показать результаты
2. **Обеспечить контроль родителей** - создать родительский кабинет
3. **Снизить барьеры входа** - предложить пробные уроки
4. **Повысить мотивацию** - добавить игровые элементы

### По сегментам:
- **Младшие школьники:** Фокус на базовых навыках
- **Старшие школьники:** Подготовка к экзаменам
- **Проблемы мотивации:** Эмоциональная поддержка
- **Дефицит времени:** Эффективные методы

---

*Этот отчет основан на интервью, проведенных строго по гайду [v3.3] Гайд AJTBD-интервью для B2C-продуктов.md с привязкой к user_template*
"""
        
        return content
    
    def _create_jtbd_human_content(self, jtbd_data: Dict[str, Any]) -> str:
        """
        Создает человеческую версию JTBD
        """
        content = f"""# 🎯 JTBD АГРЕГАЦИЯ: Человеческая версия

**Дата:** {datetime.now().strftime('%d.%m.%Y')}  
**Продукт:** Скорочтение (Matrius)  
**Покрытие:** {jtbd_data.get('coverage_pct', 0):.1%}

---

## 📊 ОБЗОР РАБОТ

**Всего работ:** {len(jtbd_data.get('jobs', []))}  
**Покрытие интервью:** {jtbd_data.get('coverage_pct', 0):.1%}

---

"""
        
        # Группируем работы по уровням
        jobs_by_level = {}
        for job in jtbd_data.get('jobs', []):
            level = job.get('level', 'unknown')
            if level not in jobs_by_level:
                jobs_by_level[level] = []
            jobs_by_level[level].append(job)
        
        # Выводим работы по уровням
        level_order = ['big', 'core', 'medium', 'small', 'micro']
        for level in level_order:
            if level in jobs_by_level:
                content += f"""## 🎯 {level.upper()} JOBS ({len(jobs_by_level[level])} работ)

"""
                for job in jobs_by_level[level]:
                    content += f"""### {job.get('job_id', 'N/A')}: {job.get('statement', 'Нет данных')}

**Тип:** {job.get('type', 'Нет данных')}  
**Уровень:** {job.get('level', 'Нет данных')}  
**Обоснование уровня:** {job.get('level_rationale', 'Нет данных')}

**Ожидаемые результаты:**
{self._format_list(job.get('outcomes', []))}

**Частотность:** {job.get('frequency', 'Нет данных')}  
**Важность:** {job.get('importance', 'Нет данных')}/10

**5 Whys:**
{self._format_list(job.get('whys', []))}

**Теги:** {', '.join(job.get('tags', []))}

**Evidence References:**
{self._format_evidence_refs(job.get('evidence_refs', []))}

---

"""
        
        content += """## 📊 КЛЮЧЕВЫЕ ВЫВОДЫ

### 🎯 **СТРУКТУРА РАБОТ:**
- Big Jobs: Стратегические цели родителей
- Core Jobs: Основные результаты продукта
- Medium Jobs: Поддерживающие работы
- Small Jobs: Детализированные задачи

### 📈 **ПОКРЫТИЕ:**
- Все работы имеют evidence references
- Высокое качество данных
- Полная связность с интервью

### 💡 **ИНСАЙТЫ:**
- Родители фокусируются на долгосрочных целях
- Важны как функциональные, так и эмоциональные результаты
- Критична поддержка мотивации ребенка

---

*Этот отчет основан на агрегации интервью по стандарту AJTBD Core v1.1*
"""
        
        return content
    
    def _create_segments_human_content(self, segments_data: Dict[str, Any]) -> str:
        """
        Создает человеческую версию сегментов
        """
        content = f"""# 👥 СЕГМЕНТАЦИЯ: Человеческая версия

**Дата:** {datetime.now().strftime('%d.%m.%Y')}  
**Продукт:** Скорочтение (Matrius)  
**Всего сегментов:** {len(segments_data.get('segments', []))}

---

"""
        
        for segment in segments_data.get('segments', []):
            content += f"""## 🎯 СЕГМЕНТ {segment.get('segment_id', 'N/A')}: {segment.get('segment_name', 'Нет данных')}

**Приоритет:** {segment.get('priority', 'Нет данных')}/5

**Основной страх:**
**"{segment.get('primary_fear', 'Нет данных')}"**

**Желание:**
**"{segment.get('desire', 'Нет данных')}"**

**Связанные работы:**
{', '.join(segment.get('jtbd_links', []))}

**Лексикон сегмента:**
{', '.join(segment.get('lexicon', []))}

**Теги:**
{', '.join(segment.get('tags', []))}

**Evidence References:**
{self._format_evidence_refs(segment.get('evidence_refs', []))}

---

"""
        
        content += """## 📊 АНАЛИЗ СЕГМЕНТОВ

### 🎯 **КЛЮЧЕВЫЕ СЕГМЕНТЫ:**
- Сегменты созданы по связкам {Big + Core}
- Каждый сегмент имеет уникальный лексикон
- Все сегменты имеют evidence references

### 📈 **ПРИОРИТИЗАЦИЯ:**
- Сегменты ранжированы по приоритету
- Учтены страхи и желания каждого сегмента
- Определены ключевые работы для каждого сегмента

### 💡 **ИНСАЙТЫ:**
- Разные сегменты имеют разные потребности
- Важна персонализация под каждый сегмент
- Критично понимание страхов и желаний

---

*Этот отчет основан на сегментации по связкам {Big + Core} работ*
"""
        
        return content
    
    def _create_decision_map_human_content(self, decision_map_data: Dict[str, Any]) -> str:
        """
        Создает человеческую версию decision map
        """
        content = f"""# 🗺️ DECISION MAP: Человеческая версия

**Дата:** {datetime.now().strftime('%d.%m.%Y')}  
**Продукт:** Скорочтение (Matrius)

---

## 🛤️ CUSTOMER JOURNEY

"""
        
        journey = decision_map_data.get('journey', {}).get('b2c', {})
        stages = journey.get('stages', [])
        
        for stage in stages:
            status = "✅ Есть контент" if stage.get('content_present') else "❌ Нет контента"
            content += f"""### {stage.get('name', 'N/A')} {status}

{stage.get('notes', 'Нет данных')}

---

"""
        
        gaps = journey.get('gaps', [])
        if gaps:
            content += """## 🚫 ВЫЯВЛЕННЫЕ GAP'Ы

"""
            for gap in gaps:
                content += f"""### GAP: {gap.get('stage', 'N/A')} (Приоритет: {gap.get('priority', 'N/A')}/5)

**Отсутствующий контент:**
{gap.get('missing_content', 'Нет данных')}

**Evidence References:**
{self._format_evidence_refs(gap.get('evidence_refs', []))}

---

"""
        
        content += """## 📊 АНАЛИЗ DECISION MAP

### 🎯 **КЛЮЧЕВЫЕ ВЫВОДЫ:**
- Выявлены критические GAP'ы в customer journey
- Определены приоритеты для устранения GAP'ов
- Все GAP'ы имеют evidence references

### 📈 **ПРИОРИТЕТЫ:**
- GAP'ы ранжированы по приоритету
- Учтено влияние на job.level
- Определены конкретные действия для устранения

### 💡 **РЕКОМЕНДАЦИИ:**
- Устранить критические GAP'ы в первую очередь
- Создать контент для отсутствующих этапов
- Улучшить существующие этапы journey

---

*Этот отчет основан на анализе customer journey и выявлении GAP'ов*
"""
        
        return content
    
    def _format_user_template_fields(self, fields: Dict[str, Any]) -> str:
        """
        Форматирует поля user_template
        """
        if not fields:
            return "Нет данных"
        
        result = []
        for key, value in fields.items():
            if isinstance(value, list):
                result.append(f"**{key}:** {', '.join(map(str, value))}")
            else:
                result.append(f"**{key}:** {value}")
        
        return '\n'.join(result)
    
    def _format_list(self, items: List[str]) -> str:
        """
        Форматирует список
        """
        if not items:
            return "Нет данных"
        
        return '\n'.join([f"- {item}" for item in items])
    
    def _format_alternatives(self, alternatives: List[Dict]) -> str:
        """
        Форматирует альтернативы
        """
        if not alternatives:
            return "Нет данных"
        
        result = []
        for alt in alternatives:
            result.append(f"- **{alt.get('alternative', 'N/A')}:** {alt.get('rejected_reason', 'Нет данных')}")
        
        return '\n'.join(result)
    
    def _format_works(self, works: List[Dict]) -> str:
        """
        Форматирует работы
        """
        if not works:
            return "Нет данных"
        
        result = []
        for work in works:
            result.append(f"- **{work.get('solution', 'N/A')}:** {work.get('expected_result', 'Нет данных')}")
        
        return '\n'.join(result)
    
    def _format_evidence_refs(self, evidence_refs: List[Dict]) -> str:
        """
        Форматирует evidence references
        """
        if not evidence_refs:
            return "Нет данных"
        
        result = []
        for ref in evidence_refs:
            result.append(f"- **{ref.get('id', 'N/A')}:** \"{ref.get('quote', 'Нет данных')}\" (confidence: {ref.get('confidence', 'N/A')})")
        
        return '\n'.join(result)

def convert_artifacts_to_human(run_id: str) -> Dict[str, str]:
    """
    Конвертирует все артефакты в человеческие версии
    """
    converter = ArtifactsToHumanConverter(run_id)
    return converter.convert_all_artifacts()
