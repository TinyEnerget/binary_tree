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
        """Получает все узлы в дереве"""
        nodes = set()
        
        def traverse(node):
            if node:
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
        """Вычисляет глубину дерева"""
        if not root:
            return 0
        
        if not root.children:
            return 1
        
        max_depth = 0
        for child in root.children:
            max_depth = max(max_depth, self._get_tree_depth(child))
        
        return max_depth + 1
    
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
    root_1.add_child(node_e)
    root_1.add_child(node_f)
    root_2.add_child(node_g)
    root_2.add_child(node_k)
    root_3.add_child(node_l)
    root_3.add_child(node_m)
    root_3.add_child(node_n)
    node_f.add_child(node_g)
    node_f.add_child(node_k)
    node_d.add_child(node_o)
    node_o.add_child(node_g)
    node_o.add_child(node_m)
    
    # Анализ нескольких корней
    multi_analyzer = MultiRootAnalyzer([root_1, root_2, root_3])
    multi_analyzer.print_forest_statistics()
    multi_analyzer.print_shared_nodes()
    multi_analyzer.print_connections_between_roots()

    # Визуализация леса
    from visualize_forest_connection import VisualizeForest
    VisualizeForest(multi_analyzer).visualize_forest_connections()
    