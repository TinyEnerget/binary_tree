# Этот код реализует базовую структуру узла дерева (Node) 
# с методами для построения и отображения древовидных структур.
# Как он работает:
# Класс Node - Основа древовидной структуры
# Особенности:
#   Каждый узел хранит значение (value) и список детей (children)
#   Это не бинарное дерево - узел может иметь любое количество детей
#   Структура поддерживает n-арные деревья
# Методы управления структурой
# 1. add_child() - Добавление дочернего узла к текущему узлу
# 2. remove_child() - Удаление дочернего узла из текущего узла
# 3. print_tree() - Вывод древовидной структуры в консоль
#   Как работает:
#       Рекурсивный обход дерева в глубину
#       Отступы: level * 4 пробела для каждого уровня
#       ASCII-графика:
#       ├── для промежуточных узлов
#       └── для последнего узла на уровне
#       Префиксы: "Root: " для корня, затем символы веток
## TODO: Добавить методы для проверки входных данных и обработки ошибок

# Imports

class Node:
    """
    Represents a node in a tree data structure with a value and child nodes.
    
    Attributes:
        value (str): The value stored in the node.
        children (list): A list of child nodes connected to this node.
    
    Methods:
        add_child(child_node): Adds a child node to the current node's children.
        remove_child(child_node): Removes a specified child node from the current node's children.
    """
        
    def __init__(self, 
                 value: str):
        self.value = value # Наименование узла 
        self.children = [] # Список дочерних узлов

    def add_child(self, child_node):
        self.children.append(child_node)

    def remove_child(self, child_node):
        self.children.remove(child_node)

    def print_tree(self, level=0, prefix="Root: "):
        if self.value is not None:
            print(" " * (level * 4) + prefix + str(self.value))
            if self.children:
                for i, child in enumerate(self.children):
                    extension = "├── " if i < len(self.children) - 1 else "└── "
                    Node.print_tree(child, level + 1, extension)


# Use example
if __name__ == '__main__':
    root = Node('root')
    child1 = Node('child1')
    child2 = Node('child2')
    root.add_child(child1)
    root.add_child(child2)
    root.print_tree()
    print(root.value)

