"""
Этот модуль определяет иерархию классов-анализаторов для различных типов
элементов электрической сети. Каждый анализатор инкапсулирует логику,
специфичную для определенного типа элемента, такую как определение его
топологической роли (например, является ли он корневым узлом), поиск
дочерних элементов и определение направленности.

Основным является абстрактный базовый класс `ElementAnalyzer`, который
определяет общий интерфейс для всех конкретных анализаторов.

This module defines a hierarchy of analyzer classes for various types of
electrical network elements. Each analyzer encapsulates logic specific
to a particular element type, such as determining its topological role
(e.g., whether it is a root node), finding its children, and
determining its directionality.

The core is the abstract base class `ElementAnalyzer`, which defines
a common interface for all concrete analyzers.
"""
from abc import ABC, abstractmethod
from typing import List, Union, TYPE_CHECKING

# Отложенный импорт для NetworkElement, ElementType, NetworkModel используется только для проверки типов,
# чтобы избежать циклических зависимостей во время выполнения.
# Deferred import for NetworkElement, ElementType, NetworkModel is used only for type checking
# to avoid circular dependencies at runtime.
# from .models import NetworkElement, ElementType, NetworkModel # Закомментировано, т.к. используется через TYPE_CHECKING

import logging
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .models import NetworkElement, ElementType, NetworkModel # Импорты для статической типизации / Imports for static typing

class ElementAnalyzer(ABC):
    """
    Абстрактный базовый класс (интерфейс) для анализаторов элементов электрической сети.
    Abstract base class (interface) for analyzers of electrical network elements.

    Определяет контракт, которому должны следовать все конкретные анализаторы элементов.
    Каждый анализатор отвечает за предоставление информации о топологических свойствах
    элемента определенного типа, таких как его тип, является ли он корневым,
    каковы его дочерние элементы и является ли он направленным.
    Defines the contract that all concrete element analyzers must follow.
    Each analyzer is responsible for providing information about the topological
    properties of an element of a specific type, such as its type, whether it is
    a root, what its children are, and whether it is directional.
    """

    @abstractmethod
    def get_element_type(self) -> Union['ElementType', str]:
        """
        Абстрактный метод для получения типа элемента, который обрабатывает данный анализатор.
        Abstract method to get the element type that this analyzer handles.

        Возвращает / Returns:
            Union['ElementType', str]: Тип элемента (член перечисления `ElementType` из `models.py`
                                       или строка для пользовательских/неизвестных типов).
                                       The element type (an `ElementType` enum member from `models.py`
                                       or a string for custom/unknown types).
        """
        pass

    @abstractmethod
    def is_root(self, element: 'NetworkElement') -> bool:
        """
        Абстрактный метод для определения, является ли данный элемент корневым в топологии сети.
        Abstract method to determine if the given element is a root in the network topology.

        Параметры / Parameters:
            element ('NetworkElement'): Экземпляр элемента сети для анализа.
                                       The network element instance to analyze.

        Возвращает / Returns:
            bool: True, если элемент считается корневым, иначе False.
                  True if the element is considered a root, False otherwise.
        """
        pass

    @abstractmethod
    def get_children(self, element: 'NetworkElement', model: 'NetworkModel') -> List[str]:
        """
        Абстрактный метод для получения списка идентификаторов дочерних элементов для данного элемента.
        Abstract method to get a list of child element identifiers for the given element.

        Логика определения дочерних элементов зависит от типа элемента и общей структуры модели.
        The logic for determining children depends on the element type and the overall model structure.

        Параметры / Parameters:
            element ('NetworkElement'): Элемент сети, для которого ищутся дочерние элементы.
                                       The network element for which children are being sought.
            model ('NetworkModel'): Полная модель сети, содержащая все элементы и их соединения.
                                    The complete network model containing all elements and their connections.

        Возвращает / Returns:
            List[str]: Список строковых идентификаторов дочерних элементов.
                       A list of string identifiers of child elements.
        """
        pass

    @abstractmethod
    def is_directional(self) -> bool:
        """
        Абстрактный метод для определения, является ли тип элемента, обрабатываемый этим анализатором, направленным.
        Abstract method to determine if the element type handled by this analyzer is directional.

        Направленные элементы обычно имеют определенное начало и конец (например, линии электропередачи, трансформаторы).
        Directional elements typically have a defined start and end (e.g., transmission lines, transformers).

        Возвращает / Returns:
            bool: True, если тип элемента направленный, иначе False.
                  True if the element type is directional, False otherwise.
        """
        pass


