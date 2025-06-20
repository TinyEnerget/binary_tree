"""
Этот модуль предназначен для создания графовых структур из моделей.
Он использует `NetworkAnalyzer` для первоначальной обработки модели и получения
древовидной структуры, которая затем преобразуется в неориентированный граф
(представленный в виде списка смежности). Модуль также включает утилиты
для сохранения и загрузки графа в формате JSON и его визуализации.
"""
import json
from pathlib import Path
from typing import Dict, Any, Set, Optional as TypingOptional, Union # Добавлен Union
from collections import defaultdict
import sys
import os
# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model_processing import NetworkAnalyzer
from model_processing.models import NetworkAnalysisResult

import logging
# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GraphCreator:
    """
    Класс `GraphCreator` отвечает за преобразование модели сети в неориентированный граф.
    Может либо сам выполнить анализ модели через `NetworkAnalyzer` (если пути к файлам предоставлены),
    либо использовать предварительно полученный `NetworkAnalysisResult`.
    The `GraphCreator` class is responsible for transforming a network model into an undirected graph.
    It can either perform model analysis itself via `NetworkAnalyzer` (if file paths are provided)
    or use a pre-obtained `NetworkAnalysisResult`.

    Процесс включает / Process includes:
    1. Опциональный анализ исходной модели для получения `NetworkAnalysisResult` (если не предоставлен).
       Optional analysis of the source model to obtain `NetworkAnalysisResult` (if not provided).
    2. Преобразование древовидной структуры из `NetworkAnalysisResult.tree` в неориентированный граф.
       Conversion of the tree-like structure from `NetworkAnalysisResult.tree` into an undirected graph.
    3. Сохранение полученного графа в JSON-файл.
       Saving the resulting graph to a JSON file.
    Класс также предоставляет методы для визуализации графа.
    The class also provides methods for graph visualization.

    Атрибуты / Attributes:
        model_path (Optional[Path]): Путь к файлу исходной модели. Используется, если `analysis_result` не предоставлен.
                                     Path to the source model file. Used if `analysis_result` is not provided.
        out_path (Path): Путь для сохранения файла графа (`output_graph.json`) и, если применимо,
                         промежуточных результатов `NetworkAnalyzer`.
                         Path for saving the graph file (`output_graph.json`) and, if applicable,
                         intermediate results from `NetworkAnalyzer`.
        result (Optional[NetworkAnalysisResult]): Объект, хранящий результат анализа модели.
                                                  Может быть предоставлен при инициализации или получен
                                                  в результате вызова `_ensure_analysis_result()`.
                                                  An object storing the model analysis result.
                                                  Can be provided during initialization or obtained
                                                  by calling `_ensure_analysis_result()`.
    """
    def __init__(self, out_path: str, model_path: TypingOptional[str] = None, analysis_result: TypingOptional[NetworkAnalysisResult] = None):
        """
        Инициализирует объект GraphCreator.

        Необходимо предоставить `out_path`. Дополнительно, либо `analysis_result` должен быть предоставлен,
        либо `model_path` (для выполнения анализа). Если `analysis_result` предоставлен, `model_path`
        игнорируется для этапа анализа. `out_path` всегда необходим для сохранения графа.

        Initializes the GraphCreator object.

        `out_path` must be provided. Additionally, either `analysis_result` must be provided,
        or `model_path` (for performing the analysis). If `analysis_result` is provided,
        `model_path` is ignored for the analysis step. `out_path` is always required for saving the graph.

        Параметры / Parameters:
            out_path (str): Строковый путь для сохранения файла графа (`output_graph.json`).
                            Также используется как `out_path` для `NetworkAnalyzer`, если `model_path` задан.
                            String path for saving the graph file (`output_graph.json`).
                            Also used as `out_path` for `NetworkAnalyzer` if `model_path` is provided.
            model_path (Optional[str]): Путь к файлу модели (строка).
                                        Path to the model file (string).
            analysis_result (Optional[NetworkAnalysisResult]): Предварительно полученный результат анализа сети.
                                                               Pre-obtained network analysis result.
        """
        self.out_path: Path = Path(out_path) # out_path обязателен и преобразуется в Path

        if analysis_result:
            if not isinstance(analysis_result, NetworkAnalysisResult):
                msg = "Предоставленный analysis_result должен быть экземпляром NetworkAnalysisResult. / Provided analysis_result must be an instance of NetworkAnalysisResult."
                logger.error(msg)
                raise TypeError(msg)
            self.result: TypingOptional[NetworkAnalysisResult] = analysis_result
            self.model_path: TypingOptional[Path] = Path(model_path) if model_path else None
            logger.info("GraphCreator инициализирован с предварительно загруженным NetworkAnalysisResult. out_path используется для сохранения графа. / GraphCreator initialized with pre-loaded NetworkAnalysisResult. out_path is used for saving the graph.")
        elif model_path:
            input_file = Path(model_path)
            if not input_file.exists():
                msg = f"Входной файл модели {input_file} не найден. / Model input file {input_file} not found."
                logger.error(msg)
                raise FileNotFoundError(msg)
            self.model_path = input_file
            self.result = None
            logger.info(f"GraphCreator инициализирован с путями: model_path='{self.model_path}', out_path='{self.out_path}'. / GraphCreator initialized with paths: model_path='{self.model_path}', out_path='{self.out_path}'.")
        else:
            msg = "Необходимо предоставить либо 'analysis_result', либо 'model_path' (out_path обязателен в любом случае). / Either 'analysis_result' or 'model_path' must be provided (out_path is mandatory in any case)."
            logger.error(msg)
            raise ValueError(msg)


    def _ensure_analysis_result(self) -> None:
        """
        Гарантирует, что `self.result` (результат анализа типа `NetworkAnalysisResult`) доступен.
        Если `self.result` еще не установлен (None), вызывает `model_to_tree()` для его получения.
        Ensures that `self.result` (the `NetworkAnalysisResult` analysis result) is available.
        If `self.result` is not yet set (None), calls `model_to_tree()` to obtain it.

        Выбрасывает / Raises:
            ValueError: Если `model_path` не был установлен (необходим для `model_to_tree`),
                        или если `model_to_tree()` не смог установить `self.result`.
                        If `model_path` was not set (needed for `model_to_tree`),
                        or if `model_to_tree()` failed to set `self.result`.
            Исключения от `NetworkAnalyzer.analyze_network` (через `model_to_tree`).
            Exceptions from `NetworkAnalyzer.analyze_network` (via `model_to_tree`).
        """
        if self.result is None:
            if not self.model_path: # self.out_path всегда есть и проверен в __init__
                msg = "model_path должен быть установлен для выполнения model_to_tree, если analysis_result не предоставлен изначально. / model_path must be set to execute model_to_tree if analysis_result was not provided initially."
                logger.error(msg)
                raise ValueError(msg)
            logger.info("self.result не найден, вызов model_to_tree(). / self.result not found, calling model_to_tree().")
            self.model_to_tree()
            if not isinstance(self.result, NetworkAnalysisResult): # Проверка типа после вызова
                msg = "model_to_tree() не смог установить корректный self.result (ожидался NetworkAnalysisResult). / model_to_tree() failed to set a correct self.result (NetworkAnalysisResult expected)."
                logger.error(msg)
                raise ValueError(msg)

    @staticmethod
    def save_json(graph_output_path: Path, data: Dict[str, Set[str]]) -> None: # data: Dict[str, Set[str]]
        """
        Сохраняет данные графа (список смежности) в JSON-файл.

        Имя выходного файла будет `output_graph.json` и он будет сохранен
        в той же директории, что и `file_path_param`.
        Перед сохранением множества соседей конвертируются в списки.

        Параметры / Parameters:
            graph_output_path (Path): Путь к директории, куда будет сохранен файл `output_graph.json`.
                                      Path to the directory where `output_graph.json` will be saved.
            data (Dict[str, Set[str]]): Данные графа в виде словаря списков смежности (узлы и соседи - строки).
                                        Graph data as an adjacency list dictionary (nodes and neighbors are strings).
        """
        # Преобразование множеств строк в списки строк для JSON-сериализации
        adjacency_dict_serializable: Dict[str, List[str]] = {
            str(node): [str(neighbor) for neighbor in neighbors]
            for node, neighbors in data.items()
        }
        
        output_directory = graph_output_path
        if output_directory.is_file(): # Если случайно передали путь к файлу вместо директории
            output_directory = output_directory.parent

        output_directory.mkdir(parents=True, exist_ok=True)
        actual_save_path = output_directory / 'output_graph.json'

        logger.info(f"Сохранение графа в: {actual_save_path} / Saving graph to: {actual_save_path}")
        try:
            with open(actual_save_path, 'w', encoding='utf-8') as file:
                json.dump(adjacency_dict_serializable, file, indent=4, ensure_ascii=False)
            logger.info(f"Граф успешно сохранен в {actual_save_path}. / Graph saved successfully to {actual_save_path}.")
        except IOError as e:
            logger.error(f"Ошибка ввода-вывода при сохранении файла графа {actual_save_path}: {e} / IO error saving graph file {actual_save_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при сохранении графа в {actual_save_path}: {type(e).__name__} - {e} / Unexpected error saving graph to {actual_save_path}: {type(e).__name__} - {e}")
            raise


    def load_json(self, file_path: Union[str, Path]) -> Dict[str, Set[str]]: # file_path должен быть полным путем к файлу output_graph.json
        """
        Загружает данные графа (список смежности) из JSON-файла.

        Эта функция является общей утилитой и не используется напрямую другими методами
        класса `GraphCreator` в текущей реализации для его основной логики работы.
        Она может быть полезна для загрузки ранее сохраненных графов для анализа или тестирования.

        Параметры / Parameters:
            file_path (Union[str, Path]): Путь к JSON-файлу, содержащему граф.
                                          Path to the JSON file containing the graph.

        Возвращает / Returns:
            Dict[str, Set[str]]: Загруженный граф в виде словаря, где ключи - узлы (строки),
                                 а значения - множества их соседей (строк).
                                 The loaded graph as a dictionary, where keys are nodes (strings)
                                 and values are sets of their neighbors (strings).
        """
        file_path_obj = Path(file_path) if isinstance(file_path, str) else file_path
        try:
            logger.info(f"Загрузка графа из: {file_path_obj} / Loading graph from: {file_path_obj}")
            with open(file_path_obj, 'r', encoding='utf-8') as file:
                adjacency_list_loaded = json.load(file)

            graph: Dict[str, Set[str]] = {
                str(node): {str(neighbor) for neighbor in neighbors}
                for node, neighbors in adjacency_list_loaded.items()
            }
            logger.info(f"Граф успешно загружен из {file_path_obj}. / Graph loaded successfully from {file_path_obj}.")
            return graph
        except FileNotFoundError:
            logger.error(f"Файл графа не найден: {file_path_obj} / Graph file not found: {file_path_obj}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON из файла графа {file_path_obj}: {e} / JSON decoding error from graph file {file_path_obj}: {e}")
            raise
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при загрузке графа из {file_path_obj}: {type(e).__name__} - {e} / Unexpected error loading graph from {file_path_obj}: {type(e).__name__} - {e}")
            raise

    def model_to_tree(self) -> None: # Этот метод теперь только устанавливает self.result
        """
        Обрабатывает исходную модель с помощью `NetworkAnalyzer` для получения
        промежуточной древовидной структуры в виде объекта `NetworkAnalysisResult`.

        Результат анализа (экземпляр `NetworkAnalysisResult`) сохраняется в атрибуте `self.result`.
        `NetworkAnalyzer` также может самостоятельно сохранять этот результат в файл,
        указанный при инициализации `NetworkAnalyzer` (в данном случае, `self.out_path`).
        Этот метод является подготовительным шагом перед созданием графа.
        Processes the source model using `NetworkAnalyzer` to obtain an intermediate
        tree-like structure as a `NetworkAnalysisResult` object.

        The analysis result (an instance of `NetworkAnalysisResult`) is stored in the
        `self.result` attribute. `NetworkAnalyzer` might also save this result to
        the file specified during its initialization (`self.out_path` in this case).
        This method is a preparatory step before graph creation.

        Выбрасывает / Raises:
            FileNotFoundError: Если файл модели `model_path` не найден (от `NetworkAnalyzer`).
            json.JSONDecodeError: Если файл модели содержит некорректный JSON (от `NetworkAnalyzer`).
            ValueError: Если структура данных модели некорректна (от `NetworkAnalyzer`).
            NetworkModelError: Если возникают ошибки при создании или парсинге `NetworkModel` (от `NetworkAnalyzer`).
            Exception: Любые другие непредвиденные исключения от `NetworkAnalyzer.analyze_network`.
                       Propagates exceptions from `NetworkAnalyzer.analyze_network` such as
                       `FileNotFoundError`, `json.JSONDecodeError`, `ValueError`, `NetworkModelError`.
        """
        try:
            logger.info(f"Анализ модели для создания графа: {self.model_path} / Analyzing model for graph creation: {self.model_path}")
            analysis_result_obj: NetworkAnalysisResult = NetworkAnalyzer.analyze_network(str(self.model_path), str(self.out_path))
            self.result = analysis_result_obj
            logger.info(f"Анализ модели (для графа) завершен. Промежуточные результаты (если сохранены NetworkAnalyzer) в: {self.out_path} / Model analysis (for graph) complete. Intermediate results (if saved by NetworkAnalyzer) are in: {self.out_path}")
        except (FileNotFoundError, json.JSONDecodeError, ValueError, NetworkModelError) as e:
            # Эти ошибки уже залогированы в NetworkAnalyzer, здесь просто пробрасываем их выше.
            logger.error(f"Ошибка при анализе модели в NetworkAnalyzer (вызов из GraphCreator): {type(e).__name__} - {e} / Error during model analysis in NetworkAnalyzer (called from GraphCreator): {type(e).__name__} - {e}")
            raise
        except Exception as e: # Другие неожиданные ошибки
            logger.error(f"Непредвиденная ошибка при анализе модели (вызов NetworkAnalyzer.analyze_network): {type(e).__name__} - {e} / Unexpected error during model analysis (calling NetworkAnalyzer.analyze_network): {type(e).__name__} - {e}")
            raise e
        # Метод изменяет состояние объекта (self.result), поэтому возвращать None - нормально.

    def create_graph(self) -> Dict[str, Set[Any]]:
        """
        Создает неориентированный граф из древовидной структуры, хранящейся в `self.result.tree`.
        Creates an undirected graph from the tree-like structure stored in `self.result.tree`.

        Граф представляется в виде списка смежности (словарь, где ключи - узлы,
        а значения - множества их соседей).
        Для каждой связи "родитель-потомок" из `self.result.tree` добавляются
        ребра в обоих направлениях (родитель-потомок и потомок-родитель).
        Созданный граф сохраняется в файл `output_graph.json` в директории,
        определяемой `self.out_path`, с помощью `save_json`.
        The graph is represented as an adjacency list (dictionary where keys are nodes,
        and values are sets of their neighbors).
        For each parent-child link from `self.result.tree`, edges are added in
        both directions (parent-child and child-parent).
        The created graph is saved to `output_graph.json` in the directory
        determined by `self.out_path`, using `save_json`.

        Перед вызовом этого метода должен быть успешно выполнен `model_to_tree`,
        чтобы `self.result` (типа `NetworkAnalysisResult`) содержал необходимые данные.
        Before calling this method, `model_to_tree` must have been successfully executed
        so that `self.result` (of type `NetworkAnalysisResult`) contains the necessary data.

        Возвращает / Returns:
            Dict[str, Set[Any]]: Созданный граф в виде списка смежности.
                                 The created graph as an adjacency list.

        Перед вызовом этого метода, атрибут `self.result` должен быть корректно установлен.
        Before calling this method, the `self.result` attribute must be correctly set.

        Возвращает / Returns:
            Dict[str, Set[str]]: Созданный граф в виде списка смежности (узлы и соседи - строки).
                                 The created graph as an adjacency list (nodes and neighbors are strings).

        Выбрасывает / Raises:
            ValueError: Если `self.result` или `self.result.tree` отсутствуют или имеют неверный тип.
                        If `self.result` or `self.result.tree` are missing or have an incorrect type.
            OSError: Если возникает ошибка при сохранении созданного графа в JSON-файл.
                     If an error occurs while saving the created graph to a JSON file.
        """
        self._ensure_analysis_result()

        if not isinstance(self.result, NetworkAnalysisResult) or \
           not hasattr(self.result, 'tree') or \
           not isinstance(self.result.tree, dict):
            msg = "Атрибут 'tree' в self.result отсутствует или имеет неверный тип. Невозможно создать граф. / 'tree' attribute in self.result is missing or has an incorrect type. Cannot create graph."
            logger.error(msg)
            raise ValueError(msg)

        undirected_graph: Dict[str, Set[str]] = defaultdict(set)
        tree_data = self.result.tree

        try:
            for parent, info in tree_data.items():
                parent_str = str(parent)
                if isinstance(info, dict) and "child" in info:
                    children = info["child"]
                    if isinstance(children, list):
                        for child in children:
                            child_str = str(child)
                            undirected_graph[parent_str].add(child_str)
                            undirected_graph[child_str].add(parent_str)
                    else:
                        logger.warning(f"Для родителя '{parent_str}' поле 'child' не является списком: {children}. Пропуск этих детей. / For parent '{parent_str}', 'child' field is not a list: {children}. Skipping these children.")
                else:
                    logger.warning(f"Узел '{parent_str}' в self.result.tree имеет некорректный формат данных (отсутствует 'child' или не словарь): {info}. / Node '{parent_str}' in self.result.tree has incorrect data format (missing 'child' or not a dictionary): {info}.")
        except (TypeError, AttributeError) as e:
            msg = f"Ошибка при доступе к данным в self.result.tree при построении графа: {e} / Error accessing data in self.result.tree during graph construction: {e}"
            logger.error(msg)
            raise ValueError(msg) from e

        try:
            GraphCreator.save_json(self.out_path, undirected_graph)
            logger.info(f"Граф создан и сохранен в директории '{self.out_path}' как 'output_graph.json'. / Graph created and saved in directory '{self.out_path}' as 'output_graph.json'.")
        except OSError as e:
            logger.error(f"Ошибка при сохранении файла графа: {e} / Error saving graph file: {e}")
            raise

        return undirected_graph

    def visualize_graph_with_print(self, graph: Dict[str, Set[str]]) -> None:
        """
        Выполняет простую текстовую визуализацию графа в консоли.

        Печатает каждое ребро графа в формате "узел1 --- узел2".
        Чтобы избежать дублирования ребер (например, A --- B и B --- A),
        отслеживает уже напечатанные ребра. Для вывода отображаются только первые 6 символов имени узла.

        Параметры / Parameters:
            graph (Dict[str, Set[str]]): Граф в виде списка смежности (узлы и соседи - строки) для визуализации.
                                         The graph as an adjacency list (nodes and neighbors are strings) to visualize.
        """
        logger.info("Визуализация графа (текстовая) / Visualizing graph (text-based):")
        if not graph:
            print("Граф пуст. Нечего визуализировать. / Graph is empty. Nothing to visualize.")
            return

        printed_edges: Set[Tuple[str,str]] = set()

        for node, neighbors in graph.items():
            for neighbor in neighbors:
                edge = tuple(sorted((str(node), str(neighbor))))
                if edge not in printed_edges:
                    print(f"{edge[0][:20]:<20} --- {edge[1][:20]}")
                    printed_edges.add(edge)
        if not printed_edges:
            print("В графе нет ребер для отображения. / No edges in the graph to display.")


    def visualize_graph_with_plot(self, graph: TypingOptional[Dict[str, Set[str]]] = None) -> None:
        """
        Визуализирует граф с использованием библиотек `networkx` и `matplotlib`.
        Visualizes the graph using `networkx` and `matplotlib` libraries.

        Если граф не передан в параметре `graph`, используется `self.result.tree`
        (данные из `NetworkAnalysisResult`) для построения временного графа для визуализации.
        Это может быть не всегда желаемым поведением, если `create_graph` уже был вызван
        и, возможно, граф был изменен после этого.
        Для корректной работы этого метода должны быть установлены библиотеки
        `networkx` и `matplotlib`.
        If a graph is not provided in the `graph` parameter, `self.result.tree`
        (data from `NetworkAnalysisResult`) is used to build a temporary graph for visualization.
        This might not always be the desired behavior if `create_graph` has already been
        called and the graph potentially modified afterwards.
        The `networkx` and `matplotlib` libraries must be installed for this method to work.

        Параметры / Parameters:
            graph (Optional[Dict[str, Set[Any]]]): Граф в виде списка смежности для визуализации.
                                                   Если None, будет использован `self.result.tree`.
                                                   The graph as an adjacency list. If None, `self.result.tree` will be used.

        Примечание / Note:
            Убедитесь, что библиотеки `networkx` и `matplotlib` установлены:
            `pip install networkx matplotlib`
            Ensure `networkx` and `matplotlib` are installed:
            `pip install networkx matplotlib`
        """
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
        except ImportError:
            logger.error("Библиотеки networkx и/или matplotlib не установлены. Визуализация невозможна. / Networkx and/or matplotlib are not installed. Visualization is not possible.")
            print("Пожалуйста, установите networkx и matplotlib для использования этой функции: pip install networkx matplotlib")
            return

        logger.info("Визуализация графа (графическая) / Visualizing graph (plot-based):")

        target_graph_data: TypingOptional[Dict[str, Any]] = None # Уточнил тип
        if graph is not None:
            target_graph_data = graph
            logger.info("Используется переданный граф для визуализации. / Using provided graph for visualization.")
        elif self.result is not None and hasattr(self.result, 'tree') and isinstance(self.result.tree, dict): # self.result должен быть NetworkAnalysisResult
            self._ensure_analysis_result() # Убедимся, что self.result точно NetworkAnalysisResult, если он был None
            logger.info("Граф не передан, используется self.result.tree для построения временного графа для визуализации. / Graph not provided, using self.result.tree to build a temporary graph for visualization.")
            temp_graph = defaultdict(set)
            tree_data_for_plot = self.result.tree # self.result здесь точно NetworkAnalysisResult
            try:
                for parent, info in tree_data_for_plot.items():
                     if isinstance(info, dict) and "child" in info and isinstance(info["child"], list):
                        for child_node in info["child"]:
                            temp_graph[str(parent)].add(str(child_node))
                            temp_graph[str(child_node)].add(str(parent))
                     else:
                        logger.warning(f"Узел '{parent}' в self.result.tree (для visualize_graph_with_plot) имеет некорректный формат 'child': {info}. / Node '{parent}' in self.result.tree (for visualize_graph_with_plot) has incorrect 'child' format: {info}.")
                target_graph_data = temp_graph
            except (TypeError, AttributeError) as e:
                logger.error(f"Ошибка при доступе к данным в self.result.tree для визуализации: {e} / Error accessing data in self.result.tree for visualization: {e}")
                print("Ошибка данных для визуализации графа. / Data error for graph visualization.")
                return
        else:
            # Вызов _ensure_analysis_result(), если self.result еще не установлен
            if self.result is None:
                try:
                    self._ensure_analysis_result()
                    # Повторная попытка получить данные для target_graph_data
                    if isinstance(self.result, NetworkAnalysisResult) and hasattr(self.result, 'tree') and isinstance(self.result.tree, dict):
                        # Эта часть дублирует логику выше, можно вынести в отдельный метод
                        logger.info("Повторная попытка: используется self.result.tree для построения временного графа. / Retry: using self.result.tree to build temporary graph.")
                        temp_graph = defaultdict(set)
                        tree_data_for_plot = self.result.tree
                        for parent, info in tree_data_for_plot.items():
                             if isinstance(info, dict) and "child" in info and isinstance(info["child"], list):
                                for child_node in info["child"]:
                                    temp_graph[str(parent)].add(str(child_node))
                                    temp_graph[str(child_node)].add(str(parent))
                             else:
                                logger.warning(f"Узел '{parent}' в self.result.tree (для visualize_graph_with_plot, повтор) имеет некорректный формат 'child': {info}.")
                        target_graph_data = temp_graph
                    else:
                        logger.warning("Не удалось получить self.result.tree даже после _ensure_analysis_result. / Failed to obtain self.result.tree even after _ensure_analysis_result.")
                        print("Нет данных для визуализации графа. / No data to visualize graph.")
                        return
                except Exception as e:
                    logger.error(f"Ошибка при вызове _ensure_analysis_result для visualize_graph_with_plot: {e} / Error calling _ensure_analysis_result for visualize_graph_with_plot: {e}")
                    print("Ошибка подготовки данных для визуализации графа. / Error preparing data for graph visualization.")
                    return
            else: # self.result есть, но это не NetworkAnalysisResult или .tree некорректен
                print("Нет данных для визуализации графа (self.result некорректен). / No data to visualize graph (self.result is incorrect).")
                logger.warning("Нет данных для визуализации графа (self.result некорректен или отсутствует .tree). / No data for graph visualization (self.result incorrect or .tree missing).")
            return

        if not target_graph_data: # Дополнительная проверка
            print("Данные графа пусты. Нечего визуализировать. / Graph data is empty. Nothing to visualize.")
            return

        G = nx.Graph()
        # Добавление рёбер из списка смежности
        for node, neighbors in target_graph_data.items():
            for neighbor in neighbors:
                G.add_edge(str(node), str(neighbor))


        if not G.nodes():
            print("Граф не содержит узлов после обработки. Нечего визуализировать. / Graph contains no nodes after processing. Nothing to visualize.")
            return

        plt.figure(figsize=(16, 12)) # Увеличен размер для лучшей читаемости
        pos = nx.spring_layout(G, seed=42)  # расположение узлов
        nx.draw(G, pos, with_labels=True, node_size=700, node_color="skyblue", font_size=8, font_weight="bold", edge_color="gray")
        plt.title("Визуализация ненаправленного графа", fontsize=14)
        plt.axis("off")
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    model_path = "model_processing\\available_modification\\converted.json"
    out_path = "res\\output_tree.json"
    graph_creator = GraphCreator(model_path, out_path)
    graph_creator.model_to_tree()
    graph = graph_creator.create_graph()
    #graph_creator.visualize_graph_with_print(graph)
    #graph_creator.visualize_graph_with_plot()
        