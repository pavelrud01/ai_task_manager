#!/usr/bin/env python3
"""
Quality Checks для AJTBD Pipeline
Строгие проверки качества с автоматическим возвратом к шагам
"""

import json
import os
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

@dataclass
class QualityCheckResult:
    """Результат проверки качества"""
    passed: bool
    errors: List[str]
    warnings: List[str]
    required_step: str = None  # Шаг, к которому нужно вернуться
    missing_data: Dict[str, Any] = None

class QualityChecker:
    """Класс для проверки качества данных"""
    
    def __init__(self, artifacts_dir: str):
        self.artifacts_dir = artifacts_dir
        
    def check_step_03_quality(self) -> QualityCheckResult:
        """
        Проверка качества STEP-03 (интервью)
        """
        errors = []
        warnings = []
        
        # Загружаем интервью
        interviews_file = f"{self.artifacts_dir}/interviews/simulated.jsonl"
        if not os.path.exists(interviews_file):
            errors.append("Файл интервью не найден")
            return QualityCheckResult(False, errors, warnings, "step_03")
        
        interviews = self._load_interviews(interviews_file)
        if not interviews:
            errors.append("Интервью не загружены")
            return QualityCheckResult(False, errors, warnings, "step_03")
        
        # Проверяем каждое интервью
        for i, interview in enumerate(interviews):
            interview_id = interview.get('interview_id', f'I-{i+1}')
            
            # Проверяем структуру enhanced интервью
            if 'all_solutions' not in interview:
                errors.append(f"{interview_id}: Отсутствует all_solutions")
                continue
                
            if 'top_solutions_analysis' not in interview:
                errors.append(f"{interview_id}: Отсутствует top_solutions_analysis")
                continue
        
        # Проверяем детальные требования
        core_jobs_issues = self._check_core_jobs_requirements(interviews)
        errors.extend(core_jobs_issues)
        
        # Проверяем обязательные поля
        mandatory_fields_issues = self._check_mandatory_fields(interviews)
        errors.extend(mandatory_fields_issues)
        
        if errors:
            return QualityCheckResult(False, errors, warnings, "step_03")
        
        return QualityCheckResult(True, [], warnings)
    
    def check_step_04_quality(self) -> QualityCheckResult:
        """
        Проверка качества STEP-04 (JTBD)
        """
        errors = []
        warnings = []
        
        # Загружаем JTBD данные
        jtbd_file = f"{self.artifacts_dir}/step_04_jtbd.json"
        if not os.path.exists(jtbd_file):
            errors.append("Файл JTBD не найден")
            return QualityCheckResult(False, errors, warnings, "step_04")
        
        with open(jtbd_file, 'r', encoding='utf-8') as f:
            jtbd_data = json.load(f)
        
        # Проверяем evidence_refs
        evidence_issues = self._check_evidence_refs_jtbd(jtbd_data)
        errors.extend(evidence_issues)
        
        # Проверяем level + level_rationale
        level_issues = self._check_job_levels(jtbd_data)
        errors.extend(level_issues)
        
        if errors:
            return QualityCheckResult(False, errors, warnings, "step_04")
        
        return QualityCheckResult(True, [], warnings)
    
    def check_step_05_quality(self) -> QualityCheckResult:
        """
        Проверка качества STEP-05 (сегменты)
        """
        errors = []
        warnings = []
        
        # Загружаем сегменты
        segments_file = f"{self.artifacts_dir}/step_05_segments.json"
        if not os.path.exists(segments_file):
            errors.append("Файл сегментов не найден")
            return QualityCheckResult(False, errors, warnings, "step_05")
        
        with open(segments_file, 'r', encoding='utf-8') as f:
            segments_data = json.load(f)
        
        # Проверяем evidence_refs
        evidence_issues = self._check_evidence_refs_segments(segments_data)
        errors.extend(evidence_issues)
        
        # Проверяем структуру сегментов
        structure_issues = self._check_segments_structure(segments_data)
        errors.extend(structure_issues)
        
        if errors:
            return QualityCheckResult(False, errors, warnings, "step_05")
        
        return QualityCheckResult(True, [], warnings)
    
    def check_step_06_quality(self) -> QualityCheckResult:
        """
        Проверка качества STEP-06 (Decision Map)
        """
        errors = []
        warnings = []
        
        # Загружаем Decision Map
        decision_map_file = f"{self.artifacts_dir}/step_06_decision_mapping.json"
        if not os.path.exists(decision_map_file):
            errors.append("Файл Decision Map не найден")
            return QualityCheckResult(False, errors, warnings, "step_06")
        
        with open(decision_map_file, 'r', encoding='utf-8') as f:
            decision_map_data = json.load(f)
        
        # Проверяем evidence_refs
        evidence_issues = self._check_evidence_refs_decision_map(decision_map_data)
        errors.extend(evidence_issues)
        
        # Проверяем job.level в GAPs
        job_level_issues = self._check_job_levels_in_gaps(decision_map_data)
        errors.extend(job_level_issues)
        
        if errors:
            return QualityCheckResult(False, errors, warnings, "step_06")
        
        return QualityCheckResult(True, [], warnings)
    
    def check_human_readable_versions(self) -> QualityCheckResult:
        """
        Проверка наличия human-readable версий
        """
        errors = []
        warnings = []
        
        required_files = [
            f"{self.artifacts_dir}/interviews_HUMAN_READABLE.md",
            f"{self.artifacts_dir}/jtbd_HUMAN_READABLE.md",
            f"{self.artifacts_dir}/segments_HUMAN_READABLE.md",
            f"{self.artifacts_dir}/decision_map_HUMAN_READABLE.md"
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                errors.append(f"Отсутствует human-readable версия: {os.path.basename(file_path)}")
        
        if errors:
            return QualityCheckResult(False, errors, warnings, "human_readable")
        
        return QualityCheckResult(True, [], warnings)
    
    def _load_interviews(self, interviews_file: str) -> List[Dict]:
        """Загрузка интервью из файла"""
        interviews = []
        if os.path.exists(interviews_file):
            with open(interviews_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        interviews.append(json.loads(line))
        return interviews
    
    def _check_core_jobs_requirements(self, interviews: List[Dict]) -> List[str]:
        """
        Проверка требований для Core Jobs:
        - минимум 2 решения
        - минимум 3-5 проблем с follow-up
        """
        errors = []
        
        for i, interview in enumerate(interviews):
            interview_id = interview.get('interview_id', f'I-{i+1}')
            
            # Проверяем all_solutions
            all_solutions = interview.get('all_solutions', {}).get('content', {})
            solutions = all_solutions.get('solutions', [])
            
            if len(solutions) < 2:
                errors.append(f"{interview_id}: Меньше 2 решений (найдено: {len(solutions)})")
            
            # Проверяем top_solutions_analysis
            top_analysis = interview.get('top_solutions_analysis', {})
            detailed_analysis = top_analysis.get('detailed_analysis', [])
            
            for j, analysis in enumerate(detailed_analysis):
                solution_data = analysis.get('content', {})
                problems = solution_data.get('problems', [])
                
                if len(problems) < 3:
                    errors.append(f"{interview_id} Solution #{j+1}: Меньше 3 проблем (найдено: {len(problems)})")
                
                # Проверяем follow-ups для каждой проблемы
                for k, problem in enumerate(problems):
                    if not isinstance(problem, dict):
                        continue
                    
                    required_followup_fields = ['context', 'frequency', 'severity', 'critical_moment']
                    missing_followups = [field for field in required_followup_fields 
                                       if not problem.get(field) or problem.get(field) == 'Нет данных']
                    
                    if missing_followups:
                        errors.append(f"{interview_id} Solution #{j+1} Problem #{k+1}: Отсутствуют follow-ups: {', '.join(missing_followups)}")
        
        return errors
    
    def _check_mandatory_fields(self, interviews: List[Dict]) -> List[str]:
        """
        Проверка обязательных полей:
        activation_knowledge, psych_traits, prior_experience, aha_moment, value_story, price_value_alignment
        """
        errors = []
        mandatory_fields = [
            'activation_knowledge', 'psych_traits', 'prior_experience', 
            'aha_moment', 'value_story', 'price_value_alignment'
        ]
        
        for i, interview in enumerate(interviews):
            interview_id = interview.get('interview_id', f'I-{i+1}')
            
            top_analysis = interview.get('top_solutions_analysis', {})
            detailed_analysis = top_analysis.get('detailed_analysis', [])
            
            for j, analysis in enumerate(detailed_analysis):
                solution_data = analysis.get('content', {})
                
                for field in mandatory_fields:
                    value = solution_data.get(field)
                    if not value or value == 'Нет данных' or value == '':
                        errors.append(f"{interview_id} Solution #{j+1}: Отсутствует обязательное поле '{field}'")
        
        return errors
    
    def _check_evidence_refs_jtbd(self, jtbd_data: Dict[str, Any]) -> List[str]:
        """Проверка evidence_refs в JTBD"""
        errors = []
        
        big_jobs = jtbd_data.get('big_jobs', [])
        for i, big_job in enumerate(big_jobs):
            job_id = big_job.get('job_id', f'BJ-{i+1}')
            
            if not big_job.get('evidence_refs'):
                errors.append(f"JTBD {job_id}: Отсутствуют evidence_refs")
            
            # Проверяем medium jobs
            medium_jobs = big_job.get('medium_jobs', [])
            for j, medium_job in enumerate(medium_jobs):
                medium_job_id = medium_job.get('job_id', f'MJ-{j+1}')
                
                if not medium_job.get('evidence_refs'):
                    errors.append(f"JTBD {medium_job_id}: Отсутствуют evidence_refs")
                
                # Проверяем small jobs
                small_jobs = medium_job.get('small_jobs', [])
                for k, small_job in enumerate(small_jobs):
                    small_job_id = small_job.get('job_id', f'SJ-{k+1}')
                    
                    if not small_job.get('evidence_refs'):
                        errors.append(f"JTBD {small_job_id}: Отсутствуют evidence_refs")
        
        return errors
    
    def _check_job_levels(self, jtbd_data: Dict[str, Any]) -> List[str]:
        """Проверка level + level_rationale для каждого job"""
        errors = []
        
        def check_job_level(job, job_id):
            if not job.get('level'):
                errors.append(f"JTBD {job_id}: Отсутствует level")
            
            if not job.get('level_rationale'):
                errors.append(f"JTBD {job_id}: Отсутствует level_rationale")
        
        big_jobs = jtbd_data.get('big_jobs', [])
        for i, big_job in enumerate(big_jobs):
            job_id = big_job.get('job_id', f'BJ-{i+1}')
            check_job_level(big_job, job_id)
            
            # Проверяем medium jobs
            medium_jobs = big_job.get('medium_jobs', [])
            for j, medium_job in enumerate(medium_jobs):
                medium_job_id = medium_job.get('job_id', f'MJ-{j+1}')
                check_job_level(medium_job, medium_job_id)
                
                # Проверяем small jobs
                small_jobs = medium_job.get('small_jobs', [])
                for k, small_job in enumerate(small_jobs):
                    small_job_id = small_job.get('job_id', f'SJ-{k+1}')
                    check_job_level(small_job, small_job_id)
        
        return errors
    
    def _check_evidence_refs_segments(self, segments_data: Dict[str, Any]) -> List[str]:
        """Проверка evidence_refs в сегментах"""
        errors = []
        
        segments = segments_data.get('segments', [])
        for i, segment in enumerate(segments):
            segment_id = segment.get('segment_id', f'S-{i+1}')
            
            if not segment.get('evidence_refs'):
                errors.append(f"Segment {segment_id}: Отсутствуют evidence_refs")
        
        return errors
    
    def _check_segments_structure(self, segments_data: Dict[str, Any]) -> List[str]:
        """Проверка структуры сегментов"""
        errors = []
        
        segments = segments_data.get('segments', [])
        for i, segment in enumerate(segments):
            segment_id = segment.get('segment_id', f'S-{i+1}')
            
            # Проверяем обязательные поля
            required_fields = ['big_job', 'core_job', 'lexicon', 'jtbd_links']
            for field in required_fields:
                if not segment.get(field):
                    errors.append(f"Segment {segment_id}: Отсутствует поле '{field}'")
        
        return errors
    
    def _check_evidence_refs_decision_map(self, decision_map_data: Dict[str, Any]) -> List[str]:
        """Проверка evidence_refs в Decision Map"""
        errors = []
        
        decision_map = decision_map_data.get('decision_map', {})
        gaps = decision_map.get('gaps', [])
        
        for i, gap in enumerate(gaps):
            gap_id = gap.get('gap_id', f'GAP-{i+1}')
            
            if not gap.get('evidence_refs'):
                errors.append(f"Decision Map {gap_id}: Отсутствуют evidence_refs")
        
        return errors
    
    def _check_job_levels_in_gaps(self, decision_map_data: Dict[str, Any]) -> List[str]:
        """Проверка job.level в GAPs"""
        errors = []
        
        decision_map = decision_map_data.get('decision_map', {})
        gaps = decision_map.get('gaps', [])
        
        for i, gap in enumerate(gaps):
            gap_id = gap.get('gap_id', f'GAP-{i+1}')
            
            affected_job_levels = gap.get('affected_job_levels', [])
            if not affected_job_levels:
                errors.append(f"Decision Map {gap_id}: Отсутствуют affected_job_levels")
            
            for j, job_level in enumerate(affected_job_levels):
                if not job_level.get('level'):
                    errors.append(f"Decision Map {gap_id} Job #{j+1}: Отсутствует level")
        
        return errors

def run_quality_checks(artifacts_dir: str) -> Dict[str, QualityCheckResult]:
    """
    Запуск всех проверок качества
    """
    checker = QualityChecker(artifacts_dir)
    
    results = {
        'step_03': checker.check_step_03_quality(),
        'step_04': checker.check_step_04_quality(),
        'step_05': checker.check_step_05_quality(),
        'step_06': checker.check_step_06_quality(),
        'human_readable': checker.check_human_readable_versions()
    }
    
    return results

def should_break_pipeline(results: Dict[str, QualityCheckResult]) -> Tuple[bool, str, List[str]]:
    """
    Определяет, нужно ли прерывать пайплайн
    """
    all_errors = []
    failed_steps = []
    
    for step, result in results.items():
        if not result.passed:
            failed_steps.append(step)
            all_errors.extend(result.errors)
    
    if failed_steps:
        # Определяем шаг, к которому нужно вернуться
        step_priority = ['step_03', 'step_04', 'step_05', 'step_06', 'human_readable']
        required_step = None
        
        for step in step_priority:
            if step in failed_steps:
                required_step = step
                break
        
        return True, required_step, all_errors
    
    return False, None, []
