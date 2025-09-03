#!/usr/bin/env python3
import json
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.getcwd())

try:
    from llm.client import LLM
    from config import MODEL_NAME, OPENAI_API_KEY
    
    # Проверяем конфигурацию
    if not OPENAI_API_KEY:
        result = {
            "provider": "openai",
            "model": MODEL_NAME,
            "ok": False,
            "error": "OPENAI_API_KEY not configured"
        }
    else:
        # Пробуем создать клиент
        llm = LLM()
        result = {
            "provider": "openai", 
            "model": MODEL_NAME,
            "ok": True,
            "error": None
        }
        
except Exception as e:
    result = {
        "provider": "openai",
        "model": "gpt-5-high", 
        "ok": False,
        "error": str(e)
    }

print(json.dumps(result, indent=2))
