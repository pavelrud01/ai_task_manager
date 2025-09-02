"""
Утилиты для обеспечения детерминизма в AI Marketing Agent.
Использует RANDOM_SEED для воспроизводимости результатов.
"""
import random
import numpy as np
from typing import Optional


def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Устанавливает seed для всех генераторов случайных чисел.
    
    Args:
        seed: Значение seed. Если None, используется значение из config.py
    """
    if seed is None:
        from config import RANDOM_SEED
        seed = RANDOM_SEED
    
    if seed is not None:
        # Устанавливаем seed для Python random
        random.seed(seed)
        
        # Устанавливаем seed для numpy (если используется)
        try:
            np.random.seed(seed)
        except ImportError:
            # numpy не установлен, это нормально
            pass
        
        print(f"🔒 Random seed set to: {seed}")


def get_deterministic_choice(items: list, seed_suffix: str = "") -> any:
    """
    Получает детерминистический выбор из списка элементов.
    
    Args:
        items: Список элементов для выбора
        seed_suffix: Суффикс для seed (для разных выборов в одном запуске)
    
    Returns:
        Выбранный элемент
    """
    if not items:
        return None
    
    from config import RANDOM_SEED
    if RANDOM_SEED is not None:
        # Создаем уникальный seed для этого выбора
        choice_seed = RANDOM_SEED + hash(seed_suffix) % 1000
        random.seed(choice_seed)
    
    return random.choice(items)


def get_deterministic_sample(items: list, k: int, seed_suffix: str = "") -> list:
    """
    Получает детерминистическую выборку из списка элементов.
    
    Args:
        items: Список элементов для выборки
        k: Количество элементов для выборки
        seed_suffix: Суффикс для seed
    
    Returns:
        Список выбранных элементов
    """
    if not items or k <= 0:
        return []
    
    if k >= len(items):
        return items.copy()
    
    from config import RANDOM_SEED
    if RANDOM_SEED is not None:
        # Создаем уникальный seed для этой выборки
        sample_seed = RANDOM_SEED + hash(seed_suffix) % 1000
        random.seed(sample_seed)
    
    return random.sample(items, k)


def get_deterministic_shuffle(items: list, seed_suffix: str = "") -> list:
    """
    Получает детерминистически перемешанный список.
    
    Args:
        items: Список для перемешивания
        seed_suffix: Суффикс для seed
    
    Returns:
        Перемешанный список
    """
    if not items:
        return []
    
    from config import RANDOM_SEED
    if RANDOM_SEED is not None:
        # Создаем уникальный seed для этого перемешивания
        shuffle_seed = RANDOM_SEED + hash(seed_suffix) % 1000
        random.seed(shuffle_seed)
    
    shuffled = items.copy()
    random.shuffle(shuffled)
    return shuffled


def ensure_determinism(func):
    """
    Декоратор для обеспечения детерминизма функции.
    Автоматически устанавливает seed перед выполнением функции.
    """
    def wrapper(*args, **kwargs):
        set_random_seed()
        return func(*args, **kwargs)
    return wrapper

