"""
Этот модуль предназначен для создания древовидной структуры на основе анализа модели сети.
Он использует класс `NetworkAnalyzer` из модуля `model_processing` для анализа
исходной модели и класс `Node` из `tree_analyzer.tree_construction` для построения
узлов дерева. Результатом работы является список корневых узлов дерева.
"""
import json
from pathlib import Path
from typing import Dict, Any, List as TypingList, Optional # Added Optional
import sys
import os
# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree_analyzer.tree_construction import Node
from model_processing import NetworkAnalyzer
from model_processing.models import NetworkAnalysisResult

import logging
# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TreeCreator:
    """
    Класс `TreeCreator` отвечает за преобразование модели сети в древовидную структуру данных.
    Может либо сам выполнить анализ модели через `NetworkAnalyzer` (если пути к файлам предоставлены),
    либо использовать предварительно полученный `NetworkAnalysisResult`.
    The `TreeCreator` class is responsible for transforming a network model into a tree-like data structure.
    It can either perform model analysis itself via `NetworkAnalyzer` (if file paths are provided)
    or use a pre-obtained `NetworkAnalysisResult`.

    Атрибуты / Attributes:
        model_path (Optional[Path]): Путь к файлу модели. Используется, если `analysis_result` не предоставлен.
                                     Path to the model file. Used if `analysis_result` is not provided.
        out_path (Optional[Path]): Путь для сохранения промежуточных результатов анализа `NetworkAnalyzer`.
                                   Path for saving intermediate analysis results by `NetworkAnalyzer`.
        result (Optional[NetworkAnalysisResult]): Объект, содержащий результаты анализа модели.
                                                  Может быть предоставлен при инициализации или получен
                                                  в результате вызова `model_to_tree()`.
                                                  An object containing the model analysis results.
                                                  Can be provided during initialization or obtained
                                                  by calling `model_to_tree()`.
    """
    def __init__(self, model_path: Optional[str] = None, out_path: Optional[str] = None, analysis_result: Optional[NetworkAnalysisResult] = None):
        """
        Инициализирует объект TreeCreator.

        Либо `analysis_result` должен быть предоставлен, либо `model_path` и `out_path`
        (для выполнения анализа). Если `analysis_result` предоставлен, `model_path` и `out_path` игнорируются
        для этапа анализа, но могут быть использованы для других целей, если класс будет расширен.

        Initializes the TreeCreator object.

        Either `analysis_result` must be provided, or both `model_path` and `out_path`
        (for performing the analysis). If `analysis_result` is provided, `model_path` and `out_path`
        are ignored for the analysis step but might be used for other purposes if the class is extended.

        Параметры / Parameters:
            model_path (Optional[str]): Путь к файлу модели.
                                        Path to the model file.
            out_path (Optional[str]): Путь для сохранения файла с результатами анализа `NetworkAnalyzer`.
                                      Path to save the analysis results file by `NetworkAnalyzer`.
            analysis_result (Optional[NetworkAnalysisResult]): Предварительно полученный результат анализа сети.
                                                               Pre-obtained network analysis result.
        """
        if analysis_result:
            if not isinstance(analysis_result, NetworkAnalysisResult):
                raise TypeError("Предоставленный analysis_result должен быть экземпляром NetworkAnalysisResult. / Provided analysis_result must be an instance of NetworkAnalysisResult.")
            self.result = analysis_result
            # model_path и out_path могут быть None, если результат уже есть
            self.model_path = Path(model_path) if model_path else None
            self.out_path = Path(out_path) if out_path else None
            logger.info("TreeCreator инициализирован с предварительно загруженным NetworkAnalysisResult. / TreeCreator initialized with pre-loaded NetworkAnalysisResult.")
        elif model_path and out_path:
            input_file = Path(model_path)
            if not input_file.exists():
                logger.error(f"Входной файл модели {input_file} не найден. / Model input file {input_file} not found.")
                # Рекомендуется выбрасывать исключение, если файл критичен и результат не предоставлен
                raise FileNotFoundError(f"Входной файл модели {input_file} не найден. / Model input file {input_file} not found.")
            self.model_path = input_file
            self.out_path = Path(out_path)
            self.result = None
            logger.info(f"TreeCreator инициализирован с путями: model_path='{model_path}', out_path='{out_path}'. / TreeCreator initialized with paths: model_path='{model_path}', out_path='{out_path}'.")
        else:
            msg = "Необходимо предоставить либо 'analysis_result', либо 'model_path' и 'out_path'. / Either 'analysis_result' or both 'model_path' and 'out_path' must be provided."
            logger.error(msg)
            raise ValueError(msg)

    def _ensure_analysis_result(self) -> None:
        """
        Гарантирует, что `self.result` (результат анализа) доступен.
        Если `self.result` еще не установлен (None), вызывает `model_to_tree()` для его получения.
        Ensures that `self.result` (the analysis result) is available.
        If `self.result` is not yet set (None), calls `model_to_tree()` to obtain it.

        Выбрасывает / Raises:
            ValueError: Если `model_path` или `out_path` не были установлены (необходимы для `model_to_tree`).
                        If `model_path` or `out_path` were not set (needed for `model_to_tree`).
            Исключения от `NetworkAnalyzer.analyze_network` (через `model_to_tree`).
            Exceptions from `NetworkAnalyzer.analyze_network` (via `model_to_tree`).
        """
        if self.result is None:
            if not self.model_path or not self.out_path:
                msg = "model_path и out_path должны быть установлены для выполнения model_to_tree, если analysis_result не предоставлен изначально. / model_path and out_path must be set to execute model_to_tree if analysis_result was not provided initially."
                logger.error(msg)
                raise ValueError(msg)
            logger.info("self.result не найден, вызов model_to_tree(). / self.result not found, calling model_to_tree().")
            self.model_to_tree() # Загрузит и проанализирует модель
            if self.result is None: # Дополнительная проверка после вызова model_to_tree
                msg = "model_to_tree() не смог установить self.result. / model_to_tree() failed to set self.result."
                logger.error(msg)
                raise ValueError(msg)


    def model_to_tree(self) -> None: # Этот метод теперь только устанавливает self.result, если он не был передан в __init__
        """
        Анализирует модель сети с помощью `NetworkAnalyzer` и сохраняет результат в `self.result`.
        Вызывается, если `self.result` не был предоставлен при инициализации.

        Этот метод вызывает `NetworkAnalyzer.analyze_network` для обработки файла модели,
        указанного в `self.model_path`. Результаты анализа, инкапсулированные в объект
        `NetworkAnalysisResult`, сохраняются в атрибуте `self.result`.
        `NetworkAnalyzer` также может сохранять эти данные в файл, указанный в `self.out_path`.

        В случае ошибок при анализе моделью в `NetworkAnalyzer.analyze_network` (например,
        `FileNotFoundError`, `json.JSONDecodeError`, `ValueError`, `NetworkModelError`),
        эти исключения будут проброшены дальше. Данный метод логирует ошибку и также
        пробрасывает исключение.
        """
        if not self.model_path or not self.out_path: # Должны быть установлены, если result не передан
             msg = "model_path и out_path не установлены. Невозможно выполнить анализ модели. / model_path and out_path are not set. Cannot perform model analysis."
             logger.error(msg)
             raise ValueError(msg)
        try:
            logger.info("Анализ модели %s для построения дерева / Analyzing model %s for tree construction", self.model_path, self.model_path)
            analysis_result_obj: NetworkAnalysisResult = NetworkAnalyzer.analyze_network(str(self.model_path), str(self.out_path))
            self.result = analysis_result_obj
            logger.info("Анализ модели завершен. Промежуточные результаты (если были сохранены NetworkAnalyzer) находятся в %s / Model analysis complete. Intermediate results (if saved by NetworkAnalyzer) are in %s", self.out_path, self.out_path)
        except Exception as e:
            logger.error("Ошибка при вызове NetworkAnalyzer.analyze_network из TreeCreator.model_to_tree: %s (%s) / Error calling NetworkAnalyzer.analyze_network from TreeCreator.model_to_tree: %s (%s)", type(e).__name__, e, type(e).__name__, e)
            raise # Пробрасываем исключение дальше

    def create_tree(self) -> TypingList[Node]: # Используем TypingList для ясности
        """
        Создает и возвращает список корневых узлов дерева на основе данных из `self.result`.

        Если `self.result` еще не установлен (например, `analysis_result` не был передан в `__init__`),
        сначала вызывается `_ensure_analysis_result()` для его получения через `model_to_tree()`.
        Затем, на основе данных из `self.result.tree` (описывающего связи) и `self.result.nodes`
        (списка всех ID элементов), строятся объекты `Node`. Связи между узлами устанавливаются
        в соответствии со структурой в `self.result.tree`. Корневые узлы определяются из `self.result.roots`.

        Возвращает / Returns:
            TypingList[Node]: Список корневых узлов построенного дерева. Если модель пуста,
                              результат анализа отсутствует или некорректен, или не удалось
                              определить корни, может вернуть пустой список.
        """
        self._ensure_analysis_result() # Гарантируем, что self.result доступен
        
        # После _ensure_analysis_result, self.result не должен быть None и должен быть NetworkAnalysisResult
        if not isinstance(self.result, NetworkAnalysisResult):
            logger.warning("Результаты анализа модели (self.result) отсутствуют или имеют неверный тип. Невозможно построить дерево. / Model analysis results (self.result) are missing or have an incorrect type. Cannot build tree.")
            return []

        # Доступ к данным через атрибуты объекта NetworkAnalysisResult
        tree_dict: Dict[str, Dict[str, List[str]]] = self.result.tree
        all_node_ids: TypingList[str] = self.result.nodes
        root_ids_from_result: TypingList[str] = self.result.roots

        if not tree_dict or not all_node_ids:
            logger.warning("Данные дерева (tree_dict) или список узлов (all_node_ids) пусты в NetworkAnalysisResult. Невозможно построить дерево. / Tree data (tree_dict) or node list (all_node_ids) is empty in NetworkAnalysisResult. Cannot build tree.")
            return []

        created_nodes: Dict[str, Node] = {}

        # Создаем все узлы (экземпляры Node)
        for node_id in all_node_ids:
            node = Node(node_id)
            created_nodes[node_id] = node

        # Устанавливаем связи между узлами на основе tree_dict
        for parent_id, connection_info in tree_dict.items():
            parent_node_obj = created_nodes.get(parent_id)
            if parent_node_obj and 'child' in connection_info:
                for child_id_str in connection_info['child']:
                    child_node_obj = created_nodes.get(child_id_str)
                    if child_node_obj:
                        parent_node_obj.add_child(child_node_obj)
                    else:
                        logger.warning(f"Дочерний узел с ID '{child_id_str}' не найден в created_nodes для родителя '{parent_id}'. / Child node with ID '{child_id_str}' not found in created_nodes for parent '{parent_id}'.")
            elif not parent_node_obj:
                 logger.warning(f"Родительский узел с ID '{parent_id}' из tree_dict не найден в created_nodes. / Parent node with ID '{parent_id}' from tree_dict not found in created_nodes.")

        # Формируем список корневых узлов
        actual_roots: TypingList[Node] = [created_nodes[root_id] for root_id in root_ids_from_result if root_id in created_nodes]
        
        # Логика автоматического определения корней, если они не были заданы явно
        if not actual_roots and all_node_ids:
             logger.info("Корневые узлы не были предоставлены в NetworkAnalysisResult или не найдены. Попытка автоматического определения. / Root nodes were not provided in NetworkAnalysisResult or not found. Attempting automatic detection.")
             all_children_ids: Set[str] = set()
             for connection_info in tree_dict.values():
                 all_children_ids.update(connection_info.get('child', []))

             potential_roots = [created_nodes[node_id] for node_id in all_node_ids if node_id not in all_children_ids and node_id in created_nodes]

             if not potential_roots and all_node_ids:
                 logger.warning("Не удалось автоматически определить корневые узлы. / Failed to automatically determine root nodes.")
                 return []
             actual_roots = potential_roots
             logger.info(f"Автоматически определенные корневые узлы: {[r.value for r in actual_roots]} / Automatically determined root nodes: {[r.value for r in actual_roots]}")

        if not actual_roots:
            logger.warning("Не удалось сформировать список корневых узлов. / Failed to form the list of root nodes.")

        return actual_roots
if __name__ == '__main__':
    model_path = 'C:\\Users\\Vlad Titov\\Desktop\\Work\\binary_tree\\model_processing\\available_modification\\converted.json'
    out_path = "output.json"
    tree = TreeCreator(model_path, out_path)
    #result = tree.model_to_tree()
    roots = tree.create_tree()