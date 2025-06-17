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
from typing import List, Dict, Any, Set, Optional, Tuple # Добавлены необходимые типы

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

    Атрибуты:
        roots (list): Коллекция корневых узлов (объектов Node) для анализа.
                      A collection of root nodes to be analyzed.
        forest_map (dict): Отображение значения узла на корневые узлы деревьев, в которых он встречается.
                           Mapping of node values to their root nodes. (Примечание: этот атрибут инициализируется, но не используется в текущей реализации)
        shared_nodes (dict): Отслеживает значения узлов, которые появляются в нескольких деревьях,
                             и список этих деревьев.
                             Tracks node values that appear in multiple trees.
        connections (list): Список словарей, описывающих связи между парами корневых узлов через общие узлы.
                            Заполняется методом `find_connections_between_roots`.
    Attributes:
        roots (list): A collection of root nodes to be analyzed
        forest_map (dict): Mapping of node values to their root nodes
        shared_nodes (dict): Tracks node values that appear in multiple trees
    """

    def __init__(self,
                 roots: list): # TODO: Указать тип Node после импорта
        """
        Инициализирует анализатор леса MultiRootAnalyzer.

        Параметры:
            roots (list): Список корневых узлов (экземпляров класса Node), представляющих деревья в лесу.
                          A list of root nodes (Node instances) representing the trees in the forest.
        """
        self.roots = roots  # список корневых узлов
        self.forest_map: Dict[Any, list] = {}  # node_value -> list of root_node names (Tree_i_root.value)
        self.shared_nodes: Dict[Any, list] = {}  # node_value -> [roots_that_contain_it]
        self.connections: list = [] # Инициализация атрибута connections
        self.analyze_forest() # Первичный анализ для заполнения shared_nodes

    def analyze_forest(self) -> Dict[Any, list]:
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
        all_nodes_in_trees: Dict[Any, list] = {} # node_value -> list of tree identifiers
        self.shared_nodes = {} # Очищаем перед каждым анализом

        for i, root in enumerate(self.roots):
            # TODO: Убедиться, что root имеет атрибут value (например, является объектом Node)
            if not hasattr(root, 'value'):
                # Обработка случая, если root не является ожидаемым объектом Node
                # Можно логировать ошибку или пропускать такой корень
                print(f"Warning: Root at index {i} does not have a 'value' attribute and will be skipped.")
                continue

            tree_nodes = self._get_all_nodes_in_tree(root)
            tree_identifier = f"Tree_{i}_{root.value}"

            for node_value in tree_nodes:
                if node_value not in all_nodes_in_trees:
                    all_nodes_in_trees[node_value] = []
                all_nodes_in_trees[node_value].append(tree_identifier)

        # Находим узлы, которые встречаются в нескольких деревьях
        for node_value, trees in all_nodes_in_trees.items():
            if len(trees) > 1:
                self.shared_nodes[node_value] = trees

        return all_nodes_in_trees

    def _get_all_nodes_in_tree(self, root) -> Set[Any]: # TODO: Указать тип Node
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
        nodes: Set[Any] = set()
        visited_in_current_traversal: Set[Any] = set() # Отслеживание для текущего DFS вызова

        def traverse(node): # TODO: Указать тип Node
            # TODO: Убедиться, что node имеет атрибут value и children
            if node and hasattr(node, 'value') and node.value not in visited_in_current_traversal:
                visited_in_current_traversal.add(node.value)
                nodes.add(node.value)
                if hasattr(node, 'children') and node.children:
                    for child in node.children:
                        traverse(child)
            elif node and hasattr(node, 'value') and node.value in visited_in_current_traversal:
                # Обнаружен цикл или повторное посещение в текущем обходе
                return


        traverse(root)
        return nodes

    def find_connections_between_roots(self) -> list:
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
        self.connections = [] # Очищаем перед каждым поиском
        # Предварительно получаем все узлы для каждого дерева, чтобы избежать повторных вызовов _get_all_nodes_in_tree
        nodes_per_tree: Dict[str, Set[Any]] = {}
        for i, root in enumerate(self.roots):
            if hasattr(root, 'value'):
                 tree_identifier = f"Tree_{i}_{root.value}" # Используем для ключа, чтобы был уникальным
                 nodes_per_tree[tree_identifier] = self._get_all_nodes_in_tree(root)


        root_identifiers = list(nodes_per_tree.keys())

        for i in range(len(root_identifiers)):
            for j in range(i + 1, len(root_identifiers)):
                # Извлекаем оригинальные значения корней из идентификаторов
                # Формат идентификатора: "Tree_index_originalRootValue"
                # Это немного громоздко; лучше хранить объекты Node или их исходные значения напрямую, если возможно
                original_root1_value = root_identifiers[i].split('_', 2)[-1]
                original_root2_value = root_identifiers[j].split('_', 2)[-1]

                nodes1 = nodes_per_tree[root_identifiers[i]]
                nodes2 = nodes_per_tree[root_identifiers[j]]

                common_nodes = nodes1.intersection(nodes2)

                if common_nodes:
                    self.connections.append({
                        'root1': original_root1_value,
                        'root2': original_root2_value,
                        'common_nodes': list(common_nodes),
                        'connection_type': 'shared_nodes'
                    })
        return self.connections

    def get_forest_statistics(self) -> Dict[str, Any]:
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

        stats: Dict[str, Any] = {
            'total_roots': len(self.roots),
            'trees_info': [],
            'shared_nodes': self.shared_nodes.copy() # Возвращаем копию
        }

        for i, root in enumerate(self.roots):
            if not hasattr(root, 'value'): continue # Пропуск некорректных корней

            tree_nodes = self._get_all_nodes_in_tree(root)
            tree_depth = self._get_tree_depth(root)

            stats['trees_info'].append({
                'root': root.value,
                'nodes_count': len(tree_nodes),
                'depth': tree_depth,
                'nodes': list(tree_nodes)
            })

        return stats

    def _get_tree_depth(self, root) -> int: # TODO: Указать тип Node
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
        if not root or not hasattr(root, 'value'): # Проверка на None и наличие value
            return 0

        max_depth_val = 0
        # visited_paths_dfs хранит кортежи значений узлов пути для обнаружения уже пройденных уникальных путей
        # Это важно для графов, где узел может быть достигнут разными путями, но мы не хотим зацикливаться.
        
        # queue для DFS: (node, current_depth, current_path_tuple)
        # current_path_tuple используется для обнаружения циклов на текущем пути обхода.
        queue: List[Tuple[Any, int, Tuple[Any, ...]]] = [(root, 1, (root.value,))] # TODO: Указать тип Node для root

        while queue:
            current_node, current_depth, path_tuple = queue.pop(0) # Берем из начала для BFS-подобного исследования уровней глубины
                                                                 # или queue.pop() для DFS. Для глубины чаще DFS.
                                                                 # Используем DFS (pop())

            current_node_value = current_node.value # TODO: Убедиться, что current_node имеет value
            max_depth_val = max(max_depth_val, current_depth)

            if hasattr(current_node, 'children') and current_node.children:
                for child in current_node.children:
                    # TODO: Убедиться, что child имеет value
                    if hasattr(child, 'value'):
                        child_value = child.value
                        if child_value not in path_tuple: # Проверка на цикл в текущем пути
                            new_path_tuple = path_tuple + (child_value,)
                            queue.append((child, current_depth + 1, new_path_tuple))
                        # Если child_value in path_tuple, это цикл, не идем дальше по этому пути.

        return max_depth_val

        # Старая рекурсивная реализация с более сложной защитой от циклов:
        # max_depth = 0
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

    def find_all_paths_to_node(self, target_value: Any) -> Dict[str, List[List[Any]]]:
        """
        Находит все возможные пути от любого из корневых узлов до указанного целевого узла
        во всех деревьях леса.

        Итерирует по каждому дереву в `self.roots`, вызывая `_find_paths_in_tree`
        для поиска путей к `target_value` внутри этого дерева.
        Результаты агрегируются в словарь, где ключами являются идентификаторы деревьев
        (например, "Tree_0_RootA"), а значениями — списки найденных путей.

        Параметры / Args:
            target_value (Any): Значение узла, до которого необходимо найти пути.
                                The value of the target node.

        Возвращает / Returns:
            Dict[str, List[List[Any]]]: Словарь, где ключ - это имя дерева (например, "Tree_0_A"),
                                        а значение - список путей (списков значений узлов) до целевого узла в этом дереве.
                                        A dictionary mapping tree names to lists of paths (lists of node values).
        """
        all_paths: Dict[str, List[List[Any]]] = {}

        for i, root in enumerate(self.roots):
            if not hasattr(root, 'value'): continue # Пропускаем некорректные корни
            tree_name = f"Tree_{i}_{root.value}"
            paths = self._find_paths_in_tree(root, target_value)

            if paths:
                all_paths[tree_name] = paths

        return all_paths

    def _find_paths_in_tree(self, root, target_value: Any) -> List[List[Any]]: # TODO: Указать тип Node для root
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
        all_paths_in_tree: List[List[Any]] = []

        # path_so_far - текущий путь (список значений узлов)
        # visited_in_path - множество значений узлов в текущем пути для обнаружения циклов
        # TODO: Указать тип Node для node в стеке
        stack: List[Tuple[Any, List[Any], Set[Any]]] = []
        if hasattr(root, 'value'): # Начальная проверка для root
            stack.append((root, [root.value], {root.value}))

        while stack:
            current_node, path_so_far, visited_in_path = stack.pop()

            if not hasattr(current_node, 'value'): continue

            # Если текущий узел - целевой, добавляем копию пути в результаты
            if current_node.value == target_value:
                all_paths_in_tree.append(list(path_so_far)) # list() для копии

            if hasattr(current_node, 'children') and current_node.children:
                # Обходим дочерние узлы в обратном порядке, чтобы DFS исследовал их "слева направо"
                # если рассматривать порядок добавления в стек
                for child in reversed(current_node.children):
                    if hasattr(child, 'value') and child.value not in visited_in_path:
                        new_path = path_so_far + [child.value]
                        new_visited = visited_in_path.copy()
                        new_visited.add(child.value)
                        stack.append((child, new_path, new_visited))
        return all_paths_in_tree

    def find_shortest_path_to_node(self, target_value: Any) -> Optional[Dict[str, Any]]:
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
        all_paths = self.find_all_paths_to_node(target_value)

        if not all_paths:
            return None

        shortest_path_data: Optional[Dict[str, Any]] = None
        shortest_length = float('inf')

        for tree_name, paths_in_tree in all_paths.items():
            for path in paths_in_tree:
                if len(path) < shortest_length:
                    shortest_length = len(path)
                    shortest_path_data = {
                        'tree': tree_name,
                        'path': path,
                        'length': shortest_length # Длина в количестве узлов
                    }
        return shortest_path_data

    def find_all_paths_between_nodes(self, start_value: Any, end_value: Any) -> Dict[str, List[List[Any]]]:
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
        all_paths_result: Dict[str, List[List[Any]]] = {}

        for i, root in enumerate(self.roots):
            if not hasattr(root, 'value'): continue
            tree_name = f"Tree_{i}_{root.value}"
            paths = self._find_paths_between_nodes_in_tree(root, start_value, end_value)

            if paths:
                all_paths_result[tree_name] = paths

        return all_paths_result

    def _find_paths_between_nodes_in_tree(self, root, start_value: Any, end_value: Any) -> List[List[Any]]: # TODO: Указать тип Node для root
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
        paths_found: List[List[Any]] = []
        # Стек для DFS: (node, current_path_values, visited_on_path_values, has_found_start_node)
        # TODO: Указать тип Node для node в стеке
        stack: List[Tuple[Any, List[Any], Set[Any], bool]] = []
        if hasattr(root, 'value'):
            stack.append((root, [root.value], {root.value}, root.value == start_value))


        while stack:
            current_node, path_values, visited_on_path, found_start = stack.pop()

            if not hasattr(current_node, 'value'): continue

            # Если текущий узел - это start_value, отмечаем это
            if current_node.value == start_value:
                found_start = True
                # Если start_value меняется, нужно обновить path_values и visited_on_path,
                # чтобы путь начинался с текущего start_value.
                path_values = [current_node.value]
                visited_on_path = {current_node.value}


            # Если мы уже нашли start_value и текущий узел - это end_value, то путь найден
            if found_start and current_node.value == end_value:
                paths_found.append(list(path_values)) # Добавляем копию пути

            # Продолжаем поиск в дочерних узлах
            if hasattr(current_node, 'children') and current_node.children:
                for child in reversed(current_node.children): # Обходим в обратном порядке для "естественного" DFS
                    if hasattr(child, 'value') and child.value not in visited_on_path:
                        new_path_values = path_values + [child.value] if found_start else [child.value] if child.value == start_value else []
                        # Путь строится только если found_start is True, или если child является start_value

                        if found_start or child.value == start_value: # Только если мы уже на пути от start_value или child - это start_value
                            current_found_start = found_start or (child.value == start_value)

                            new_visited_on_path = visited_on_path.copy()
                            new_visited_on_path.add(child.value)

                            # Если child это start_value и мы его еще не нашли, то path_values должен начаться с него
                            actual_new_path_values = [child.value] if (child.value == start_value and not found_start) else path_values + [child.value] if found_start else []

                            if actual_new_path_values : # Только если есть что добавлять в стек (т.е. путь валиден)
                                stack.append((child, actual_new_path_values, new_visited_on_path, current_found_start))
        return paths_found

    def print_all_paths_to_node(self, target_value: Any):
        """
        Выводит в консоль все найденные пути до указанного целевого узла.

        Использует `find_all_paths_to_node` для получения данных, затем форматирует и печатает их.
        Prints all found paths to the specified target node to the console.
        Uses `find_all_paths_to_node` to get the data, then formats and prints it.

        Параметры / Args:
            target_value (Any): Значение целевого узла. / The value of the target node.
        """
        paths = self.find_all_paths_to_node(target_value)
        print(f"\nВсе пути к узлу '{target_value}' / All paths to node '{target_value}':")

        if not paths:
            print(f"  Узел '{target_value}' не найден ни в одном дереве. / Node '{target_value}' not found in any tree.")
            return

        for tree_name, tree_paths in paths.items():
            print(f"\n  В дереве / In tree '{tree_name}':")
            if not tree_paths:
                print(f"    Нет путей к '{target_value}' в этом дереве. / No paths to '{target_value}' in this tree.")
                continue
            for i, path in enumerate(tree_paths, 1):
                print(f"    Путь {i} / Path {i}: {' -> '.join(map(str, path))}")

    def print_shortest_path_to_node(self, target_value: Any):
        """
        Выводит в консоль кратчайший путь до указанного целевого узла.

        Использует `find_shortest_path_to_node` для получения данных, затем форматирует и печатает их.
        Prints the shortest path to the specified target node to the console.
        Uses `find_shortest_path_to_node` to get the data, then formats and prints it.

        Параметры / Args:
            target_value (Any): Значение целевого узла. / The value of the target node.
        """
        shortest = self.find_shortest_path_to_node(target_value)

        print(f"\nКратчайший путь к узлу '{target_value}' / Shortest path to node '{target_value}':")
        if not shortest:
            print(f"  Узел '{target_value}' не найден ни в одном дереве. / Node '{target_value}' not found in any tree.")
            return

        print(f"  Дерево / Tree: {shortest['tree']}")
        print(f"  Путь / Path: {' -> '.join(map(str, shortest['path']))}")
        print(f"  Длина / Length: {shortest['length']} узлов / nodes")

    def print_paths_between_nodes(self, start_value: Any, end_value: Any):
        """
        Выводит в консоль все пути между двумя указанными узлами.

        Использует `find_all_paths_between_nodes` для получения данных, затем форматирует и печатает их.
        Prints all paths between two specified nodes to the console.
        Uses `find_all_paths_between_nodes` to get the data, then formats and prints it.

        Параметры / Args:
            start_value (Any): Значение начального узла. / The value of the start node.
            end_value (Any): Значение конечного узла. / The value of the end node.
        """
        paths = self.find_all_paths_between_nodes(start_value, end_value)
        print(f"\nВсе пути от '{start_value}' к '{end_value}' / All paths from '{start_value}' to '{end_value}':")

        if not paths:
            print(f"  Пути от '{start_value}' к '{end_value}' не найдены. / No paths found from '{start_value}' to '{end_value}'.")
            return

        for tree_name, tree_paths in paths.items():
            print(f"\n  В дереве / In tree '{tree_name}':")
            if not tree_paths:
                print(f"    Нет путей от '{start_value}' к '{end_value}' в этом дереве. / No paths from '{start_value}' to '{end_value}' in this tree.")
                continue
            for i, path in enumerate(tree_paths, 1):
                print(f"    Путь {i} / Path {i}: {' -> '.join(map(str, path))}")
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
    