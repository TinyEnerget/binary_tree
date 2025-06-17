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
# import numpy as np # Не используется в предоставленном коде, можно закомментировать или удалить
from typing import Set, List as TypingList, Dict as TypingDict, Tuple, Optional, Any # Добавлен Any
import threading # Не используется напрямую, но может быть полезен для сложных сценариев синхронизации
from collections import defaultdict, deque
import time # Используется в __main__ для демонстрации


class MultiRootAnalyzerOpt:
    """
    Оптимизированный анализатор леса деревьев с поддержкой многопоточности и кэширования.
    Optimized multi-root tree forest analyzer with multithreading and caching support.

    Этот класс является улучшенной версией `MultiRootAnalyzer` и предназначен для
    эффективного анализа больших лесов деревьев или сложных древовидных структур.
    Ключевые отличия и особенности:
    - Использование `ThreadPoolExecutor` для параллельного выполнения многих операций анализа.
    - Применение `@lru_cache` и внутренних словарей кэширования (`_node_cache`, `_depth_cache`)
      для уменьшения избыточных вычислений.
    - Оптимизированные внутренние алгоритмы, например, использование `deque` для BFS-подобного обхода.

    Атрибуты / Attributes:
        roots (list): Коллекция корневых узлов (объектов Node) для анализа.
                      A collection of root nodes to be analyzed.
        max_workers (int): Максимальное количество потоков, используемых `ThreadPoolExecutor`.
                           Defaults to a value based on CPU cores.
                           The maximum number of threads used by `ThreadPoolExecutor`.
        forest_map (dict): Отображение значений узлов на их корневые узлы (менее используется в этой версии).
                           Mapping of node values to their root nodes (less used in this version).
        shared_nodes (dict): Отслеживает значения узлов, которые появляются в нескольких деревьях.
                             Tracks node values that appear in multiple trees.
        connections (list): Список связей (общих узлов) между корневыми узлами.
                            List of connections (shared nodes) between root nodes.
        _node_cache (dict): Внутренний кэш для хранения наборов узлов деревьев.
                            (Примечание: `@lru_cache` на `_get_all_nodes_in_tree_cached`
                            может дублировать или заменять эту функциональность).
                            Internal cache for storing sets of tree nodes.
        _depth_cache (dict): Внутренний кэш для хранения рассчитанных глубин деревьев.
                             (Примечание: `@lru_cache` на `_get_tree_depth`
                             может дублировать или заменять эту функциональность).
                             Internal cache for storing calculated tree depths.
    """

    def __init__(self, roots: TypingList[Any], max_workers: Optional[int] = None):
        """
        Инициализирует оптимизированный анализатор леса.

        Параметры / Parameters:
            roots (list): Список корневых узлов (предположительно, объектов типа Node).
                          A list of root nodes (presumably, Node-like objects).
            max_workers (Optional[int]): Максимальное количество потоков для `ThreadPoolExecutor`.
                                         Если None, вычисляется на основе количества CPU.
                                         Maximum number of threads for `ThreadPoolExecutor`.
                                         If None, it's calculated based on CPU count.
        """
        self.roots = roots
        # Определение количества рабочих потоков: минимум 32 или количество ядер CPU + 4
        # mp.cpu_count() может вернуть None или вызвать ошибку в некоторых окружениях, поэтому (mp.cpu_count() or 1)
        self.max_workers = max_workers or min(32, (mp.cpu_count() if mp.cpu_count() else 1) + 4)
        self.forest_map: TypingDict[Any, TypingList[Any]] = {} # Не активно используется
        self.shared_nodes: TypingDict[Any, TypingList[str]] = {}
        self.connections: TypingList[TypingDict[str, Any]] = []
        # _node_cache и _depth_cache используются методами, обернутыми в lru_cache,
        # что создает двухуровневую систему кэширования. Обычно lru_cache самодостаточен.
        # Если методы _get_all_nodes_in_tree и _get_tree_depth (не кэшированные версии)
        # вызываются напрямую из других мест, то эти кэши могут быть полезны.
        # В текущей структуре они выглядят как потенциальное дублирование с lru_cache.
        self._node_cache: TypingDict[Tuple[int, int], Set[Any]] = {}
        self._depth_cache: TypingDict[int, int] = {}

    def analyze_forest(self) -> TypingDict[Any, TypingList[str]]:
        """
        Выполняет параллельный анализ леса для идентификации всех узлов и общих узлов между деревьями.

        Использует `ThreadPoolExecutor` для параллельного вызова `_get_all_nodes_in_tree_cached`
        для каждого дерева в лесу. Затем агрегирует результаты для определения узлов,
        присутствующих в нескольких деревьях (записываются в `self.shared_nodes`).

        Возвращает / Returns:
            TypingDict[Any, TypingList[str]]: Словарь `all_nodes_in_trees`, где ключ - значение узла,
                                             а значение - список строковых идентификаторов деревьев
                                             (например, "Tree_0_RootName"), в которых этот узел встречается.
                                             A dictionary `all_nodes_in_trees` mapping node values to a list
                                             of tree string identifiers where the node appears.
        """
        all_nodes_in_trees: TypingDict[Any, TypingList[str]] = defaultdict(list)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Словарь для связи future с информацией о дереве (корневой узел, индекс)
            future_to_tree_info = {
                executor.submit(self._get_all_nodes_in_tree_cached, root, i): (root, i)
                for i, root in enumerate(self.roots)
                if hasattr(root, 'value') # Проверка, что корень имеет атрибут value
            }

            for future in concurrent.futures.as_completed(future_to_tree_info):
                root_node, tree_idx = future_to_tree_info[future]
                try:
                    nodes_in_tree_set = future.result()
                    # Предполагается, что root_node имеет атрибут 'value'
                    tree_identifier = f"Tree_{tree_idx}_{root_node.value}"

                    for node_val in nodes_in_tree_set:
                        all_nodes_in_trees[node_val].append(tree_identifier)

                except Exception as exc:
                    # Логирование или обработка ошибки анализа конкретного дерева
                    print(f'Анализ дерева {tree_idx} вызвал исключение: {exc} / Tree analysis for index {tree_idx} generated an exception: {exc}')
        
        self.shared_nodes = {
            node_val: tree_ids
            for node_val, tree_ids in all_nodes_in_trees.items()
            if len(tree_ids) > 1
        }
        return all_nodes_in_trees

    @lru_cache(maxsize=1000) # lru_cache кэширует результаты вызовов функции с теми же аргументами
    def _get_all_nodes_in_tree_cached(self, root: Any, tree_idx: int) -> Set[Any]:
        """
        Кэшированное получение всех уникальных значений узлов в одном дереве.

        Этот метод является оберткой над `_get_all_nodes_in_tree`.
        Он использует `@lru_cache` для автоматического кэширования результатов.
        Дополнительно, он проверяет и использует ручной кэш `self._node_cache`.
        Такая двухуровневая система кэширования может быть избыточной,
        так как `lru_cache` уже предоставляет эффективное кэширование.

        Параметры / Parameters:
            root (Any): Корневой узел дерева (должен иметь атрибуты 'value' и 'children').
                        The root node of the tree.
            tree_idx (int): Индекс дерева в списке корней (используется для ключа в ручном кэше).
                            The index of the tree in the roots list.

        Возвращает / Returns:
            Set[Any]: Множество всех уникальных значений узлов в дереве.
                      A set of all unique node values in the tree.
        """
        # Ключ для ручного кэша _node_cache. id(root) используется для уникальности объекта.
        cache_key = (id(root), tree_idx)
        if cache_key in self._node_cache:
            return self._node_cache[cache_key]

        # Если в ручном кэше нет, вызываем основной метод для получения узлов
        nodes = self._get_all_nodes_in_tree(root)
        self._node_cache[cache_key] = nodes # Сохраняем в ручной кэш
        return nodes

    def _get_all_nodes_in_tree(self, root: Any) -> Set[Any]:
        """
        Оптимизированный метод для сбора всех уникальных значений узлов в одном дереве.

        Использует обход в ширину (BFS) с помощью `collections.deque` для эффективного
        исследования дерева. Применяет множество `visited` для отслеживания уже
        посещенных узлов и предотвращения зацикливания в графах с циклами.

        Параметры / Parameters:
            root (Any): Корневой узел дерева.
                        The root node of the tree.

        Возвращает / Returns:
            Set[Any]: Множество уникальных значений узлов.
                      A set of unique node values.
        """
        if not root or not hasattr(root, 'value'): # Проверка на None и наличие value
            return set()

        nodes: Set[Any] = set()
        # visited хранит значения узлов, чтобы избежать повторной обработки узла с тем же значением
        visited_values: Set[Any] = set()
        queue = deque() # Очередь для BFS

        # Добавляем корень в очередь и отмечаем его значение как посещенное
        nodes.add(root.value)
        visited_values.add(root.value)
        queue.append(root)

        while queue:
            current_node = queue.popleft()

            # Предполагается, что узлы имеют атрибут 'children' (список дочерних узлов)
            if hasattr(current_node, 'children') and current_node.children:
                for child in current_node.children:
                    # Проверяем, что child существует, имеет значение и это значение еще не было посещено
                    if child and hasattr(child, 'value') and child.value not in visited_values:
                        visited_values.add(child.value)
                        nodes.add(child.value)
                        queue.append(child)
        return nodes

    def find_connections_between_roots(self) -> TypingList[TypingDict[str, Any]]:
        """
        Выполняет параллельный поиск связей (общих узлов) между всеми уникальными парами деревьев в лесу.

        Процесс разбит на два этапа:
        1. Сбор всех узлов для каждого дерева: Параллельно вызывается `_get_all_nodes_in_tree_cached`
           для каждого корня, результаты сохраняются в `tree_nodes_map`.
        2. Поиск связей для каждой пары: Генерируются все уникальные пары индексов деревьев.
           Для каждой пары параллельно вызывается `_find_connection_for_pair`
           с использованием `ThreadPoolExecutor`.

        Результаты (словари, описывающие связи) собираются и сохраняются в `self.connections`.

        Возвращает / Returns:
            TypingList[TypingDict[str, Any]]: Список словарей, где каждый словарь описывает связь
                                             между двумя деревьями через общие узлы.
                                             A list of dictionaries, each describing a connection.
        """
        tree_nodes_map: TypingDict[int, Set[Any]] = {} # Карта: индекс дерева -> множество его узлов
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(self._get_all_nodes_in_tree_cached, root, i): i
                for i, root in enumerate(self.roots) if hasattr(root, 'value')
            }
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    tree_nodes_map[idx] = future.result()
                except Exception as exc:
                    print(f"Ошибка при получении узлов для дерева {idx}: {exc} / Error getting nodes for tree {idx}: {exc}")

        # Генерация пар индексов деревьев для сравнения
        root_indices = list(tree_nodes_map.keys())
        pairs_to_check = [(i, j) for idx_i, i in enumerate(root_indices) for j in root_indices[idx_i + 1:]]

        found_connections: TypingList[TypingDict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # future_to_pair_info = {
            #     executor.submit(self._find_connection_for_pair, pair_idx_i, pair_idx_j, tree_nodes_map): (pair_idx_i, pair_idx_j)
            #     for pair_idx_i, pair_idx_j in pairs_to_check
            # }
            futures = [executor.submit(self._find_connection_for_pair, i, j, tree_nodes_map) for i,j in pairs_to_check]

            for future in concurrent.futures.as_completed(futures):
                try:
                    connection_result = future.result()
                    if connection_result:
                        found_connections.append(connection_result)
                except Exception as exc:
                     print(f"Ошибка при поиске связей для пары: {exc} / Error finding connection for pair: {exc}")
        
        self.connections = found_connections
        return self.connections

    def _find_connection_for_pair(self, tree_idx_1: int, tree_idx_2: int,
                                  all_tree_nodes: TypingDict[int, Set[Any]]) -> Optional[TypingDict[str, Any]]:
        """
        Вспомогательный метод для нахождения общих узлов между одной конкретной парой деревьев.

        Использует предварительно собранные множества узлов для каждого дерева.

        Параметры / Parameters:
            tree_idx_1 (int): Индекс первого дерева в `self.roots`.
            tree_idx_2 (int): Индекс второго дерева в `self.roots`.
            all_tree_nodes (TypingDict[int, Set[Any]]): Словарь, где ключи - индексы деревьев,
                                                       а значения - множества их узлов.

        Возвращает / Returns:
            Optional[TypingDict[str, Any]]: Словарь, описывающий связь, если найдены общие узлы,
                                           иначе None.
                                           A dictionary describing the connection if common nodes are found,
                                           otherwise None.
        """
        nodes1 = all_tree_nodes.get(tree_idx_1)
        nodes2 = all_tree_nodes.get(tree_idx_2)

        if not nodes1 or not nodes2: # Если для какого-то дерева узлы не были получены
            return None

        common_nodes = nodes1.intersection(nodes2)

        if common_nodes:
            # Предполагаем, что self.roots[idx] имеет атрибут 'value'
            root1_val = self.roots[tree_idx_1].value if hasattr(self.roots[tree_idx_1], 'value') else f"Tree_{tree_idx_1}"
            root2_val = self.roots[tree_idx_2].value if hasattr(self.roots[tree_idx_2], 'value') else f"Tree_{tree_idx_2}"
            return {
                'root1': root1_val,
                'root2': root2_val,
                'common_nodes': list(common_nodes),
                'connection_type': 'shared_nodes'
            }
        return None

    def get_forest_statistics(self) -> TypingDict[str, Any]:
        """
        Собирает и возвращает статистику по всему лесу, используя параллельные вычисления.

        Для каждого дерева в лесу параллельно запускается `_get_tree_stats`
        с использованием `ThreadPoolExecutor`. Результаты агрегируются.
        Статистика включает общее количество корней, информацию по каждому дереву
        (имя корня, количество узлов, глубина, список узлов) и список общих узлов.

        Возвращает / Returns:
            TypingDict[str, Any]: Словарь со статистикой по лесу.
                                  A dictionary containing forest statistics.
        """
        # Убедимся, что shared_nodes актуальны (если они нужны здесь)
        if not self.shared_nodes and self.roots:
            self.analyze_forest() # Может быть избыточным, если shared_nodes не являются частью прямого вывода статистики get_forest_statistics

        stats: TypingDict[str, Any] = {
            'total_roots': len(self.roots),
            'trees_info': [None] * len(self.roots), # Предварительное выделение списка для сохранения порядка
            'shared_nodes': self.shared_nodes.copy() # Копия актуальных общих узлов
        }

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(self._get_tree_stats, root, i): i
                for i, root in enumerate(self.roots) if hasattr(root, 'value')
            }

            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    stats['trees_info'][idx] = future.result()
                except Exception as exc:
                    print(f"Ошибка при получении статистики для дерева {idx}: {exc} / Error getting stats for tree {idx}: {exc}")
                    stats['trees_info'][idx] = {'root': self.roots[idx].value if hasattr(self.roots[idx], 'value') else f"UnknownTree_{idx}", 'error': str(exc)}
        
        # Удаление пустых элементов, если какие-то задачи не выполнились успешно и не добавили информацию
        stats['trees_info'] = [s for s in stats['trees_info'] if s is not None]
        return stats

    def _get_tree_stats(self, root: Any, idx: int) -> TypingDict[str, Any]:
        """
        Вспомогательный метод для расчета статистики одного дерева.

        Использует кэшированные методы `_get_all_nodes_in_tree_cached` для получения узлов
        и `_get_tree_depth` для вычисления глубины.

        Параметры / Parameters:
            root (Any): Корневой узел дерева.
            idx (int): Индекс дерева (используется для кэширования узлов).

        Возвращает / Returns:
            TypingDict[str, Any]: Словарь со статистикой для данного дерева.
                                  A dictionary with statistics for the given tree.
        """
        tree_nodes = self._get_all_nodes_in_tree_cached(root, idx) # Использует tree_idx для ключа кэша
        tree_depth = self._get_tree_depth(root) # lru_cache на _get_tree_depth использует сам объект root как часть ключа

        root_val = root.value if hasattr(root, 'value') else f"Tree_{idx}"
        return {
            'root': root_val,
            'nodes_count': len(tree_nodes),
            'depth': tree_depth,
            'nodes': list(tree_nodes)
        }

    @lru_cache(maxsize=500) # Кэширует результаты для разных объектов root
    def _get_tree_depth(self, root: Any) -> int:
        """
        Оптимизированное вычисление глубины дерева с использованием итеративного подхода (DFS на стеке)
        и кэширования.

        Метод обернут в `@lru_cache` для автоматического кэширования результатов на основе
        аргумента `root`. Также использует внутренний кэш `self._depth_cache`, что может быть
        избыточным (см. примечание в `__init__`).
        Использует стек для обхода в глубину, отслеживая текущую глубину и посещенные узлы
        на текущем пути для предотвращения циклов.

        Параметры / Parameters:
            root (Any): Корневой узел дерева.

        Возвращает / Returns:
            int: Глубина дерева. Равно 0, если дерево пустое.
                 The depth of the tree. 0 if the tree is empty.
        """
        # Ручной кэш _depth_cache. id(root) делает ключ уникальным для объекта root.
        # lru_cache также кэширует по объекту root, так что этот ручной кэш может быть не нужен,
        # если _get_tree_depth вызывается только через этот обернутый метод.
        cache_key = id(root)
        if cache_key in self._depth_cache:
            return self._depth_cache[cache_key]

        if not root or not hasattr(root, 'value'):
            return 0

        max_calculated_depth = 0
        # Стек: (узел, текущая_глубина, множество_посещенных_в_пути_значений_узлов)
        # frozenset для посещенных узлов, т.к. он должен быть хешируемым для возможного использования в качестве ключа кэша (хотя здесь не используется так)
        dfs_stack: TypingList[Tuple[Any, int, frozenset]] = [(root, 1, frozenset([root.value]))]

        while dfs_stack:
            current_node, current_depth, visited_on_path = dfs_stack.pop()

            max_calculated_depth = max(max_calculated_depth, current_depth)

            if hasattr(current_node, 'children') and current_node.children:
                for child in current_node.children:
                    # Проверяем, что child существует, имеет значение и это значение еще не было посещено на текущем пути
                    if child and hasattr(child, 'value') and child.value not in visited_on_path:
                        dfs_stack.append((child, current_depth + 1, visited_on_path | {child.value}))

        self._depth_cache[cache_key] = max_calculated_depth
        return max_calculated_depth

    def find_all_paths_to_node(self, target_value: Any) -> TypingDict[str, TypingList[TypingList[Any]]]:
        """
        Параллельный поиск всех путей от корневых узлов до заданного `target_value` во всех деревьях леса.

        Использует `ThreadPoolExecutor` для параллельного вызова `_find_paths_in_tree`
        для каждого дерева. Результаты собираются в словарь.

        Параметры / Parameters:
            target_value (Any): Значение целевого узла.

        Возвращает / Returns:
            TypingDict[str, TypingList[TypingList[Any]]]: Словарь, где ключ - идентификатор дерева,
                                                          а значение - список путей до целевого узла.
                                                          A dictionary mapping tree identifiers to lists of paths.
        """
        all_found_paths: TypingDict[str, TypingList[TypingList[Any]]] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_tree_idx = {
                executor.submit(self._find_paths_in_tree, root, target_value, i): i
                for i, root in enumerate(self.roots) if hasattr(root, 'value')
            }

            for future in concurrent.futures.as_completed(future_to_tree_idx):
                tree_idx = future_to_tree_idx[future]
                try:
                    paths_in_tree = future.result()
                    if paths_in_tree:
                        tree_name = f"Tree_{tree_idx}_{self.roots[tree_idx].value}"
                        all_found_paths[tree_name] = paths_in_tree
                except Exception as exc:
                    print(f"Ошибка при поиске путей в дереве {tree_idx}: {exc} / Error finding paths in tree {tree_idx}: {exc}")
        
        return all_found_paths

    def _find_paths_in_tree(self, root: Any, target_value: Any, tree_idx: int = 0) -> TypingList[TypingList[Any]]:
        """
        Оптимизированный поиск всех путей от корневого узла до `target_value` в одном дереве.

        Использует итеративный обход в глубину (DFS) с помощью стека.
        Каждый элемент стека хранит узел, текущий путь до него и множество посещенных узлов на этом пути
        для предотвращения циклов.

        Параметры / Parameters:
            root (Any): Корневой узел дерева.
            target_value (Any): Значение целевого узла.
            tree_idx (int): Индекс дерева (для отладки или логирования, не используется в логике поиска).

        Возвращает / Returns:
            TypingList[TypingList[Any]]: Список всех найденных путей. Каждый путь - это список значений узлов.
                                         A list of all found paths. Each path is a list of node values.
        """
        if not root or not hasattr(root, 'value'):
            return []

        found_paths: TypingList[TypingList[Any]] = []
        # Стек: (узел, текущий_путь_значений, множество_посещенных_в_пути_значений)
        dfs_stack: TypingList[Tuple[Any, TypingList[Any], Set[Any]]] = [(root, [root.value], {root.value})]

        while dfs_stack:
            current_node, current_path, visited_on_path = dfs_stack.pop()

            if current_node.value == target_value:
                found_paths.append(list(current_path)) # Добавляем копию пути
                # Не продолжаем дальше по этому пути, если цель найдена (можно и продолжить, если нужны пути *через* цель)
                # continue # Если нужно найти пути только ДО цели, а не через нее к другим целям с тем же значением

            if hasattr(current_node, 'children') and current_node.children:
                # Обходим дочерние узлы в обратном порядке для более "естественного" порядка путей в DFS
                for child in reversed(current_node.children):
                    if child and hasattr(child, 'value') and child.value not in visited_on_path:
                        new_path = current_path + [child.value]
                        new_visited_on_path = visited_on_path | {child.value} # Создаем новое множество для следующей ветви
                        dfs_stack.append((child, new_path, new_visited_on_path))
        return found_paths

    def find_shortest_path_to_node(self, target_value: Any) -> Optional[TypingDict[str, Any]]:
        """
        Находит кратчайший путь до узла `target_value` среди всех деревьев в лесу.

        Сначала вызывает `find_all_paths_to_node` (который работает параллельно) для получения всех путей,
        а затем итерирует по ним для определения самого короткого.

        Параметры / Parameters:
            target_value (Any): Значение целевого узла.

        Возвращает / Returns:
            Optional[TypingDict[str, Any]]: Словарь с информацией о кратчайшем пути
                                           (имя дерева, путь, длина) или None, если путь не найден.
                                           A dictionary with shortest path info, or None if not found.
        """
        all_paths_data = self.find_all_paths_to_node(target_value)

        if not all_paths_data:
            return None

        shortest_path_info: Optional[TypingDict[str, Any]] = None
        min_len = float('inf')

        for tree_id, paths_list in all_paths_data.items():
            for path_item in paths_list:
                if len(path_item) < min_len:
                    min_len = len(path_item)
                    shortest_path_info = {
                        'tree': tree_id,
                        'path': path_item,
                        'length': min_len
                    }
        return shortest_path_info

    def find_all_paths_between_nodes(self, start_value: Any, end_value: Any) -> TypingDict[str, TypingList[TypingList[Any]]]:
        """
        Параллельный поиск всех путей между двумя заданными узлами (`start_value` и `end_value`)
        во всех деревьях леса.

        Использует `ThreadPoolExecutor` для параллельного вызова `_find_paths_between_nodes_in_tree`
        для каждого дерева.

        Параметры / Parameters:
            start_value (Any): Значение начального узла.
            end_value (Any): Значение конечного узла.

        Возвращает / Returns:
            TypingDict[str, TypingList[TypingList[Any]]]: Словарь, где ключ - идентификатор дерева,
                                                          а значение - список путей между узлами.
                                                          A dictionary mapping tree IDs to lists of paths.
        """
        all_found_paths_map: TypingDict[str, TypingList[TypingList[Any]]] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(self._find_paths_between_nodes_in_tree, root, start_value, end_value, i): i
                for i, root in enumerate(self.roots) if hasattr(root, 'value')
            }

            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    paths = future.result()
                    if paths:
                        tree_name = f"Tree_{idx}_{self.roots[idx].value}"
                        all_found_paths_map[tree_name] = paths
                except Exception as exc:
                    print(f"Ошибка при поиске путей между узлами в дереве {idx}: {exc} / Error finding paths between nodes in tree {idx}: {exc}")
        
        return all_found_paths_map

    def _find_paths_between_nodes_in_tree(self, root: Any, start_value: Any, end_value: Any,
                                          tree_idx: int = 0) -> TypingList[TypingList[Any]]:
        """
        Оптимизированный поиск всех путей между `start_value` и `end_value` в одном дереве.

        Использует итеративный DFS. Путь начинается только после нахождения `start_value`.
        Защита от циклов обеспечивается отслеживанием посещенных узлов на текущем пути.

        Параметры / Parameters:
            root (Any): Корневой узел дерева.
            start_value (Any): Значение начального узла.
            end_value (Any): Значение конечного узла.
            tree_idx (int): Индекс дерева (для отладки/логирования).

        Возвращает / Returns:
            TypingList[TypingList[Any]]: Список всех найденных путей.
                                         A list of all found paths.
        """
        if not root or not hasattr(root, 'value'):
            return []

        paths_result: TypingList[TypingList[Any]] = []
        # Стек: (узел, текущий_путь, посещенные_в_пути, флаг_найден_ли_start_value)
        dfs_stack: TypingList[Tuple[Any, TypingList[Any], Set[Any], bool]] = []
        
        # Начальная инициализация стека: начинаем обход с корня
        # Флаг found_start изначально False, если корень не является start_value
        dfs_stack.append((root, [root.value], {root.value}, root.value == start_value))


        while dfs_stack:
            current_node, current_path, visited_on_path, has_found_start = dfs_stack.pop()

            # Если текущий узел - это start_value, обновляем состояние
            if current_node.value == start_value:
                has_found_start = True
                # "Перезапускаем" путь с этого узла
                current_path = [current_node.value]
                visited_on_path = {current_node.value}


            # Если start_value был найден и текущий узел - это end_value, путь найден
            if has_found_start and current_node.value == end_value:
                paths_result.append(list(current_path)) # Добавляем копию
                # Можно не продолжать дальше по этому пути, если не ищем пути, проходящие через end_value к другим узлам
                # continue

            # Продолжаем поиск в дочерних узлах
            if hasattr(current_node, 'children') and current_node.children:
                for child in reversed(current_node.children): # Обратный порядок для "естественного" DFS
                    if child and hasattr(child, 'value') and child.value not in visited_on_path:
                        # Новый путь строится только если has_found_start истинно,
                        # или если сам child является start_value (тогда он начнет новый потенциальный путь).
                        if has_found_start or child.value == start_value:
                            new_visited = visited_on_path | {child.value}

                            # Если мы только что нашли start_value в child, путь начинается с child
                            if child.value == start_value and not has_found_start:
                                new_path = [child.value]
                                dfs_stack.append((child, new_path, {child.value}, True))
                            elif has_found_start: # Если start_value уже был найден ранее, продолжаем текущий путь
                                new_path = current_path + [child.value]
                                dfs_stack.append((child, new_path, new_visited, True))
                            # Случай, когда child не start_value и start_value еще не найден, пропускается
                            # (т.е. мы не начинаем строить путь от произвольного узла до start_value)
        return paths_result

    def print_forest_statistics(self):
        """
        Выводит в консоль статистику по лесу деревьев.
        Prints forest statistics to the console.
        """
        stats = self.get_forest_statistics()
        print("Статистика по лесу (оптимизированная) / Forest Statistics (Optimized):")
        print(f"  Всего корневых узлов / Total Roots: {stats['total_roots']}")
        if 'trees_info' in stats:
            for tree_info in stats['trees_info']:
                if tree_info and 'root' in tree_info : # Проверка, что информация о дереве существует
                    print(f"    Дерево (корень) / Tree (root) '{tree_info['root']}': "
                          f"{tree_info.get('nodes_count', 'N/A')} узлов / nodes, "
                          f"глубина / depth {tree_info.get('depth', 'N/A')}")
                elif tree_info and 'error' in tree_info:
                     print(f"    Дерево (корень) / Tree (root) '{tree_info.get('root', 'Unknown')}': Ошибка / Error - {tree_info['error']}")


    def print_shared_nodes(self):
        """
        Выводит в консоль информацию об общих узлах в лесу.
        Prints information about shared nodes in the forest to the console.
        """
        # analyze_forest должен быть вызван, чтобы self.shared_nodes был актуален
        if not self.shared_nodes and self.roots:
             self.analyze_forest() # Убедимся, что анализ проведен
        print("\nОбщие узлы (оптимизированный анализ) / Shared Nodes (Optimized Analysis):")
        if not self.shared_nodes:
            print("  Нет общих узлов в лесу. / No shared nodes found.")
            return
        for node_value, tree_ids in self.shared_nodes.items():
            print(f"  Узел / Node '{node_value}': встречается в деревьях / found in trees {tree_ids}")

    def print_connections_between_roots(self):
        """
        Выводит в консоль информацию о связях между корневыми узлами.
        Prints information about connections between root nodes to the console.
        """
        # find_connections_between_roots должен быть вызван для актуализации self.connections
        if not self.connections and self.roots:
            self.find_connections_between_roots()
        print("\nСвязи между корневыми узлами (оптимизированный анализ) / Connections Between Roots (Optimized Analysis):")
        if not self.connections:
            print("  Нет связей между корневыми узлами. / No connections found between roots.")
            return
        for conn in self.connections:
            print(f"  Между '{conn['root1']}' и '{conn['root2']}': через общие узлы / via common nodes {conn['common_nodes']}")

    def print_all_paths_to_node(self, target_value: Any):
        """
        Выводит все пути до указанного узла.
        Prints all paths to the specified node.
        """
        paths_data = self.find_all_paths_to_node(target_value)
        print(f"\nВсе пути к узлу '{target_value}' (оптимизированный анализ) / All paths to node '{target_value}' (Optimized Analysis):")
        if not paths_data:
            print(f"  Узел '{target_value}' не найден. / Node '{target_value}' not found.")
            return
        
        for tree_id, paths_list in paths_data.items():
            print(f"  В дереве / In tree '{tree_id}':")
            if not paths_list:
                print(f"    Нет путей к '{target_value}' в этом дереве. / No paths to '{target_value}' in this tree.")
                continue
            for i, path_item in enumerate(paths_list, 1):
                print(f"    Путь {i} / Path {i}: {' -> '.join(map(str, path_item))}")

    def print_shortest_path_to_node(self, target_value: Any):
        """
        Выводит кратчайший путь до указанного узла.
        Prints the shortest path to the specified node.
        """
        shortest_data = self.find_shortest_path_to_node(target_value)
        print(f"\nКратчайший путь к узлу '{target_value}' (оптимизированный анализ) / Shortest path to node '{target_value}' (Optimized Analysis):")

        if not shortest_data:
            print(f"  Узел '{target_value}' не найден. / Node '{target_value}' not found.")
            return
        
        print(f"  Дерево / Tree: {shortest_data['tree']}")
        print(f"  Путь / Path: {' -> '.join(map(str, shortest_data['path']))}")
        print(f"  Длина / Length: {shortest_data['length']} узлов / nodes")

    def print_paths_between_nodes(self, start_value: Any, end_value: Any):
        """
        Выводит все пути между двумя указанными узлами.
        Prints all paths between two specified nodes.
        """
        paths_map = self.find_all_paths_between_nodes(start_value, end_value)
        print(f"\nВсе пути от '{start_value}' к '{end_value}' (оптимизированный анализ) / All paths from '{start_value}' to '{end_value}' (Optimized Analysis):")

        if not paths_map:
            print(f"  Пути от '{start_value}' к '{end_value}' не найдены. / No paths found from '{start_value}' to '{end_value}'.")
            return
        
        for tree_id, paths_list in paths_map.items():
            print(f"  В дереве / In tree '{tree_id}':")
            if not paths_list:
                 print(f"    Нет путей от '{start_value}' к '{end_value}' в этом дереве. / No paths from '{start_value}' to '{end_value}' in this tree.")
                 continue
            for i, path_item in enumerate(paths_list, 1):
                print(f"    Путь {i} / Path {i}: {' -> '.join(map(str, path_item))}")


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