from typing import Dict, Any
from .utils import load_json, save_json
from .comparator import TreeComparator
from .models import NetworkModel
from .tree_builder import NetworkTreeBuilder


class NetworkAnalyzer:
    """Основной класс для анализа электрической сети и построения её дерева.

    Координирует процесс загрузки модели, создания дерева и сравнения c эталонным результатом.
    """
    
    @staticmethod
    def load_model(file_path: str) -> Dict[str, Any]:
        """Загружает модель сети из JSON-файла.

        Args:
            file_path (str): Путь к JSON-файлу.

        Returns:
            Dict[str, Any]: Данные модели сети.

        Raises:
            FileNotFoundError: Если файл не найден.
            json.JSONDecodeError: Если файл содержит некорректный JSON.
        """
        return load_json(file_path)
    
    @staticmethod
    def save_tree(tree_data: Dict[str, Any], file_path: str) -> None:
        """Сохраняет дерево сети в JSON-файл.

        Args:
            tree_data (Dict[str, Any]): Данные дерева сети.
            file_path (str): Путь для сохранения файла.

        Raises:
            OSError: Если не удается записать файл.
        """
        save_json(file_path, tree_data)
    
    @classmethod
    def analyze_network(cls, model_path: str, output_path: str | None = None) -> Dict[str, Any]:
        """Анализирует сеть и строит дерево.

        Args:
            model_path (str): Путь к JSON-файлу c моделью сети.
            output_path (str, optional): Путь для сохранения результирующего дерева. Если не указан,
                результат не сохраняется.

        Returns:
            Dict[str, Any]: Словарь c полями 'roots', 'nodes' и 'tree', описывающий структуру сети.

        Raises:
            FileNotFoundError: Если входной файл модели не найден.
        """
        # Загружаем модель
        model_data = cls.load_model(model_path)
        model_data = cls.rewrite_nodes(model_data)
        model_data = cls.find_root_nodes(model_data)
        
        # Создаем модель сети
        network_model = NetworkModel(model_data)
        # Строим дерево
        tree_builder = NetworkTreeBuilder(network_model)
        tree_result = tree_builder.build_tree()
        
        # Сохраняем результат, если указан путь
        if output_path:
            cls.save_tree(tree_result, output_path)
        
        return tree_result
    
    @classmethod
    def compare_with_reference(cls, result: Dict[str, Any], reference_path: str) -> bool:
        """Сравнивает результат построения дерева c эталонным.

        Args:
            result (Dict[str, Any]): Результат построения дерева (содержит 'roots', 'nodes', 'tree').
            reference_path (str): Путь к JSON-файлу c эталонным деревом.

        Returns:
            bool: True, если результат совпадает c эталоном, иначе False.

        Raises:
            FileNotFoundError: Если эталонный файл не найден.
        """
        reference = cls.load_model(reference_path)
        return TreeComparator.compare(result, reference)
    
    @classmethod
    def rewrite_nodes(cls, model: dict) -> dict:
        nodes = {}
        for key, value in model['nodes'].items():
            #print(f'Key: {key}, Value: {value}')
            for id in value:
                if 'bus' == model['elements'][id]['Type']:
                    nodes[id] = value
                    #print(f'Node: {id}, Value: {value}')

        clear_nodes = {}
        for key, value in nodes.items():
            new_value = []
            #print(f'Key: {key}, Value: {value}')
            for item in value:
                if key != item:
                    new_value.append(item)
            clear_nodes[key] = new_value
            #print(f'New Key: {key}, New Value: {new_value}')
        model['nodes'] = clear_nodes
        return model

    @classmethod
    def find_root_nodes(cls, model):
        nodes = []
        roots = []
        for key, node in model['nodes'].items():
            nodes.extend(node)
            #nodes.append(key)

        nodes = list(set(nodes))

        for node in nodes: 
            if model['elements'][node]['Type'] == 'system':
                roots.append(node)

        model['roots'] = roots
        model['nodes_id'] = nodes
        return model
