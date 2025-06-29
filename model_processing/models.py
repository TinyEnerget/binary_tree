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

# TODO: Consider extending with elements from LabRZA (Original Russian comment: Дополнить элементы схемы из ЛабРЗА)
class ElementType(Enum):
    """Defines the types of elements in an electrical network."""
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
    """
    Represents a basic element within the electrical network model.

    Attributes:
        id (str): Unique identifier of the element.
        name (str): Name of the element.
        element_type (ElementType): Type of the element (e.g., BUS, LINE).
                                    Note: Original code allowed Union[ElementType, str],
                                    but strict ElementType is preferred if possible.
        nodes (List[str]): List of other element IDs to which this element is connected.
                           Changed from List[int] for consistency with string-based IDs (UUIDs).
        data (Dict[str, Any]): Additional properties and data associated with the element.
    """
    id: str
    name: str
    element_type: ElementType
    nodes: List[str] # Assuming string IDs for connected nodes/elements
    data: Dict[str, Any]


class NetworkModelError(Exception):
    """Custom exception for errors related to the electrical network model processing."""
    pass


class NetworkModel:
    """
    Represents an electrical network model.

    This class parses preprocessed input data, stores network elements
    (as NetworkElement objects) and their connections, and provides methods
    to access and work with these components. It also includes a system for
    element-specific "analyzers," though this is not central to the basic
    graph construction used by GraphCreator.

    Args:
        model_data (Dict[str, Any]): Preprocessed model data, typically from ModelPreprocessor.
                                     Expected to contain 'elements', 'nodes', and 'roots'.
    Attributes:
        raw_data (Dict[str, Any]): The input (preprocessed) model data dictionary.
        elements (Dict[str, NetworkElement]): A dictionary of network elements, keyed by element ID.
        node_connections (Dict[str, List[str]]): Stores connections between elements,
                                                 derived from the 'nodes' section of the input data.
                                                 Typically, keys are element IDs, and values are lists
                                                 of connected element IDs.
        roots (List[str]): A list of root element IDs, taken directly from the preprocessed model_data.
        analyzers (Dict[Union[ElementType, str], Any]): A registry for element-specific analyzers.
                                                        (Type hint for value was ElementAnalyzer).
    """
    
    def __init__(self, model_data: Dict[str, Any]):
        """
        Initializes the NetworkModel.

        Args:
            model_data (Dict[str, Any]): Preprocessed model data. It's expected to have
                                         'elements', 'nodes' (for connections), and 'roots' keys.
        """
        self.raw_data = model_data # This is preprocessed data from ModelPreprocessor
        self.elements: Dict[str, NetworkElement] = {}
        self.node_connections: Dict[str, List[str]] = {}
        self.analyzers: Dict[Union[ElementType, str], Any] = {} # For ElementAnalyzer system

        # Directly store roots from preprocessed data
        self.roots: List[str] = self.raw_data.get('roots', [])
        
        # Register default analyzers (if the analyzer system is still actively used).
        self._register_default_analyzers()
        
        # Parse the model components (elements and connections).
        self._parse_model()
        logger.debug("Model initialized: %s elements, %s connections, %s roots",
                     len(self.elements), len(self.node_connections), len(self.roots))
    
    def _register_default_analyzers(self) -> None:
        """
        Registers default element analyzers from the AnalyzerRegistry.
        This system allows for element-type-specific logic.
        """
        from .registry import AnalyzerRegistry  # Delayed import to avoid circular dependencies
        AnalyzerRegistry.register_default_analyzers() # Ensure defaults are loaded in the central registry
        try:
            # Assuming AnalyzerRegistry.get_analyzers() returns a list of analyzer classes or instances
            for analyzer_ref in AnalyzerRegistry.get_analyzers():
                # If analyzer_ref is a class, it needs to be instantiated.
                # If it's already an instance, this depends on AnalyzerRegistry's design.
                # Assuming it returns classes that need instantiation:
                analyzer_instance = analyzer_ref() # Example: MyAnalyzerClass()
                element_type = analyzer_instance.get_element_type() # Must be a method on the instance
                self.analyzers[element_type] = analyzer_instance
                logger.debug("Registered analyzer for type: %s", element_type)
        except ImportError as e: # More specific exceptions might be better
            logger.error("Error registering analyzers: %s", e)
            raise NetworkModelError(f"Failed to register analyzers: {e}")
        except Exception as e: # Catch other potential errors during analyzer instantiation/registration
            logger.error("Unexpected error during analyzer registration: %s", e)
            # Decide if this should also raise NetworkModelError or just log
            raise NetworkModelError(f"Unexpected error registering analyzers: {e}")
    
    #def register_analyzer(self, analyzer: ElementAnalyzer):
    #    """Регистрирует анализатор для определенного типа элемента.
    #
    #    Args:
    #        analyzer (ElementAnalyzer): Экземпляр анализатора.
    #    """
    #    self.analyzers[analyzer.get_element_type()] = analyzer
    
    @lru_cache(maxsize=None)
    def get_analyzer(self, element_type: Union[ElementType, str]) -> Optional[Any]: # Type hint was Optional[ElementAnalyzer]
        """
        Retrieves an instantiated analyzer for the specified element type.
        Uses LRU cache for performance.

        Args:
            element_type (Union[ElementType, str]): The element type (Enum member or string).

        Returns:
            Optional[Any]: An instance of the analyzer for the element type,
                           or None if not found. (Should be Optional[ElementAnalyzer])
        """
        analyzer_instance = self.analyzers.get(element_type)
        if not analyzer_instance:
            logger.warning("Analyzer for type '%s' not found.", element_type)
        return analyzer_instance
    
    def _parse_model(self) -> None:
        """
        Parses the raw model data to populate elements and their connections.
        This is called during initialization.
        """
        try:
            logger.debug("Starting to parse model elements.")
            self._parse_elements()
            logger.debug("Finished parsing model elements. Starting to parse connections.")
            self._parse_connections()
            logger.debug("Finished parsing connections.")
        except Exception as e: # Consider more specific exceptions for parsing errors
            logger.error("Error during model parsing process: %s", e, exc_info=True)
            # Wrapping the original exception can be helpful for debugging.
            raise NetworkModelError(f"Error parsing model data: {e}") from e
    
    def _parse_elements(self) -> None:
        """
        Parses network elements from the 'elements' section of `self.raw_data`.
        Populates `self.elements` with NetworkElement objects.
        It ensures that element IDs and connected node IDs within NetworkElement are strings.
        """
        elements_data = self.raw_data.get('elements', {})
        if not isinstance(elements_data, dict): # Check if elements_data is a dictionary
            logger.warning("'elements' section is missing or not a dictionary in the model data. No elements will be parsed.")
            return # No elements to parse

        for element_id_orig, element_data in elements_data.items():
            element_id = str(element_id_orig) # Ensure element_id is a string

            if not isinstance(element_data, dict): # Ensure element_data is a dictionary
                logger.warning("Element data for ID '%s' is not a dictionary. Skipping.", element_id)
                continue

            element_type_str = element_data.get('Type', '')
            if not element_type_str: # Check for empty Type
                logger.warning("Element ID '%s' has missing or empty 'Type'. Skipping.", element_id)
                continue

            try:
                element_type = ElementType(element_type_str)
            except ValueError:
                logger.warning(
                    "Unknown element type string: '%s' for element ID '%s'. Skipping element. "
                    "Ensure this type is defined in the ElementType enum.",
                    element_type_str, element_id
                )
                continue # Skip this element if its type is not in the enum
            
            # Process 'Nodes' - ensuring it's a list of strings
            nodes_raw = element_data.get('Nodes', []) # Default to empty list if 'Nodes' is missing
            nodes_str_list: List[str] = []
            if isinstance(nodes_raw, (int, str)):
                nodes_str_list = [str(nodes_raw)]
            elif isinstance(nodes_raw, list):
                # Filter out None values and convert all items to string
                nodes_str_list = [str(n) for n in nodes_raw if n is not None]
            else:
                logger.warning(
                    "Incorrect 'Nodes' data type for element '%s' (expected list, str, or int, found %s). Using empty list for nodes.",
                    element_id, type(nodes_raw).__name__
                )
                # nodes_str_list remains empty as initialized
            
            element = NetworkElement(
                id=element_id,
                name=str(element_data.get('Name', f'Element_{element_id[:8]}')), # Ensure name is also string
                element_type=element_type,
                nodes=nodes_str_list,    # This is List[str]
                data=element_data
            )
            
            self.elements[element_id] = element
            logger.debug("Added element '%s': type=%s, nodes=%s",
                         element_id, element_type.value, nodes_str_list)
    
    def _parse_connections(self) -> None:
        """
        Parses connections between elements from the 'nodes' section of `self.raw_data`.
        Populates `self.node_connections`.
        It ensures that IDs are strings, and excludes self-connections and connections
        to non-existent elements.
        """
        nodes_data = self.raw_data.get('nodes', {})
        if not isinstance(nodes_data, dict):
            logger.warning("'nodes' section is missing or not a dictionary. No connections will be parsed.")
            return

        for node_id_orig, connected_elements_raw in nodes_data.items():
            node_id = str(node_id_orig) # Ensure node_id is a string

            if not isinstance(connected_elements_raw, list):
                logger.warning("Connections for node ID '%s' is not a list. Skipping.", node_id)
                continue

            valid_elements = []
            for elem_id_raw in connected_elements_raw:
                elem_id = str(elem_id_raw) # Ensure connected element id is a string
                # Add to valid_elements if it's a known element and not a self-connection
                if elem_id in self.elements and elem_id != node_id:
                    valid_elements.append(elem_id)
                elif elem_id == node_id:
                    logger.debug("Self-connection found and ignored for node '%s'.", node_id)
                elif elem_id not in self.elements:
                    logger.debug("Connection from '%s' to non-existent element '%s' ignored.", node_id, elem_id)

            if valid_elements:
                self.node_connections[node_id] = valid_elements
                logger.debug("Node '%s': connections = %s", node_id, valid_elements)
            # else:
                # logger.debug("Node '%s': no valid connections after filtering.", node_id) # Can be noisy

        if not self.node_connections:
            logger.warning("No node connections were formed. Check the 'nodes' section in the model data and element definitions.")

    def get_undirected_graph(self) -> Dict[str, List[str]]:
        """
        Constructs an undirected graph (adjacency list) based on `self.node_connections`.
        This method implements specific logic for how connections are formed,
        especially concerning 'BUS' type elements.

        Returns:
            Dict[str, List[str]]: An adjacency list where keys are element IDs and
                                  values are lists of connected element IDs.
                                  Elements with no connections might be excluded from keys.
        """
        # Initialize graph with all parsed elements, ensuring even isolated elements are represented if desired.
        # However, the current logic filters out nodes with no connections at the end.
        undirected_graph: Dict[str, List[str]] = {elem_id: [] for elem_id in self.elements.keys()}

        for node_id, connected_elements in self.node_connections.items():
            # This logic seems to treat node_id as a primary element and connected_elements as its direct links.
            # The special handling for BUS elements implies a star-like connection pattern around buses,
            # or specific rules for how non-bus elements connect if a bus is involved.

            # Ensure node_id itself is in the elements dictionary before proceeding
            if node_id not in self.elements:
                logger.warning("Node ID '%s' from connections data not found in parsed elements. Skipping its connections.", node_id)
                continue

            # Check if the current node_id (key in node_connections) is a BUS
            # This part of original logic was complex: "Явно делим на шины и не-шины"
            # The original logic iterated through connected_elements to find buses within that list.
            # Let's try to maintain the spirit: if node_id is a BUS, it connects to all its listed elements.
            # If node_id is NOT a BUS, and it connects to BUSes, special logic might apply,
            # or it connects to all its listed elements.
            # The original code had:
            # bus_elements = [eid for eid in connected_elements if self.elements[eid].element_type == ElementType.BUS]
            # non_bus_elements = [eid for eid in connected_elements if eid not in bus_elements]
            # This was applied *within* the loop of connected_elements for a node_id.
            # This means 'connected_elements' is a list of items that are connected *through* node_id (if node_id is a conceptual point)
            # OR 'node_id' is an element, and 'connected_elements' are its direct peers.
            # Given 'node_connections' is populated from 'raw_data.nodes', it's likely the latter.

            # Simplified interpretation: each element in 'connected_elements' is connected to 'node_id'.
            # And by unＤirected nature, they also connect back.
            for target_element_id in connected_elements:
                if target_element_id not in self.elements: # Should have been filtered by _parse_connections
                    continue

                # Add edge: node_id <-> target_element_id
                if target_element_id not in undirected_graph.get(node_id, []): # Check before append
                    undirected_graph.setdefault(node_id, []).append(target_element_id)
                if node_id not in undirected_graph.get(target_element_id, []): # Check before append
                    undirected_graph.setdefault(target_element_id, []).append(node_id)

        # Filter out elements that ended up with no connections from the graph's keys
        # This also means if an element was in self.elements but never participated in any valid connection,
        # it won't be in the final graph keys.
        final_graph = {k: v for k, v in undirected_graph.items() if v}
    
        logger.debug("Undirected graph formed: %d nodes with connections, %d edges (approx, sum of degrees / 2)",
                     len(final_graph),
                     sum(len(v) for v in final_graph.values()) // 2)
        return final_graph
    
    def get_element(self, element_id: str) -> Optional[NetworkElement]:
        """
        Retrieves a network element by its ID.

        Args:
            element_id (str): The ID of the element to retrieve.

        Returns:
            Optional[NetworkElement]: The NetworkElement object if found, otherwise None.
        """
        element = self.elements.get(str(element_id)) # Ensure lookup ID is also string
        if not element:
            logger.debug("Element with ID '%s' not found.", element_id)
        return element
    
    # def get_root_elements(self) -> List[str]: # DEPRECATED and REMOVED
    #     """Находит корневые элементы сети. (DEPRECATED)
    #     Корневые элементы теперь определяются Preprocessor'ом и хранятся в self.roots.
    #     Returns:
    #         List[str]: Список идентификаторов корневых элементов.
    #     """
    #     # Эта логика больше не должна использоваться для основного пути определения корней.
    #     # Оставлено закомментированным для справки о старой системе анализаторов.
    #     # roots = []
    #     # for element_id, element in self.elements.items():
    #     #     analyzer = self.get_analyzer(element.element_type)
    #     #     if analyzer and analyzer.is_root(element):
    #     #         roots.append(element_id)
    #     #         logger.debug("Корневой элемент (через get_root_elements): %s (%s)", element_id, element.element_type)
    #     # if not roots:
    #     #     logger.warning("Корневые элементы не найдены через get_root_elements (DEPRECATED). Используйте self.roots.")
    #     # return roots
    pass # End of class NetworkModel