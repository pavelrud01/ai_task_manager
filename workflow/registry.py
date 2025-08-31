import importlib
from .steps.base import BaseStep  # Исправленный импорт, который теперь работает

def load_step(step_name: str) -> BaseStep:
    """
    Динамически загружает и инстанцирует класс шага из модуля по его имени.
    Ищет класс, унаследованный от BaseStep, внутри файла workflow/steps/{step_name}.py.
    """
    try:
        module_path = f"workflow.steps.{step_name}"
        module = importlib.import_module(module_path)
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseStep) and attr is not BaseStep:
                step_instance = attr()
                step_instance.name = step_name
                return step_instance

        raise ImportError(f"Could not find a class inheriting from BaseStep in module: {module_path}")
    
    except ImportError as e:
        print(f"ERROR: Failed to load step '{step_name}'. Make sure the file 'workflow/steps/{step_name}.py' exists and contains a valid Step class. Details: {e}")
        raise