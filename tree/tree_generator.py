import json
from pathlib import Path
from typing import Dict, Any
import sys
import os
# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree_analyzer.tree_construction import Node
from model_processing import NetworkAnalyzer

import logging
# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TreeCreator:
    def __init__(self, model_path: str, out_path: str):
        input_file = Path(model_path)
        output_file = Path(out_path)
        if not input_file.exists():
            logger.error("Входной файл %s не найден", input_file)
        self.model_path = input_file
        self.out_path = output_file
        pass
    def model_to_tree(self) -> Dict[str, Any]:
        """
        Конвертирует модель в словарь дерева.
        :param model_path: путь к модели
        :param out_path: путь к выходному файлу
        :return: словарь дерева
        """
        try:
            logger.info("Анализ модели %s", self.model_path)
            self.result: Dict[str, Any] = NetworkAnalyzer.analyze_network(str(self.model_path), str(self.out_path))
            logger.info("Анализ завершен. Результаты сохранены в %s", self.out_path)
        except Exception as e:
            logger.error("Ошибка при анализе модели: %s", e)
            raise e
        return 

    def create_tree(self) -> list[Node]: #, result: Dict[str, Any]
        """
        Создает дерево из словаря.
        :param tree_dict: словарь дерева
        :return: корневой узел дерева
        """
        #if not result:
        #    return None

        self.model_to_tree()
        tree_dict: Dict[str, list[str]] = self.result['tree']

        def create_node(value: str) -> Node:
            node = Node(value)
            return node
        
        for node_id in self.result['nodes']:
            node = create_node(node_id)
            setattr(self, node_id, node)

        for key, value in tree_dict.items():
            [getattr(self, key).add_child(getattr(self,item)) for item in value['child']]
        
        roots = [getattr(self, item) for item in self.result['roots']]
        return roots
if __name__ == '__main__':
    model_path = 'C:\\Users\\Vlad Titov\\Desktop\\Work\\binary_tree\\model_processing\\available_modification\\converted.json'
    out_path = "output.json"
    tree = TreeCreator(model_path, out_path)
    #result = tree.model_to_tree()
    roots = tree.create_tree()