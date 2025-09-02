from .base import BaseStep, StepResult
from llm.client import LLM
import json
import pathlib
import config
from typing import List, Dict, Any
from collections import Counter
import re

class Step(BaseStep):
    name = "step_06a_cluster"
    
    def __init__(self):
        self.llm = LLM()

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Объединить все сегменты в кластеры по признакам AJTBD.
        """
        run_id = context.get("run_id", "default_run")
        
        # Собираем все LJD данные
        ljd_data = self._collect_ljd_data(run_id)
        
        if not ljd_data:
            return StepResult(
                data={},
                score=0.0,
                notes="No LJD data found for clustering",
                uncertainty=0.0
            )
        
        # Извлекаем фичи для кластеризации
        features = self._extract_features(ljd_data)
        
        # Выполняем кластеризацию
        clusters = self._perform_clustering(ljd_data, features)
        
        # Формируем результат
        result_data = {
            "algo": "rule_based_similarity",
            "features": list(features.keys()),
            "clusters": clusters
        }
        
        # Сохраняем результат
        cluster_dir = pathlib.Path("artifacts") / run_id / "05_cluster"
        cluster_dir.mkdir(parents=True, exist_ok=True)
        
        clusters_path = cluster_dir / "clusters.json"
        with open(clusters_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        return StepResult(
            data=result_data,
            score=0.8 if clusters else 0.0,
            notes=f"Created {len(clusters)} clusters from {len(ljd_data)} segments",
            uncertainty=0.2
        )
    
    def _collect_ljd_data(self, run_id: str) -> List[Dict[str, Any]]:
        """Собирает все LJD данные из директорий"""
        ljd_data = []
        ljd_dir = pathlib.Path("artifacts") / run_id / "03_ljd"
        
        if not ljd_dir.exists():
            return ljd_data
        
        # Ищем все ljd.json файлы
        for segment_dir in ljd_dir.iterdir():
            if segment_dir.is_dir():
                ljd_file = segment_dir / "ljd.json"
                if ljd_file.exists():
                    try:
                        with open(ljd_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            ljd_data.append(data)
                    except Exception as e:
                        continue
        
        return ljd_data
    
    def _extract_features(self, ljd_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Извлекает ключевые фичи из LJD данных"""
        features = {
            "job_titles": [],
            "pains": [],
            "triggers": [],
            "constraints": [],
            "desired_outcomes": []
        }
        
        for ljd in ljd_data:
            # Извлекаем job_title
            job_title = ljd.get("job_title", "")
            if job_title:
                features["job_titles"].append(job_title.lower())
            
            # Извлекаем pains
            pains = ljd.get("pains", [])
            features["pains"].extend([pain.lower() for pain in pains])
            
            # Извлекаем triggers
            triggers = ljd.get("triggers", [])
            features["triggers"].extend([trigger.lower() for trigger in triggers])
            
            # Извлекаем constraints
            constraints = ljd.get("constraints", [])
            features["constraints"].extend([constraint.lower() for constraint in constraints])
            
            # Извлекаем desired_outcomes
            outcomes = ljd.get("desired_outcomes", [])
            features["desired_outcomes"].extend([outcome.lower() for outcome in outcomes])
        
        return features
    
    def _perform_clustering(self, ljd_data: List[Dict[str, Any]], features: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Выполняет простую rule-based кластеризацию"""
        clusters = []
        
        # Находим наиболее частые паттерны
        common_pains = self._get_common_terms(features["pains"], min_count=2)
        common_triggers = self._get_common_terms(features["triggers"], min_count=2)
        common_outcomes = self._get_common_terms(features["desired_outcomes"], min_count=2)
        
        # Создаем кластеры на основе общих паттернов
        cluster_id = 1
        
        # Кластер по общим болям
        if common_pains:
            pain_cluster = self._create_cluster_by_pattern(
                ljd_data, "pain", common_pains[0], f"cluster_{cluster_id}"
            )
            if pain_cluster:
                clusters.append(pain_cluster)
                cluster_id += 1
        
        # Кластер по общим триггерам
        if common_triggers:
            trigger_cluster = self._create_cluster_by_pattern(
                ljd_data, "trigger", common_triggers[0], f"cluster_{cluster_id}"
            )
            if trigger_cluster:
                clusters.append(trigger_cluster)
                cluster_id += 1
        
        # Кластер по общим результатам
        if common_outcomes:
            outcome_cluster = self._create_cluster_by_pattern(
                ljd_data, "outcome", common_outcomes[0], f"cluster_{cluster_id}"
            )
            if outcome_cluster:
                clusters.append(outcome_cluster)
                cluster_id += 1
        
        # Если нет явных кластеров, создаем один общий
        if not clusters:
            all_segments = [ljd["segment_id"] for ljd in ljd_data]
            clusters.append({
                "id": "cluster_1",
                "label": "General Segments",
                "members": all_segments,
                "unify_rule": "All segments grouped together"
            })
        
        return clusters
    
    def _get_common_terms(self, terms: List[str], min_count: int = 2) -> List[str]:
        """Находит наиболее частые термины"""
        # Простая нормализация и подсчет
        normalized_terms = []
        for term in terms:
            # Убираем стоп-слова и нормализуем
            words = re.findall(r'\b\w+\b', term.lower())
            normalized_terms.extend(words)
        
        counter = Counter(normalized_terms)
        return [term for term, count in counter.most_common(5) if count >= min_count]
    
    def _create_cluster_by_pattern(self, ljd_data: List[Dict[str, Any]], pattern_type: str, 
                                 pattern_term: str, cluster_id: str) -> Dict[str, Any]:
        """Создает кластер на основе паттерна"""
        members = []
        
        for ljd in ljd_data:
            if pattern_type == "pain":
                pains = [pain.lower() for pain in ljd.get("pains", [])]
                if any(pattern_term in pain for pain in pains):
                    members.append(ljd["segment_id"])
            elif pattern_type == "trigger":
                triggers = [trigger.lower() for trigger in ljd.get("triggers", [])]
                if any(pattern_term in trigger for trigger in triggers):
                    members.append(ljd["segment_id"])
            elif pattern_type == "outcome":
                outcomes = [outcome.lower() for outcome in ljd.get("desired_outcomes", [])]
                if any(pattern_term in outcome for outcome in outcomes):
                    members.append(ljd["segment_id"])
        
        if len(members) >= 2:  # Минимум 2 сегмента для кластера
            return {
                "id": cluster_id,
                "label": f"Segments with {pattern_type}: {pattern_term}",
                "members": members,
                "unify_rule": f"Common {pattern_type} pattern: {pattern_term}"
            }
        
        return None
