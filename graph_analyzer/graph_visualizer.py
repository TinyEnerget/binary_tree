from typing import Dict, Set
from collections import deque
try:
    import matplotlib.pyplot as plt
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


class GraphVisualizer:
    def __init__(self, graph: Dict[str, Set[str]]):
        self.graph = graph

    def print_edge_list(self):
        """Выводит ненаправленный граф в виде списка рёбер"""
        printed = set()
        print("Список рёбер ненаправленного графа:\n")
        for node, neighbors in self.graph.items():
            for neighbor in neighbors:
                edge = tuple(sorted((node, neighbor)))
                if edge not in printed:
                    print(f"{edge[0]} --- {edge[1]}")
                    printed.add(edge)

    def print_tree_view(self, start_node: str, max_depth: int = 5):
        """Печатает граф от указанного узла в древовидной форме"""
        visited = set()
        queue = deque([(start_node, 0)])
        print(f"\nДревовидная визуализация от узла {start_node}:\n")
        
        while queue:
            node, depth = queue.popleft()
            if node in visited or depth > max_depth:
                continue
            visited.add(node)
            indent = "    " * depth
            print(f"{indent}└── {node}")
            for neighbor in sorted(self.graph.get(node, [])):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))

    def draw_graph(self, show_labels: bool = True, node_size: int = 700):
        """Графическая визуализация с помощью networkx и matplotlib"""
        if not HAS_NETWORKX:
            print("Визуализация недоступна: не установлены networkx или matplotlib.")
            return

        G = nx.Graph()
        for node, neighbors in self.graph.items():
            for neighbor in neighbors:
                G.add_edge(node, neighbor)

        pos = nx.spring_layout(G, seed=42)
        plt.figure(figsize=(10, 7))
        nx.draw(
            G, pos, with_labels=show_labels, node_size=node_size,
            node_color="skyblue", edge_color="gray", font_size=8, font_weight="bold"
        )
        plt.title("Графическая визуализация графа")
        plt.axis("off")
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    example_graph = {
        "A": {"B", "C"},
        "B": {"A", "D"},
        "C": {"A", "D"},
        "D": {"B", "C", "E"},
        "E": {"D"}
    }

    visualizer = GraphVisualizer(example_graph)
    visualizer.print_edge_list()
    visualizer.print_tree_view("A")
    visualizer.draw_graph()