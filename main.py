import sys
import os
# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tree_analyzer import MultiRootAnalyzer, VisualizeForest
from tree import TreeCreator

model_path = 'C:\\Users\\Vlad Titov\\Desktop\\Work\\binary_tree\\model_processing\\available_modification\\converted.json'
out_path = "output.json"

tree_creator = TreeCreator(model_path, out_path)
tree = tree_creator.create_tree()

analyzer = MultiRootAnalyzer(tree)
stats = analyzer.get_forest_statistics()
forest_analysis = analyzer.analyze_forest()
connections = analyzer.find_connections_between_roots()
print(stats)
print(f"  Глубина дерева: {stats['trees_info'][0]['depth']}")
print(f"  Фактическое количество узлов: {stats['trees_info'][0]['nodes_count']}")

node_A = 'ebe34ba8-6a85-416d-884e-f81ac31e3d72'
node_B = 'c287dc60-661f-4e21-87c7-2b6366b25f8f'

print(f"  Количество путей от {node_A} до {node_B}:")
analyzer.print_paths_between_nodes(node_A, node_B)
analyzer.print_paths_between_nodes(node_B, node_A)

visualizer = VisualizeForest(analyzer)
visualizer.visualize_forest_connections()