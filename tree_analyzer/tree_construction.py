"""
Этот модуль реализует базовую структуру узла дерева (Node)
с методами для построения и отображения древовидных структур.

Класс Node является основой древовидной структуры.
Ключевые особенности:
- Каждый узел хранит значение (value) и список дочерних узлов (children).
- Поддерживаются n-арные деревья, то есть узел может иметь любое количество дочерних узлов.

Методы управления структурой:
- add_child(): Добавление дочернего узла к текущему узлу.
- remove_child(): Удаление дочернего узла из текущего узла.
- print_tree(): Вывод древовидной структуры в консоль.
    - Осуществляет рекурсивный обход дерева в глубину.
    - Использует отступы (level * 4 пробела) для каждого уровня вложенности.
    - Применяет ASCII-графику для визуализации связей:
        - '├──' для промежуточных узлов.
        - '└──' для последнего узла на данном уровне.
        - Префикс "Root: " используется для корневого узла.

TODO: Добавить методы для проверки входных данных и обработки ошибок.
"""

# Imports

class Node:
    """
    Представляет узел в древовидной структуре данных со значением и дочерними узлами.
    Represents a node in a tree data structure with a value and child nodes.

    Атрибуты:
        value (str): Значение, хранящееся в узле.
        children (list): Список дочерних узлов, связанных с этим узлом.
    Attributes:
        value (str): The value stored in the node.
        children (list): A list of child nodes connected to this node.

    Методы:
        add_child(child_node): Добавляет дочерний узел к списку дочерних узлов текущего узла.
        remove_child(child_node): Удаляет указанный дочерний узел из списка дочерних узлов текущего узла.
    Methods:
        add_child(child_node): Adds a child node to the current node's children.
        remove_child(child_node): Removes a specified child node from the current node's children.
    """

    def __init__(self,
                 value: str):
        """
        Инициализирует новый узел с заданным значением.

        Параметры:
            value (str): Значение, которое будет присвоено узлу.
        """
        self.value = value # Наименование узла
        self.children = [] # Список дочерних узлов

    def add_child(self, child_node):
        """
        Добавляет дочерний узел к текущему узлу.

        Параметры:
            child_node (Node): Узел, который будет добавлен как дочерний.
        """
        self.children.append(child_node)

    def remove_child(self, child_node):
        """
        Удаляет дочерний узел из текущего узла.

        Параметры:
            child_node (Node): Узел, который будет удален из дочерних.
        """
        self.children.remove(child_node)

    def print_tree(self, level=0, prefix="Root: "):
        """
        Выводит древовидную структуру в консоль, начиная с текущего узла.

        Параметры:
            level (int): Текущий уровень вложенности узла (используется для отступов).
            prefix (str): Префикс строки, используемый для визуализации структуры дерева (например, "├── ", "└── ").
        """
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

