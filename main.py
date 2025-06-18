import sys
import os

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_analyzer import GraphCreator, GraphVisualizer, UndirectedGraphAnalyzer

model_path = 'model_processing\\available_modification\\converted.json'
out_path = "res\\output.json"

graph_creator = GraphCreator(model_path, out_path)
graph = graph_creator.create_graph()

analyzer_graph = UndirectedGraphAnalyzer(graph)
node_A = 'ebe34ba8-6a85-416d-884e-f81ac31e3d72'
node_B = 'c287dc60-661f-4e21-87c7-2b6366b25f8f'

print(f"  Количество путей от {node_A} до {node_B}:")
analyzer_graph.print_all_paths(node_A, node_B)

visualizer = GraphVisualizer(graph)
visualizer.draw_graph()