class SystemAnalyzer(ElementAnalyzer):
    """
    Анализатор для элементов типа "Энергосистема" (`ElementType.SYSTEM`).
    Analyzer for "Power System" (`ElementType.SYSTEM`) elements.

    Энергосистемы обычно рассматриваются как корневые элементы в модели сети.
    Power systems are typically considered root elements in a network model.
    """

    def get_element_type(self) -> 'ElementType':
        """
        Возвращает тип элемента, обрабатываемый этим анализатором.
        Returns the element type handled by this analyzer.

        Возвращает / Returns:
            'ElementType': Всегда `ElementType.SYSTEM`.
                           Always `ElementType.SYSTEM`.
        """
        from .models import ElementType # Импорт внутри метода для избежания циклических зависимостей при загрузке модуля
        return ElementType.SYSTEM

    def is_root(self, element: 'NetworkElement') -> bool:
        """
        Определяет, является ли элемент энергосистемы корневым.
        Determines if a power system element is a root.

        Параметры / Parameters:
            element ('NetworkElement'): Анализируемый элемент энергосистемы.
                                       The power system element being analyzed.

        Возвращает / Returns:
            bool: Всегда True, так как энергосистемы считаются корневыми.
                  Always True, as power systems are considered roots.
        """
        return True

    def get_children(self, element: 'NetworkElement', model: 'NetworkModel') -> List[str]:
        """
        Определяет дочерние элементы для энергосистемы.
        Determines child elements for a power system.

        Дочерними элементами энергосистемы считаются все узлы (шины),
        к которым она непосредственно подключена согласно карте соединений `model.node_connections`.
        Child elements of a power system are considered to be all nodes (buses)
        to which it is directly connected according to the `model.node_connections` map.

        Параметры / Parameters:
            element ('NetworkElement'): Элемент энергосистемы.
                                       The power system element.
            model ('NetworkModel'): Модель сети.
                                    The network model.

        Возвращает / Returns:
            List[str]: Список ID шин (узлов), подключенных к данной энергосистеме.
                       A list of bus (node) IDs connected to this power system.
        """
        children_ids: List[str] = []
        # Итерируемся по всем узлам в модели, которые имеют соединения
        for node_id, connected_elements_at_node in model.node_connections.items():
            # Если ID текущего элемента (энергосистемы) есть в списке подключенных к узлу элементов,
            # то этот узел (шина) является дочерним для энергосистемы.
            if element.id in connected_elements_at_node:
                # Убедимся, что сам узел (шина) существует как элемент в модели, если это необходимо
                # (хотя здесь мы просто возвращаем ID узла/шины).
                # Проверяем, является ли node_id также элементом типа BUS, если такая логика нужна.
                # В данном контексте, node_id это ID шины.
                bus_element = model.get_element(node_id)
                if bus_element and bus_element.element_type.value == "bus": # Используем .value для сравнения со строкой, если ElementType это Enum
                     children_ids.append(node_id)
                elif not bus_element: # Если узел не найден как элемент (маловероятно, если он ключ в node_connections)
                     logger.debug(f"Узел {node_id}, подключенный к системе {element.id}, не найден как элемент.")

        logger.debug(f"Для системы {element.id} найдены дочерние шины: {children_ids} / For system {element.id} found child buses: {children_ids}")
        return children_ids

    def is_directional(self) -> bool:
        """
        Определяет, является ли энергосистема направленным элементом.
        Determines if a power system is a directional element.

        Возвращает / Returns:
            bool: Всегда False, так как энергосистемы обычно не считаются направленными
                  в контексте определения дочерних элементов таким образом.
                  Always False, as power systems are generally not considered directional
                  in the context of determining children this way.
        """
        return False


