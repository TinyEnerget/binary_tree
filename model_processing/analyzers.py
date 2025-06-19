from abc import ABC, abstractmethod
from typing import List, Union, TYPE_CHECKING
#from .models import NetworkElement, ElementType, NetworkModel

import logging
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .models import NetworkElement, ElementType, NetworkModel

class ElementAnalyzer(ABC):
    """Абстрактный базовый класс для анализа элементов электрической сети.

    Определяет интерфейс для обработки элементов, включая определение типа, 
    корневого статуса, дочерних элементов и направленности.
    """

    @abstractmethod
    def get_element_type(self) -> Union['ElementType', str]:
        """Возвращает тип элемента.

        Returns:
            Union[ElementType, str]: Тип элемента (стандартный или пользовательский).
        """
        pass
    
    @abstractmethod
    def is_root(self, element: 'NetworkElement') -> bool:
        """Определяет, является ли элемент корневым.

        Args:
            element (NetworkElement): Элемент сети.

        Returns:
            bool: True, если элемент корневой, иначе False.
        """
        pass
    
    @abstractmethod
    def get_children(self, element: 'NetworkElement', model: 'NetworkModel') -> List[str]:
        """Возвращает список идентификаторов дочерних элементов.

        Args:
            element (NetworkElement): Элемент сети.
            model (NetworkModel): Модель сети, содержащая элементы и соединения.

        Returns:
            List[str]: Список идентификаторов дочерних элементов.
        """
        pass
    
    @abstractmethod
    def is_directional(self) -> bool:
        """Определяет, является ли элемент направленным.

        Returns:
            bool: True, если элемент направленный, иначе False.
        """
        pass


class SystemAnalyzer(ElementAnalyzer):
    """Анализатор системных элементов"""
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType ###
        return ElementType.SYSTEM
    
    def is_root(self, element: 'NetworkElement') -> bool:
        return True
    
    def get_children(self, element: 'NetworkElement', model: 'NetworkModel') -> List[str]:
        """Возвращает шины, подключенные к системному элементу."""
        children = []
        for bus_id, connected_elements in model.node_connections.items():
            if element.id in connected_elements:
                children.append(bus_id)
        return children
    
    def is_directional(self) -> bool:
        return False


class BusAnalyzer(ElementAnalyzer):
    """Анализатор шинных элементов.

    Шины подключаются к направленным (линии, трансформаторы) и 
    ненаправленным (генераторы, нагрузки) элементам, учитывая направление для направленных элементов.
    """
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.BUS
    
    def is_root(self, element: 'NetworkElement') -> bool:
        return False
    
    def get_children(self, element: 'NetworkElement', model: 'NetworkModel') -> List[str]:
        """Возвращает дочерние элементы, подключенные к шине."""
        from .models import ElementType###
        if element.id not in model.node_connections:
            return []

        children = []
        for connected_id in model.node_connections[element.id]:
            connected_element = model.get_element(connected_id)
            if not connected_element or connected_element.element_type == ElementType.SYSTEM:
                continue

            analyzer = model.get_analyzer(connected_element.element_type)
            if not analyzer:
                logger.warning("Анализатор для типа %s не найден", connected_element.element_type)
                continue

            if analyzer.is_directional():
                if self._is_start_node(element, connected_element):
                    children.append(connected_id)
            elif connected_element.element_type in [ElementType.LOAD, ElementType.GENERATOR]:
                children.append(connected_id)
        #children = []
        #if element.id not in model.node_connections:
        #    return children
        #    
        #for connected_id in model.node_connections[element.id]:
        #    connected_element = model.get_element(connected_id)
        #    if not connected_element:
        #        continue
        #        
        #    # Пропускаем системные элементы (они родители)
        #    if connected_element.element_type == ElementType.SYSTEM:
        #        continue
        #        
        #    # Для направленных элементов проверяем направление
        #    analyzer = model.get_analyzer(connected_element.element_type)
        #    if analyzer.is_directional():
        #        if self._is_start_node(element, connected_element):
        #            children.append(connected_id)
        #    else:
        #        # Для ненаправленных элементов (нагрузки, генераторы) всегда добавляем
        #        if connected_element.element_type in [ElementType.LOAD, ElementType.GENERATOR]:
        #            children.append(connected_id)
                    
        return children
    
    def _is_start_node(self, bus_element: 'NetworkElement', connected_element: 'NetworkElement') -> bool:
        """Определяет, является ли шина начальным узлом для подключенного элемента.

        Args:
            bus_element (NetworkElement): Шина.
            connected_element (NetworkElement): Подключенный элемент.

        Returns:
            bool: True, если шина является начальным узлом, иначе False.
        """
        bus_node = bus_element.nodes[0] if bus_element.nodes else 0
        connected_nodes = connected_element.nodes
        
        if len(connected_nodes) >= 2:
            return bus_node == connected_nodes[0]
        return True
    
    def is_directional(self) -> bool:
        return False


