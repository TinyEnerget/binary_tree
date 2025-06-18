import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import sys
import os

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model_processing import NetworkAnalyzer, NetworkModel, NetworkTreeBuilder

import logging
# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GraphCreator:
    """Класс для создания ненаправленного графа из модели электрической сети.

    Attributes:
        model_path (Path): Путь к входному JSON-файлу модели.
        out_path (Path): Путь для сохранения результирующего графа.
        result (Dict[str, Any]): Результат построения графа.
    """
    def __init__(self, model_path: str, out_path: str):
        """Инициализирует GraphCreator.

        Args:
            model_path (str): Путь к JSON-файлу модели.
            out_path (str): Путь для сохранения результирующего графа.

        Raises:
            FileNotFoundError: Если входной файл не существует.
        """
        input_file = Path(model_path)
        output_file = Path(out_path)
        if not input_file.exists():
            logger.error("Входной файл %s не найден", input_file)
            raise FileNotFoundError(f"Входной файл {input_file} не найден")
        self.model_path = input_file
        self.out_path = output_file
        self.result: Dict[str, Any] = {}
    
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
    def model_to_graph(self) -> Dict[str, Any]:
        """Конвертирует модель в ненаправленный граф.

        Returns:
            Dict[str, Any]: Словарь с полями:
                - 'nodes': список идентификаторов узлов.
                - 'edges': список кортежей (source, target), представляющих рёбра.

        Raises:
            Exception: Если произошла ошибка при анализе модели.
        """
        try:
            logger.info("Анализ модели %s для построения графа", self.model_path)
            # Загружаем модель
            model_data = NetworkAnalyzer.load_model(str(self.model_path))
            # Создаем модель сети
            network_model = NetworkModel(model_data)
            # Строим ненаправленный граф
            tree_builder = NetworkTreeBuilder(network_model)
            self.result = tree_builder.build_undirected_graph()
            # Сохраняем результат
            NetworkAnalyzer.save_tree(self.result, str(self.out_path))
            logger.info("Построение графа завершено. Результаты сохранены в %s", self.out_path)
        except Exception as e:
            logger.error("Ошибка при построении графа: %s", e)
            raise e
        finally:
            logger.info("Анализ модели завершен")
        
        return self.result
    
    def create_graph(self) -> Dict[str, Any]:
        """Создает и возвращает структуру ненаправленного графа.

        Returns:
            Dict[str, Any]: Словарь с полями 'nodes' и 'edges', представляющий граф.
        """
        if not self.result:
            self.model_to_graph()
        return self.result
    
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

    def visualize_graph_with_plot(self, graph = None) -> None:
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
    model_path = 'model_processing\\available_modification\\converted.json'
    out_path = "output_graph.json"
    graph_creator = GraphCreator(model_path, out_path)
    graph = graph_creator.create_graph()
    print(f"Граф создан: {len(graph)} узлов, "
          f"{sum(len(connections) for connections in graph.values()) // 2} рёбер")
    from graph_visualizer import GraphVisualizer
    graph_visualizer = GraphVisualizer(graph)
    graph_visualizer.draw_graph()

        