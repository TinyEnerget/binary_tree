from typing import Dict, Any
from .models import NetworkModel, NetworkElement, ElementType

class NetworkTreeBuilder:
    """Построитель дерева электрической сети.

    Формирует иерархическую структуру сети, определяя корневые элементы и их дочерние связи.

    Args:
        model (NetworkModel): Модель сети, содержащая элементы и их соединения.
    """
    
    def __init__(self, model: NetworkModel):
        self.model = model
    
    def build_tree(self) -> Dict[str, Any]:
        """Строит дерево сети.

        Проходит по всем элементам сети, определяет их дочерние элементы с использованием
        соответствующих анализаторов и формирует структуру дерева.

        Returns:
            Dict[str, Any]: Словарь с полями:
                - 'roots': список идентификаторов корневых элементов.
                - 'nodes': список всех идентификаторов элементов.
                - 'tree': словарь, где ключ — идентификатор элемента, значение — словарь с полем
                          'child', содержащим список идентификаторов дочерних элементов.
        """
        tree: Dict[str, Dict[str, Any]] = {}
        all_nodes = list(self.model.elements.keys())
        roots = self.model.get_root_elements()
        # Строим дерево для каждого узла
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