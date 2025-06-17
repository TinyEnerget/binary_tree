"""
Этот модуль предназначен для визуализации лесов деревьев и связей между ними.
Он работает в связке с классом-анализатором (например, `MultiRootAnalyzer`
или `MultiRootAnalyzerOpt`), который предоставляет данные о структуре деревьев и их соединениях.

Основные функции:
- Печать отдельных деревьев с использованием ASCII-графики для отображения иерархии.
- Обнаружение и отображение циклов внутри деревьев во время печати.
- Визуализация всего леса, включая печать каждого дерева и списка связей между ними.
"""
from typing import Any, List, Optional # Импортируем необходимые типы

# Предполагается, что класс Node определен где-то и имеет атрибуты 'value' и 'children'
# from .tree_construction import Node # Пример, если Node в том же пакете

class VisualizeForest:
    """
    Класс `VisualizeForest` предоставляет функциональность для текстовой визуализации
    леса деревьев и связей между ними, используя данные от класса-анализатора.
    The `VisualizeForest` class provides functionality for text-based visualization
    of a tree forest and the connections between them, using data from an analyzer class.

    Атрибуты / Attributes:
        analyzer (Any): Экземпляр класса-анализатора (например, `MultiRootAnalyzer`),
                        который содержит проанализированные данные о лесе (корневые узлы, связи).
                        An instance of an analyzer class (e.g., `MultiRootAnalyzer`)
                        that holds analyzed forest data (roots, connections).
    """
    def __init__(self, analyzer: Any):
        """
        Инициализирует объект `VisualizeForest`.

        Параметры / Parameters:
            analyzer (Any): Экземпляр анализатора (например, `MultiRootAnalyzer` или `MultiRootAnalyzerOpt`),
                            который уже обработал лес и содержит атрибуты `roots` и `connections`.
                            An analyzer instance that has processed the forest and contains
                            `roots` and `connections` attributes.
        """
        self.analyzer = analyzer

    @staticmethod
    def print_tree(node: Any, level: int = 0, prefix: str = "Root: ", path: Optional[List[Any]] = None):
        """
        Статический метод для рекурсивной печати одного дерева с использованием ASCII-графики.
        Static method to recursively print a single tree using ASCII graphics.

        Отображает иерархическую структуру дерева, используя отступы и специальные префиксы.
        Обнаруживает циклы в дереве, отслеживая узлы в текущем пути обхода (`path`).
        Если цикл обнаружен, он печатается, и дальнейший обход по этой ветке прекращается.

        Параметры / Parameters:
            node (Any): Текущий узел для печати (ожидается объект с атрибутами 'value' и 'children').
                        The current node to print (expected to be an object with 'value' and 'children' attributes).
            level (int): Текущий уровень вложенности узла, используется для определения отступа.
                         The current nesting level of the node, used for indentation.
            prefix (str): Строковый префикс для текущего узла (например, "├── ", "└── ", "Root: ").
                          String prefix for the current node (e.g., "├── ", "└── ", "Root: ").
            path (Optional[List[Any]]): Список значений узлов, представляющий текущий путь от корня
                                        до родительского узла. Используется для обнаружения циклов.
                                        A list of node values representing the current path from the root
                                        to the parent node. Used for cycle detection.
        """
        if path is None:
            path = [] # Инициализация пустого пути, если он не передан

        # Проверка, что узел существует и имеет атрибут 'value'
        if node is not None and hasattr(node, 'value'):
            # Проверка на циклы: если значение текущего узла уже есть в 'path'
            if node.value in path:
                try:
                    cycle_start_index = path.index(node.value)
                    # Формируем строку, показывающую цикл
                    cycle_path_str = " -> ".join(map(str, path[cycle_start_index:] + [node.value]))
                    print(" " * (level * 4) + prefix + str(node.value) + f" [ОБНАРУЖЕН ЦИКЛ / CYCLE DETECTED: {cycle_path_str}]")
                except ValueError: # На случай, если node.value не найден в path, хотя проверка 'in' прошла
                    print(" " * (level * 4) + prefix + str(node.value) + f" [ОШИБКА В ОПРЕДЕЛЕНИИ ЦИКЛА / CYCLE DETECTION ERROR]")
                return # Прерываем дальнейший обход этой ветки

            print(" " * (level * 4) + prefix + str(node.value))

            # Проверка, что узел имеет дочерние элементы
            if hasattr(node, 'children') and node.children:
                # Добавляем значение текущего узла в путь для передачи дочерним узлам
                new_path = path + [node.value]
                # Рекурсивно выводим дочерние узлы
                for i, child in enumerate(node.children):
                    # Определяем префикс для дочернего узла: "├── " для промежуточных, "└── " для последнего
                    extension = "├── " if i < len(node.children) - 1 else "└── "
                    VisualizeForest.print_tree(child, level + 1, extension, new_path)
        elif node is not None:
             print(" " * (level * 4) + prefix + "[Узел без значения / Node without value]")
        # Если node is None, ничего не печатаем


    def visualize_forest_connections(self, level: int = 0, prefix: str = "Root: "):
        """
        Визуализирует весь лес деревьев и связи между ними.
        Visualizes the entire tree forest and the connections between them.

        Сначала печатает каждое дерево в лесу, используя статический метод `print_tree`.
        Затем, если анализатор нашел связи между деревьями (атрибут `connections` у `self.analyzer`),
        эти связи выводятся в консоль, показывая, между какими корнями и через какие общие узлы
        они установлены.

        Параметры / Parameters:
            level (int): Начальный уровень отступа для печати корневых узлов.
                         Initial indentation level for printing root nodes.
            prefix (str): Начальный префикс для печати корневых узлов.
                          Initial prefix for printing root nodes.
        """
        print("=== ВИЗУАЛИЗАЦИЯ ЛЕСА / FOREST VISUALIZATION ===\n")

        # Проверка наличия self.analyzer и атрибута roots
        if not hasattr(self.analyzer, 'roots'):
            print("Анализатор не содержит информации о корнях деревьев. / Analyzer does not contain root information.")
            return

        roots = self.analyzer.roots
        # Получаем связи, если они есть, иначе пустой список
        connections = getattr(self.analyzer, 'connections', [])

        # Печать каждого дерева
        for i, root in enumerate(roots):
            # Проверка, что root является ожидаемым объектом узла
            if hasattr(root, 'value'):
                print(f"Дерево {i+1} (корень / root: {root.value}):")
                VisualizeForest.print_tree(root, level, prefix, path=[]) # path инициализируется здесь для каждого дерева
            else:
                print(f"Дерево {i+1} (некорректный корневой узел / invalid root node)")
            print() # Пустая строка для разделения деревьев

        # Анализ и печать связей
        if connections:
            print("НАЙДЕННЫЕ СВЯЗИ МЕЖДУ ДЕРЕВЬЯМИ / CONNECTIONS FOUND BETWEEN TREES:")
            for conn in connections:
                # Проверка наличия ключей в словаре conn
                root1_val = conn.get('root1', 'N/A')
                root2_val = conn.get('root2', 'N/A')
                common_nodes_list = conn.get('common_nodes', [])

                print(f"  {root1_val} ↔ {root2_val}")
                print(f"    Общие узлы / Common nodes: {', '.join(map(str, common_nodes_list))}")
                print()
        else:
            print("Связей между деревьями не найдено. / No connections found between trees.")