class DirectionalElementAnalyzer(ElementAnalyzer):
    """Базовый анализатор для направленных элементов (линии, трансформаторы).

    Определяет дочерние элементы на основе конечного узла.
    """
    
    def is_root(self, element: 'NetworkElement') -> bool:
        return False
    
    def get_children(self, element: 'NetworkElement', model: 'NetworkModel') -> List[str]:
        """Возвращает дочерние шины, подключенные к конечному узлу элемента."""
        children = []
        end_node = self._get_end_node(element)
        
        for bus_id, connected_elements in model.node_connections.items():
            if element.id in connected_elements:
                bus_element = model.get_element(bus_id)
                if bus_element and bus_element.nodes and bus_element.nodes[0] == end_node:
                    children.append(bus_id)
                    
        return children
    
    def _get_end_node(self, element: 'NetworkElement') -> int:
        """Получает конечный узел элемента (второй в списке для направленных элементов).

        Args:
            element (NetworkElement): Элемент сети.

        Returns:
            int: Идентификатор конечного узла.
        """
        if len(element.nodes) >= 2:
            return element.nodes[1]  # Второй узел - это конечный
        return element.nodes[0] if element.nodes else 0
    
    def is_directional(self) -> bool:
        return True


class OverheadLineAnalyzer(DirectionalElementAnalyzer):
    """Анализатор воздушных линий"""
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.OVERHEAD_LINE


class TransformerAnalyzer(DirectionalElementAnalyzer):
    """Анализатор трансформаторов"""
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.TRANSFORMER2


class SeriesTransformerAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.SERIES_TRANSFORMER
    

class AutoTransformerAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.AUTO_TRANSFORMER


class SwitchAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.SWITCH


class BreakerAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.BREAKER

class Transformer2SWAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.TRANSFORMER2SW


class EquivalentBranchAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.EQUIVALENT_BRANCH
    

class CorridorAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.CORRIDOR
    

class CableLineAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.CABLE_LINE


class Transformer3Analyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.TRANSFORMER3
    

class AutoTransformerSinglePhaseAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.AUTO_TRANSFORMER_SINGLE_PHASE
    

class CurrentLimiterAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.CURRENT_LIMITER_REACTOR
    

class MutualCoupledReactorAnalyzer(DirectionalElementAnalyzer):
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.MUTUAL_COUPLED_REACTOR


class TerminalElementAnalyzer(ElementAnalyzer):
    """Базовый анализатор для терминальных элементов (генераторы, нагрузки).

    Терминальные элементы не имеют дочерних элементов.
    """
    
    def is_root(self, element: 'NetworkElement') -> bool:
        return False
    
    def get_children(self, element: 'NetworkElement', model: 'NetworkModel') -> List[str]:
        return []  # Терминальные элементы не имеют дочерних элементов
    
    def is_directional(self) -> bool:
        return False


class GeneratorAnalyzer(TerminalElementAnalyzer):
    """Анализатор генераторов"""
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.GENERATOR


class LoadAnalyzer(TerminalElementAnalyzer):
    """Анализатор нагрузок"""
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.LOAD
    

class ShortCircuitAnalyzer(TerminalElementAnalyzer):
    """Анализатор коротких замыканий"""
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.SHORT_CIRCUIT
    

class AsynchronousMotorAnalyzer(TerminalElementAnalyzer):
    """Анализатор асинхронных двигателей"""
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.ASYNCHRONOUS_MOTOR
    

class SynchronousMotorAnalyzer(TerminalElementAnalyzer):
    """Анализатор синхронных двигателей"""
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.SYNCHRONOUS_MOTOR
    

class PetersenCoilAnalyzer(TerminalElementAnalyzer):
    """Анализатор петерсонских сопротивлений"""
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.PETERSEN_COIL
    

class StaticCapacitorBankAnalyzer(TerminalElementAnalyzer):
    """Анализатор статических капиторов"""
    
    def get_element_type(self) -> 'ElementType':
        from .models import ElementType
        return ElementType.STATIC_CAPACITOR_BANK
    

