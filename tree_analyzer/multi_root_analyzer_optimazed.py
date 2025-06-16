import concurrent.futures
import multiprocessing as mp
from functools import lru_cache
import numpy as np
from typing import Set, List as TypingList, Dict as TypingDict, Tuple, Optional
import threading
from collections import defaultdict, deque
import time


class MultiRootAnalyzerOpt:
    """
    Оптимизированный анализатор леса деревьев с поддержкой многопоточности и JIT-компиляции.
    
    Этот класс обеспечивает расширенный анализ леса путем:
    - Отслеживания общих узлов между несколькими деревьями
    - Поиска связей между корневыми узлами
    - Генерации детальной статистики леса и деревьев
    - Параллельной обработки для повышения производительности
    
    Attributes:
        roots (list): Коллекция корневых узлов для анализа
        max_workers (int): Максимальное количество потоков для параллельной обработки
        forest_map (dict): Отображение значений узлов на их корневые узлы
        shared_nodes (dict): Отслеживает значения узлов, которые появляются в нескольких деревьях
        connections (list): Список связей между корневыми узлами
    """
        
    def __init__(self, roots: list, max_workers: Optional[int] = None):
        self.roots = roots
        self.max_workers = max_workers or min(32, (mp.cpu_count() or 1) + 4)
        self.forest_map = {}
        self.shared_nodes = {}
        self.connections = []
        self._node_cache = {}
        self._depth_cache = {}
        
    def analyze_forest(self):
        """Параллельный анализ леса деревьев"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Параллельно получаем узлы для каждого дерева
            future_to_tree = {
                executor.submit(self._get_all_nodes_in_tree_cached, root, i): (root, i) 
                for i, root in enumerate(self.roots)
            }
            
            all_nodes_in_trees = {}
            
            for future in concurrent.futures.as_completed(future_to_tree):
                root, tree_idx = future_to_tree[future]
                try:
                    tree_nodes = future.result()
                    tree_name = f"Tree_{tree_idx}_{root.value}"
                    
                    for node_value in tree_nodes:
                        if node_value not in all_nodes_in_trees:
                            all_nodes_in_trees[node_value] = []
                        all_nodes_in_trees[node_value].append(tree_name)
                        
                except Exception as exc:
                    print(f'Tree analysis generated an exception: {exc}')
        
        # Находим общие узлы
        self.shared_nodes = {
            node_value: trees 
            for node_value, trees in all_nodes_in_trees.items() 
            if len(trees) > 1
        }
        
        return all_nodes_in_trees
    
    @lru_cache(maxsize=1000)
    def _get_all_nodes_in_tree_cached(self, root, tree_idx: int):
        """Кэшированное получение всех узлов в дереве"""
        cache_key = (id(root), tree_idx)
        if cache_key in self._node_cache:
            return self._node_cache[cache_key]
            
        nodes = self._get_all_nodes_in_tree(root)
        self._node_cache[cache_key] = nodes
        return nodes
    
    def _get_all_nodes_in_tree(self, root):
        """Оптимизированное получение всех узлов с использованием deque и защитой от циклов"""
        if not root:
            return set()
            
        nodes = set()
        visited = set()
        queue = deque([root])
        
        while queue:
            node = queue.popleft()
            if node and node.value not in visited:
                visited.add(node.value)
                nodes.add(node.value)
                
                if hasattr(node, 'children') and node.children:
                    queue.extend(node.children)
        
        return nodes
    
    def find_connections_between_roots(self):
        """Параллельный поиск связей между корневыми узлами"""
        # Предварительно получаем все узлы для каждого дерева
        tree_nodes = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(self._get_all_nodes_in_tree_cached, root, i): i
                for i, root in enumerate(self.roots)
            }
            
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                tree_nodes[idx] = future.result()
        
        # Генерируем пары для сравнения
        pairs = [(i, j) for i in range(len(self.roots)) for j in range(i + 1, len(self.roots))]
        
        # Параллельно обрабатываем пары
        connections = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_pair = {
                executor.submit(self._find_connection_for_pair, i, j, tree_nodes): (i, j)
                for i, j in pairs
            }
            
            for future in concurrent.futures.as_completed(future_to_pair):
                connection = future.result()
                if connection:
                    connections.append(connection)
        
        self.connections = connections
        return connections
    
    def _find_connection_for_pair(self, i: int, j: int, tree_nodes: dict):
        """Находит связь между парой деревьев"""
        nodes1 = tree_nodes[i]
        nodes2 = tree_nodes[j]
        
        common_nodes = nodes1.intersection(nodes2)
        
        if common_nodes:
            return {
                'root1': self.roots[i].value,
                'root2': self.roots[j].value,
                'common_nodes': list(common_nodes),
                'connection_type': 'shared_nodes'
            }
        return None
    
    def get_forest_statistics(self):
        """Параллельное получение статистики по лесу"""
        stats = {
            'total_roots': len(self.roots),
            'trees_info': [],
            'shared_nodes': self.shared_nodes if hasattr(self, 'shared_nodes') else None
        }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(self._get_tree_stats, root, i): i
                for i, root in enumerate(self.roots)
            }
            
            tree_stats = [None] * len(self.roots)
            
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                tree_stats[idx] = future.result()
        
        stats['trees_info'] = tree_stats
        return stats
    def _get_tree_stats(self, root, idx: int):
        """Получает статистику для одного дерева"""
        tree_nodes = self._get_all_nodes_in_tree_cached(root, idx)
        tree_depth = self._get_tree_depth(root)
        
        return {
            'root': root.value,
            'nodes_count': len(tree_nodes),
            'depth': tree_depth,
            'nodes': list(tree_nodes)
        }
    
    @lru_cache(maxsize=500)
    def _get_tree_depth(self, root):
        """Оптимизированное вычисление глубины дерева с защитой от циклов"""
        cache_key = id(root)
        if cache_key in self._depth_cache:
            return self._depth_cache[cache_key]
        
        if not root:
            return 0
        
        max_depth = 0
        stack = [(root, 1, frozenset())]  # (node, depth, visited_path)
        
        while stack:
            node, depth, visited = stack.pop()
            
            if not node or node.value in visited:
                continue
            
            max_depth = max(max_depth, depth)
            new_visited = visited | {node.value}
            
            if hasattr(node, 'children') and node.children:
                for child in node.children:
                    if child and child.value not in visited:
                        stack.append((child, depth + 1, new_visited))
        
        self._depth_cache[cache_key] = max_depth
        return max_depth
    
    def find_all_paths_to_node(self, target_value):
        """Параллельный поиск всех путей до узла"""
        all_paths = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_tree = {
                executor.submit(self._find_paths_in_tree, root, target_value, i): i
                for i, root in enumerate(self.roots)
            }
            
            for future in concurrent.futures.as_completed(future_to_tree):
                tree_idx = future_to_tree[future]
                paths = future.result()
                
                if paths:
                    tree_name = f"Tree_{tree_idx}_{self.roots[tree_idx].value}"
                    all_paths[tree_name] = paths
        
        return all_paths
    
    def _find_paths_in_tree(self, root, target_value, tree_idx: int = 0):
        """Оптимизированный поиск путей в дереве с защитой от циклов"""
        if not root:
            return []
        
        all_paths = []
        stack = [(root, [root.value], {root.value})]  # (node, path, visited)
        
        while stack:
            node, path, visited = stack.pop()
            
            if node.value == target_value:
                all_paths.append(path.copy())
                continue
            
            if hasattr(node, 'children') and node.children:
                for child in node.children:
                    if child and child.value not in visited:
                        new_path = path + [child.value]
                        new_visited = visited | {child.value}
                        stack.append((child, new_path, new_visited))
        
        return all_paths
    
    def find_shortest_path_to_node(self, target_value):
        """Находит кратчайший путь до узла среди всех деревьев"""
        all_paths = self.find_all_paths_to_node(target_value)
        
        if not all_paths:
            return None
        
        shortest_path = None
        shortest_length = float('inf')
        shortest_tree = None
        
        for tree_name, paths in all_paths.items():
            for path in paths:
                if len(path) < shortest_length:
                    shortest_length = len(path)
                    shortest_path = path
                    shortest_tree = tree_name
        
        return {
            'tree': shortest_tree,
            'path': shortest_path,
            'length': shortest_length
        }
    
    def find_all_paths_between_nodes(self, start_value, end_value):
        """Параллельный поиск всех путей между двумя узлами в лесу"""
        all_paths = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_tree = {
                executor.submit(self._find_paths_between_nodes_in_tree, root, start_value, end_value, i): i
                for i, root in enumerate(self.roots)
            }
            
            for future in concurrent.futures.as_completed(future_to_tree):
                tree_idx = future_to_tree[future]
                paths = future.result()
                
                if paths:
                    tree_name = f"Tree_{tree_idx}_{self.roots[tree_idx].value}"
                    all_paths[tree_name] = paths
        
        return all_paths
    
    def _find_paths_between_nodes_in_tree(self, root, start_value, end_value, tree_idx: int = 0):
        """Оптимизированный поиск путей между двумя узлами в конкретном дереве"""
        if not root:
            return []
        
        all_paths = []
        stack = [(root, [root.value], {root.value}, root.value == start_value)]
        # (node, path, visited, found_start)
        
        while stack:
            node, path, visited, found_start = stack.pop()
            
            # Проверяем, нашли ли начальный узел
            if node.value == start_value:
                found_start = True
            
            # Если нашли конечный узел и уже прошли через начальный
            if node.value == end_value and found_start:
                all_paths.append(path.copy())
                continue
            
            if hasattr(node, 'children') and node.children:
                for child in node.children:
                    if child and child.value not in visited:
                        new_path = path + [child.value]
                        new_visited = visited | {child.value}
                        stack.append((child, new_path, new_visited, found_start))
        
        return all_paths
    
    def print_forest_statistics(self):
        """Выводит статистику по лесу деревьев"""
        stats = self.get_forest_statistics()
        print("Forest Statistics:")
        print(f"Total Roots: {stats['total_roots']}")
        for tree_info in stats['trees_info']:
            print(f"Tree {tree_info['root']}: {tree_info['nodes_count']} nodes, depth {tree_info['depth']}")
    
    def print_shared_nodes(self):
        """Выводит общие узлы"""
        self.analyze_forest()
        print("Shared Nodes:")
        for node_value, roots in self.shared_nodes.items():
            print(f"{node_value}: {roots}")
    
    def print_connections_between_roots(self):
        """Выводит связи между корневыми узлами"""
        connections = self.find_connections_between_roots()
        print("Connections Between Roots:")
        for connection in connections:
            print(f"{connection['root1']} - {connection['root2']}: {connection['common_nodes']}")
    
    def print_all_paths_to_node(self, target_value):
        """Выводит все пути до указанного узла"""
        paths = self.find_all_paths_to_node(target_value)
        print(f"\nAll paths to node '{target_value}':")
        if not paths:
            print(f"Node '{target_value}' not found in any tree.")
            return
        
        for tree_name, tree_paths in paths.items():
            print(f"\n{tree_name}:")
            for i, path in enumerate(tree_paths, 1):
                print(f"  Path {i}: {' -> '.join(map(str, path))}")
    
    def print_shortest_path_to_node(self, target_value):
        """Выводит кратчайший путь до узла"""
        shortest = self.find_shortest_path_to_node(target_value)
        
        if not shortest:
            print(f"Node '{target_value}' not found in any tree.")
            return
        
        print(f"\nShortest path to node '{target_value}':")
        print(f"Tree: {shortest['tree']}")
        print(f"Path: {' -> '.join(map(str, shortest['path']))}")
        print(f"Length: {shortest['length']} nodes")
    
    def print_paths_between_nodes(self, start_value, end_value):
        """Выводит все пути между двумя узлами"""
        paths = self.find_all_paths_between_nodes(start_value, end_value)
        print(f"\nAll paths from '{start_value}' to '{end_value}':")
        
        if not paths:
            print(f"No paths found from '{start_value}' to '{end_value}'.")
            return
        
        for tree_name, tree_paths in paths.items():
            print(f"\n{tree_name}:")
            for i, path in enumerate(tree_paths, 1):
                print(f"  Path {i}: {' -> '.join(map(str, path))}")


if __name__ == '__main__':
    from tree_construction import Node

    root_1 = Node("A")
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