#Этот код реализует анализатор леса деревьев (MultiRootAnalyzer), 
# который работает с несколькими корневыми узлами одновременно. 
# Как он работает:
# Класс принимает список корневых узлов и создает структуры 
# для отслеживания связей между деревьями.
# 1. analyze_forest() - Анализ всего леса
# Проходит по каждому дереву и собирает все узлы
# Отслеживает, в каких деревьях встречается каждый узел
# Находит узлы, которые присутствуют в нескольких деревьях
# 2. find_connections_between_roots() - Поиск связей между корнями
# Сравнивает каждую пару деревьев
# Находит общие узлы между деревьями
# Создает карту связей через общие узлы
# 3. get_forest_statistics() - Статистика леса
# Подсчитывает количество узлов в каждом дереве
# Вычисляет глубину каждого дерева
# Собирает общую статистику по лесу
# Возвращает статистику по лесу

# Imports

class MultiRootAnalyzer:
    """
    A multi-root tree forest analyzer that provides comprehensive analysis of multiple tree structures.
    
    This class enables advanced forest analysis by:
    - Tracking shared nodes across multiple trees
    - Finding connections between root nodes
    - Generating detailed forest and tree statistics
    
    Attributes:
        roots (list): A collection of root nodes to be analyzed
        forest_map (dict): Mapping of node values to their root nodes
        shared_nodes (dict): Tracks node values that appear in multiple trees
    """
        
    def __init__(self, 
                 roots: list):
        self.roots = roots  # список корневых узлов
        self.forest_map = {}  # node_value -> root_node
        self.shared_nodes = {}  # node_value -> [roots_that_contain_it]
        
    def analyze_forest(self):
        """Анализирует лес из нескольких деревьев"""
        all_nodes_in_trees = {}
        
        for i, root in enumerate(self.roots):
            tree_nodes = self._get_all_nodes_in_tree(root)
            
            for node_value in tree_nodes:
                if node_value not in all_nodes_in_trees:
                    all_nodes_in_trees[node_value] = []
                all_nodes_in_trees[node_value].append(f"Tree_{i}_{root.value}")
        
        # Находим узлы, которые встречаются в нескольких деревьях
        for node_value, trees in all_nodes_in_trees.items():
            if len(trees) > 1:
                self.shared_nodes[node_value] = trees
        
        return all_nodes_in_trees
    
    def _get_all_nodes_in_tree(self, root):
        """Получает все узлы в дереве с защитой от циклов"""
        nodes = set()
        visited = set()  # Добавляем отслеживание посещенных узлов
        def traverse(node):
            if node and node.value not in visited:
                visited.add(node.value)  # Отмечаем узел как посещенный
                nodes.add(node.value)
                if node.children:
                    for child in node.children:
                        traverse(child)
        
        traverse(root)
        return nodes
    
    def find_connections_between_roots(self):
        """Находит связи между корневыми узлами через общие узлы"""
        connections = []
        
        for i in range(len(self.roots)):
            for j in range(i + 1, len(self.roots)):
                root1, root2 = self.roots[i], self.roots[j]
                
                nodes1 = self._get_all_nodes_in_tree(root1)
                nodes2 = self._get_all_nodes_in_tree(root2)
                
                common_nodes = nodes1.intersection(nodes2)
                
                if common_nodes:
                    connections.append({
                        'root1': root1.value,
                        'root2': root2.value,
                        'common_nodes': list(common_nodes),
                        'connection_type': 'shared_nodes'
                    })
        self.connections = connections
        return connections
    
    def get_forest_statistics(self):
        """Получает статистику по лесу деревьев"""
        stats = {
            'total_roots': len(self.roots),
            'trees_info': [],
            'shared_nodes': self.shared_nodes
        }
        
        for i, root in enumerate(self.roots):
            tree_nodes = self._get_all_nodes_in_tree(root)
            tree_depth = self._get_tree_depth(root)
            
            stats['trees_info'].append({
                'root': root.value,
                'nodes_count': len(tree_nodes),
                'depth': tree_depth,
                'nodes': list(tree_nodes)
            })
        
        return stats
    
    def _get_tree_depth(self, root):
        """Вычисляет глубину дерева с защитой от циклов"""
        if not root:
            return 0
        
        max_depth = 0
        visited_paths = set()

        def dfs(node, depth, path):
            nonlocal max_depth

            if not node:
                return

            # Создаем уникальный идентификатор для текущего пути
            path_key = tuple(path + [node.value])

            if path_key in visited_paths or node.value in path:
                return

            visited_paths.add(path_key)
            max_depth = max(max_depth, depth + 1)

            if node.children:
                for child in node.children:
                    dfs(child, depth + 1, path + [node.value])
    
        dfs(root, 0, [])

        #if not root.children:
        #    return 1
        #
        #max_depth = 0
        #for child in root.children:
        #    max_depth = max(max_depth, self._get_tree_depth(child))
        
        return max_depth# + 1
    
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

    def find_connections_between_roots(self):
        """Находит связи между корневыми узлами через общие узлы"""
        connections = []
        
        for i in range(len(self.roots)):
            for j in range(i + 1, len(self.roots)):
                root1, root2 = self.roots[i], self.roots[j]
                
                nodes1 = self._get_all_nodes_in_tree(root1)
                nodes2 = self._get_all_nodes_in_tree(root2)
                
                common_nodes = nodes1.intersection(nodes2)
                
                if common_nodes:
                    connections.append({
                        'root1': root1.value,
                        'root2': root2.value,
                        'common_nodes': list(common_nodes),
                        'connection_type': 'shared_nodes'
                    })
        self.connections = connections
        return connections
    
    def find_all_paths_to_node(self, target_value):
        """
        Находит все возможные пути до указанного узла во всех деревьях леса
        
        Args:
            target_value: Значение узла, до которого нужно найти пути
            
        Returns:
            dict: Словарь с путями, сгруппированными по корневым узлам
        """
        all_paths = {}
        
        for i, root in enumerate(self.roots):
            tree_name = f"Tree_{i}_{root.value}"
            paths = self._find_paths_in_tree(root, target_value)
            
            if paths:
                all_paths[tree_name] = paths
        
        return all_paths
    
    def _find_paths_in_tree(self, root, target_value):
        """
        Находит все пути до узла в конкретном дереве
        
        Args:
            root: Корневой узел дерева
            target_value: Значение искомого узла
            
        Returns:
            list: Список всех путей до узла
        """
        all_paths = []
        
        def dfs(node, current_path, visited):
            if not node:
                return
            
            # Проверяем циклы
            if node.value in visited:
                return
            
            current_path.append(node.value)
            visited.add(node.value)
            
            # Если нашли целевой узел, сохраняем путь
            if node.value == target_value:
                all_paths.append(current_path.copy())
            
            # Продолжаем поиск в дочерних узлах
            if node.children:
                for child in node.children:
                    dfs(child, current_path, visited.copy())
            
            current_path.pop()
        
        dfs(root, [], set())
        return all_paths
    
    def find_shortest_path_to_node(self, target_value):
        """
        Находит кратчайший путь до узла среди всех деревьев
        
        Args:
            target_value: Значение искомого узла
            
        Returns:
            dict: Информация о кратчайшем пути
        """
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
        """
        Находит все пути между двумя узлами в лесу
        
        Args:
            start_value: Значение начального узла
            end_value: Значение конечного узла
            
        Returns:
            dict: Все пути между узлами, сгруппированные по деревьям
        """
        all_paths = {}
        
        for i, root in enumerate(self.roots):
            tree_name = f"Tree_{i}_{root.value}"
            paths = self._find_paths_between_nodes_in_tree(root, start_value, end_value)
            
            if paths:
                all_paths[tree_name] = paths
        
        return all_paths
    
    def _find_paths_between_nodes_in_tree(self, root, start_value, end_value):
        """
        Находит все пути между двумя узлами в конкретном дереве
        """
        all_paths = []
        
        def dfs(node, current_path, visited, found_start):
            if not node:
                return
            
            if node.value in visited:
                return
            
            current_path.append(node.value)
            visited.add(node.value)
            
            # Проверяем, нашли ли начальный узел
            if node.value == start_value:
                found_start = True
            
            # Если нашли конечный узел и уже прошли через начальный
            if node.value == end_value and found_start:
                all_paths.append(current_path.copy())
            
            # Продолжаем поиск в дочерних узлах
            if node.children:
                for child in node.children:
                    dfs(child, current_path, visited.copy(), found_start)
            
            current_path.pop()
        
        dfs(root, [], set(), False)
        return all_paths
    
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
    