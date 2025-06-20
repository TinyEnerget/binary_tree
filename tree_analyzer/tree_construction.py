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
from typing import List, Optional, Any # Any пока оставим, если value может быть не только str

# Imports

class Node:
    """
    Представляет узел в древовидной структуре данных со значением и дочерними узлами.
    Represents a node in a tree data structure with a value and child nodes.

    Атрибуты / Attributes:
        value (str): Значение, хранящееся в узле. Предполагается строковым,
                     так как ID элементов обычно строки.
                     The value stored in the node. Assumed to be a string,
                     as element IDs are typically strings.
        children (List['Node']): Список дочерних узлов (экземпляров `Node`), связанных с этим узлом.
                                 A list of child nodes (`Node` instances) connected to this node.
    """

    def __init__(self, value: str):
        """
        Инициализирует новый узел с заданным значением.
        Initializes a new node with the given value.

        Параметры / Parameters:
            value (str): Значение, которое будет присвоено узлу. Ожидается строка.
                         The value to be assigned to the node. Expected to be a string.
        """
        self.value: str = value
        self.children: List['Node'] = []

    def add_child(self, child_node: 'Node') -> None:
        """
        Добавляет дочерний узел к текущему узлу.
        Adds a child node to the current node.

        Параметры / Parameters:
            child_node ('Node'): Узел (экземпляр `Node`), который будет добавлен как дочерний.
                                The node (`Node` instance) to be added as a child.
        """
        if not isinstance(child_node, Node):
            # Можно добавить более строгую проверку или логирование, если тип не Node
            # For now, assuming child_node will always be a Node instance due to type hint.
            pass
        self.children.append(child_node)

    def remove_child(self, child_node: 'Node') -> None:
        """
        Удаляет указанный дочерний узел из списка дочерних узлов текущего узла.
        Removes the specified child node from the current node's list of children.

        Если дочерний узел не найден в списке, метод вызовет `ValueError`.
        If the child node is not found in the list, the method will raise a `ValueError`.

        Параметры / Parameters:
            child_node ('Node'): Узел (экземпляр `Node`), который должен быть удален.
                                The node (`Node` instance) to be removed.
        Выбрасывает / Raises:
            ValueError: Если `child_node` не является дочерним узлом.
                        If `child_node` is not a child of this node.
        """
        try:
            self.children.remove(child_node)
        except ValueError:
            # Логирование или специфическая обработка, если узел не найден
            # logger.warning(f"Попытка удалить несуществующий дочерний узел: {child_node.value} из родителя {self.value}")
            raise # Перевыбрасываем ValueError, чтобы поведение было стандартным

    def print_tree(self, level: int = 0, prefix: str = "Root: ") -> None:
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

