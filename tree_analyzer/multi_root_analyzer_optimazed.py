"""
Этот модуль предоставляет оптимизированную версию анализатора леса деревьев,
`MultiRootAnalyzerOpt`. Оптимизации включают использование параллельных вычислений
с помощью `concurrent.futures.ThreadPoolExecutor` для ускорения анализа
и применение механизмов кэширования (`functools.lru_cache` и пользовательские кэши на словарях)
для запоминания результатов вычислений для узлов и глубин деревьев,
чтобы избежать повторной работы при многократных запросах к одним и тем же структурам.

Основные возможности:
- Параллельный сбор информации об узлах в деревьях.
- Параллельный поиск связей между деревьями.
- Параллельный расчет статистики по лесу.
- Кэширование результатов для ускорения повторных операций.
- Оптимизированные алгоритмы обхода дерева (например, BFS с deque для сбора узлов).
"""
import concurrent.futures
import multiprocessing as mp
from functools import lru_cache
from typing import Set, List as TypingList, Dict as TypingDict, Tuple, Optional, Any, Union
import threading
from collections import defaultdict, deque
import time
from .tree_construction import Node

import logging
logger = logging.getLogger(__name__)

class MultiRootAnalyzerOpt:
    """
    Оптимизированный анализатор леса деревьев с поддержкой многопоточности и кэширования.
    Optimized multi-root tree forest analyzer with multithreading and caching support.

    Атрибуты / Attributes:
        roots (TypingList[Node]): Коллекция корневых узлов (объектов `Node`) для анализа.
        max_workers (int): Максимальное количество потоков, используемых `ThreadPoolExecutor`.
        shared_nodes (TypingDict[str, TypingList[str]]): Отслеживает значения узлов (строки), которые появляются
                                                          в нескольких деревьях, и список идентификаторов этих деревьев.
        connections (TypingList[TypingDict[str, Any]]): Список словарей, описывающих связи между парами корневых узлов.
        _node_cache (TypingDict[Tuple[int, int], Set[str]]): Кэш для `_get_all_nodes_in_tree_cached`.
                                                              Ключ - `(id(root), tree_idx)`, значение - множество ID узлов (строк).
        _depth_cache (TypingDict[int, int]): Кэш для `_get_tree_depth`. Ключ - `id(root)`, значение - глубина (int).
    """

    def __init__(self, roots: TypingList[Node], max_workers: Optional[int] = None):
        """
        Инициализирует оптимизированный анализатор леса.

        Параметры / Parameters:
            roots (TypingList[Node]): Список корневых узлов (экземпляров `Node`).
            max_workers (Optional[int]): Максимальное количество потоков для `ThreadPoolExecutor`.
                                         Если None, вычисляется на основе количества CPU.
        """
        self.roots: TypingList[Node] = roots
        self.max_workers: int = max_workers or min(32, (mp.cpu_count() if mp.cpu_count() else 1) + 4)
        self.shared_nodes: TypingDict[str, TypingList[str]] = {}
        self.connections: TypingList[TypingDict[str, Any]] = []
        self._node_cache: TypingDict[Tuple[int, int], Set[str]] = {}
        self._depth_cache: TypingDict[int, int] = {}

        if self.roots:
            self.analyze_forest()

    def analyze_forest(self) -> TypingDict[str, TypingList[str]]:
        """
        Выполняет параллельный анализ леса для идентификации всех узлов и общих узлов между деревьями.
        Returns a dictionary mapping node values (strings) to a list of tree string identifiers.
        """
        all_nodes_in_trees_map: TypingDict[str, TypingList[str]] = defaultdict(list)
        self.shared_nodes = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_root_info: TypingDict[concurrent.futures.Future, Tuple[Node, int]] = {
                executor.submit(self._get_all_nodes_in_tree_cached, root_node, idx): (root_node, idx)
                for idx, root_node in enumerate(self.roots)
                if isinstance(root_node, Node) and hasattr(root_node, 'value')
            }

            for future in concurrent.futures.as_completed(future_to_root_info):
                root_node_obj, tree_index = future_to_root_info[future]
                try:
                    nodes_set = future.result()
                    tree_id_str = f"Tree_{tree_index}_{str(root_node_obj.value)}"
                    for node_value_str in nodes_set:
                        all_nodes_in_trees_map[node_value_str].append(tree_id_str)
                except Exception as exc:
                    logger.error(f"Ошибка анализа дерева (индекс {tree_index}, корень {getattr(root_node_obj, 'value', 'N/A')}) в analyze_forest: {exc}", exc_info=True)
        
        for node_val_str, tree_list in all_nodes_in_trees_map.items():
            if len(tree_list) > 1:
                self.shared_nodes[node_val_str] = tree_list

        return all_nodes_in_trees_map

    @lru_cache(maxsize=1000)
    def _get_all_nodes_in_tree_cached(self, root: Node, tree_idx: int) -> Set[str]:
        """
        Кэшированное получение всех уникальных значений узлов в одном дереве.
        Returns a set of all unique node values (IDs) in the tree (strings).
        """
        cache_key = (id(root), tree_idx)
        if cache_key in self._node_cache:
            return self._node_cache[cache_key].copy()

        nodes_set = self._get_all_nodes_in_tree(root)
        self._node_cache[cache_key] = nodes_set
        return nodes_set.copy()

    def _get_all_nodes_in_tree(self, root: Node) -> Set[str]:
        """
        Оптимизированный метод для сбора всех уникальных значений узлов в одном дереве (BFS).
        Returns a set of unique node values (IDs) as strings.
        """
        if not isinstance(root, Node) or not hasattr(root, 'value'):
            return set()

        nodes_set: Set[str] = set()
        visited_values: Set[str] = set()
        queue: deque[Node] = deque()

        root_value_str = str(root.value)
        nodes_set.add(root_value_str)
        visited_values.add(root_value_str)
        queue.append(root)

        while queue:
            current_node_obj = queue.popleft()
            if hasattr(current_node_obj, 'children') and current_node_obj.children:
                for child_obj in current_node_obj.children:
                    if isinstance(child_obj, Node) and hasattr(child_obj, 'value'):
                        child_val_str = str(child_obj.value)
                        if child_val_str not in visited_values:
                            visited_values.add(child_val_str)
                            nodes_set.add(child_val_str)
                            queue.append(child_obj)
        return nodes_set

    def find_connections_between_roots(self) -> TypingList[TypingDict[str, Any]]:
        """
        Выполняет параллельный поиск связей (общих узлов) между всеми уникальными парами деревьев в лесу.
        Returns a list of dictionaries, each describing a connection.
        """
        tree_nodes_map: TypingDict[int, Set[str]] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx: TypingDict[concurrent.futures.Future, int] = {
                executor.submit(self._get_all_nodes_in_tree_cached, root_node, i): i
                for i, root_node in enumerate(self.roots) if isinstance(root_node, Node) and hasattr(root_node, 'value')
            }
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    tree_nodes_map[idx] = future.result()
                except Exception as exc:
                    logger.error(f"Ошибка при получении узлов для дерева {idx} в find_connections_between_roots: {exc}", exc_info=True)

        root_indices = list(tree_nodes_map.keys())
        pairs_to_check: TypingList[Tuple[int, int]] = [(idx_val, root_indices[j]) for i, idx_val in enumerate(root_indices) for j in range(i + 1, len(root_indices))]

        found_connections_list: TypingList[TypingDict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures_list: TypingList[concurrent.futures.Future] = [
                executor.submit(self._find_connection_for_pair, pair_idx1, pair_idx2, tree_nodes_map)
                for pair_idx1, pair_idx2 in pairs_to_check
            ]
            for future in concurrent.futures.as_completed(futures_list):
                try:
                    connection_dict = future.result()
                    if connection_dict:
                        found_connections_list.append(connection_dict)
                except Exception as exc:
                     logger.error(f"Ошибка при поиске связей для пары в find_connections_between_roots: {exc}", exc_info=True)
        
        self.connections = found_connections_list
        return self.connections

    def _find_connection_for_pair(self, tree_idx_1: int, tree_idx_2: int,
                                  all_tree_nodes: TypingDict[int, Set[str]]) -> Optional[TypingDict[str, Any]]:
        """
        Вспомогательный метод для нахождения общих узлов между одной конкретной парой деревьев.
        Returns a dictionary describing the connection or None.
        """
        nodes1_set = all_tree_nodes.get(tree_idx_1)
        nodes2_set = all_tree_nodes.get(tree_idx_2)

        if nodes1_set is None or nodes2_set is None:
            logger.debug(f"Данные узлов для пары индексов ({tree_idx_1}, {tree_idx_2}) не найдены в all_tree_nodes.")
            return None

        common_nodes_set = nodes1_set.intersection(nodes2_set)

        if common_nodes_set:
            root1_obj = self.roots[tree_idx_1]
            root2_obj = self.roots[tree_idx_2]

            root1_val_str = str(root1_obj.value) if isinstance(root1_obj, Node) and hasattr(root1_obj, 'value') else f"Tree_{tree_idx_1}"
            root2_val_str = str(root2_obj.value) if isinstance(root2_obj, Node) and hasattr(root2_obj, 'value') else f"Tree_{tree_idx_2}"

            return {
                'root1': root1_val_str,
                'root2': root2_val_str,
                'common_nodes': sorted(list(common_nodes_set)),
                'connection_type': 'shared_nodes'
            }
        return None

    def get_forest_statistics(self) -> TypingDict[str, Any]:
        """
        Собирает и возвращает статистику по всему лесу, используя параллельные вычисления.
        Returns a dictionary containing forest statistics.
        """
        if not self.shared_nodes and self.roots:
             self.analyze_forest()

        TreeInfoDetailType = TypingDict[str, Union[str, int, TypingList[str]]]
        trees_info_list_result: TypingList[TreeInfoDetailType] = [{} for _ in self.roots]

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx_map: TypingDict[concurrent.futures.Future, int] = {
                executor.submit(self._get_tree_stats, root_node, i): i
                for i, root_node in enumerate(self.roots) if isinstance(root_node, Node) and hasattr(root_node, 'value')
            }

            for future in concurrent.futures.as_completed(future_to_idx_map):
                idx = future_to_idx_map[future]
                try:
                    trees_info_list_result[idx] = future.result()
                except Exception as exc:
                    logger.error(f"Ошибка при получении статистики для дерева {idx}: {exc}", exc_info=True)
                    root_val_str = str(self.roots[idx].value) if isinstance(self.roots[idx], Node) and hasattr(self.roots[idx], 'value') else f"UnknownTree_{idx}"
                    trees_info_list_result[idx] = {'root': root_val_str, 'error': str(exc), 'nodes_count':0, 'depth':0, 'nodes':[]}
        
        final_trees_info = [info for info in trees_info_list_result if info]

        return {
            'total_roots': len(self.roots),
            'trees_info': final_trees_info,
            'shared_nodes': self.shared_nodes.copy()
        }

    def _get_tree_stats(self, root: Node, idx: int) -> TypingDict[str, Any]:
        """
        Вспомогательный метод для расчета статистики одного дерева.
        Returns a dictionary with statistics for the given tree.
        """
        tree_nodes_set = self._get_all_nodes_in_tree_cached(root, idx)
        tree_depth_val = self._get_tree_depth(root)

        root_value_str = str(root.value)
        return {
            'root': root_value_str,
            'nodes_count': len(tree_nodes_set),
            'depth': tree_depth_val,
            'nodes': sorted(list(tree_nodes_set))
        }

    @lru_cache(maxsize=500)
    def _get_tree_depth(self, root: Node) -> int:
        """
        Оптимизированное вычисление глубины дерева с использованием итеративного подхода (DFS на стеке) и кэширования.
        Returns the depth of the tree. 0 if the node is invalid.
        """
        if not isinstance(root, Node) or not hasattr(root, 'value'):
            return 0

        cache_key = id(root)
        if cache_key in self._depth_cache:
            return self._depth_cache[cache_key]

        current_max_depth = 0
        root_value_str = str(root.value)
        dfs_iter_stack: TypingList[Tuple[Node, int, Set[str]]] = [(root, 1, {root_value_str})]

        while dfs_iter_stack:
            node_obj, depth, visited_path_values = dfs_iter_stack.pop()
            current_max_depth = max(current_max_depth, depth)
            if hasattr(node_obj, 'children') and node_obj.children:
                for child_node_obj in reversed(node_obj.children):
                    if isinstance(child_node_obj, Node) and hasattr(child_node_obj, 'value'):
                        child_val_str = str(child_node_obj.value)
                        if child_val_str not in visited_path_values:
                            new_visited_path = visited_path_values.copy()
                            new_visited_path.add(child_val_str)
                            dfs_iter_stack.append((child_node_obj, depth + 1, new_visited_path))

        self._depth_cache[cache_key] = current_max_depth
        return current_max_depth

    def find_all_paths_to_node(self, target_value: str) -> TypingDict[str, TypingList[TypingList[str]]]:
        """
        Параллельный поиск всех путей до указанного целевого узла (по его ID) во всех деревьях леса.
        Returns a dictionary {tree_identifier: list_of_paths}. Each path is a list of node IDs (strings).
        """
        all_paths_result: TypingDict[str, TypingList[TypingList[str]]] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_root_info: TypingDict[concurrent.futures.Future, Tuple[Node, int]] = {
                executor.submit(self._find_paths_in_tree, root_node, target_value, idx): (root_node, idx)
                for idx, root_node in enumerate(self.roots) if isinstance(root_node, Node) and hasattr(root_node, 'value')
            }
            for future in concurrent.futures.as_completed(future_to_root_info):
                root_node_obj, tree_index = future_to_root_info[future]
                try:
                    paths_list = future.result()
                    if paths_list:
                        tree_id_str = f"Tree_{tree_index}_{str(root_node_obj.value)}"
                        all_paths_result[tree_id_str] = paths_list
                except Exception as exc:
                    logger.error(f"Ошибка при поиске путей в дереве (индекс {tree_index}, корень {getattr(root_node_obj, 'value', 'N/A')}): {exc}", exc_info=True)
        return all_paths_result

    def _find_paths_in_tree(self, root: Node, target_value: str, tree_idx: int = 0) -> TypingList[TypingList[str]]:
        """
        Оптимизированный поиск всех путей от корневого узла до `target_value` в одном дереве.
        Returns a list of all found paths. Each path is a list of node IDs (strings).
        """
        if not isinstance(root, Node) or not hasattr(root, 'value'):
            return []

        paths_list_result: TypingList[TypingList[str]] = []
        dfs_iter_stack: TypingList[Tuple[Node, TypingList[str], Set[str]]] = []
        root_value_str = str(root.value)
        dfs_iter_stack.append((root, [root_value_str], {root_value_str}))

        while dfs_iter_stack:
            current_node_obj, path_str_list, visited_values_set = dfs_iter_stack.pop()
            if current_node_obj.value == target_value:
                paths_list_result.append(list(path_str_list))
            if hasattr(current_node_obj, 'children') and current_node_obj.children:
                for child_obj in reversed(current_node_obj.children):
                    if isinstance(child_obj, Node) and hasattr(child_obj, 'value'):
                        child_val_str = str(child_obj.value)
                        if child_val_str not in visited_values_set:
                            new_path = path_str_list + [child_val_str]
                            new_visited = visited_values_set.copy()
                            new_visited.add(child_val_str)
                            dfs_iter_stack.append((child_obj, new_path, new_visited))
        return paths_list_result

    def find_shortest_path_to_node(self, target_value: str) -> Optional[TypingDict[str, Any]]:
        """
        Находит кратчайший путь до узла `target_value` среди всех деревьев в лесу.
        Returns a dictionary with shortest path info or None.
        """
        all_paths_map = self.find_all_paths_to_node(target_value)
        if not all_paths_map:
            return None

        shortest_path_result: Optional[TypingDict[str, Any]] = None
        current_min_length = float('inf')

        for tree_identifier, paths_list_str in all_paths_map.items():
            for path_str_list in paths_list_str:
                if len(path_str_list) < current_min_length:
                    current_min_length = len(path_str_list)
                    shortest_path_result = {
                        'tree': tree_identifier,
                        'path': path_str_list,
                        'length': current_min_length
                    }
        return shortest_path_result

    def find_all_paths_between_nodes(self, start_value: str, end_value: str) -> TypingDict[str, TypingList[TypingList[str]]]:
        """
        Параллельный поиск всех путей между двумя заданными узлами (`start_value` и `end_value`) во всех деревьях леса.
        Returns a dictionary {tree_identifier: list_of_paths}. Each path is a list of node IDs (strings).
        """
        all_paths_result_map: TypingDict[str, TypingList[TypingList[str]]] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_root_info: TypingDict[concurrent.futures.Future, Tuple[Node, int]] = {
                executor.submit(self._find_paths_between_nodes_in_tree, root_node, start_value, end_value, idx): (root_node, idx)
                for idx, root_node in enumerate(self.roots) if isinstance(root_node, Node) and hasattr(root_node, 'value')
            }
            for future in concurrent.futures.as_completed(future_to_root_info):
                root_node_obj, tree_index = future_to_root_info[future]
                try:
                    paths_list_str = future.result()
                    if paths_list_str:
                        tree_id_str = f"Tree_{tree_index}_{str(root_node_obj.value)}"
                        all_paths_result_map[tree_id_str] = paths_list_str
                except Exception as exc:
                    logger.error(f"Ошибка при поиске путей между узлами в дереве (индекс {tree_index}, корень {getattr(root_node_obj, 'value', 'N/A')}): {exc}", exc_info=True)
        return all_paths_result_map

    def _find_paths_between_nodes_in_tree(self, root: Node, start_value: str, end_value: str,
                                          tree_idx: int = 0) -> TypingList[TypingList[str]]:
        """
        Оптимизированный поиск всех путей между `start_value` и `end_value` в одном дереве.
        Returns a list of all found paths (each path is a list of node IDs).
        """
        if not isinstance(root, Node) or not hasattr(root, 'value'):
            return []

        paths_list_result: TypingList[TypingList[str]] = []
        dfs_iter_stack: TypingList[Tuple[Node, TypingList[str], Set[str], bool]] = []
        root_value_str = str(root.value)
        dfs_iter_stack.append((root, [root_value_str], {root_value_str}, root_value_str == start_value))

        while dfs_iter_stack:
            current_node_obj, path_str_list, visited_values_set, has_found_start = dfs_iter_stack.pop()
            current_node_val_str = str(current_node_obj.value)

            if current_node_val_str == start_value:
                has_found_start = True
                path_str_list = [current_node_val_str]
                visited_values_set = {current_node_val_str}

            if has_found_start and current_node_val_str == end_value:
                paths_list_result.append(list(path_str_list))

            if hasattr(current_node_obj, 'children') and current_node_obj.children:
                for child_obj in reversed(current_node_obj.children):
                    if isinstance(child_obj, Node) and hasattr(child_obj, 'value'):
                        child_val_str = str(child_obj.value)
                        if child_val_str not in visited_values_set:
                            if has_found_start:
                                new_path = path_str_list + [child_val_str]
                                new_visited = visited_values_set.copy()
                                new_visited.add(child_val_str)
                                dfs_iter_stack.append((child_obj, new_path, new_visited, True))
                            elif child_val_str == start_value:
                                dfs_iter_stack.append((child_obj, [child_val_str], {child_val_str}, True))
        return paths_list_result

    def print_forest_statistics(self) -> None:
        """
        Выводит в консоль статистику по лесу деревьев.
        Prints forest statistics to the console.
        """
        stats = self.get_forest_statistics()
        print("Статистика по лесу (оптимизированная) / Forest Statistics (Optimized):")
        print(f"  Всего корневых узлов / Total Roots: {stats['total_roots']}")
        if 'trees_info' in stats:
            for tree_info in stats['trees_info']:
                if tree_info and 'root' in tree_info :
                    print(f"    Дерево (корень) / Tree (root) '{tree_info['root']}': "
                          f"{tree_info.get('nodes_count', 'N/A')} узлов / nodes, "
                          f"глубина / depth {tree_info.get('depth', 'N/A')}")
                elif tree_info and 'error' in tree_info:
                     print(f"    Дерево (корень) / Tree (root) '{tree_info.get('root', 'Unknown')}': Ошибка / Error - {tree_info['error']}")

    def print_shared_nodes(self) -> None:
        """
        Выводит в консоль информацию об общих узлах в лесу.
        Prints information about shared nodes in the forest to the console.
        """
        print("\nОбщие узлы (оптимизированный анализ) / Shared Nodes (Optimized Analysis):")
        if not self.shared_nodes:
            print("  Нет общих узлов в лесу. / No shared nodes found.")
            return
        for node_value, tree_ids in self.shared_nodes.items():
            print(f"  Узел / Node '{node_value}': встречается в деревьях / found in trees {tree_ids}")

    def print_connections_between_roots(self) -> None:
        """
        Выводит в консоль информацию о связях между корневыми узлами.
        Prints information about connections between root nodes to the console.
        """
        current_connections = self.find_connections_between_roots()

        print("\nСвязи между корневыми узлами (оптимизированный анализ) / Connections Between Roots (Optimized Analysis):")
        if not current_connections:
            print("  Нет связей между корневыми узлами. / No connections found between roots.")
            return
        for conn in current_connections:
            root1_str = str(conn.get('root1', 'N/A'))
            root2_str = str(conn.get('root2', 'N/A'))
            common_nodes_list = conn.get('common_nodes', [])
            print(f"  Между '{root1_str}' и '{root2_str}': через общие узлы / via common nodes {common_nodes_list}")

    def print_all_paths_to_node(self, target_value: str) -> None:
        """
        Выводит все пути до указанного узла.
        Prints all paths to the specified node.
        """
        paths_map = self.find_all_paths_to_node(target_value)
        print(f"\nВсе пути к узлу '{target_value}' (оптимизированный анализ) / All paths to node '{target_value}' (Optimized Analysis):")
        if not paths_map:
            print(f"  Узел '{target_value}' не найден. / Node '{target_value}' not found.")
            return
        
        for tree_identifier, paths_list_str in paths_map.items():
            print(f"  В дереве / In tree '{tree_identifier}':")
            if not paths_list_str:
                print(f"    Нет путей к '{target_value}' в этом дереве. / No paths to '{target_value}' in this tree.")
                continue
            for i, path_str_list in enumerate(paths_list_str, 1):
                print(f"    Путь {i} / Path {i}: {' -> '.join(path_str_list)}")

    def print_shortest_path_to_node(self, target_value: str) -> None:
        """
        Выводит кратчайший путь до указанного узла.
        Prints the shortest path to the specified node.
        """
        shortest_path_info = self.find_shortest_path_to_node(target_value)
        print(f"\nКратчайший путь к узлу '{target_value}' (оптимизированный анализ) / Shortest path to node '{target_value}' (Optimized Analysis):")

        if not shortest_path_info:
            print(f"  Узел '{target_value}' не найден. / Node '{target_value}' not found.")
            return
        
        print(f"  Дерево / Tree: {shortest_path_info['tree']}")
        print(f"  Путь / Path: {' -> '.join(shortest_path_info['path'])}")
        print(f"  Длина / Length: {shortest_path_info['length']} узлов / nodes")

    def print_paths_between_nodes(self, start_value: str, end_value: str) -> None:
        """
        Выводит все пути между двумя указанными узлами.
        Prints all paths between two specified nodes.
        """
        paths_result_map = self.find_all_paths_between_nodes(start_value, end_value)
        print(f"\nВсе пути от '{start_value}' к '{end_value}' (оптимизированный анализ) / All paths from '{start_value}' to '{end_value}' (Optimized Analysis):")

        if not paths_result_map:
            print(f"  Пути от '{start_value}' к '{end_value}' не найдены. / No paths found from '{start_value}' to '{end_value}'.")
            return
        
        for tree_identifier, paths_list_str in paths_result_map.items():
            print(f"  В дереве / In tree '{tree_identifier}':")
            if not paths_list_str:
                 print(f"    Нет путей от '{start_value}' к '{end_value}' в этом дереве. / No paths from '{start_value}' to '{end_value}' in this tree.")
                 continue
            for i, path_str_list in enumerate(paths_list_str, 1):
                print(f"    Путь {i} / Path {i}: {' -> '.join(path_str_list)}")


if __name__ == '__main__':
    from .tree_construction import Node # Относительный импорт для запуска как части пакета

    # Пример использования анализатора (требует наличия объектов Node)
    # Создадим несколько узлов и деревьев для примера
    root_1 = Node("Root1")
    root_2 = Node("B")
    root_3 = Node("C")

    node_d = Node("D")
    node_e = Node("E")
    node_f = Node("F")
    node_g = Node("G")
    node_k = Node("K")
    node_l = Node("L")
    node_m = Node("M")
    node_n = Node("N")
    node_o = Node("O")

    root_1.add_child(node_d)
    #root_1.add_child(node_e)
    #root_1.add_child(node_f)
    #root_2.add_child(node_g)
    root_2.add_child(node_k)
    root_3.add_child(node_l)
    root_3.add_child(node_m)
    root_3.add_child(node_n)

    node_d.add_child(node_e)
    node_e.add_child(node_f)
    node_f.add_child(node_g)
    node_f.add_child(node_d)
    node_e.add_child(node_g)
    #node_f.add_child(node_g)
    #node_f.add_child(node_k)
    #node_d.add_child(node_o)
    #node_o.add_child(node_g)
    #node_o.add_child(node_m)
    
    start_time = time.time()
    # Анализ нескольких корней
    multi_analyzer = MultiRootAnalyzerOpt([root_1, root_2, root_3])
    multi_analyzer.print_forest_statistics()
    multi_analyzer.print_shared_nodes()
    multi_analyzer.print_connections_between_roots()
    multi_analyzer.print_forest_statistics()
    multi_analyzer.print_shared_nodes()
    multi_analyzer.print_connections_between_roots()
    multi_analyzer.print_paths_between_nodes("A", "G")
    multi_analyzer.print_shortest_path_to_node("G")
    print("\n")
    end_time = time.time()
    print(f"\nВремя выполнения оптимизированного анализа: {end_time - start_time:.4f} секунд")
    
    print("\n")
    # Визуализация леса
    try:
        from visualize_forest_connection import VisualizeForest
        VisualizeForest(multi_analyzer).visualize_forest_connections()
    except ImportError:
        print("Модуль визуализации недоступен")