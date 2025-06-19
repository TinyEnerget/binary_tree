import sys
import os

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_analyzer import GraphCreator, GraphVisualizer, UndirectedGraphAnalyzer, UndirectedGraphConnectingAnalyzer

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

model_path = 'example_data\\three_system_model_with_connection_of_systems_converted.json'
out_path = "res\\three_system_model_with_connection_of_systems_converted.json"
logger.info(f"Creating graph from {model_path}")

graph_creator = GraphCreator(model_path, out_path)
graph, roots = graph_creator.create_graph()
logger.info(f"Graph created with {len(graph)} nodes and {len(roots)} roots")
print(roots)
analyzer_graph = UndirectedGraphAnalyzer(graph)
logger.info(f"Graph analyzed with {len(graph)} nodes and {len(roots)} roots")
node_A = 'a9f8bc28-8b2f-4f4d-bb11-a76205ba5c07'
node_B = '7911384c-1671-4ea0-a002-cdaa840e5c65'
logger.info(f"Analyzing graph from {node_A} to {node_B}")

logger.info(f"Printing all paths from {node_A} to {node_B}")
analyzer_graph.print_all_paths(node_A, node_B)

#logger.info(f"Printing longest path from {node_A} to {node_B}")
#analyzer_graph.print_longest_path(node_A, node_B)
#
#logger.info(f"Printing shortest path from {node_A} to {node_B}")
#analyzer_graph.print_shortest_path(node_A, node_B)

logger.info(f"Printing all elements into model of systems {roots}")
connecting_analyzer = UndirectedGraphConnectingAnalyzer(graph, roots)

connecting_analyzer.analyze()






#visualizer = GraphVisualizer(graph)
#visualizer.draw_graph()