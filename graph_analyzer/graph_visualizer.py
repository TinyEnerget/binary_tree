"""
Этот модуль предоставляет класс `GraphVisualizer` для различных способов
визуализации графовых структур, представленных в виде списка смежности.
Поддерживается текстовая визуализация (список ребер, древовидное представление)
и графическая визуализация с использованием библиотек `networkx` и `matplotlib`
(если они установлены).

This module provides the `GraphVisualizer` class for various ways of
visualizing graph structures represented as adjacency lists.
It supports text-based visualization (edge list, tree-like view)
and graphical visualization using `networkx` and `matplotlib` libraries
(if installed).
"""
from typing import Dict, Set, Tuple, Deque # Добавлены Tuple и Deque для типизации
from collections import deque

# Попытка импорта опциональных библиотек для графической визуализации
try:
    import matplotlib.pyplot as plt
    import networkx as nx
    HAS_NETWORKX = True
    """Флаг, указывающий на доступность библиотек networkx и matplotlib.
    Flag indicating availability of networkx and matplotlib libraries."""
except ImportError:
    HAS_NETWORKX = False


class GraphVisualizer:
    """
    Класс `GraphVisualizer` инкапсулирует логику для отображения графа,
    заданного в виде списка смежности.
    The `GraphVisualizer` class encapsulates the logic for displaying a graph
    provided as an adjacency list.

    Атрибуты / Attributes:
        graph (Dict[str, Set[str]]): Граф, представленный как словарь, где ключи - это
                                     имена узлов (строки), а значения - множества
                                     имен смежных узлов (строк).
                                     The graph represented as a dictionary where keys are
                                     node names (strings) and values are sets of
                                     adjacent node names (strings).
    """
    def __init__(self, graph: Dict[str, Set[str]]):
        """
        Инициализирует `GraphVisualizer` с предоставленным графом.
        Initializes the `GraphVisualizer` with the provided graph.

        Параметры / Parameters:
            graph (Dict[str, Set[str]]): Граф в формате списка смежности.
                                         The graph as an adjacency list.
        """
        self.graph = graph

    def print_edge_list(self) -> None:
        """
        Выводит граф в консоль в виде списка уникальных ребер.
        Prints the graph to the console as a list of unique edges.

        Для каждого ребра узлы сортируются лексикографически, чтобы обеспечить
        каноническое представление (например, ребро между 'A' и 'B' будет всегда
        напечатано как 'A --- B', а не 'B --- A'). Это также помогает
        избежать дублирования при печати ребер неориентированного графа.
        For each edge, nodes are sorted lexicographically to ensure
        a canonical representation (e.g., an edge between 'A' and 'B' will
        always be printed as 'A --- B', not 'B --- A'). This also helps
        avoid duplicates when printing edges of an undirected graph.
        """
        printed_edges: Set[Tuple[str, str]] = set()
        print("\nСписок рёбер графа / Graph Edge List:\n")
        if not self.graph:
            print("  Граф пуст. / Graph is empty.")
            return

        for node, neighbors in self.graph.items():
            for neighbor in neighbors:
                # Сортировка узлов в ребре для канонического представления
                edge = tuple(sorted((node, neighbor)))
                if edge not in printed_edges:
                    print(f"  {edge[0]} --- {edge[1]}")
                    printed_edges.add(edge)
        if not printed_edges:
            print("  В графе нет ребер. / Graph has no edges.")


    def print_tree_view(self, start_node: str, max_depth: int = 5) -> None:
        """
        Печатает граф в древовидной форме, начиная с указанного узла `start_node`.
        Prints the graph in a tree-like format starting from the specified `start_node`.

        Использует обход в ширину (BFS) для исследования графа до `max_depth`.
        Посещенные узлы отслеживаются, чтобы избежать циклов и повторного вывода.
        Uses Breadth-First Search (BFS) to explore the graph up to `max_depth`.
        Visited nodes are tracked to avoid cycles and redundant printing.

        Параметры / Parameters:
            start_node (str): Узел, с которого начинается древовидное представление.
                              The node from which the tree-like view starts.
            max_depth (int): Максимальная глубина обхода от `start_node`.
                             Maximum traversal depth from `start_node`.
        """
        if start_node not in self.graph:
            print(f"\nСтартовый узел '{start_node}' не найден в графе. / Start node '{start_node}' not found in graph.")
            return

        print(f"\nДревовидная визуализация от узла '{start_node}' (до глубины {max_depth}):\nTree-like view from node '{start_node}' (up to depth {max_depth}):\n")

        visited_nodes: Set[str] = set()
        # Очередь хранит кортежи (узел, текущая_глубина)
        queue: Deque[Tuple[str, int]] = deque([(start_node, 0)])
        
        while queue:
            current_node, depth = queue.popleft()

            # Пропускаем, если узел уже посещен или превышена максимальная глубина
            if current_node in visited_nodes or depth > max_depth:
                continue

            visited_nodes.add(current_node)

            # Формируем отступ и печатаем узел
            indent = "    " * depth
            print(f"{indent}└── {current_node}")

            # Добавляем соседей в очередь, если они еще не посещены и глубина не превышена
            if depth < max_depth:
                # Сортируем соседей для более предсказуемого вывода
                for neighbor in sorted(list(self.graph.get(current_node, set()))):
                    if neighbor not in visited_nodes: # Проверяем здесь, чтобы не добавлять лишнего в очередь
                        queue.append((neighbor, depth + 1))

    def draw_graph(self, show_labels: bool = True, node_size: int = 700) -> None:
        """
        Выполняет графическую визуализацию графа с помощью `networkx` и `matplotlib`.
        Performs graphical visualization of the graph using `networkx` and `matplotlib`.

        Если эти библиотеки не установлены, выводит сообщение об ошибке.
        If these libraries are not installed, an error message is printed.

        Параметры / Parameters:
            show_labels (bool): Если True, отображать метки (имена) узлов на графике.
                                If True, display node labels on the graph.
            node_size (int): Размер узлов на графике.
                             Size of the nodes in the graph.
        """
        if not HAS_NETWORKX:
            print("Визуализация недоступна: библиотеки networkx и/или matplotlib не установлены. / Visualization unavailable: networkx and/or matplotlib are not installed.")
            print("Пожалуйста, установите их: `pip install networkx matplotlib` / Please install them: `pip install networkx matplotlib`")
            return

        if not self.graph:
            print("Граф пуст. Графическая визуализация невозможна. / Graph is empty. Graphical visualization not possible.")
            return

        G = nx.Graph()
        for node, neighbors in self.graph.items():
            for neighbor in neighbors:
                G.add_edge(node, neighbor)

        if not G.nodes():
            print("Граф не содержит узлов после обработки. Графическая визуализация невозможна. / Graph contains no nodes after processing. Graphical visualization not possible.")
            return

        plt.figure(figsize=(12, 9)) # Немного увеличен размер для лучшей читаемости
        # Использование Fruchterman-Reingold layout для более "естественного" расположения узлов в графах общего вида
        try:
            pos = nx.spring_layout(G, seed=42, k=0.5, iterations=50) # k для настройки расстояния, iterations для качества
        except Exception: # На случай, если spring_layout не сработает для очень маленьких/особых графов
            pos = nx.kamada_kawai_layout(G) if len(G.nodes()) > 1 else nx.random_layout(G, seed=42)


        nx.draw(
            G, pos, with_labels=show_labels, node_size=node_size,
            node_color="skyblue", edge_color="gray", font_size=9, font_weight="bold",
            width=1.5 # толщина ребер
        )
        plt.title("Графическая визуализация графа / Graph Visualization", fontsize=15)
        plt.axis("off") # Отключаем оси координат
        plt.tight_layout() # Автоматически подгоняет параметры для плотного размещения
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