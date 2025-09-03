import os
import yaml
import pathlib
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()

# Load YAML configuration
def load_yaml_config() -> Dict[str, Any]:
    """Load configuration from ajtd.yaml file"""
    config_path = os.path.join(os.path.dirname(__file__), 'configs', 'ajtd.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Warning: Configuration file {config_path} not found. Using default values.")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}")
        return {}

def load_ajtd_config(path="configs/ajtd.yaml") -> dict:
    """Load AJTD configuration from YAML file"""
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No config at {path}")
    return yaml.safe_load(p.read_text(encoding="utf-8"))

# Load YAML config
YAML_CONFIG = load_yaml_config()

# Helper functions to access YAML config
def get_config_path(key, default=None):
    """Get path configuration from YAML"""
    return YAML_CONFIG.get('paths', {}).get(key, default)

def get_config_model(key, default=None):
    """Get model configuration from YAML"""
    return YAML_CONFIG.get('models', {}).get(key, default)

def get_config_interview(key, default=None):
    """Get interview configuration from YAML"""
    return YAML_CONFIG.get('interview', {}).get(key, default)

def get_config_split_policy(key, default=None):
    """Get split policy configuration from YAML"""
    return YAML_CONFIG.get('split_policy', {}).get(key, default)

def get_config_qa(key, default=None):
    """Get QA configuration from YAML"""
    return YAML_CONFIG.get('qa', {}).get(key, default)

def get_config_orchestration(key: str, default: Any = None) -> Any:
    """Get orchestration configuration from YAML"""
    return YAML_CONFIG.get('orchestration', {}).get(key, default)


def load_unified_config() -> Dict[str, Any]:
    """
    Единая загрузка конфигурации без «расползания» по файлам.
    Возвращает словарь с всеми настройками.
    """
    return {
        # Core settings
        "openai_api_key": OPENAI_API_KEY,
        "model_name": MODEL_NAME,
        
        # Workflow control
        "quality_threshold": QUALITY_THRESHOLD,
        "max_reflection_loops": MAX_REFLECTION_LOOPS,
        "autofix_until_valid": AUTOFIX_UNTIL_VALID,
        "max_passes": MAX_PASSES,
        
        # HITL thresholds
        "uncertainty_threshold_ask": UNCERTAINTY_THRESHOLD_ASK,
        "hitl_uncertainty_trigger": HITL_UNCERTAINTY_TRIGGER,
        "hitl_score_buffer": HITL_SCORE_BUFFER,
        
        # Determinism
        "random_seed": RANDOM_SEED,
        
        # Workflow definition
        "workflow_steps": WORKFLOW_STEPS,
        "critical_steps_for_hitl": CRITICAL_STEPS_FOR_HITL,
        
        # YAML config
        "yaml_config": YAML_CONFIG
    }

# --- Core Settings ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5-high")

# --- Workflow Control ---
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", 0.75))
MAX_REFLECTION_LOOPS = int(os.getenv("MAX_REFLECTION_LOOPS", 1))
AUTOFIX_UNTIL_VALID = os.getenv("AUTOFIX_UNTIL_VALID", "true").lower() == "true"
MAX_PASSES = int(os.getenv("MAX_PASSES", 3))

# --- HITL Thresholds ---
UNCERTAINTY_THRESHOLD_ASK = float(os.getenv("UNCERTAINTY_THRESHOLD_ASK", 0.6))
HITL_UNCERTAINTY_TRIGGER = float(os.getenv("HITL_UNCERTAINTY_TRIGGER", 0.3))
HITL_SCORE_BUFFER = float(os.getenv("HITL_SCORE_BUFFER", 0.1))

# --- Determinism ---
RANDOM_SEED = os.getenv("RANDOM_SEED")
if RANDOM_SEED:
    RANDOM_SEED = int(RANDOM_SEED)

# --- Workflow Definition ---
WORKFLOW_STEPS = [
    "step_00_compliance_check",
    "step_00a_llm_preflight",
    "step_02_extract",
    "step_02a_guide_compile",
    "step_02b_initial_classification",
    "step_03_interview_collect",
    "step_04_jtbd",
    "step_05_segments",
    "step_06_decision_mapping",
    "step_10_synthesis",
    "step_11_tasks",
    "step_export_human_readable",
]
CRITICAL_STEPS_FOR_HITL = [
    "step_02a_guide_compile",  # <— добавить эту строку
    "step_11_tasks"
]