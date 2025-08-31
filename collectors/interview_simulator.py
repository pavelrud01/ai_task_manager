import os
import json
from openai import OpenAI
from typing import List, Dict
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _extract_questions_from_standard(md_text: str) -> List[str]:
    questions = []
    for line in md_text.splitlines():
        clean_line = line.strip()
        if clean_line.startswith('[') and ']' in clean_line and '?' in clean_line:
            question_text = clean_line.split(']', 1)[-1].strip()
            questions.append(question_text)
    return questions if questions else ["Tell me the story of how you solve this problem?"]

def run_simulation(standard_text: str, personas: List[Dict], org_context_text: str) -> Dict:
    questions = _extract_questions_from_standard(standard_text)
    transcripts = []
    facilitator_instructions = "You are a skilled JTBD interviewer. Your goal is to get deep, honest answers. Ask the provided question clearly. Your output must be ONLY the question text."
    
    for persona in personas:
        persona_id = persona.get("id", "persona_1")
        persona_profile = persona.get("profile", "a typical user")
        persona_transcript = {"persona_id": persona_id, "profile": persona_profile, "dialogue": []}
        persona_instructions = f"You are playing a role. Your persona is: {persona_profile}. Answer the interviewer's questions from this perspective. Be detailed, honest, and mention your motivations, frustrations, and context. Your output must be ONLY your answer text."
        
        for q_idx, question in enumerate(questions):
            fac_resp = client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": facilitator_instructions},
                    {"role": "user", "content": f"Business context:\n{org_context_text}\n\nAsk this question:\n{question}"}
                ],
                temperature=0.1
            )
            asked_question = fac_resp.choices[0].message.content.strip()
            
            persona_resp = client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "gpt-4o"),
                messages=[
                    {"role": "system", "content": persona_instructions},
                    {"role": "user", "content": f"Business context:\n{org_context_text}\n\nInterviewer asks: '{asked_question}'"}
                ],
                temperature=0.7
            )
            answer = persona_resp.choices[0].message.content.strip()
            
            persona_transcript["dialogue"].append({"question": asked_question, "answer": answer})
        transcripts.append(persona_transcript)
    
    return {"transcripts": transcripts}