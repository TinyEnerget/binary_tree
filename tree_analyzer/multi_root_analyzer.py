"""
Этот модуль реализует анализатор леса деревьев (MultiRootAnalyzer),
который предназначен для работы с несколькими корневыми узлами (деревьями) одновременно.
Он позволяет выполнять следующие операции:
- Анализ всего леса: сбор информации о всех узлах и идентификация общих узлов между деревьями.
- Поиск связей между корнями: определение, через какие общие узлы связаны различные деревья.
- Сбор статистики по лесу: подсчет количества узлов, вычисление глубины для каждого дерева и общая статистика.
- Поиск путей: нахождение всех путей до заданного узла, кратчайшего пути до узла,
  а также всех путей между двумя указанными узлами в пределах всего леса.

Основным классом является `MultiRootAnalyzer`, который принимает список корневых узлов
и предоставляет методы для вышеописанного анализа.
"""

# Imports
from typing import List, Dict, Any, Set, Optional, Tuple
from collections import deque # Импортируем deque для _get_tree_depth
from .tree_construction import Node # Импортируем Node

class MultiRootAnalyzer:
    """
    Анализатор леса с несколькими корнями, предоставляющий комплексный анализ множественных древовидных структур.
    A multi-root tree forest analyzer that provides comprehensive analysis of multiple tree structures.

    Этот класс позволяет выполнять расширенный анализ леса путем:
    - Отслеживания общих узлов в нескольких деревьях.
    - Нахождения связей между корневыми узлами.
    - Генерации подробной статистики по лесу и отдельным деревьям.
    This class enables advanced forest analysis by:
    - Tracking shared nodes across multiple trees
    - Finding connections between root nodes
    - Generating detailed forest and tree statistics

    Атрибуты / Attributes:
        roots (List[Node]): Коллекция корневых узлов (объектов `Node`) для анализа.
                            A collection of `Node` objects to be analyzed.
        shared_nodes (Dict[str, List[str]]): Отслеживает значения узлов (строки), которые появляются
                                             в нескольких деревьях, и список идентификаторов этих деревьев
                                             (например, "Tree_0_RootValue").
                                             Tracks node values (strings) that appear in multiple trees,
                                             and a list of tree identifiers (e.g., "Tree_0_RootValue").
        connections (List[Dict[str, Any]]): Список словарей, описывающих связи между парами корневых
                                            узлов через общие узлы. Заполняется методом `find_connections_between_roots`.
                                            A list of dictionaries describing connections between pairs of root
                                            nodes via common nodes. Populated by `find_connections_between_roots`.
    """

    def __init__(self, roots: List[Node]):
        """
        Инициализирует анализатор леса MultiRootAnalyzer.
        Initializes the MultiRootAnalyzer.

        Параметры / Parameters:
            roots (List[Node]): Список корневых узлов (экземпляров класса `Node`),
                                представляющих деревья в лесу.
                                A list of root nodes (`Node` instances) representing
                                the trees in the forest.
        """
        self.roots: List[Node] = roots
        # self.forest_map: Dict[str, List[str]] = {} # Атрибут не используется, удален.
        self.shared_nodes: Dict[str, List[str]] = {}
        self.connections: List[Dict[str, Any]] = []

        if self.roots: # Выполняем первичный анализ, только если есть корни
            self.analyze_forest()

    def analyze_forest(self) -> Dict[str, List[str]]:
        """
        Анализирует лес, состоящий из нескольких деревьев, для идентификации всех узлов и общих узлов.

        Проходит по каждому дереву, используя `_get_all_nodes_in_tree` для сбора всех уникальных узлов.
        Составляет карту `all_nodes_in_trees`, где ключ - значение узла, а значение - список
        идентификаторов деревьев (например, "Tree_0_RootA"), в которых этот узел встречается.
        На основе этой карты заполняет атрибут `self.shared_nodes` узлами,
        присутствующими более чем в одном дереве.

        Возвращает:
            dict: Словарь `all_nodes_in_trees`, отображающий каждое значение узла на список деревьев,
                  в которых он присутствует.
                  A dictionary mapping each node value to a list of trees it appears in.
        """
        all_nodes_in_trees: Dict[str, List[str]] = {}
        self.shared_nodes = {} # Очищаем перед каждым анализом

        for i, root_node in enumerate(self.roots): # Переименовано в root_node для ясности
            if not isinstance(root_node, Node) or not hasattr(root_node, 'value'):
                print(f"Warning: Корень по индексу {i} не является корректным объектом Node или не имеет атрибута 'value'. Пропуск. / Root at index {i} is not a valid Node object or lacks 'value' attribute. Skipping.")
                continue

            tree_nodes_set = self._get_all_nodes_in_tree(root_node) # root_node это Node
            # Идентификатор дерева формируется из индекса и значения корневого узла
            tree_identifier = f"Tree_{i}_{str(root_node.value)}"

            for node_val in tree_nodes_set: # node_val здесь уже str из _get_all_nodes_in_tree
                if node_val not in all_nodes_in_trees:
                    all_nodes_in_trees[node_val] = []
                all_nodes_in_trees[node_val].append(tree_identifier)

        for node_val, tree_list in all_nodes_in_trees.items():
            if len(tree_list) > 1:
                self.shared_nodes[node_val] = tree_list

        return all_nodes_in_trees

    def _get_all_nodes_in_tree(self, root: Node) -> Set[str]: # root это Node, возвращает Set[str]
        """
        Вспомогательный метод для получения всех уникальных значений узлов в одном дереве.

        Выполняет обход дерева в глубину (DFS), начиная с указанного `root`.
        Использует множество `visited` для отслеживания уже посещенных узлов и предотвращения
        бесконечных циклов в случае циклических графов.

        Параметры:
            root: Корневой узел дерева (экземпляр Node), с которого начинается обход.
                  The root node of the tree (Node instance) to traverse.

        Возвращает:
            set: Множество всех уникальных значений узлов, найденных в дереве.
                 A set of all unique node values found in the tree.
        """
        nodes_set: Set[str] = set()
        # Используем deque для BFS-подобного обхода для сбора узлов, хотя DFS тоже подойдет
        # visited_in_traversal отслеживает узлы (по их значению), чтобы не зацикливаться
        # Важно: Node.value должно быть хешируемым (например, строка)

        # Стек для DFS: (Node_instance)
        dfs_stack: List[Node] = [root]
        visited_values_in_dfs: Set[str] = set()

        while dfs_stack:
            current_node_obj = dfs_stack.pop()

            if not isinstance(current_node_obj, Node) or not hasattr(current_node_obj, 'value'):
                # Пропускаем некорректные объекты в структуре дерева
                continue

            node_val_str = str(current_node_obj.value) # Приводим значение к строке

            if node_val_str not in visited_values_in_dfs:
                visited_values_in_dfs.add(node_val_str)
                nodes_set.add(node_val_str)

                if hasattr(current_node_obj, 'children') and current_node_obj.children:
                    # Добавляем дочерние узлы в стек для дальнейшего обхода
                    # Добавляем в обратном порядке, чтобы при извлечении (pop) порядок был "естественным"
                    for child_node in reversed(current_node_obj.children):
                        if isinstance(child_node, Node) and hasattr(child_node, 'value') and str(child_node.value) not in visited_values_in_dfs:
                             dfs_stack.append(child_node)
                        # Если child_node уже посещен на этом пути DFS, он не добавляется, предотвращая цикл.
        return nodes_set

    def find_connections_between_roots(self) -> List[Dict[str, Any]]:
        """
        Находит и записывает связи между различными деревьями (корневыми узлами) в лесу через общие узлы.

        Метод сравнивает каждую уникальную пару деревьев в лесу. Для каждой пары он получает
        наборы узлов с помощью `_get_all_nodes_in_tree`. Если пересечение этих наборов не пусто
        (т.е. есть общие узлы), информация о такой связи (имена корневых узлов и список общих узлов)
        добавляется в атрибут `self.connections`.

        Возвращает:
            list: Список словарей, где каждый словарь описывает одну связь между двумя деревьями.
                  A list of dictionaries, each describing a connection between two trees.
                  Пример: [{'root1': 'A', 'root2': 'B', 'common_nodes': ['D'], 'connection_type': 'shared_nodes'}]
        """
        self.connections = []

        # Создаем список кортежей (имя_корня_строка, множество_узлов_строк)
        # Это помогает избежать повторного вызова _get_all_nodes_in_tree для одного и того же корня
        # и упрощает доступ к данным.
        root_node_sets: List[Tuple[str, Set[str]]] = []
        for i, root_node in enumerate(self.roots):
            if isinstance(root_node, Node) and hasattr(root_node, 'value'):
                root_node_value_str = str(root_node.value)
                nodes_in_this_tree = self._get_all_nodes_in_tree(root_node)
                root_node_sets.append((root_node_value_str, nodes_in_this_tree))
            else:
                # Логируем пропуск некорректного корневого элемента
                print(f"Warning: Корень по индексу {i} пропущен при поиске связей (некорректный объект). / Root at index {i} skipped in find_connections (invalid object).")


        for i in range(len(root_node_sets)):
            for j in range(i + 1, len(root_node_sets)):
                root1_val_str, nodes1_set = root_node_sets[i]
                root2_val_str, nodes2_set = root_node_sets[j]

                common_nodes_set = nodes1_set.intersection(nodes2_set)

                if common_nodes_set:
                    self.connections.append({
                        'root1': root1_val_str,
                        'root2': root2_val_str,
                        'common_nodes': sorted(list(common_nodes_set)), # Сортируем для консистентности
                        'connection_type': 'shared_nodes'
                    })
        return self.connections

    def get_forest_statistics(self) -> Dict[str, Any]: # Структура возвращаемого словаря детализирована в docstring
        """
        Собирает и возвращает статистику по всему лесу деревьев.

        Статистика включает:
        - `total_roots`: Общее количество деревьев (корневых узлов) в лесу.
        - `trees_info`: Список словарей, где каждый словарь содержит информацию
          об отдельном дереве:
            - `root`: Значение корневого узла.
            - `nodes_count`: Количество уникальных узлов в дереве (используя `_get_all_nodes_in_tree`).
            - `depth`: Глубина дерева (используя `_get_tree_depth`).
            - `nodes`: Список значений всех узлов в данном дереве.
        - `shared_nodes`: Словарь общих узлов, полученный из `self.shared_nodes` (заполняется в `analyze_forest`).

        Возвращает:
            dict: Словарь со статистикой по лесу.
                  A dictionary containing forest statistics.
        """
        # Убедимся, что shared_nodes актуальны, если analyze_forest не был вызван ранее или roots изменились
        if not self.shared_nodes and self.roots:
             self.analyze_forest()

        # Убедимся, что shared_nodes актуальны
        if not self.shared_nodes and self.roots: # Если shared_nodes пуст, но есть корни
             self.analyze_forest() # Это может быть избыточным, если analyze_forest уже вызывался в __init__

        # Типизация trees_info как список словарей с определенной структурой
        TreeInfoType = Dict[str, Union[str, int, List[str]]]
        trees_info_list: List[TreeInfoType] = []

        for i, root_node in enumerate(self.roots): # root_node это Node
            if not isinstance(root_node, Node) or not hasattr(root_node, 'value'):
                # Пропускаем некорректные корневые узлы
                continue

            tree_nodes_set = self._get_all_nodes_in_tree(root_node) # Возвращает Set[str]
            tree_depth_val = self._get_tree_depth(root_node) # Возвращает int

            trees_info_list.append({
                'root': str(root_node.value), # Значение корня как строка
                'nodes_count': len(tree_nodes_set),
                'depth': tree_depth_val,
                'nodes': sorted(list(tree_nodes_set)) # Список узлов как строки, отсортированный
            })

        stats_result: Dict[str, Any] = {
            'total_roots': len(self.roots),
            'trees_info': trees_info_list,
            'shared_nodes': self.shared_nodes.copy()
        }
        return stats_result

    def _get_tree_depth(self, root: Node) -> int:
        """
        Вспомогательный метод для вычисления глубины одного дерева с защитой от циклов.

        Глубина определяется как максимальное количество узлов на пути от корневого узла
        до самого дальнего листового узла. Использует обход в глубину (DFS).
        Для предотвращения бесконечных циклов и повторной обработки путей в циклических графах,
        отслеживает `visited_paths` (полные пути от корня до текущего узла) и
        `path` (узлы в текущем пути DFS для обнаружения прямого цикла).

        Параметры:
            root: Корневой узел дерева (экземпляр Node), для которого вычисляется глубина.
                  The root node of the tree (Node instance) for which depth is calculated.

        Возвращает:
            int: Глубина дерева. Равно 0, если дерево пустое (root is None).
                 The depth of the tree. Returns 0 if the tree is empty.
        """
        if not isinstance(root, Node) or not hasattr(root, 'value'):
            return 0 # Некорректный узел или узел без значения

        max_depth_val = 0
        # Стек для DFS: (Node_instance, current_depth, set_of_visited_values_on_this_path)
        dfs_stack: List[Tuple[Node, int, Set[str]]] = [(root, 1, {str(root.value)})]

        while dfs_stack:
            current_node_obj, current_d, visited_on_path = dfs_stack.pop()

            max_depth_val = max(max_depth_val, current_d)

            if hasattr(current_node_obj, 'children') and current_node_obj.children:
                for child_obj in reversed(current_node_obj.children): # Обходим в обратном порядке для "естественного" DFS
                    if isinstance(child_obj, Node) and hasattr(child_obj, 'value'):
                        child_val_str = str(child_obj.value)
                        if child_val_str not in visited_on_path: # Предотвращение цикла
                            new_visited_on_path = visited_on_path.copy() # Копируем для новой ветки
                            new_visited_on_path.add(child_val_str)
                            dfs_stack.append((child_obj, current_d + 1, new_visited_on_path))
        return max_depth_val


    # Старая рекурсивная реализация с более сложной защитой от циклов: (оставлена для справки, если понадобится)
    # def _get_tree_depth_recursive(self, root: Node, visited_paths: Optional[Set[Tuple[str, ...]]] = None, path: Optional[List[str]] = None) -> int:
    #     if visited_paths is None:
    #         visited_paths = set()
    #     if path is None:
    #         path = []

    #     if not isinstance(root, Node) or not hasattr(root, 'value'):
    #         return 0

    #     current_node_value_str = str(root.value)
    #     # path_key для visited_paths должен быть уникальным для пути, чтобы избежать повторного обхода
    #     # path_tuple для проверки цикла в текущей ветке
    #     path_tuple_for_cycle_check = tuple(path + [current_node_value_str])

    #     if path_tuple_for_cycle_check in visited_paths: # Этот путь уже полностью исследован
    #         return 0
    #     if current_node_value_str in path: # Обнаружен цикл в текущей ветке DFS
    #         return 0

    #     visited_paths.add(path_tuple_for_cycle_check)

    #     current_max_depth = 1 # Текущий узел добавляет 1 к глубине

    #     if hasattr(root, 'children') and root.children:
    #         max_child_depth = 0
    #         for child in root.children:
    #             child_depth = self._get_tree_depth_recursive(child, visited_paths, path + [current_node_value_str])
    #             if child_depth > max_child_depth:
    #                 max_child_depth = child_depth
    #         current_max_depth += max_child_depth
        
    #     return current_max_depth


    def print_forest_statistics(self) -> None:
        # visited_paths = set() # Хранит кортежи путей (node.value, node.value, ...)

        # def dfs(node, depth, current_path_values): # current_path_values - значения узлов в текущем пути dfs
        #     nonlocal max_depth

        #     if not node or not hasattr(node, 'value'):
        #         return

        #     # Ключ для visited_paths должен представлять уникальный путь до узла,
        #     # а не только значения в текущей ветке DFS, чтобы избежать повторного обсчета одного и того же поддерева через разные пути.
        #     # Однако, для простой защиты от циклов в глубину, достаточно current_path_values.
        #     # path_key = tuple(current_path_values + [node.value])

        #     # if path_key in visited_paths: # Этот вариант может быть слишком строгим, если узел достижим разными путями
        #     #     return
        #     if node.value in current_path_values: # Простой цикл обнаружен
        #          return

        #     # visited_paths.add(path_key)
        #     max_depth = max(max_depth, depth + 1)

        #     if hasattr(node, 'children') and node.children:
        #         for child in node.children:
        #             dfs(child, depth + 1, current_path_values + [node.value])
    
        # dfs(root, 0, [])
        # return max_depth


    def print_forest_statistics(self):
        """
        Выводит в консоль статистику по лесу деревьев.

        Получает статистику с помощью `get_forest_statistics()` и форматирует вывод.
        """
        stats = self.get_forest_statistics()
        print("Статистика по лесу / Forest Statistics:")
        print(f"Всего корневых узлов / Total Roots: {stats['total_roots']}")
        for tree_info in stats['trees_info']:
            print(f"  Дерево (корень) / Tree (root) '{tree_info['root']}': {tree_info['nodes_count']} узлов / nodes, глубина / depth {tree_info['depth']}")

    def print_shared_nodes(self):
        """
        Выводит в консоль информацию об общих узлах в лесу.

        Общие узлы - это узлы, которые присутствуют в нескольких деревьях.
        Предварительно вызывает `analyze_forest()`, если это не было сделано,
        для актуализации данных об общих узлах.
        """
        if not self.shared_nodes and self.roots: # Если shared_nodes пуст, но есть корни, возможно, анализ не проводился
            self.analyze_forest()
        print("\nОбщие узлы / Shared Nodes:")
        if not self.shared_nodes:
            print("  Нет общих узлов в лесу. / No shared nodes found in the forest.")
            return
        for node_value, trees in self.shared_nodes.items():
            print(f"  Узел / Node '{node_value}': встречается в деревьях / found in trees {trees}")

    def print_connections_between_roots(self):
        """
        Выводит в консоль информацию о связях между корневыми узлами через общие узлы.

        Предварительно вызывает `find_connections_between_roots()` для получения актуальных связей.
        """
        # find_connections_between_roots() вызывается внутри, если self.connections неактуальны или пусты
        # но для явности можно вызвать здесь, если требуется всегда свежий результат перед печатью.
        if not self.connections and self.roots: # Если connections не заполнены, но есть корни
            self.find_connections_between_roots()

        print("\nСвязи между корневыми узлами / Connections Between Roots:")
        if not self.connections:
            print("  Нет связей между корневыми узлами через общие узлы. / No connections found between roots via shared nodes.")
            return
        for connection in self.connections:
            print(f"  Между '{connection['root1']}' и '{connection['root2']}': через общие узлы / via common nodes {connection['common_nodes']}")

    # Дублирующийся метод find_connections_between_roots удален. Оставлен первый.

    def find_all_paths_to_node(self, target_value: str) -> Dict[str, List[List[str]]]: # target_value это str
        """
        Находит все возможные пути от любого из корневых узлов до указанного целевого узла
        (по его значению) во всех деревьях леса.
        Finds all possible paths from any of the root nodes to the specified target node
        (by its value) in all trees of the forest.

        Итерирует по каждому дереву в `self.roots`, вызывая `_find_paths_in_tree`
        для поиска путей к `target_value` внутри этого дерева.
        Результаты агрегируются в словарь, где ключами являются идентификаторы деревьев
        (например, "Tree_0_RootA"), а значениями — списки найденных путей (списков строк).
        Iterates through each tree in `self.roots`, calling `_find_paths_in_tree`
        to find paths to `target_value` within that tree.
        Results are aggregated into a dictionary where keys are tree identifiers
        (e.g., "Tree_0_RootA"), and values are lists of found paths (lists of strings).

        Параметры / Parameters:
            target_value (str): Значение (ID) узла, до которого необходимо найти пути.
                                The value (ID) of the target node.

        Возвращает / Returns:
            Dict[str, List[List[str]]]: Словарь, где ключ - это имя дерева,
                                        а значение - список путей (каждый путь - список ID узлов)
                                        до целевого узла в этом дереве.
                                        A dictionary where the key is the tree name,
                                        and the value is a list of paths (each path a list of node IDs)
                                        to the target node in that tree.
        """
        all_found_paths: Dict[str, List[List[str]]] = {}

        for i, root_node in enumerate(self.roots): # root_node это Node
            if not isinstance(root_node, Node) or not hasattr(root_node, 'value'):
                continue
            tree_identifier = f"Tree_{i}_{str(root_node.value)}"
            paths_in_tree = self._find_paths_in_tree(root_node, target_value) # target_value это str

            if paths_in_tree:
                all_found_paths[tree_identifier] = paths_in_tree

        return all_found_paths

    def _find_paths_in_tree(self, root: Node, target_value: str) -> List[List[str]]: # root это Node, target_value это str
        """
        Вспомогательный метод для поиска всех путей от заданного корневого узла до целевого узла
        в пределах одного дерева. Использует обход в глубину (DFS).

        Для предотвращения зацикливания используется множество `visited_in_path`,
        отслеживающее узлы в текущем пути DFS.

        Параметры / Args:
            root: Корневой узел дерева (экземпляр Node), с которого начинается поиск.
                  The root node of the tree (Node instance) to start the search from.
            target_value (Any): Значение целевого узла.
                                The value of the target node.

        Возвращает / Returns:
            List[List[Any]]: Список всех найденных путей. Каждый путь представлен как список значений узлов.
                             A list of all paths found. Each path is a list of node values.
        """
        all_paths_in_tree: List[List[str]] = [] # Список путей, каждый путь - список строк (ID узлов)

        if not isinstance(root, Node) or not hasattr(root, 'value'):
            return all_paths_in_tree # Возвращаем пустой список, если корень некорректен

        # Стек для DFS: (Node_instance, current_path_list_of_strings, visited_on_path_set_of_strings)
        dfs_stack: List[Tuple[Node, List[str], Set[str]]] = []

        root_value_str = str(root.value)
        dfs_stack.append((root, [root_value_str], {root_value_str}))

        while dfs_stack:
            current_node_obj, path_list_str, visited_set_str = dfs_stack.pop()

            # current_node_obj.value уже должен быть str из-за Node.value: str
            if current_node_obj.value == target_value: # Сравниваем со строкой target_value
                all_paths_in_tree.append(list(path_list_str))

            if hasattr(current_node_obj, 'children') and current_node_obj.children:
                for child_obj in reversed(current_node_obj.children):
                    if isinstance(child_obj, Node) and hasattr(child_obj, 'value'):
                        child_val_str = str(child_obj.value)
                        if child_val_str not in visited_set_str: # Проверка на цикл в текущем пути
                            new_path = path_list_str + [child_val_str]
                            new_visited_set = visited_set_str.copy() # Важно копировать для каждой новой ветки
                            new_visited_set.add(child_val_str)
                            dfs_stack.append((child_obj, new_path, new_visited_set))
        return all_paths_in_tree

    def find_shortest_path_to_node(self, target_value: str) -> Optional[Dict[str, Any]]: # target_value это str
        """
        Находит кратчайший путь до указанного целевого узла среди всех деревьев в лесу.

        Сначала вызывает `find_all_paths_to_node` для получения всех возможных путей.
        Затем итерирует по этим путям, чтобы определить самый короткий.

        Параметры / Args:
            target_value (Any): Значение целевого узла.
                                The value of the target node.

        Возвращает / Returns:
            Optional[Dict[str, Any]]: Словарь с информацией о кратчайшем пути (имя дерева, путь, длина)
                                      или None, если узел не найден или пути отсутствуют.
                                      A dictionary with shortest path info (tree name, path, length),
                                      or None if the node is not found or no paths exist.
                                      Пример: {'tree': 'Tree_0_A', 'path': ['A', 'D'], 'length': 2}
        """
        all_paths_dict = self.find_all_paths_to_node(target_value) # target_value это str

        if not all_paths_dict:
            return None

        shortest_path_info: Optional[Dict[str, Any]] = None
        min_path_len = float('inf')

        for tree_identifier, paths_list in all_paths_dict.items():
            for current_path in paths_list: # current_path это List[str]
                if len(current_path) < min_path_len:
                    min_path_len = len(current_path)
                    shortest_path_info = {
                        'tree': tree_identifier, # Имя дерева, где найден кратчайший путь
                        'path': current_path,    # Сам путь (List[str])
                        'length': min_path_len   # Длина пути (количество узлов)
                    }
        return shortest_path_info

    def find_all_paths_between_nodes(self, start_value: str, end_value: str) -> Dict[str, List[List[str]]]: # start/end_value это str
        """
        Находит все пути между двумя заданными узлами (по их значениям) во всех деревьях леса.

        Итерирует по каждому дереву, вызывая `_find_paths_between_nodes_in_tree`
        для поиска путей между `start_value` и `end_value` внутри этого дерева.
        Результаты агрегируются в словарь.

        Параметры / Args:
            start_value (Any): Значение начального узла пути.
                               The value of the starting node.
            end_value (Any): Значение конечного узла пути.
                             The value of the ending node.

        Возвращает / Returns:
            Dict[str, List[List[Any]]]: Словарь, где ключ - имя дерева, а значение - список путей
                                        (списков значений узлов) между начальным и конечным узлами в этом дереве.
                                        A dictionary mapping tree names to lists of paths.
        """
        all_found_paths_dict: Dict[str, List[List[str]]] = {}

        for i, root_node in enumerate(self.roots): # root_node это Node
            if not isinstance(root_node, Node) or not hasattr(root_node, 'value'):
                 continue
            tree_identifier = f"Tree_{i}_{str(root_node.value)}"
            paths_list = self._find_paths_between_nodes_in_tree(root_node, start_value, end_value) # start/end_value это str

            if paths_list:
                all_found_paths_dict[tree_identifier] = paths_list

        return all_found_paths_dict

    def _find_paths_between_nodes_in_tree(self, root: Node, start_value: str, end_value: str) -> List[List[str]]: # root это Node, start/end_value это str
        """
        Вспомогательный метод для поиска всех путей между начальным и конечным узлами
        (по их значениям) в пределах одного дерева. Использует DFS.

        Путь считается валидным, если он начинается с `start_value` и заканчивается на `end_value`.
        Отслеживает посещенные узлы в текущем пути (`visited_in_path`) для избежания циклов.

        Параметры / Args:
            root: Корневой узел дерева (экземпляр Node) для поиска.
                  The root node of the tree (Node instance).
            start_value (Any): Значение начального узла.
                               The value of the start node.
            end_value (Any): Значение конечного узла.
                             The value of the end node.

        Возвращает / Returns:
            List[List[Any]]: Список всех найденных путей между `start_value` и `end_value`.
                             A list of all paths found.
        """
        paths_result_list: List[List[str]] = [] # Список путей, каждый путь - список строк

        if not isinstance(root, Node) or not hasattr(root, 'value'):
            return paths_result_list

        # Стек для DFS: (Node_instance, current_path_list_of_strings, visited_on_path_set_of_strings, has_found_start_flag)
        dfs_stack: List[Tuple[Node, List[str], Set[str], bool]] = []

        root_value_str = str(root.value)
        # Начальное состояние: начинаем с корневого узла, путь содержит только его,
        # он посещен на этом пути, флаг found_start зависит от того, является ли корень начальным узлом.
        dfs_stack.append((root, [root_value_str], {root_value_str}, root_value_str == start_value))

        while dfs_stack:
            current_node_obj, current_path_list_str, visited_set_str, has_found_start_node = dfs_stack.pop()

            current_node_val_str = str(current_node_obj.value) # Гарантируем строку

            # Если текущий узел - это start_value, обновляем состояние пути
            if current_node_val_str == start_value:
                has_found_start_node = True
                current_path_list_str = [current_node_val_str] # Путь начинается заново с этого узла
                visited_set_str = {current_node_val_str}   # Посещенные на этом "новом" пути

            # Если start_value уже был найден на пути и текущий узел - это end_value, то путь найден
            if has_found_start_node and current_node_val_str == end_value:
                paths_result_list.append(list(current_path_list_str))
                # Продолжаем поиск других путей, если они есть (не делаем continue)

            # Продолжаем поиск в дочерних узлах
            if hasattr(current_node_obj, 'children') and current_node_obj.children:
                for child_obj in reversed(current_node_obj.children):
                    if isinstance(child_obj, Node) and hasattr(child_obj, 'value'):
                        child_val_str = str(child_obj.value)
                        if child_val_str not in visited_set_str: # Предотвращаем циклы в текущем пути
                            # Если start_value уже найден, просто расширяем путь
                            if has_found_start_node:
                                new_path = current_path_list_str + [child_val_str]
                                new_visited = visited_set_str.copy()
                                new_visited.add(child_val_str)
                                dfs_stack.append((child_obj, new_path, new_visited, True))
                            # Если start_value еще не найден, но текущий child - это start_value, начинаем новый путь
                            elif child_val_str == start_value:
                                dfs_stack.append((child_obj, [child_val_str], {child_val_str}, True))
                            # Иначе (start_value не найден и child не start_value) - этот путь не рассматриваем,
                            # так как он не начинается с start_value.
        return paths_result_list

    def print_all_paths_to_node(self, target_value: str) -> None: # target_value это str
        """
        Выводит в консоль все найденные пути до указанного целевого узла.

        Использует `find_all_paths_to_node` для получения данных, затем форматирует и печатает их.
        Prints all found paths to the specified target node to the console.
        Uses `find_all_paths_to_node` to get the data, then formats and prints it.

        Параметры / Parameters:
            target_value (str): Значение (ID) целевого узла. / The value (ID) of the target node.
        """
        paths_dict = self.find_all_paths_to_node(target_value) # target_value это str
        print(f"\nВсе пути к узлу '{target_value}' / All paths to node '{target_value}':")

        if not paths_dict:
            print(f"  Узел '{target_value}' не найден ни в одном дереве. / Node '{target_value}' not found in any tree.")
            return

        for tree_identifier, paths_list in paths_dict.items():
            print(f"\n  В дереве / In tree '{tree_identifier}':")
            if not paths_list:
                print(f"    Нет путей к '{target_value}' в этом дереве. / No paths to '{target_value}' in this tree.")
                continue
            for i, current_path in enumerate(paths_list, 1): # current_path это List[str]
                print(f"    Путь {i} / Path {i}: {' -> '.join(current_path)}") # map(str, path) не нужен, т.к. уже строки

    def print_shortest_path_to_node(self, target_value: str) -> None: # target_value это str
        """
        Выводит в консоль кратчайший путь до указанного целевого узла.

        Использует `find_shortest_path_to_node` для получения данных, затем форматирует и печатает их.
        Prints the shortest path to the specified target node to the console.
        Uses `find_shortest_path_to_node` to get the data, then formats and prints it.

        Параметры / Parameters:
            target_value (str): Значение (ID) целевого узла. / The value (ID) of the target node.
        """
        shortest_path_info = self.find_shortest_path_to_node(target_value) # target_value это str

        print(f"\nКратчайший путь к узлу '{target_value}' / Shortest path to node '{target_value}':")
        if not shortest_path_info:
            print(f"  Узел '{target_value}' не найден ни в одном дереве. / Node '{target_value}' not found in any tree.")
            return

        print(f"  Дерево / Tree: {shortest_path_info['tree']}")
        print(f"  Путь / Path: {' -> '.join(shortest_path_info['path'])}") # path уже List[str]
        print(f"  Длина / Length: {shortest_path_info['length']} узлов / nodes") # Длина в узлах

    def print_paths_between_nodes(self, start_value: str, end_value: str) -> None: # start/end_value это str
        """
        Выводит в консоль все пути между двумя указанными узлами.

        Использует `find_all_paths_between_nodes` для получения данных, затем форматирует и печатает их.
        Prints all paths between two specified nodes to the console.
        Uses `find_all_paths_between_nodes` to get the data, then formats and prints it.

        Параметры / Parameters:
            start_value (str): Значение (ID) начального узла. / The value (ID) of the start node.
            end_value (str): Значение (ID) конечного узла. / The value (ID) of the end node.
        """
        paths_dict = self.find_all_paths_between_nodes(start_value, end_value) # start/end_value это str
        print(f"\nВсе пути от '{start_value}' к '{end_value}' / All paths from '{start_value}' to '{end_value}':")

        if not paths_dict:
            print(f"  Пути от '{start_value}' к '{end_value}' не найдены. / No paths found from '{start_value}' to '{end_value}'.")
            return

        for tree_identifier, paths_list in paths_dict.items():
            print(f"\n  В дереве / In tree '{tree_identifier}':")
            if not paths_list:
                 print(f"    Нет путей от '{start_value}' к '{end_value}' в этом дереве. / No paths from '{start_value}' to '{end_value}' in this tree.")
                 continue
            for i, current_path in enumerate(paths_list, 1): # current_path это List[str]
                print(f"    Путь {i} / Path {i}: {' -> '.join(current_path)}") # map(str, path) не нужен
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
    
    # Анализ нескольких корней
    multi_analyzer = MultiRootAnalyzer([root_1, root_2, root_3])
    multi_analyzer.print_forest_statistics()
    multi_analyzer.print_shared_nodes()
    multi_analyzer.print_connections_between_roots()
    multi_analyzer.print_paths_between_nodes("A", "G")
    multi_analyzer.print_shortest_path_to_node("G")
    print("\n")

    # Визуализация леса
    from visualize_forest_connection import VisualizeForest
    VisualizeForest(multi_analyzer).visualize_forest_connections()
    