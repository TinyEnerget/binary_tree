import json
from pathlib import Path
from typing import Dict, Any
from collections import defaultdict
import sys
import os
# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model_processing import NetworkAnalyzer

import logging
# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GraphCreator:
    def __init__(self, model_path: str, out_path: str):
        input_file = Path(model_path)
        output_file = Path(out_path)
        if not input_file.exists():
            logger.error("Входной файл %s не найден", input_file)
        self.model_path = input_file
        self.out_path = output_file
        pass
    
    @staticmethod
    def save_json(file_path: Path, data: Dict[str, Any]) -> None:
        """Сохраняет данные в JSON-файл."""
        adjacency_dict = {node: list(neighbors) for node, neighbors in data.items()}
        text  = os.path.split(file_path)
        file_path_graph = []
        [file_path_graph.append(item) for item in text]
        file_path_graph[-1] = 'output_graph.json'
        print(file_path_graph)
        file_path_graph = os.path.join(*file_path_graph)
        print(file_path_graph)
        file_path = Path(file_path_graph)
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(adjacency_dict, file, indent=6, ensure_ascii=False)

    def load_json(self, file_path: Path) -> Dict[str, Any]:
        """Загружает данные из JSON-файла."""
        
        with open(file_path, 'r', encoding='utf-8') as file:
            adjacency_list = json.load(file)

        graph = {node: set(neighbors) for node, neighbors in adjacency_list.items()}
        return graph
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
    
    def create_graph(self) -> Dict[str, Any]:
        """
        Создает граф из словаря дерева.
        :param tree_dict: словарь дерева
        :return: словарь графа
        """

        # Построение графа
        undirected_graph = defaultdict(set)

        for parent, info in self.result["tree"].items():
            for child in info["child"]:
                undirected_graph[parent].add(child)
                undirected_graph[child].add(parent)  # добавляем обратное ребро

        GraphCreator.save_json(self.out_path, undirected_graph)
        return undirected_graph
    
    def visualize_graph_with_print(self, graph: Dict[str, Any]) -> None:
        """
        Визуализирует граф.
        :param graph: словарь графа
        :return: None
        """
        # Визуализация в виде списка рёбер
        printed = set()

        for node, neighbors in graph.items():
            for neighbor in neighbors:
                edge = tuple(sorted((node, neighbor)))
                if edge not in printed:
                    print(f"{edge[0][:6]} --- {edge[1][:6]}")
                    printed.add(edge)

    def visualize_graph_with_plot(self) -> None:
        """
        Визуализирует граф.
        :param graph: словарь графа
        :return: None
        """
        import networkx as nx
        import matplotlib.pyplot as plt
        # Визуализация в виде графика
        # Создание ненаправленного графа
        G = nx.Graph()

        # Добавление рёбер
        for parent, info in self.result["tree"].items():
            for child in info["child"]:
                G.add_edge(parent, child)

        # Визуализация
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, seed=42)  # расположение узлов
        nx.draw(G, pos, with_labels=True, node_size=700, node_color="skyblue", font_size=8, font_weight="bold", edge_color="gray")
        plt.title("Визуализация ненаправленного графа", fontsize=14)
        plt.axis("off")
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    model_path = "C:\\Users\\Vlad Titov\\Desktop\\Work\\binary_tree\\model_processing\\available_modification\\converted.json"
    out_path = "res\\output_tree.json"
    graph_creator = GraphCreator(model_path, out_path)
    graph_creator.model_to_tree()
    graph = graph_creator.create_graph()
    #graph_creator.visualize_graph_with_print(graph)
    #graph_creator.visualize_graph_with_plot()
        