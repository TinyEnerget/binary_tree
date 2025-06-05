"""
Utilits: 
    - for testing algorithms
    - for creating trees
"""
import sys
import os

# Добавляем текущую директорию в путь поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from utils.tests import TreeGenerator
    from utils.tests import PerformanceTester
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    # Попробуем относительные импорты
    try:
        from .tests import TreeGenerator
        from .tests import PerformanceTester
    except ImportError as e2:
        print(f"Ошибка относительного импорта: {e2}")
        raise

__version__ = "1.1.0"
__author__ = "Titov Vladislav"

__all__ = [
    'TreeGenerator',
    'PerformanceTester'
]

