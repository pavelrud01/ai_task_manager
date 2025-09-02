from .base import BaseStep, StepResult
from llm.client import LLM
from validators.standards_loader import get_standard_for_step
import json
import pathlib
import config

class Step(BaseStep):
    name = "step_05b_interview_refine"
    
    def __init__(self):
        self.llm = LLM()

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Второй круг интервью - уточняем сегмент на основе LJD, при необходимости делим на под-сегменты.
        """
        run_id = context.get("run_id", "default_run")
        segments_data = artifacts.get("step_05_segments", {}).get("data", {})
        segments = segments_data.get("segments", [])
        
        if not segments:
            return StepResult(
                data={},
                score=0.0,
                notes="No segments found from step_05_segments",
                uncertainty=0.0
            )
        
        refined_segments = []
        split_reasons = []
        
        # Получаем настройки из конфигурации
        max_children = config.get_config_split_policy('max_children_per_segment', 3)
        min_similarity_delta = config.get_config_split_policy('min_similarity_delta', 0.2)
        
        for segment in segments:
            segment_id = segment.get("segment_id", "unknown")
            
            # Читаем LJD файл для этого сегмента
            ljd_path = pathlib.Path("artifacts") / run_id / "03_ljd" / segment_id / "ljd.json"
            
            if not ljd_path.exists():
                # Если LJD нет, пропускаем сегмент
                refined_segments.append(segment)
                continue
            
            try:
                with open(ljd_path, 'r', encoding='utf-8') as f:
                    ljd_data = json.load(f)
            except Exception as e:
                refined_segments.append(segment)
                continue
            
            # Генерируем уточняющие вопросы на основе LJD
            system = "You are an expert interviewer. Analyze the LJD data and generate clarifying questions to refine the segment understanding."
            user = f"""
            LJD DATA:
            {json.dumps(ljd_data, indent=2, ensure_ascii=False)}
            
            SEGMENT INFO:
            {json.dumps(segment, indent=2, ensure_ascii=False)}
            
            Generate 3-5 clarifying questions to better understand this segment.
            Consider if this segment should be split into sub-segments based on:
            - Different job titles or roles
            - Different pain points or triggers
            - Different desired outcomes
            - Different constraints or contexts
            
            Return JSON with:
            {{
                "questions": ["question1", "question2", ...],
                "should_split": true/false,
                "split_reason": "explanation if should_split is true",
                "sub_segments": [
                    {{"id": "segment_A", "label": "description", "criteria": "..."}},
                    {{"id": "segment_B", "label": "description", "criteria": "..."}}
                ]
            }}
            """
            
            try:
                resp = self.llm.generate_json(
                    system_prompt=system,
                    user_prompt=user,
                    org_context=str(context.get("org_context", {})),
                    standard_schema={},
                    standard_text="",
                    reflection_notes=""
                )
                
                # Обрабатываем ответ
                if resp.get("should_split", False):
                    # Создаем под-сегменты
                    sub_segments = resp.get("sub_segments", [])
                    split_reason = resp.get("split_reason", "Segment split based on LJD analysis")
                    
                    for i, sub_seg in enumerate(sub_segments[:max_children]):
                        sub_segment_id = f"{segment_id}_{chr(65+i)}"  # A, B, C
                        
                        # Создаем директорию для под-сегмента
                        sub_dir = pathlib.Path("artifacts") / run_id / "04_refine" / sub_segment_id
                        sub_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Создаем уточненное интервью для под-сегмента
                        refined_interview = {
                            "segment_id": sub_segment_id,
                            "parent_segment_id": segment_id,
                            "split_reason": split_reason,
                            "questions": resp.get("questions", []),
                            "criteria": sub_seg.get("criteria", ""),
                            "label": sub_seg.get("label", ""),
                            "original_segment": segment
                        }
                        
                        # Сохраняем уточненное интервью
                        interview_path = sub_dir / "interview_refined.json"
                        with open(interview_path, 'w', encoding='utf-8') as f:
                            json.dump(refined_interview, f, indent=2, ensure_ascii=False)
                        
                        refined_segments.append({
                            **segment,
                            "segment_id": sub_segment_id,
                            "parent_segment_id": segment_id,
                            "split_reason": split_reason,
                            "label": sub_seg.get("label", segment.get("label", ""))
                        })
                    
                    split_reasons.append({
                        "original_segment_id": segment_id,
                        "split_reason": split_reason,
                        "sub_segments": [sub_seg["id"] for sub_seg in sub_segments[:max_children]]
                    })
                else:
                    # Не разделяем, просто уточняем
                    refine_dir = pathlib.Path("artifacts") / run_id / "04_refine" / segment_id
                    refine_dir.mkdir(parents=True, exist_ok=True)
                    
                    refined_interview = {
                        "segment_id": segment_id,
                        "questions": resp.get("questions", []),
                        "refinement_notes": "Segment refined but not split",
                        "original_segment": segment
                    }
                    
                    interview_path = refine_dir / "interview_refined.json"
                    with open(interview_path, 'w', encoding='utf-8') as f:
                        json.dump(refined_interview, f, indent=2, ensure_ascii=False)
                    
                    refined_segments.append(segment)
                    
            except Exception as e:
                # В случае ошибки оставляем оригинальный сегмент
                refined_segments.append(segment)
                continue
        
        # Формируем результат
        result_data = {
            "segments": refined_segments,
            "split_reasons": split_reasons,
            "total_segments": len(refined_segments),
            "splits_performed": len(split_reasons)
        }
        
        return StepResult(
            data=result_data,
            score=0.8 if refined_segments else 0.0,
            notes=f"Refined {len(segments)} segments, performed {len(split_reasons)} splits",
            uncertainty=0.2 if split_reasons else 0.1
        )
