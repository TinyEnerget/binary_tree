import sys
import os

# Добавляем текущую директорию в путь поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from tree_generator import TreeCreator
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    try:
        from .tree_generator import TreeCreator
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        raise

__version__ = "1.1.0"
__author__ = "Vlad Titov"

__all__ = [
    'TreeCreator',
]

