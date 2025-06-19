"""
Graph Analyzer Package

Пакет для анализа графов с поддержкой:
- Многопоточного анализа
- Поиска путей между узлами
- Визуализации связей
- Статистического анализа
"""

import sys
import os

# Добавляем текущую директорию в путь поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from multi_root_graph_analyzer import UndirectedGraphAnalyzer
    from graph_creator import GraphCreator
    from graph_visualizer import GraphVisualizer
    from connecting_graphs_checker import UndirectedGraphConnectingAnalyzer
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    # Попробуем относительные импорты
    try:
        from .multi_root_graph_analyzer import UndirectedGraphAnalyzer
        from .graph_creator import GraphCreator
        from .graph_visualizer import GraphVisualizer
        from .connecting_graphs_checker import UndirectedGraphConnectingAnalyzer
    except ImportError as e2:
        print(f"Ошибка относительного импорта: {e2}")
        raise

__version__ = "1.1.0"
__author__ = "Titov Vladislav"

__all__ = [
    'UndirectedGraphAnalyzer',
    'GraphCreator',
    'GraphVisualizer',
    'UndirectedGraphConnectingAnalyzer',
]
