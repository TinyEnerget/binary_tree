"""
Основной скрипт для запуска анализа сети, построения дерева и графа,
а также их последующего анализа и визуализации.

This is the main script to run network analysis, tree and graph construction,
and subsequent analysis and visualization of these structures.
"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Set

# Добавляем родительскую директорию в путь
# Adding the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем необходимые классы
# Importing necessary classes
from model_processing.analyzer import NetworkAnalyzer
from model_processing.models import NetworkAnalysisResult
from tree_analyzer.tree_construction import Node
from tree_analyzer import MultiRootAnalyzer, VisualizeForest, TreeCreator
from graph_analyzer import GraphCreator, GraphVisualizer, UndirectedGraphAnalyzer

# Пути к файлам модели и для выходных данных
# File paths for the model and output data
# TODO: Замените на актуальные пути или используйте относительные пути / переменные окружения
#       Replace with actual paths or use relative paths / environment variables
# model_file_path_str: str = 'C:\\Users\\Vlad Titov\\Desktop\\Work\\binary_tree\\model_processing\\available_modification\\converted.json'

# Используем относительные пути для примера
# Using relative paths for the example
project_root: Path = Path(os.path.dirname(os.path.abspath(__file__)))
model_file_path: Path = project_root / 'model_processing' / 'available_modification' / 'converted.json'

# Директория для сохранения результатов
# Directory for saving results
results_dir: Path = project_root / "analysis_results"
os.makedirs(results_dir, exist_ok=True)

# Путь для сохранения промежуточного дерева от NetworkAnalyzer
network_analyzer_output_tree_file_path: Path = results_dir / "network_analysis_tree.json"
# Директория для GraphCreator, куда он сохранит output_graph.json
graph_creator_output_dir: Path = results_dir


# 1. Выполняем анализ сети ОДИН РАЗ
# 1. Perform network analysis ONCE
print(f"Анализ модели из: {model_file_path}")
analysis_result: Optional[NetworkAnalysisResult] = None # Инициализация / Initialization
try:
    analysis_result = NetworkAnalyzer.analyze_network(
        str(model_file_path),
        str(network_analyzer_output_tree_file_path)
    )
    print(f"Анализ сети завершен. Промежуточное дерево сохранено в: {network_analyzer_output_tree_file_path}")
except FileNotFoundError:
    print(f"ОШИБКА: Файл модели не найден по пути: {model_file_path}")
    sys.exit(1)
except Exception as e:
    print(f"ОШИБКА: Произошла ошибка во время анализа сети: {e}")
    sys.exit(1)

if not analysis_result:
    print("ОШИБКА: Результат анализа сети не был получен. Завершение работы. / ERROR: Network analysis result was not obtained. Exiting.")
    sys.exit(1)

# 2. Создаем дерево Node-объектов, передавая результат анализа
# 2. Create a tree of Node objects, passing the analysis result
print("\nСоздание структуры дерева Node...")
# TreeCreator теперь может не нуждаться в model_path и out_path, если ему передан analysis_result
# The out_path for TreeCreator was for NetworkAnalyzer, which is now called separately.
tree_creator: TreeCreator = TreeCreator(analysis_result=analysis_result)
tree_roots: List[Node] = tree_creator.create_tree()
print(f"Структура дерева Node создана. Количество корневых узлов: {len(tree_roots)}")

# 3. Создаем граф, передавая результат анализа
# 3. Create a graph, passing the analysis result
# GraphCreator все еще нужен out_path для сохранения своего output_graph.json
print("\nСоздание структуры графа...")
graph_creator: GraphCreator = GraphCreator(out_path=str(graph_creator_output_dir), analysis_result=analysis_result)
graph_adj_list: Dict[str, Set[str]] = graph_creator.create_graph()
print(f"Структура графа создана и сохранена в директории: {graph_creator_output_dir / 'output_graph.json'}")


# Анализ дерева (списка Node)
# Analyzing the tree (list of Node objects)
print("\nАнализ дерева (MultiRootAnalyzer)...")
analyzer_tree: MultiRootAnalyzer = MultiRootAnalyzer(tree_roots)
stats_tree: Dict[str, Any] = analyzer_tree.get_forest_statistics()
# connections_tree: List[Dict[str, Any]] = analyzer_tree.find_connections_between_roots() # Вызывается в get_forest_statistics если надо

if stats_tree.get('trees_info'):
    # Убедимся, что trees_info не пустой, прежде чем обращаться по индексу
    if stats_tree['trees_info']:
        print(f"  Статистика по первому дереву: Глубина: {stats_tree['trees_info'][0].get('depth', 'N/A')}, Количество узлов: {stats_tree['trees_info'][0].get('nodes_count', 'N/A')}")
    else:
        print("  Информация о деревьях в статистике отсутствует (trees_info пуст).")
else:
    print("  Информация о деревьях (trees_info) отсутствует в статистике.")

# Анализ графа (словаря смежности)
# Analyzing the graph (adjacency list dictionary)
print("\nАнализ графа (UndirectedGraphAnalyzer)...")
analyzer_graph: UndirectedGraphAnalyzer = UndirectedGraphAnalyzer(graph_adj_list)
stats_graph: Dict[str, Any] = analyzer_graph.graph_statistics()
print(f"  Статистика по графу: Всего узлов: {stats_graph.get('total_nodes', 'N/A')}, Всего ребер: {stats_graph.get('total_edges', 'N/A')}")

# Пример поиска путей
# Example of pathfinding
# Используем ID из analysis_result.nodes, если они там есть, или примеры
# Use IDs from analysis_result.nodes if available, or examples
node_A: str = 'ebe34ba8-6a85-416d-884e-f81ac31e3d72' # Пример ID / Example ID
node_B: str = 'c287dc60-661f-4e21-87c7-2b6366b25f8f' # Пример ID / Example ID

if analysis_result.nodes and node_A in analysis_result.nodes and node_B in analysis_result.nodes:
    print(f"\nПоиск путей в дереве между '{node_A}' и '{node_B}':")
    analyzer_tree.print_paths_between_nodes(node_A, node_B)

    if node_A in graph_adj_list and node_B in graph_adj_list:
        print(f"\nПоиск путей в графе между '{node_A}' и '{node_B}':")
        analyzer_graph.print_all_paths(node_A, node_B)
    else:
        print(f"\nУзлы '{node_A}' или '{node_B}' отсутствуют в созданном графе для поиска путей.")
else:
    print(f"\nУзлы '{node_A}' или '{node_B}' (или оба) отсутствуют в исходной модели для примера поиска путей.")


# Визуализация дерева
# Visualizing the tree
print("\nВизуализация леса (дерева)...")
visualizer_forest: VisualizeForest = VisualizeForest(analyzer_tree)
visualizer_forest.visualize_forest_connections()

# Визуализация графа
# Visualizing the graph
print("\nВизуализация графа...")
visualizer_graph: GraphVisualizer = GraphVisualizer(graph_adj_list)
visualizer_graph.draw_graph()

print("\nЗавершено. / Finished.")
# Удаляем дублирующиеся вызовы анализа и печати
# forest_analysis = analyzer_tree.analyze_forest() # Already done in init or stats
# connections_tree = analyzer_tree.find_connections_between_roots() # Already done in stats or directly
# print(stats_tree) # Already printed relevant parts
# print(f"  Глубина дерева: {stats_tree['trees_info'][0]['depth']}")
# print(f"  Фактическое количество узлов: {stats_tree['trees_info'][0]['nodes_count']}")

# analyzer_graph = UndirectedGraphAnalyzer(graph) # graph_adj_list is the correct graph
# stats_graph = analyzer_graph.graph_statistics()
# print(stats_graph)

# node_A = 'ebe34ba8-6a85-416d-884e-f81ac31e3d72'
# node_B = 'c287dc60-661f-4e21-87c7-2b6366b25f8f'

# print(f"  Количество путей от {node_A} до {node_B}:")
# analyzer_tree.print_paths_between_nodes(node_A, node_B)
# analyzer_tree.print_paths_between_nodes(node_B, node_A)

# print(f"  Количество путей от {node_A} до {node_B}:")
# analyzer_graph.print_all_paths(node_A, node_B)
# analyzer_graph.print_all_paths(node_B, node_A)

# visualizer = VisualizeForest(analyzer_tree)
# visualizer.visualize_forest_connections()

# visualizer = GraphVisualizer(graph)
# visualizer.draw_graph()