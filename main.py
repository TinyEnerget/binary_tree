import sys
import os

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tree_analyzer import MultiRootAnalyzer, VisualizeForest, TreeCreator

from graph_analyzer import GraphCreator, GraphVisualizer, UndirectedGraphAnalyzer

model_path = 'C:\\Users\\Vlad Titov\\Desktop\\Work\\binary_tree\\model_processing\\available_modification\\converted.json'
out_path = "output.json"

tree_creator = TreeCreator(model_path, out_path)
tree = tree_creator.create_tree()
graph_creator = GraphCreator(model_path, out_path)
graph_creator.model_to_tree()
graph = graph_creator.create_graph()

analyzer_tree = MultiRootAnalyzer(tree)
stats_tree = analyzer_tree.get_forest_statistics()
forest_analysis = analyzer_tree.analyze_forest()
connections_tree = analyzer_tree.find_connections_between_roots()
print(stats_tree)
print(f"  Глубина дерева: {stats_tree['trees_info'][0]['depth']}")
print(f"  Фактическое количество узлов: {stats_tree['trees_info'][0]['nodes_count']}")

analyzer_graph = UndirectedGraphAnalyzer(graph)
stats_graph = analyzer_graph.graph_statistics()
print(stats_graph)

node_A = 'ebe34ba8-6a85-416d-884e-f81ac31e3d72'
node_B = 'c287dc60-661f-4e21-87c7-2b6366b25f8f'

print(f"  Количество путей от {node_A} до {node_B}:")
analyzer_tree.print_paths_between_nodes(node_A, node_B)
analyzer_tree.print_paths_between_nodes(node_B, node_A)

print(f"  Количество путей от {node_A} до {node_B}:")
analyzer_graph.print_all_paths(node_A, node_B)
analyzer_graph.print_all_paths(node_B, node_A)

visualizer = VisualizeForest(analyzer_tree)
visualizer.visualize_forest_connections()

visualizer = GraphVisualizer(graph)
visualizer.draw_graph()