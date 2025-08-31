import re, json, os
from typing import List, Dict
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _extract_questions_from_md(md_text: str) -> List[str]:
    qs = []
    for line in md_text.splitlines():
        t = line.strip()
        if t.startswith(("-", "•", "[")) and "?" in t:
            # Извлекаем текст после маркера или скобки
            question_part = re.split(r'\[.*?\]', t)[-1]
            qs.append(re.sub(r"^[-\•\s]*", "", question_part).strip())
    if not qs:
        qs = [
            "When exactly do you start this job? What triggers it?",
            "How do you judge success (3–7 criteria)?",
            "What positive emotions do you seek? Negative ones to avoid?",
        ]
    return [q for q in qs if q]

def collect_responses(md_standard: str, personas: List[Dict], org_context: Dict) -> Dict:
    questions = _extract_questions_from_md(md_standard)
    results = []
    system = "You are a respondent in a user interview. Answer questions based on your persona. Your answer MUST be a single JSON object with keys: 'answer' (string) and 'followups' (list of objects with 'q' and 'a' keys)."
    
    for persona in personas:
        pid = persona.get("id") or persona.get("name") or f"p{len(results)+1}"
        pprofile = persona.get("profile","")
        persona_transcript = {"respondent_id": pid, "profile": pprofile, "qa": []}
        for i, q in enumerate(questions, start=1):
            user = (f"ORGANIZATIONAL CONTEXT:\n{json.dumps(org_context, ensure_ascii=False)}\n\n"
                    f"YOUR PERSONA: {pprofile}\n\n"
                    f"QUESTION #{i}: {q}\n\n"
                    "Provide your answer in a JSON format.")
            try:
                resp = client.chat.completions.create(
                    model=os.getenv("MODEL_NAME","gpt-4o-mini"),
                    messages=[{"role":"system","content":system},{"role":"user","content":user}],
                    response_format={"type":"json_object"},
                    temperature=0.5
                )
                data = json.loads(resp.choices[0].message.content)
                data['question'] = q
                persona_transcript['qa'].append(data)
            except Exception as e:
                print(f"WARN: LLM call failed for persona {pid}, question {i}. Error: {e}")
                persona_transcript['qa'].append({"question": q, "answer": f"Error: {e}", "followups": []})
        results.append(persona_transcript)
    return {"questions": questions, "transcripts": results}