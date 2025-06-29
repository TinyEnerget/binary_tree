from typing import Dict, Any, List, Tuple
from .models import NetworkModel, NetworkElement, ElementType
import logging
logger = logging.getLogger(__name__)
class NetworkGraphBuilder: # Renamed from NetworkTreeBuilder
    """
    Builds graph structures for an electrical network.
    Can create various graph representations (e.g., a hierarchical tree
    or a general undirected graph) based on the network model.

    Args:
        model (NetworkModel): The network model instance containing elements and their connections.
    """
    
    def __init__(self, model: NetworkModel):
        """
        Initializes the NetworkGraphBuilder with a network model.

        Args:
            model (NetworkModel): The pre-loaded and parsed network model.
        """
        self.model = model
    
    def build_tree(self) -> Dict[str, Any]:
        """
        Builds a hierarchical tree representation of the network.

        This method iterates through network elements, determining their children
        using a system of registered element analyzers (if available and configured),
        and forms the tree structure. The definition of "child" depends on the
        logic within these analyzers.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'roots' (List[str]): List of root element IDs. These are taken from
                                       `self.model.roots`, which are determined during preprocessing.
                - 'nodes' (List[str]): List of all element IDs in the model.
                - 'tree' (Dict[str, Dict[str, List[str]]]): An adjacency-list-like dictionary
                                                            representing parent-child relationships.
                                                            Keys are parent element IDs, and values are
                                                            dictionaries like `{'child': [child_ids_list]}`.
        """
        tree: Dict[str, Dict[str, Any]] = {}
        all_nodes = list(self.model.elements.keys())
        # Use self.model.roots, which was set from preprocessed_data
        roots = self.model.roots
        # Build tree for each node
        for element_id in all_nodes:
            element = self.model.get_element(element_id)
            if not element:
                continue
                
            analyzer = self.model.get_analyzer(element.element_type)
            if not analyzer:
                tree[element_id] = {"child": []}
                continue
            children = analyzer.get_children(element, self.model)
            tree[element_id] = {"child": children}
        
        return {
            "roots": roots,
            "nodes": all_nodes,
            "tree": tree
        }
    
    def build_undirected_graph(self) -> Tuple[Dict[str, Any], List[str]]:
        """Строит ненаправленный граф сети.

        Returns:
            Dict[str, Any]: Словарь с полями:
                - 'nodes': список всех идентификаторов элементов.
                - 'edges': список кортежей (source, target), представляющих связи.
        """
        graph = self.model.get_undirected_graph()
        # Используем self.model.roots, который был установлен из preprocessed_data
        roots = self.model.roots
        logger.debug("Построен ненаправленный граф: %d узлов", len(graph))
        return graph, roots
        #roots = self.model.roots # Changed from get_root_elements()
        #graph = self.model.get_undirected_graph()
        #edges = []
        #
        ## Формируем список рёбер, избегая дублирования
        #seen_edges = set()
        #for source, targets in graph.items():
        #    for target in targets:
        #        edge = tuple(sorted([source, target]))  # Сортируем, чтобы избежать (A, B) и (B, A)
        #        if edge not in seen_edges:
        #            seen_edges.add(edge)
        #            edges.append((source, target))
        #
        #return {
        #    #"roots": roots,
        #    "nodes": list(self.model.elements.keys()),
        #    "edges": edges
        #}