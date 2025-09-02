#!/usr/bin/env python3
"""
STEP-03: Interview Collection (Enhanced v3.3)
Сбор интервью по гайду v3.3 с привязкой к user_template
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from llm.client import LLMClient
from utils.io import ensure_dir, save_jsonl
from validators.validate import validate_interview_structure

class InterviewCollectorV33:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = LLMClient(config)
        self.run_id = config.get('run_id')
        self.artifacts_dir = f"artifacts/{self.run_id}"
        
    def collect_interviews(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сбор интервью по гайду v3.3 с привязкой к user_template
        """
        print("🎤 STEP-03: Сбор интервью по гайду v3.3...")
        
        # Параметры
        personas = input_data.get('personas', [])
        n_interviews = input_data.get('n_interviews', 6)
        product = input_data.get('products', ['Скорочтение'])[0]
        
        # Создаем директорию для интервью
        interviews_dir = f"{self.artifacts_dir}/interviews"
        ensure_dir(interviews_dir)
        
        # Собираем интервью
        interviews = []
        for i in range(n_interviews):
            persona = personas[i % len(personas)]
            interview = self._conduct_interview_v33(i + 1, persona, product)
            interviews.extend(interview)
        
        # Сохраняем интервью
        output_file = f"{interviews_dir}/simulated_v33.jsonl"
        save_jsonl(interviews, output_file)
        
        # Валидация
        validation_result = self._validate_interviews(interviews)
        
        # Создаем отчет
        report = self._create_report(interviews, validation_result)
        
        return {
            'interviews_file': output_file,
            'n_interviews': len(interviews),
            'validation_result': validation_result,
            'report': report
        }
    
    def _conduct_interview_v33(self, interview_id: int, persona: str, product: str) -> List[Dict]:
        """
        Проведение одного интервью по гайду v3.3
        """
        interview_data = []
        base_timestamp = datetime.now().isoformat()
        
        # Фаза 1: Квалификация и навигация
        qualification = self._phase_1_qualification(interview_id, persona, product, base_timestamp)
        interview_data.append(qualification)
        
        # Фаза 2: Глубокий профиль работы
        deep_profile = self._phase_2_deep_profile(interview_id, persona, product, base_timestamp)
        interview_data.append(deep_profile)
        
        # Фаза 3: Смежные работы
        adjacent_works = self._phase_3_adjacent_works(interview_id, persona, product, base_timestamp)
        interview_data.append(adjacent_works)
        
        # Фаза 4: Работы ниже уровнем
        lower_level_works = self._phase_4_lower_level_works(interview_id, persona, product, base_timestamp)
        interview_data.append(lower_level_works)
        
        # Фаза 5: Решенческое интервью
        solution_interview = self._phase_5_solution_interview(interview_id, persona, product, base_timestamp)
        interview_data.append(solution_interview)
        
        return interview_data
    
    def _phase_1_qualification(self, interview_id: int, persona: str, product: str, base_timestamp: str) -> Dict:
        """
        Фаза 1: Квалификация и навигация
        Собираем: [когда], [психологические особенности], [Короткое описание работы], [частота], [важность]
        """
        prompt = f"""
        Проведи Фазу 1: Квалификация и навигация для AJTBD интервью.
        
        Персона: {persona}
        Продукт: {product}
        
        Собери следующие данные для user_template:
        1. [когда] - контекст/ситуация (≥2 признака)
        2. [психологические особенности] - мотивации/страхи/установки (≥2)
        3. [Короткое описание работы] - 1-2 предложения
        4. [частота] - daily/weekly/monthly/по событию
        5. [важность] - 1-10
        
        Верни JSON с полями:
        - context: контекст респондента
        - hypothesis_work: гипотеза работы
        - work_type: частотная/последовательная
        - selected_work: выбранная работа для изучения
        - reasoning: обоснование выбора
        - user_template_fields: собранные поля для user_template
        """
        
        response = self.llm.generate(prompt)
        data = json.loads(response)
        
        return {
            "interview_id": f"I-V33-{interview_id:03d}",
            "persona": persona,
            "timestamp": base_timestamp,
            "model": self.config.get('model_name', 'gpt-5-high'),
            "phase": "qualification",
            "content": data
        }
    
    def _phase_2_deep_profile(self, interview_id: int, persona: str, product: str, base_timestamp: str) -> Dict:
        """
        Фаза 2: Глубокий профиль работы
        Собираем все основные поля user_template
        """
        prompt = f"""
        Проведи Фазу 2: Глубокий профиль работы для AJTBD интервью.
        
        Персона: {persona}
        Продукт: {product}
        
        Собери ВСЕ поля user_template:
        1. [Хочу] - формализованный ожидаемый результат (метрика/критерии)
        2. [чтобы] - работа уровнем выше (Big/эмоциональная цель)
        3. [решение] - которое клиент "нанял"
        4. [удовлетворенность] - 1-10 + почему
        5. [ценность] - что именно даёт ценность (списком)
        6. [Aha-moment] - когда «стало работать»
        7. [стоимость] - руб/мес или разовая
        8. [соответствие цены ценности] - 1-10 + почему
        9. [проблемы] - ≥3, каждую раскрыть
        10. [барьеры] - ≥3, каждую раскрыть
        11. [альтернативы] - реальные альтернативы + почему не выбрали
        
        Верни JSON с полями:
        - expected_result: ожидаемый результат
        - criteria: критерии результата
        - solution: решение
        - solution_history: история использования
        - context: контекст
        - trigger: триггер
        - higher_level_work: вышеуровневая работа
        - positive_emotions: позитивные эмоции
        - negative_emotions: негативные эмоции
        - importance: важность (1-10)
        - satisfaction: удовлетворенность (1-10)
        - value: ценность
        - aha_moment: aha-момент
        - cost: стоимость
        - price_value_match: соответствие цены ценности
        - problems: проблемы (≥3)
        - barriers: барьеры (≥3)
        - alternatives: альтернативы
        - user_template_fields: все собранные поля
        """
        
        response = self.llm.generate(prompt)
        data = json.loads(response)
        
        return {
            "interview_id": f"I-V33-{interview_id:03d}",
            "persona": persona,
            "timestamp": base_timestamp,
            "model": self.config.get('model_name', 'gpt-5-high'),
            "phase": "deep_profile",
            "content": data
        }
    
    def _phase_3_adjacent_works(self, interview_id: int, persona: str, product: str, base_timestamp: str) -> Dict:
        """
        Фаза 3: Смежные работы
        Собираем: [прошлый опыт], [активирующее знание]
        """
        prompt = f"""
        Проведи Фазу 3: Смежные работы для AJTBD интервью.
        
        Персона: {persona}
        Продукт: {product}
        
        Собери поля user_template:
        1. [прошлый опыт] - уровень/ошибки/что пробовали
        2. [активирующее знание] - что «включает» действие
        
        Верни JSON с полями:
        - previous_works: предыдущие работы
        - next_works: следующие работы
        - user_template_fields: собранные поля
        """
        
        response = self.llm.generate(prompt)
        data = json.loads(response)
        
        return {
            "interview_id": f"I-V33-{interview_id:03d}",
            "persona": persona,
            "timestamp": base_timestamp,
            "model": self.config.get('model_name', 'gpt-5-high'),
            "phase": "adjacent_works",
            "content": data
        }
    
    def _phase_4_lower_level_works(self, interview_id: int, persona: str, product: str, base_timestamp: str) -> Dict:
        """
        Фаза 4: Работы ниже уровнем
        Собираем: [низкоуровневые работы + результат]
        """
        prompt = f"""
        Проведи Фазу 4: Работы ниже уровнем для AJTBD интервью.
        
        Персона: {persona}
        Продукт: {product}
        
        Собери поле user_template:
        1. [низкоуровневые работы + результат] - список small/micro jobs
        
        Верни JSON с полями:
        - lower_level_works: низкоуровневые работы
        - user_template_fields: собранные поля
        """
        
        response = self.llm.generate(prompt)
        data = json.loads(response)
        
        return {
            "interview_id": f"I-V33-{interview_id:03d}",
            "persona": persona,
            "timestamp": base_timestamp,
            "model": self.config.get('model_name', 'gpt-5-high'),
            "phase": "lower_level_works",
            "content": data
        }
    
    def _phase_5_solution_interview(self, interview_id: int, persona: str, product: str, base_timestamp: str) -> Dict:
        """
        Фаза 5: Решенческое интервью
        Углубляем: [Aha-moment], [ценность], [проблемы], [барьеры]
        """
        prompt = f"""
        Проведи Фазу 5: Решенческое интервью для AJTBD интервью.
        
        Персона: {persona}
        Продукт: {product}
        
        Углуби поля user_template:
        1. [Aha-moment] - когда «стало работать»
        2. [ценность] - что именно даёт ценность
        3. [проблемы] - ≥3, каждую раскрыть
        4. [барьеры] - ≥3, каждую раскрыть
        
        Верни JSON с полями:
        - offer_test: тестирование оффера
        - reaction: реакция
        - objections: возражения
        - objection_handling: работа с возражениями
        - final_decision: итоговое решение
        - next_steps: следующие шаги
        - user_template_fields: углубленные поля
        """
        
        response = self.llm.generate(prompt)
        data = json.loads(response)
        
        return {
            "interview_id": f"I-V33-{interview_id:03d}",
            "persona": persona,
            "timestamp": base_timestamp,
            "model": self.config.get('model_name', 'gpt-5-high'),
            "phase": "solution_interview",
            "content": data
        }
    
    def _validate_interviews(self, interviews: List[Dict]) -> Dict[str, Any]:
        """
        Валидация интервью на соответствие user_template
        """
        validation_result = {
            'total_interviews': len(interviews),
            'valid_interviews': 0,
            'missing_fields': [],
            'quality_score': 0.0
        }
        
        required_fields = [
            'когда', 'психологические особенности', 'Хочу', 'чтобы', 
            'важность', 'частота', 'решение', 'удовлетворенность', 
            'ценность', 'Aha-moment', 'стоимость', 'соответствие цены ценности',
            'проблемы', 'барьеры', 'альтернативы', 'низкоуровневые работы + результат'
        ]
        
        for interview in interviews:
            if 'user_template_fields' in interview.get('content', {}):
                fields = interview['content']['user_template_fields']
                missing = [field for field in required_fields if field not in fields]
                if not missing:
                    validation_result['valid_interviews'] += 1
                else:
                    validation_result['missing_fields'].extend(missing)
        
        validation_result['quality_score'] = validation_result['valid_interviews'] / validation_result['total_interviews']
        
        return validation_result
    
    def _create_report(self, interviews: List[Dict], validation_result: Dict[str, Any]) -> str:
        """
        Создание отчета по сбору интервью
        """
        report = f"""
# STEP-03 Report: Interview Collection (v3.3)

## Обзор
- **Всего интервью:** {validation_result['total_interviews']}
- **Валидных интервью:** {validation_result['valid_interviews']}
- **Качество:** {validation_result['quality_score']:.2f}

## Структура интервью
Использована структура гайда v3.3:
1. Qualification & Navigation
2. Deep Profile
3. Adjacent Works
4. Lower Level Works
5. Solution Interview

## Связь с user_template
Каждое интервью собирает данные для всех полей user_template:
- [когда] - контекст/ситуация
- [психологические особенности] - мотивации/страхи
- [Хочу] - ожидаемый результат
- [чтобы] - работа уровнем выше
- [решение] - нанятое решение
- [удовлетворенность] - оценка решения
- [ценность] - ценность решения
- [Aha-moment] - момент осознания
- [стоимость] - стоимость
- [соответствие цены ценности] - оценка
- [проблемы] - проблемы с решением
- [барьеры] - барьеры к решению
- [альтернативы] - рассмотренные альтернативы
- [низкоуровневые работы + результат] - детализированные задачи

## Качество данных
- **Полнота:** {validation_result['quality_score']:.1%}
- **Отсутствующие поля:** {len(set(validation_result['missing_fields']))}

## Следующие шаги
1. STEP-04: Агрегация JTBD с привязкой к user_template
2. STEP-05: Сегментация с human-версиями
3. STEP-04b: Longform export по user_template
        """
        
        return report.strip()

def run_step_03_v33(config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Запуск STEP-03 с использованием гайда v3.3
    """
    collector = InterviewCollectorV33(config)
    return collector.collect_interviews(input_data)
