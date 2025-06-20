"""
Этот модуль предоставляет класс `UndirectedGraphAnalyzer` для анализа свойств
неориентированных графов, представленных в виде списка смежности.
Включает функции для поиска связных компонент, всех путей и кратчайшего пути
между узлами, а также для расчета общей статистики графа.

This module provides the `UndirectedGraphAnalyzer` class for analyzing
properties of undirected graphs represented as adjacency lists.
It includes functions for finding connected components, all paths, and the
shortest path between nodes, as well as calculating general graph statistics.
"""
# import concurrent.futures # Закомментировано, так как max_workers не используется активно
from collections import deque # defaultdict не используется напрямую в текущей реализации
from typing import Dict, Set, List, Optional, Any, Tuple # Tuple добавлен для dfs_stack


class UndirectedGraphAnalyzer:
    """
    Анализатор для неориентированных графов.
    Analyzer for undirected graphs.

    Этот класс принимает граф, представленный в виде списка смежности (словарь,
    где ключи - это узлы, а значения - множества их соседей), и предоставляет
    методы для анализа различных свойств этого графа.
    This class takes a graph represented as an adjacency list (a dictionary
    where keys are nodes and values are sets of their neighbors) and provides
    methods to analyze various properties of this graph.

    Атрибуты / Attributes:
        graph (Dict[str, Set[str]]): Представление графа в виде списка смежности.
                                     The graph represented as an adjacency list.
        max_workers (int): Максимальное количество рабочих потоков (в текущей реализации не используется,
                           но может быть зарезервировано для будущих параллельных алгоритмов).
                           Maximum number of worker threads (not used in the current implementation,
                           but may be reserved for future parallel algorithms).
        components (List[Set[str]]): Список связных компонент графа. Заполняется после вызова
                                     `find_connected_components`.
                                     List of connected components of the graph. Populated after calling
                                     `find_connected_components`.
        _paths_cache (Dict[Any, Any]): Кэш для хранения результатов поиска путей (в текущей
                                       реализации не используется, но может быть для будущих оптимизаций).
                                       Cache for storing pathfinding results (not used in the current
                                       implementation, but may be for future optimizations).
    """
    def __init__(self, graph: Dict[str, Set[str]], max_workers: Optional[int] = None):
        """
        Инициализирует анализатор графа.
        Initializes the graph analyzer.

        Параметры / Parameters:
            graph (Dict[str, Set[str]]): Неориентированный граф, представленный как словарь,
                                         где ключи - это узлы (строки), а значения - множества
                                         соседних узлов (строк).
                                         Undirected graph represented as a dictionary where keys
                                         are nodes (strings) and values are sets of neighboring
                                         nodes (strings).
            max_workers (Optional[int]): Максимальное количество рабочих потоков для потенциальных
                                         параллельных операций. По умолчанию 8. (Не используется активно
                                         в текущих методах).
                                         Maximum number of worker threads for potential parallel
                                         operations. Defaults to 8. (Not actively used in current methods).
        """
        self.graph: Dict[str, Set[str]] = graph
        self.max_workers: int = max_workers or 8
        self.components: List[Set[str]] = []
        self._paths_cache: Dict[Tuple[str, str], List[List[str]]] = {} # Ключ: (start_node, end_node), Значение: список путей

    def find_connected_components(self) -> List[Set[str]]:
        """
        Находит все связные компоненты в графе с использованием поиска в ширину (BFS).
        Finds all connected components in the graph using Breadth-First Search (BFS).

        Обходит граф, начиная поиск новой компоненты с каждого еще не посещенного узла.
        Результат (список множеств узлов, где каждое множество представляет компоненту)
        сохраняется в `self.components` и также возвращается.
        Traverses the graph, starting a new component search from each unvisited node.
        The result (a list of sets of nodes, where each set represents a component)
        is stored in `self.components` and also returned.

        Возвращает / Returns:
            List[Set[str]]: Список множеств строк, где каждое множество содержит ID узлов
                            одной связной компоненты.
                            A list of sets of strings, where each set contains the node IDs
                            of one connected component.
        """
        visited_nodes: Set[str] = set()
        found_components: List[Set[str]] = []

        for node_id in self.graph: # node_id здесь строка
            if node_id not in visited_nodes:
                current_component: Set[str] = set()
                queue: deque[str] = deque([node_id])
                visited_nodes.add(node_id)
                current_component.add(node_id)

                while queue:
                    current_node_val = queue.popleft()
                    for neighbor_val in self.graph.get(current_node_val, set()):
                        if neighbor_val not in visited_nodes:
                            visited_nodes.add(neighbor_val)
                            current_component.add(neighbor_val)
                            queue.append(neighbor_val)
                if current_component:
                    found_components.append(current_component)

        self.components = found_components
        return self.components

    def find_all_paths(self, start_node: str, end_node: str) -> List[List[str]]:
        """
        Находит все простые пути (без повторения узлов в одном пути) между `start_node` и `end_node`
        в графе с использованием поиска в глубину (DFS).
        Finds all simple paths (no repeated nodes within a single path) between `start_node` and `end_node`
        in the graph using Depth-First Search (DFS).

        Параметры / Parameters:
            start_node (str): ID начального узла для поиска пути.
                              The ID of the starting node for the path search.
            end_node (str): ID конечного узла для поиска пути.
                            The ID of the ending node for the path search.

        Возвращает / Returns:
            List[List[str]]: Список всех найденных путей. Каждый путь представлен как список ID узлов (строк).
                             Возвращает пустой список, если узлы не существуют в графе или путь не найден.
                             A list of all paths found. Each path is represented as a list of node IDs (strings).
                             Returns an empty list if nodes do not exist in the graph or no path is found.
        """
        if start_node not in self.graph or end_node not in self.graph:
            return []

        all_paths_list: List[List[str]] = []
        # Стек для DFS: (текущий_узел_str, текущий_путь_list_of_str, множество_посещенных_на_этом_пути_set_of_str)
        dfs_iter_stack: List[Tuple[str, List[str], Set[str]]] = [(start_node, [start_node], {start_node})]

        while dfs_iter_stack:
            current_node_val, current_path_list, visited_on_path_set = dfs_iter_stack.pop()

            if current_node_val == end_node:
                all_paths_list.append(list(current_path_list))
                continue

            for neighbor_val in self.graph.get(current_node_val, set()):
                if neighbor_val not in visited_on_path_set:
                    new_path = current_path_list + [neighbor_val]
                    new_visited_set = visited_on_path_set | {neighbor_val}
                    dfs_iter_stack.append((neighbor_val, new_path, new_visited_set))
        return all_paths_list

    def find_shortest_path(self, start_node: str, end_node: str) -> Optional[List[str]]:
        """
        Находит один из кратчайших путей между двумя узлами в графе с использованием
        поиска в ширину (BFS).
        Finds one of the shortest paths between two nodes in the graph using
        Breadth-First Search (BFS).

        BFS гарантирует нахождение кратчайшего пути в терминах количества ребер
        в невзвешенном графе.

        Параметры / Parameters:
            start_node (str): Начальный узел.
                              The starting node.
            end_node (str): Конечный узел.
                            The ending node.

        Возвращает / Returns:
            Optional[List[str]]: Список узлов, представляющий кратчайший путь,
                                 или None, если путь не найден или узлы отсутствуют в графе.
                                 A list of nodes representing the shortest path,
                                 or None if no path is found or nodes are not in the graph.
        """
        if start_node not in self.graph or end_node not in self.graph:
            return None # Если стартовый или конечный узел отсутствует в графе

        # Очередь для BFS: (текущий_узел, путь_до_него)
        bfs_queue: deque[Tuple[str, List[str]]] = deque([(start_node, [start_node])])
        # Множество для отслеживания всех посещенных узлов глобально в этом поиске
        visited_globally_set: Set[str] = {start_node}

        while bfs_queue:
            current_node_val, current_path_list = bfs_queue.popleft()

            if current_node_val == end_node:
                return current_path_list

            for neighbor_val in self.graph.get(current_node_val, set()):
                if neighbor_val not in visited_globally_set:
                    visited_globally_set.add(neighbor_val)
                    new_path = current_path_list + [neighbor_val]
                    bfs_queue.append((neighbor_val, new_path))
        return None

    def graph_statistics(self) -> Dict[str, Any]: # Возвращаемая структура детализирована в docstring
        """
        Рассчитывает и возвращает основную статистику по графу.
        Calculates and returns basic statistics for the graph.

        Статистика включает:
        - Общее количество узлов (`total_nodes`).
        - Общее количество ребер (`total_edges`).
        - Распределение степеней узлов (`degree_distribution`): словарь {узел: степень}.
        - Список связных компонент (`connected_components`): результат вызова `find_connected_components`.
        - Количество связных компонент (`num_components`).
        The statistics include:
        - Total number of nodes (`total_nodes`).
        - Total number of edges (`total_edges`).
        - Node degree distribution (`degree_distribution`): a dictionary {node: degree}.
        - List of connected components (`connected_components`): result of `find_connected_components`.
        - Number of connected components (`num_components`).

        Возвращает / Returns:
            Dict[str, Any]: Словарь со статистическими данными графа.
                            A dictionary with graph statistics.
        """
        num_nodes = len(self.graph)
        # Каждое ребро считается дважды при суммировании степеней, поэтому делим на 2
        num_edges = sum(len(neighbors) for neighbors in self.graph.values()) // 2

        degrees: Dict[str, int] = {node: len(neighbors) for node, neighbors in self.graph.items()}

        # Находим компоненты, если они еще не были найдены
        if not self.components: # или если граф мог измениться и нужно пересчитать
            self.find_connected_components()

        # Преобразуем множества компонент в списки для JSON-совместимости или простоты отображения
        components_as_lists = [list(comp) for comp in self.components]

        return {
            "total_nodes": num_nodes,
            "total_edges": num_edges,
            "degree_distribution": degrees,
            "connected_components": components_as_lists,
            "num_components": len(self.components)
        }

    def print_graph_statistics(self) -> None:
        """
        Выводит в консоль статистику графа в удобочитаемом формате.
        Prints graph statistics to the console in a readable format.

        Использует метод `graph_statistics` для получения данных.
        Uses the `graph_statistics` method to get the data.
        """
        stats = self.graph_statistics()
        print("\nСтатистика графа / Graph Statistics:")
        print(f"  Всего узлов / Total Nodes: {stats['total_nodes']}")
        print(f"  Всего ребер / Total Edges: {stats['total_edges']}")
        print(f"  Количество связных компонент / Number of Connected Components: {stats['num_components']}")
        print("  Связные компоненты / Connected Components:")
        for idx, comp in enumerate(stats['connected_components'], 1):
            # Выводим только несколько первых узлов, если компонента большая
            comp_preview = comp[:10] # Первые 10 узлов
            comp_str = ", ".join(comp_preview)
            if len(comp) > 10:
                comp_str += f", ... ({len(comp) - 10} more)"
            print(f"    Компонента {idx} / Component {idx} (всего {len(comp)} узлов / nodes): [{comp_str}]")

        print("  Распределение степеней (первые 10 узлов, если их много) / Degree Distribution (first 10 nodes if many):")
        degrees_preview = list(stats['degree_distribution'].items())[:10]
        for node, degree in degrees_preview:
            print(f"    Узел / Node '{node}': {degree}")
        if len(stats['degree_distribution']) > 10:
            print(f"    ... и еще {len(stats['degree_distribution']) - 10} узлов / ... and {len(stats['degree_distribution']) - 10} more nodes.")


    def print_all_paths(self, start_node: str, end_node: str) -> None:
        """
        Выводит в консоль все найденные пути между `start_node` и `end_node`.
        Prints all found paths between `start_node` and `end_node` to the console.

        Использует `find_all_paths` для получения путей.
        Uses `find_all_paths` to get the paths.

        Параметры / Parameters:
            start_node (str): Начальный узел. / The starting node.
            end_node (str): Конечный узел. / The ending node.
        """
        paths = self.find_all_paths(start_node, end_node)
        print(f"\nВсе пути от '{start_node}' до '{end_node}' / All paths from '{start_node}' to '{end_node}':")
        if not paths:
            print("  Пути не найдены. / No paths found.")
            return
        for i, path in enumerate(paths, 1):
            print(f"  Путь {i} / Path {i}: {' -> '.join(path)}")

    def print_shortest_path(self, start_node: str, end_node: str) -> None:
        """
        Выводит в консоль кратчайший путь между `start_node` и `end_node`.
        Prints the shortest path between `start_node` and `end_node` to the console.

        Использует `find_shortest_path` для получения пути.
        Uses `find_shortest_path` to get the path.

        Параметры / Parameters:
            start_node (str): Начальный узел. / The starting node.
            end_node (str): Конечный узел. / The ending node.
        """
        path = self.find_shortest_path(start_node, end_node)
        print(f"\nКратчайший путь от '{start_node}' до '{end_node}' / Shortest path from '{start_node}' to '{end_node}':")
        if path:
            # Длина пути - это количество ребер, т.е. количество узлов минус 1
            print(f"  {' -> '.join(path)} (Длина / Length: {len(path) -1} ребер / edges)")
        else:
            print("  Путь не найден. / No path found.")


if __name__ == "__main__":
    graph = {
        "A": {"B", "C"},
        "B": {"A", "D", "E"},
        "C": {"A", "F"},
        "D": {"B"},
        "E": {"B", "F"},
        "F": {"C", "E"}
    }



    analyzer = UndirectedGraphAnalyzer(graph)
    analyzer.print_graph_statistics()
    analyzer.print_all_paths("A", "F")
    analyzer.print_shortest_path("A", "F")