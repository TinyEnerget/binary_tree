"""model_processing package

Обеспечивает доступ к основным классам и модулям пакета для анализа электрической сети
и построения ее дерева.
"""

import sys
import os

# Добавляем текущую директорию в путь поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from model_processing.utils import load_json, save_json
    from model_processing.comparator import TreeComparator
    from model_processing.models import ElementType, NetworkElement, NetworkModel, NetworkModelError
    from model_processing.analyzers import BusAnalyzer, ElementAnalyzer, GeneratorAnalyzer, LoadAnalyzer, OverheadLineAnalyzer, SystemAnalyzer, TransformerAnalyzer
    from model_processing.registry import AnalyzerRegistry
    from model_processing.tree_builder import NetworkTreeBuilder
    from model_processing.analyzer import NetworkAnalyzer
except ImportError as e:
    print(f"Ошибка импорта модуля: {e}")
    try:
        from .utils import load_json, save_json
        from .comparator import TreeComparator
        from .models import ElementType, NetworkElement, NetworkModel, NetworkModelError
        from .analyzers import BusAnalyzer, ElementAnalyzer, GeneratorAnalyzer, LoadAnalyzer, OverheadLineAnalyzer, SystemAnalyzer, TransformerAnalyzer
        from .registry import AnalyzerRegistry
        from .tree_builder import NetworkTreeBuilder
        from .analyzer import NetworkAnalyzer
    except ImportError as e2:
        print(f"Ошибка импорта модуля: {e2}")
        raise

__version__ = "1.1.0"
__author__ = "Vlad Titov"

__all__ = ['load_json', 'save_json', 'TreeComparator', 'ElementType', 'NetworkElement', 'NetworkModel', 'BusAnalyzer', 'ElementAnalyzer', 'GeneratorAnalyzer', 'LoadAnalyzer', 'OverheadLineAnalyzer', 'SystemAnalyzer', 'TransformerAnalyzer', 'AnalyzerRegistry', 'NetworkTreeBuilder', 'NetworkAnalyzer', 'NetworkModelError']