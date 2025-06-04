# Описание: Класс работает в связке с MultiRootAnalyzer 
# и использует его данные для визуализации.
# print_tree() - Статический метод для печати дерева
# Как работает:
#Рекурсивно обходит дерево
#Использует отступы (level * 4 пробела) для показа уровня вложенности
#Применяет ASCII-символы для красивого отображения:
#├── для промежуточных узлов
#└── для последнего узла на уровне
#2. visualize_forest_connections() - Главный метод визуализации

# Imports

class VisualizeForest:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    @staticmethod    
    def print_tree(node, level=0, prefix="Root: ", path=None):
        if path is None:
            path = []
        
        if node is not None:
            # Проверяем циклы
            if node.value in path:
                cycle_start = path.index(node.value)
                cycle_path = " -> ".join(map(str, path[cycle_start:] + [node.value]))
                print(" " * (level * 4) + prefix + str(node.value) + f" [CYCLE: {cycle_path}]")
                return
            
            print(" " * (level * 4) + prefix + str(node.value))

            if node.children:
                # Добавляем текущий узел в путь
                new_path = path + [node.value]
                # Рекурсивно выводим детей
                for i, child in enumerate(node.children):
                    extension = "├── " if i < len(node.children) - 1 else "└── "
                    VisualizeForest.print_tree(child, level + 1, extension, new_path)

    def visualize_forest_connections(self, level=0, prefix="Root: "):
        """Визуализирует связи в лесу деревьев"""
        print("=== ВИЗУАЛИЗАЦИЯ ЛЕСА ===\n")
        roots = self.analyzer.roots
        connections = getattr(self.analyzer, 'connections', [])

        # Print each root and its connections
        for i, root in enumerate(roots):
            print(f"Дерево {i+1} (корень: {root.value}):")
            VisualizeForest.print_tree(root, level, prefix)
            print()

        # Analysis of connections and print them
        if connections:
            print("НАЙДЕННЫЕ СВЯЗИ:")
            for conn in connections:
                print(f"{conn['root1']} ↔ {conn['root2']}")
                print(f"Общие узлы: {', '.join(conn['common_nodes'])}")
                print()
        else:
            print("Связей между деревьями не найдено")

