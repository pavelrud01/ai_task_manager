from .base import BaseStep, StepResult
from llm.client import LLM
import json
import pathlib
import csv
import config

class Step(BaseStep):
    name = "step_06b_personas"
    
    def __init__(self):
        self.llm = LLM()

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Сгенерировать итоговые персоны и реестр сегментов для маркетинга.
        """
        run_id = context.get("run_id", "default_run")
        
        # Читаем данные кластеров
        clusters_data = artifacts.get("step_06a_cluster", {}).get("data", {})
        clusters = clusters_data.get("clusters", [])
        
        if not clusters:
            return StepResult(
                data={},
                score=0.0,
                notes="No clusters found from step_06a_cluster",
                uncertainty=0.0
            )
        
        # Собираем данные сегментов для генерации персон
        segments_data = self._collect_segments_data(run_id)
        
        # Генерируем персоны
        personas = self._generate_personas(clusters, segments_data)
        
        # Генерируем CSV реестр
        csv_data = self._generate_segments_csv(clusters, segments_data)
        
        # Сохраняем результаты
        cluster_dir = pathlib.Path("artifacts") / run_id / "05_cluster"
        cluster_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем персоны в Markdown
        personas_path = cluster_dir / "personas.md"
        with open(personas_path, 'w', encoding='utf-8') as f:
            f.write(personas)
        
        # Сохраняем CSV реестр
        csv_path = cluster_dir / "segments_final.csv"
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)
        
        result_data = {
            "personas_generated": len(clusters),
            "segments_in_csv": len(csv_data),
            "personas_file": str(personas_path),
            "csv_file": str(csv_path)
        }
        
        return StepResult(
            data=result_data,
            score=0.8 if personas and csv_data else 0.0,
            notes=f"Generated {len(clusters)} personas and {len(csv_data)} segment records",
            uncertainty=0.1
        )
    
    def _collect_segments_data(self, run_id: str) -> dict:
        """Собирает данные всех сегментов"""
        segments_data = {}
        
        # Читаем LJD данные
        ljd_dir = pathlib.Path("artifacts") / run_id / "03_ljd"
        if ljd_dir.exists():
            for segment_dir in ljd_dir.iterdir():
                if segment_dir.is_dir():
                    ljd_file = segment_dir / "ljd.json"
                    if ljd_file.exists():
                        try:
                            with open(ljd_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                segments_data[data["segment_id"]] = data
                        except Exception:
                            continue
        
        return segments_data
    
    def _generate_personas(self, clusters: list, segments_data: dict) -> str:
        """Генерирует персоны в формате Markdown"""
        personas_md = "# Персоны для маркетинга\n\n"
        
        for cluster in clusters:
            cluster_id = cluster["id"]
            cluster_label = cluster["label"]
            members = cluster["members"]
            
            personas_md += f"## {cluster_label}\n\n"
            personas_md += f"**Кластер ID:** {cluster_id}\n"
            personas_md += f"**Правило объединения:** {cluster['unify_rule']}\n"
            personas_md += f"**Количество сегментов:** {len(members)}\n\n"
            
            # Анализируем сегменты в кластере
            cluster_segments = [segments_data.get(seg_id, {}) for seg_id in members if seg_id in segments_data]
            
            if cluster_segments:
                # Находим общие паттерны
                common_job_titles = self._find_common_patterns([seg.get("job_title", "") for seg in cluster_segments])
                common_pains = self._find_common_patterns([pain for seg in cluster_segments for pain in seg.get("pains", [])])
                common_outcomes = self._find_common_patterns([outcome for seg in cluster_segments for outcome in seg.get("desired_outcomes", [])])
                
                personas_md += "### Ключевые характеристики:\n\n"
                personas_md += f"**Роли:** {', '.join(common_job_titles[:3])}\n\n"
                personas_md += f"**Основные боли:** {', '.join(common_pains[:3])}\n\n"
                personas_md += f"**Желаемые результаты:** {', '.join(common_outcomes[:3])}\n\n"
                
                # Генерируем описание персоны через LLM
                persona_description = self._generate_persona_description(cluster, cluster_segments)
                personas_md += f"### Описание персоны:\n\n{persona_description}\n\n"
            
            personas_md += "---\n\n"
        
        return personas_md
    
    def _generate_segments_csv(self, clusters: list, segments_data: dict) -> list:
        """Генерирует CSV реестр сегментов"""
        csv_data = []
        
        for cluster in clusters:
            cluster_id = cluster["id"]
            members = cluster["members"]
            
            for segment_id in members:
                segment_data = segments_data.get(segment_id, {})
                
                # Извлекаем данные для CSV
                job_title = segment_data.get("job_title", "Unknown")
                pains = segment_data.get("pains", [])
                outcomes = segment_data.get("desired_outcomes", [])
                
                # Генерируем маркетинговые элементы
                hook_attention = self._generate_hook(job_title, pains)
                value_bullets = self._generate_value_bullets(outcomes)
                mini_case = self._generate_mini_case(job_title, outcomes)
                cta_text = self._generate_cta_text(outcomes)
                gift_id = self._generate_gift_id(cluster_id)
                
                csv_row = {
                    "segment_id": segment_id,
                    "label": segment_data.get("job_title", "Unknown Role"),
                    "jtbd": segment_data.get("job_summary", "Job summary not available"),
                    "child_age": "N/A",  # Заглушка, нужно извлекать из контекста
                    "channel": "online",  # Заглушка, нужно извлекать из конфигурации
                    "cluster_id": cluster_id,
                    "hook_attention": hook_attention,
                    "value_bullets": " | ".join(value_bullets),
                    "mini_case": mini_case,
                    "cta_text": cta_text,
                    "gift_id": gift_id
                }
                
                csv_data.append(csv_row)
        
        return csv_data
    
    def _find_common_patterns(self, items: list) -> list:
        """Находит наиболее частые элементы в списке"""
        from collections import Counter
        counter = Counter(items)
        return [item for item, count in counter.most_common(5) if item.strip()]
    
    def _generate_persona_description(self, cluster: dict, segments: list) -> str:
        """Генерирует описание персоны через LLM"""
        try:
            system = "You are a marketing expert. Create a compelling persona description based on the cluster data."
            user = f"""
            CLUSTER DATA:
            {json.dumps(cluster, indent=2, ensure_ascii=False)}
            
            SEGMENTS DATA:
            {json.dumps(segments[:3], indent=2, ensure_ascii=False)}
            
            Create a 2-3 paragraph persona description that marketers can use for targeting.
            Focus on the common pain points, desired outcomes, and behavioral patterns.
            """
            
            resp = self.llm.generate_json(
                system_prompt=system,
                user_prompt=user,
                org_context="",
                standard_schema={},
                standard_text="",
                reflection_notes=""
            )
            
            return resp.get("description", "Persona description not available")
        except Exception:
            return "Persona description generation failed"
    
    def _generate_hook(self, job_title: str, pains: list) -> str:
        """Генерирует заголовок-хук"""
        if pains:
            return f"Tired of {pains[0].lower()}? {job_title}s, this is for you!"
        return f"Attention {job_title}s: Transform your workflow today!"
    
    def _generate_value_bullets(self, outcomes: list) -> list:
        """Генерирует 2-3 буллета пользы"""
        bullets = []
        for outcome in outcomes[:3]:
            bullets.append(f"✓ {outcome}")
        return bullets
    
    def _generate_mini_case(self, job_title: str, outcomes: list) -> str:
        """Генерирует мини-кейс"""
        if outcomes:
            return f"Like Sarah, a {job_title} who achieved {outcomes[0].lower()} in just 2 weeks."
        return f"Real {job_title} success story: 50% improvement in 30 days."
    
    def _generate_cta_text(self, outcomes: list) -> str:
        """Генерирует CTA текст"""
        if outcomes:
            return f"Start achieving {outcomes[0].lower()} today - Get started now!"
        return "Transform your workflow - Start your free trial!"
    
    def _generate_gift_id(self, cluster_id: str) -> str:
        """Генерирует ID подарка"""
        return f"gift_{cluster_id}_001"
