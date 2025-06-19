from ctypes.wintypes import SHORT
from functools import lru_cache
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass

if TYPE_CHECKING:
    from .registry import AnalyzerRegistry
    from .analyzers import ElementAnalyzer

import logging
logger = logging.getLogger(__name__)

#TODO: Дополнить элементы схемы из ЛабРЗА
class ElementType(Enum):
    """Типы элементов электрической сети"""
    SYSTEM = "system"
    BUS = "bus"
    EQUIVALENT_BRANCH = "equivalent_branch"
    CORRIDOR = "corridor"
    OVERHEAD_LINE = "overhead_line"
    CABLE_LINE = "cable_line"
    TRANSFORMER2 = "transformer2"
    TRANSFORMER2SW = "transformer2sw"
    TRANSFORMER3 = "transformer3"
    AUTO_TRANSFORMER = "auto_transformer"
    AUTO_TRANSFORMER_SINGLE_PHASE = "at0_single_phase"
    SWITCH = "switch"
    BREAKER = "breaker"
    SERIES_TRANSFORMER = "series_transformer"
    ASYNCHRONOUS_MOTOR = "asynchronous_motor"
    SYNCHRONOUS_MOTOR = "synchronous_motor"
    STATIC_CAPACITOR_BANK = "static_capacitor_bank"
    SHUNT_REACTOR = "shunt_reactor"
    CURRENT_LIMITER_REACTOR = "current_limiter_reactor"
    PETERSEN_COIL = "petersen_coil"
    MUTUAL_COUPLED_REACTOR = "mutual_coupled_reactor"
    GENERATOR = "generator"
    LOAD = "load"
    SHORT_CIRCUIT = "short_circuit"


@dataclass
class NetworkElement:
    """Базовый класс для элементов электрической сети.

    Attributes:
        id (str): Уникальный идентификатор элемента.
        name (str): Имя элемента.
        element_type (Union[ElementType, str]): Тип элемента (из перечисления или пользовательский).
        nodes (List[int]): Список узлов, к которым подключен элемент.
        data (Dict[str, Any]): Дополнительные данные об элементе.
    """
    id: str
    name: str
    element_type: ElementType
    nodes: List[int]
    data: Dict[str, Any]


class NetworkModelError(Exception):
    """Исключение для ошибок, связанных с моделью электрической сети."""
    pass


