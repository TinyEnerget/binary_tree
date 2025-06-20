"""
Этот модуль предназначен для визуализации лесов деревьев и связей между ними.
Он работает в связке с классом-анализатором (например, `MultiRootAnalyzer`
или `MultiRootAnalyzerOpt`), который предоставляет данные о структуре деревьев и их соединениях.

Основные функции:
- Печать отдельных деревьев с использованием ASCII-графики для отображения иерархии.
- Обнаружение и отображение циклов внутри деревьев во время печати.
- Визуализация всего леса, включая печать каждого дерева и списка связей между ними.
"""
from typing import Any, List, Optional, Union # Добавлен Union
from .tree_construction import Node # Импортируем Node
# Предполагаем, что MultiRootAnalyzer и MultiRootAnalyzerOpt могут быть переданы
# Для более строгой типизации можно создать общий базовый класс или Protocol для них
from .multi_root_analyzer import MultiRootAnalyzer
from .multi_root_analyzer_optimazed import MultiRootAnalyzerOpt

AnalyzerTypes = Union[MultiRootAnalyzer, MultiRootAnalyzerOpt]

class VisualizeForest:
    """
    Класс `VisualizeForest` предоставляет функциональность для текстовой визуализации
    леса деревьев и связей между ними, используя данные от класса-анализатора.
    The `VisualizeForest` class provides functionality for text-based visualization
    of a tree forest and the connections between them, using data from an analyzer class.

    Атрибуты / Attributes:
        analyzer (AnalyzerTypes): Экземпляр класса-анализатора (`MultiRootAnalyzer` или `MultiRootAnalyzerOpt`),
                                  который содержит проанализированные данные о лесе (корневые узлы, связи).
                                  An instance of an analyzer class (`MultiRootAnalyzer` or `MultiRootAnalyzerOpt`)
                                  that holds analyzed forest data (roots, connections).
    """
    def __init__(self, analyzer: AnalyzerTypes):
        """
        Инициализирует объект `VisualizeForest`.

        Параметры / Parameters:
            analyzer (AnalyzerTypes): Экземпляр анализатора (`MultiRootAnalyzer` или `MultiRootAnalyzerOpt`),
                                      который уже обработал лес и содержит атрибуты `roots` и `connections`.
                                      An analyzer instance (`MultiRootAnalyzer` or `MultiRootAnalyzerOpt`)
                                      that has processed the forest and contains `roots` and `connections` attributes.
        """
        self.analyzer: AnalyzerTypes = analyzer

    @staticmethod
    def print_tree(node: Optional[Node], level: int = 0, prefix: str = "Root: ", path: Optional[List[str]] = None) -> None:
        """
        Статический метод для рекурсивной печати одного дерева с использованием ASCII-графики.
        Static method to recursively print a single tree using ASCII graphics.

        Отображает иерархическую структуру дерева, используя отступы и специальные префиксы.
        Обнаруживает циклы в дереве, отслеживая узлы в текущем пути обхода (`path`).
        Если цикл обнаружен, он печатается, и дальнейший обход по этой ветке прекращается.

        Параметры / Parameters:
            node (Optional[Node]): Текущий узел `Node` для печати. Может быть None.
                                   The current `Node` to print. Can be None.
            level (int): Текущий уровень вложенности узла, используется для определения отступа.
                         The current nesting level of the node, used for indentation.
            prefix (str): Строковый префикс для текущего узла (например, "├── ", "└── ", "Root: ").
                          String prefix for the current node (e.g., "├── ", "└── ", "Root: ").
            path (Optional[List[str]]): Список строковых значений узлов, представляющий текущий путь от корня
                                        до родительского узла. Используется для обнаружения циклов.
                                        A list of string node values representing the current path from the root
                                        to the parent node. Used for cycle detection.
        """
        current_path: List[str] = path if path is not None else []

        if node is None:
            return # Если узел None, ничего не делаем

        # Node.value теперь всегда str по определению Node
        node_value_str = node.value

        if node_value_str in current_path:
            try:
                cycle_start_index = current_path.index(node_value_str)
                # Формируем строку, показывающую цикл
                cycle_path_display = " -> ".join(current_path[cycle_start_index:] + [node_value_str])
                print(" " * (level * 4) + prefix + node_value_str + f" [ОБНАРУЖЕН ЦИКЛ / CYCLE DETECTED: {cycle_path_display}]")
            except ValueError:
                # Этот блок ValueError не должен срабатывать, если 'in' проверка верна, но оставлен для безопасности
                print(" " * (level * 4) + prefix + node_value_str + f" [ОШИБКА В ОПРЕДЕЛЕНИИ ЦИКЛА / CYCLE DETECTION ERROR]")
            return

        print(" " * (level * 4) + prefix + node_value_str)

        if node.children: # children это List[Node]
            new_current_path = current_path + [node_value_str]
            for i, child_node in enumerate(node.children):
                extension = "├── " if i < len(node.children) - 1 else "└── "
                VisualizeForest.print_tree(child_node, level + 1, extension, new_current_path)


    def visualize_forest_connections(self, level: int = 0, prefix: str = "Root: ") -> None:
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