class BusAnalyzer(ElementAnalyzer):
    """
    Анализатор для элементов типа "Шина" (`ElementType.BUS`).
    Analyzer for "Bus" (`ElementType.BUS`) elements.

    Шины являются центральными точками соединения в сети. Их дочерними элементами
    могут быть различные подключенные компоненты, такие как линии, трансформаторы,
    нагрузки или генераторы. Для направленных элементов, подключенных к шине,
    важно определить, является ли шина начальной точкой для этого элемента.
    Buses are central connection points in a network. Their children can be
    various connected components like lines, transformers, loads, or generators.
    For directional elements connected to a bus, it's important to determine
    if the bus is the starting point for that element.
    """

    def get_element_type(self) -> 'ElementType':
        """
        Возвращает тип элемента, обрабатываемый этим анализатором.
        Returns the element type handled by this analyzer.

        Возвращает / Returns:
            'ElementType': Всегда `ElementType.BUS`. / Always `ElementType.BUS`.
        """
        from .models import ElementType # Импорт внутри метода
        return ElementType.BUS

    def is_root(self, element: 'NetworkElement') -> bool:
        """
        Определяет, является ли шина корневым элементом.
        Determines if a bus element is a root.

        Параметры / Parameters:
            element ('NetworkElement'): Анализируемый элемент шины.
                                       The bus element being analyzed.

        Возвращает / Returns:
            bool: Всегда False, так как шины обычно не являются корневыми элементами
                  в контексте построения ориентированного дерева от источника питания.
                  Always False, as buses are typically not root elements in the context
                  of building a directed tree from a power source.
        """
        return False

    def get_children(self, element: 'NetworkElement', model: 'NetworkModel') -> List[str]:
        """
        Определяет дочерние элементы для шины.
        Determines child elements for a bus.

        Дочерними считаются:
        - Направленные элементы (линии, трансформаторы), для которых данная шина является начальным узлом.
        - Ненаправленные элементы типа "Нагрузка" (`LOAD`) или "Генератор" (`GENERATOR`), подключенные к шине.
        - Системные элементы (`SYSTEM`) не считаются дочерними для шины, так как они обычно являются родителями.
        Children are considered to be:
        - Directional elements (lines, transformers) for which this bus is the starting node.
        - Non-directional elements of type "Load" (`LOAD`) or "Generator" (`GENERATOR`) connected to the bus.
        - System elements (`SYSTEM`) are not considered children of a bus, as they are typically parents.

        Параметры / Parameters:
            element ('NetworkElement'): Элемент шины.
                                       The bus element.
            model ('NetworkModel'): Модель сети.
                                    The network model.

        Возвращает / Returns:
            List[str]: Список ID дочерних элементов, подключенных к данной шине.
                       A list of IDs of child elements connected to this bus.
        """
        from .models import ElementType # Импорт внутри метода для доступа к ElementType.SYSTEM и др.

        # Проверяем, есть ли вообще информация о соединениях для данной шины (element.id)
        # element.id здесь - это ID шины, который также является ключом в model.node_connections
        if not hasattr(element, 'id') or element.id not in model.node_connections:
            logger.debug(f"Для шины {getattr(element, 'id', 'UNKNOWN_BUS_ID')} не найдено соединений в model.node_connections. / No connections found for bus {getattr(element, 'id', 'UNKNOWN_BUS_ID')} in model.node_connections.")
            return []

        children_ids: List[str] = []
        # Итерируемся по ID элементов, подключенных к данной шине
        for connected_element_id in model.node_connections[element.id]:
            connected_element = model.get_element(connected_element_id)

            if not connected_element:
                logger.warning(f"Элемент с ID '{connected_element_id}', подключенный к шине '{element.id}', не найден в модели. / Element with ID '{connected_element_id}' connected to bus '{element.id}' not found in model.")
                continue

            # Системные элементы не могут быть дочерними для шины, они - родители.
            if connected_element.element_type == ElementType.SYSTEM:
                continue

            analyzer = model.get_analyzer(connected_element.element_type)
            if not analyzer:
                logger.warning(f"Анализатор для элемента типа '{connected_element.element_type}' (ID: {connected_element_id}) не найден. Пропуск. / Analyzer for element type '{connected_element.element_type}' (ID: {connected_element_id}) not found. Skipping.")
                continue

            if analyzer.is_directional():
                # Для направленных элементов, шина должна быть их начальным узлом
                if self._is_start_node(element, connected_element):
                    children_ids.append(connected_element_id)
            # Для ненаправленных элементов (кроме шин и систем, которые обрабатываются иначе)
            # таких как нагрузки и генераторы, они считаются дочерними, если подключены к шине.
            elif connected_element.element_type in [ElementType.LOAD, ElementType.GENERATOR]:
                children_ids.append(connected_element_id)
            # Другие типы ненаправленных элементов (если таковые появятся) здесь не добавляются как дочерние автоматически.
            # Например, другая шина, подключенная к этой шине через выключатель, будет обработана отдельно.

        logger.debug(f"Для шины {element.id} найдены дочерние элементы: {children_ids} / For bus {element.id} found child elements: {children_ids}")
        return children_ids

    def _is_start_node(self, bus_element: 'NetworkElement', connected_element: 'NetworkElement') -> bool:
        """
        Определяет, является ли узел данной шины (`bus_element`) начальным узлом
        для подключенного к ней направленного элемента (`connected_element`).
        Determines if the node of this bus (`bus_element`) is the starting node
        for a directional element (`connected_element`) connected to it.

        Предполагается, что у шины в `bus_element.nodes` есть один ID узла,
        а у направленного элемента в `connected_element.nodes` первый элемент списка
        является начальным узлом.
        It is assumed that the bus in `bus_element.nodes` has one node ID,
        and for a directional element in `connected_element.nodes`, the first
        element in the list is its starting node.

        Параметры / Parameters:
            bus_element ('NetworkElement'): Элемент шины.
                                           The bus element.
            connected_element ('NetworkElement'): Подключенный (предположительно направленный) элемент.
                                                  The connected (presumably directional) element.

        Возвращает / Returns:
            bool: True, если узел шины совпадает с начальным узлом `connected_element`, иначе False.
                  True if the bus node matches the starting node of `connected_element`, False otherwise.
        """
        # У шины обычно один узел в списке nodes, который и является ее идентификатором как точки подключения.
        if not bus_element.nodes:
            logger.warning(f"Элемент шины '{bus_element.id}' не имеет определенных узлов. / Bus element '{bus_element.id}' has no defined nodes.")
            return False
        bus_node_id = bus_element.nodes[0] # ID узла, который представляет шину

        # У направленного элемента первый узел в списке nodes считается начальным.
        if not connected_element.nodes or len(connected_element.nodes) == 0:
            logger.warning(f"Подключенный элемент '{connected_element.id}' не имеет определенных узлов. / Connected element '{connected_element.id}' has no defined nodes.")
            return False # Невозможно определить начальный узел
        
        # Сравниваем ID узла шины с ID первого (начального) узла подключенного элемента
        return bus_node_id == connected_element.nodes[0]

    def is_directional(self) -> bool:
        """
        Определяет, является ли шина направленным элементом.
        Determines if a bus is a directional element.

        Возвращает / Returns:
            bool: Всегда False, так как шины не являются направленными.
                  Always False, as buses are not directional.
        """
        return False


