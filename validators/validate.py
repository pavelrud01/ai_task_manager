import json
from pathlib import Path
from jsonschema import validate, ValidationError

CONTRACTS_PATH = Path(__file__).resolve().parents[1] / "contracts"

REQUIRED_GUIDE_SECTIONS = [
    "Intro",
    "Definitions",
    "Inputs & Preconditions",
    "Process",
    "Core Questions",
    "Deepening",
    "Branching Rules",
    "Evidence Tags",
    "Output Contract",
    "Safety & Ethics",
    "Stop Conditions",
    "Quality Checklist",
    "Red Flags",
    "Acceptance Criteria",
    "No-Gaps Protocol",
    "Self-Review",
    "Versions"
]

def validate_artifact(step_name: str, data: dict, standards: dict) -> tuple[float, float, str]:
    """
    Возвращает (schema_score, checklist_score, notes)
    """
    schema_score, schema_notes = _validate_schema(step_name, data)
    checklist_score, checklist_notes = _validate_checklist(step_name, data)
    
    # after schema validation result:
    # HARD rule: require at least one evidence_ref for clean, verifiable data
    evidence_score, evidence_notes = _evidence_rule(step_name, data)
    
    notes = f"Schema: {schema_notes} | Checklist: {checklist_notes} | Evidence: {evidence_notes}"
    return min(schema_score, 1.0), min(checklist_score, evidence_score), notes

def _validate_schema(step_name: str, data: dict) -> tuple[float, str]:
    schema_path = CONTRACTS_PATH / f"{step_name}.schema.json"
    if not schema_path.exists():
        return 1.0, "No schema"
    try:
        schema = json.loads(schema_path.read_text("utf-8"))
        validate(instance=data, schema=schema)
        return 1.0, "OK"
    except ValidationError as e:
        return 0.0, f"Failed: {e.message}"
    except Exception as e:
        return 0.0, f"Failed: {str(e)}"

def _validate_checklist(step_name: str, data: dict) -> tuple[float, str]:
    # Спец-правила для шага компиляции гайда
    if step_name == "step_02a_guide_compile":
        sections = data.get("sections", {})
        if not isinstance(sections, dict) or not sections:
            return 0.4, "No sections parsed"

        missing = [s for s in REQUIRED_GUIDE_SECTIONS if s not in sections]
        if missing:
            return 0.6, f"Missing sections: {', '.join(missing)}"

        sources = data.get("sources", [])
        if not isinstance(sources, list) or any("sha256" not in s or not s["sha256"] for s in sources):
            return 0.7, "Sources missing sha256 hashes"

        md = data.get("markdown", "")
        if not isinstance(md, str) or len(md) < 1000:
            return 0.8, "Markdown too short (<1000 chars)"

        return 1.0, "OK"

    # Прочие правила (оставь, если были раньше)
    if step_name == "step_03_offers_inventory":
        offers = data.get("offers")
        if isinstance(offers, list) and offers:
            return 1.0, "OK"
        return 0.3, "Missing 'offers' list"

    if step_name == "step_05_segments":
        segs = data.get("segments", [])
        if isinstance(segs, list) and segs:
            return 1.0, "OK"
        return 0.4, "No segments generated"

    return 1.0, "OK"

def _evidence_rule(step_name: str, data: dict) -> tuple[float, str]:
    # ЖЁСТКОЕ правило: для ключевых шагов требуем хотя бы один evidence_ref
    MUST_HAVE = {"step_04_jtbd", "step_05_segments", "step_06_decision_mapping"}
    if step_name not in MUST_HAVE:
        return (1.0, "N/A")
    
    try:
        def has_evidence(obj):
            if isinstance(obj, dict):
                if "evidence_refs" in obj and isinstance(obj["evidence_refs"], list) and len(obj["evidence_refs"]) > 0:
                    return True
                return any(has_evidence(v) for v in obj.values())
            if isinstance(obj, list):
                return any(has_evidence(x) for x in obj)
            return False

        return (1.0, "OK") if has_evidence(data) else (0.0, "No evidence_refs — hard fail")
    except Exception as e:
        return (0.0, f"Hard evidence rule error: {e}")