class NetworkModel:
    """Модель электрической сети.

    Парсит входные данные, хранит элементы сети и их соединения, предоставляет методы для работы
    с элементами и анализаторами.

    Args:
        model_data (Dict[str, Any]): Входные данные модели в формате словаря.

    Attributes:
        raw_data (Dict[str, Any]): Исходные данные модели.
        elements (Dict[str, NetworkElement]): Словарь элементов сети (ключ — идентификатор).
        node_connections (Dict[str, List[str]]): Соединения между элементами по узлам.
        analyzers (Dict[Union[ElementType, str], ElementAnalyzer]): Зарегистрированные анализаторы.
    """
    
    def __init__(self, model_data: Dict[str, Any]):
        self.raw_data = model_data
        self.elements: Dict[str, NetworkElement] = {}
        self.node_connections: Dict[str, List[str]] = {}
        self.analyzers: Dict[Union[ElementType, str], Any] = {}#Dict[ElementType, ElementAnalyzer] = {}
        
        # Регистрируем стандартные анализаторы
        self._register_default_analyzers()
        
        # Парсим модель
        self._parse_model()
        logger.debug("Модель инициализирована: %d элементов, %d узлов", 
                     len(self.elements), len(self.node_connections))
    
    def _register_default_analyzers(self) -> None:
        """Регистрирует стандартные анализаторы элементов"""
        from .registry import AnalyzerRegistry  # Отложенный импорт
        AnalyzerRegistry.register_default_analyzers()
        try:
            for analyzer in AnalyzerRegistry.get_analyzers():
                element_type = analyzer.get_element_type()
                self.analyzers[element_type] = analyzer
                logger.debug("Зарегистрирован анализатор для типа: %s", element_type)
        except ImportError as e:
            logger.error("Ошибка регистрации анализаторов: %s", e)
            raise NetworkModelError(f"Не удалось зарегистрировать анализаторы: {e}")

        #for analyzer in AnalyzerRegistry.get_analyzers():
        #    self.register_analyzer(analyzer)
    
    #def register_analyzer(self, analyzer: ElementAnalyzer):
    #    """Регистрирует анализатор для определенного типа элемента.
    #
    #    Args:
    #        analyzer (ElementAnalyzer): Экземпляр анализатора.
    #    """
    #    self.analyzers[analyzer.get_element_type()] = analyzer
    
    @lru_cache(maxsize=None)
    def get_analyzer(self, element_type: Union[ElementType, str]) -> Optional[Any]:#ElementAnalyzer]:
        """Получает анализатор для указанного типа элемента.

        Args:
            element_type (Union[ElementType, str]): Тип элемента.

        Returns:
            Optional[ElementAnalyzer]: Анализатор для типа элемента или None, если не найден.
        """
        analyzer = self.analyzers.get(element_type)
        if not analyzer:
            logger.warning("Анализатор для типа %s не найден", element_type)
        return analyzer
    
    def _parse_model(self):
        """Парсит входные данные модели, инициализируя элементы и соединения."""
        try:
            self._parse_elements()
            self._parse_connections()
        except Exception as e:
            logger.error("Ошибка парсинга модели: %s", e)
            raise NetworkModelError(f"Ошибка парсинга модели: {e}")
    
    def _parse_elements(self):
        """Парсит элементы модели из входных данных.

        Raises:
            NetworkModelError: Если тип элемента неизвестен.
        """
        elements_data = self.raw_data.get('elements', {})
        if not elements_data:
            logger.warning("Раздел 'elements' отсутствует в модели")
            return
        for element_id, element_data in self.raw_data.get('elements', {}).items():
            element_type_str = element_data.get('Type', '')
            element_type: Union[ElementType, str]
            try:
                element_type = ElementType(element_type_str)
            except ValueError:
                logger.warning("Неизвестный тип элемента: %s, используется как строка", element_type_str)
                element_type = element_type_str
                continue
            
            nodes = element_data.get('Nodes', [])
            if isinstance(nodes, int):
                nodes = [nodes]
            if not isinstance(nodes, list):
                logger.warning("Некорректные узлы для элемента %s: %s", element_id, nodes)
                nodes = []
            
            element = NetworkElement(
                id=element_id,
                name=element_data.get('Name', f'Element_{element_id[:8]}'),
                element_type=element_type,
                nodes=nodes,
                data=element_data
            )
            
            self.elements[element_id] = element
            logger.debug("Добавлен элемент %s: тип=%s, узлы=%s", 
                         element_id, element_type, nodes)
    
    def _parse_connections(self):
        """Парсит соединения между элементами.

        Исключает автосоединения и несуществующие элементы.
        """
        nodes_data = self.raw_data.get('nodes', {})
        for node_id, connected_elements in nodes_data.items():
            valid_elements = [
                elem_id for elem_id in connected_elements
                if elem_id in self.elements and elem_id != node_id
            ]
            if valid_elements:
                self.node_connections[node_id] = valid_elements
                logger.debug("Узел %s: соединения = %s", node_id, valid_elements)
            else:
                logger.debug("Узел %s: нет действительных соединений", node_id)

        # Проверка на отсутствие соединений
        if not self.node_connections:
            logger.warning("Соединения узлов не сформированы. Проверяйте 'nodes' в модели")
        #for bus_id, connected_elements in self.raw_data.get('nodes', {}).items():
        #    # Фильтруем автосоединения
        #    for bus_id, connected_elements in self.raw_data.get('nodes', {}).items():
        #        self.node_connections[bus_id] = [
        #            elem_id for elem_id in connected_elements
        #            if elem_id != bus_id and elem_id in self.elements
        #        ]
            #filtered_connections = [elem_id for elem_id in connected_elements if elem_id != bus_id]
            #self.node_connections[bus_id] = filtered_connections

    def get_undirected_graph(self) -> Dict[str, List[str]]:
        """Формирует ненаправленный граф на основе соединений узлов.

        Returns:
            Dict[str, List[str]]: Словарь, где ключ — идентификатор элемента,
                                  значение — список идентификаторов связанных элементов.
        """
        undirected_graph: Dict[str, List[str]] = {elem_id: [] for elem_id in self.elements}

        for node_id, connected_elements in self.node_connections.items():
            # Явно делим на шины и не-шины
            bus_elements = [eid for eid in connected_elements if self.elements[eid].element_type == ElementType.BUS]
            non_bus_elements = [eid for eid in connected_elements if eid not in bus_elements]
    
            # Связи от шин ко всем остальным
            for bus_id in bus_elements:
                for eid in connected_elements:
                    if eid != bus_id:
                        if eid not in undirected_graph[bus_id]:
                            undirected_graph[bus_id].append(eid)
                        if bus_id not in undirected_graph[eid]:
                            undirected_graph[eid].append(bus_id)
    
            # Если шин нет, то делаем попарные связи между всеми элементами
            if not bus_elements:
                for i in range(len(non_bus_elements)):
                    for j in range(i + 1, len(non_bus_elements)):
                        a, b = non_bus_elements[i], non_bus_elements[j]
                        if b not in undirected_graph[a]:
                            undirected_graph[a].append(b)
                        if a not in undirected_graph[b]:
                            undirected_graph[b].append(a)
    
        # Удаляем элементы без связей
        undirected_graph = {k: v for k, v in undirected_graph.items() if v}
    
        logger.debug("Сформирован ненаправленный граф: %d узлов с непустыми связями, %d рёбер",
                     len(undirected_graph),
                     sum(len(v) for v in undirected_graph.values()) // 2)
        return undirected_graph
    
    def get_element(self, element_id: str) -> Optional[NetworkElement]:
        """Получает элемент сети по идентификатору.

        Args:
            element_id (str): Идентификатор элемента.

        Returns:
            Optional[NetworkElement]: Элемент сети или None, если не найден.
        """
        element = self.elements.get(element_id)
        if not element:
            logger.debug("Элемент %s не найден", element_id)
        return element
    
    def get_root_elements(self) -> List[str]:
        """Находит корневые элементы сети.

        Returns:
            List[str]: Список идентификаторов корневых элементов.
        """
        roots = []
        for element_id, element in self.elements.items():
            analyzer = self.get_analyzer(element.element_type)
            if analyzer and analyzer.is_root(element):
                roots.append(element_id)
                logger.debug("Корневой элемент: %s (%s)", element_id, element.element_type)
        if not roots:
            logger.warning("Корневые элементы не найдены")
        #roots = []
        #for element_id, element in self.elements.items():
        #    analyzer = self.get_analyzer(element.element_type)
        #    if analyzer and analyzer.is_root(element):
        #        roots.append(element_id)
        return roots