class DirectionalElementAnalyzer(ElementAnalyzer):
    """
    Базовый абстрактный анализатор для направленных элементов сети, таких как линии и трансформаторы.
    Base abstract analyzer for directional network elements, such as lines and transformers.

    Направленные элементы имеют определенное начало и конец. Дочерним элементом
    для такого элемента обычно является шина, подключенная к его конечному узлу.
    Directional elements have a defined start and end. The child element
    for such an element is typically the bus connected to its end node.
    """

    @abstractmethod # Конкретные подклассы все еще должны реализовывать get_element_type
    def get_element_type(self) -> 'ElementType':
        pass

    def is_root(self, element: 'NetworkElement') -> bool:
        """
        Определяет, является ли направленный элемент корневым.
        Determines if a directional element is a root.

        Параметры / Parameters:
            element ('NetworkElement'): Анализируемый направленный элемент.
                                       The directional element being analyzed.

        Возвращает / Returns:
            bool: Обычно False, так как направленные элементы передают поток и не являются источниками.
                  Typically False, as directional elements transmit flow and are not sources.
        """
        return False

    def get_children(self, element: 'NetworkElement', model: 'NetworkModel') -> List[str]:
        """
        Определяет дочерние элементы для направленного элемента.
        Determines child elements for a directional element.

        Дочерним элементом считается шина, подключенная к "конечному" узлу направленного элемента.
        Конечный узел определяется методом `_get_end_node()`.
        The child element is considered to be the bus connected to the "end" node of the directional element.
        The end node is determined by the `_get_end_node()` method.

        Параметры / Parameters:
            element ('NetworkElement'): Направленный элемент.
                                       The directional element.
            model ('NetworkModel'): Модель сети.
                                    The network model.

        Возвращает / Returns:
            List[str]: Список, содержащий ID шины, подключенной к конечному узлу элемента,
                       или пустой список, если такая шина не найдена или у элемента нет четкого конечного узла.
                       A list containing the ID of the bus connected to the element's end node,
                       or an empty list if no such bus is found or the element lacks a clear end node.
        """
        children_ids: List[str] = []
        end_node_id = self._get_end_node(element)

        if end_node_id is None: # Если конечный узел не может быть определен
            logger.warning(f"Не удалось определить конечный узел для направленного элемента {element.id}. / Could not determine end node for directional element {element.id}.")
            return []

        # Ищем шину, которая подключена к этому конечному узлу.
        # Предполагаем, что ID узлов в model.node_connections являются строками, если они ключи словаря.
        # ID узлов в element.nodes - это int. Нужно согласование типов или четкое определение.
        # В NetworkModel._parse_connections ключи node_connections - это строки.
        # А element.nodes хранит int. Поэтому приводим end_node_id к строке для поиска.

        # Ищем элемент шины, у которого в списке nodes есть end_node_id
        # и который подключен к нашему 'element' через этот end_node_id
        
        # Сначала найдем все элементы, подключенные к узлу end_node_id
        str_end_node_id = str(end_node_id) # Узлы в node_connections обычно строки
        if str_end_node_id in model.node_connections:
            # Элементы, подключенные к узлу, который является конечным для 'element'
            elements_connected_to_end_node = model.node_connections[str_end_node_id]
            for potential_child_id in elements_connected_to_end_node:
                # Дочерним будет сама шина (узел), если она представлена как элемент типа BUS.
                # Или если мы ищем другие элементы, подключенные к этому же узлу (кроме самого 'element').
                if potential_child_id == str_end_node_id: # Если ID узла совпадает с ID элемента шины
                    potential_child_element = model.get_element(potential_child_id)
                    if potential_child_element and potential_child_element.element_type.value == "bus":
                        # Убедимся, что это не тот же самый элемент, если element сам является шиной (не должно быть для DirectionalElement)
                        if element.id != potential_child_id:
                             children_ids.append(potential_child_id)
                             logger.debug(f"Для направленного элемента {element.id} найдена дочерняя шина {potential_child_id} на конечном узле {end_node_id}. / For directional element {element.id} found child bus {potential_child_id} at end node {end_node_id}.")
                             break # Обычно к конечному узлу подключена одна основная шина "продолжения"

        # Альтернативная логика, если нужно найти элементы, одним из узлов которых является end_node_id,
        # и которые не являются самим 'element'.
        # Эта логика может быть сложнее, если структура соединений нечеткая.
        # Текущая логика ищет шину, которая ИМЕЕТ ID, равный end_node_id.

        return children_ids

    def _get_end_node(self, element: 'NetworkElement') -> Optional[int]:
        """
        Определяет "конечный" узел для направленного элемента.
        Determines the "end" node for a directional element.

        Для элементов с двумя или более узлами в списке `element.nodes`,
        второй узел (индекс 1) традиционно считается конечным.
        For elements with two or more nodes in the `element.nodes` list,
        the second node (index 1) is traditionally considered the end node.

        Параметры / Parameters:
            element ('NetworkElement'): Направленный элемент.
                                       The directional element.

        Возвращает / Returns:
            Optional[int]: ID конечного узла, или ID первого узла, если только один узел определен,
                           или None, если у элемента нет узлов.
                           The ID of the end node, or the ID of the first node if only one is defined,
                           or None if the element has no nodes.
        """
        if element.nodes:
            if len(element.nodes) >= 2:
                return element.nodes[1]  # Второй узел - конечный / Second node is the end node
            else: # len(element.nodes) == 1
                logger.debug(f"Направленный элемент {element.id} имеет только один узел ({element.nodes[0]}). Он будет считаться конечным. / Directional element {element.id} has only one node ({element.nodes[0]}). It will be considered the end node.")
                return element.nodes[0] # Если только один узел, он же и конечный (и начальный)
        logger.warning(f"Направленный элемент {element.id} не имеет определенных узлов. / Directional element {element.id} has no defined nodes.")
        return None # Если узлов нет

    def is_directional(self) -> bool:
        """
        Определяет, является ли данный тип элемента направленным.
        Determines if this element type is directional.

        Возвращает / Returns:
            bool: Всегда True для анализаторов, наследующих `DirectionalElementAnalyzer`.
                  Always True for analyzers inheriting from `DirectionalElementAnalyzer`.
        """
        return True


class OverheadLineAnalyzer(DirectionalElementAnalyzer):
    """
    Анализатор для элементов типа "Воздушная Линия Электропередачи" (`ElementType.OVERHEAD_LINE`).
    Analyzer for "Overhead Transmission Line" (`ElementType.OVERHEAD_LINE`) elements.

    Наследует основную логику от `DirectionalElementAnalyzer`.
    Inherits core logic from `DirectionalElementAnalyzer`.
    """

    def get_element_type(self) -> 'ElementType':
        """
        Возвращает тип элемента: `ElementType.OVERHEAD_LINE`.
        Returns the element type: `ElementType.OVERHEAD_LINE`.
        """
        from .models import ElementType
        return ElementType.OVERHEAD_LINE


class TransformerAnalyzer(DirectionalElementAnalyzer):
    """
    Анализатор для элементов типа "Трансформатор" (в данном случае, `ElementType.TRANSFORMER2`).
    Analyzer for "Transformer" elements (in this case, `ElementType.TRANSFORMER2`).

    Наследует основную логику от `DirectionalElementAnalyzer`.
    Inherits core logic from `DirectionalElementAnalyzer`.
    """

    def get_element_type(self) -> 'ElementType':
        """
        Возвращает тип элемента: `ElementType.TRANSFORMER2`.
        Returns the element type: `ElementType.TRANSFORMER2`.
        """
        from .models import ElementType
        return ElementType.TRANSFORMER2


class TerminalElementAnalyzer(ElementAnalyzer):
    """
    Базовый абстрактный анализатор для терминальных (конечных) элементов сети,
    таких как нагрузки и генераторы.
    Base abstract analyzer for terminal network elements, such as loads and generators.

    Терминальные элементы обычно не имеют дочерних элементов в контексте
    построения иерархического дерева от источника питания. Они являются "концами" ветвей.
    Terminal elements typically do not have children in the context of building
    a hierarchical tree from a power source. They are the "ends" of branches.
    """

    @abstractmethod # Конкретные подклассы все еще должны реализовывать get_element_type
    def get_element_type(self) -> 'ElementType':
        pass

    def is_root(self, element: 'NetworkElement') -> bool:
        """
        Определяет, является ли терминальный элемент корневым.
        Determines if a terminal element is a root.

        Возвращает / Returns:
            bool: Обычно False. / Typically False.
        """
        return False

    def get_children(self, element: 'NetworkElement', model: 'NetworkModel') -> List[str]:
        """
        Возвращает дочерние элементы для терминального элемента.
        Returns child elements for a terminal element.

        Возвращает / Returns:
            List[str]: Всегда пустой список, так как терминальные элементы не имеют дочерних.
                       Always an empty list, as terminal elements have no children.
        """
        return []

    def is_directional(self) -> bool:
        """
        Определяет, является ли данный тип терминального элемента направленным.
        Determines if this terminal element type is directional.

        Возвращает / Returns:
            bool: Обычно False для нагрузок и генераторов (их подключение к шине не задает направление потока от них).
                  Typically False for loads and generators (their connection to a bus does not define a flow direction from them).
        """
        return False


class GeneratorAnalyzer(TerminalElementAnalyzer):
    """
    Анализатор для элементов типа "Генератор" (`ElementType.GENERATOR`).
    Analyzer for "Generator" (`ElementType.GENERATOR`) elements.

    Наследует основную логику от `TerminalElementAnalyzer`.
    Inherits core logic from `TerminalElementAnalyzer`.
    """

    def get_element_type(self) -> 'ElementType':
        """
        Возвращает тип элемента: `ElementType.GENERATOR`.
        Returns the element type: `ElementType.GENERATOR`.
        """
        from .models import ElementType
        return ElementType.GENERATOR


class LoadAnalyzer(TerminalElementAnalyzer):
    """
    Анализатор для элементов типа "Нагрузка" (`ElementType.LOAD`).
    Analyzer for "Load" (`ElementType.LOAD`) elements.

    Наследует основную логику от `TerminalElementAnalyzer`.
    Inherits core logic from `TerminalElementAnalyzer`.
    """

    def get_element_type(self) -> 'ElementType':
        """
        Возвращает тип элемента: `ElementType.LOAD`.
        Returns the element type: `ElementType.LOAD`.
        """
        from .models import ElementType
        return ElementType.LOAD