"""
Этот модуль предназначен для создания древовидной структуры на основе анализа модели сети.
Он использует класс `NetworkAnalyzer` из модуля `model_processing` для анализа
исходной модели и класс `Node` из `tree_analyzer.tree_construction` для построения
узлов дерева. Результатом работы является список корневых узлов дерева.
"""
import json
from pathlib import Path
from typing import Dict, Any, List as TypingList, Optional, Set as TypingSet # Added Set
import sys
import os
# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree_analyzer.tree_construction import Node # Node is imported
from model_processing import NetworkAnalyzer
from model_processing.models import NetworkAnalysisResult # NetworkAnalysisResult is imported

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
        (для выполнения анализа). Если `analysis_result` предоставлен, `model_path` и `out_path`
        (если они переданы) используются только для информационных целей или если будущие методы
        будут их требовать; основной анализ через `NetworkAnalyzer` в этом случае не выполняется.

        Initializes the TreeCreator object.

        Either `analysis_result` must be provided, or both `model_path` and `out_path`
        (for performing the analysis). If `analysis_result` is provided, `model_path` and `out_path`
        (if passed) are used for informational purposes only or if future methods require them;
        the main analysis via `NetworkAnalyzer` is not performed in this case.

        Параметры / Parameters:
            model_path (Optional[str]): Путь к файлу модели (строка).
                                        Path to the model file (string).
            out_path (Optional[str]): Путь для сохранения файла с результатами анализа `NetworkAnalyzer` (строка).
                                      Path to save the analysis results file by `NetworkAnalyzer` (string).
            analysis_result (Optional[NetworkAnalysisResult]): Предварительно полученный результат анализа сети.
                                                               Pre-obtained network analysis result.
        """
        if analysis_result:
            if not isinstance(analysis_result, NetworkAnalysisResult):
                msg = "Предоставленный analysis_result должен быть экземпляром NetworkAnalysisResult. / Provided analysis_result must be an instance of NetworkAnalysisResult."
                logger.error(msg)
                raise TypeError(msg)
            self.result: Optional[NetworkAnalysisResult] = analysis_result # Уточняем тип атрибута экземпляра
            # model_path и out_path могут быть None или предоставлены для других нужд.
            self.model_path: Optional[Path] = Path(model_path) if model_path else None
            self.out_path: Optional[Path] = Path(out_path) if out_path else None
            logger.info("TreeCreator инициализирован с предварительно загруженным NetworkAnalysisResult. / TreeCreator initialized with pre-loaded NetworkAnalysisResult.")
        elif model_path and out_path: # out_path тоже должен быть здесь обязательным
            input_file = Path(model_path)
            if not input_file.exists():
                msg = f"Входной файл модели {input_file} не найден. / Model input file {input_file} not found."
                logger.error(msg)
                raise FileNotFoundError(msg)
            self.model_path = input_file
            self.out_path = Path(out_path)
            self.result = None
            logger.info(f"TreeCreator инициализирован с путями: model_path='{self.model_path}', out_path='{self.out_path}'. / TreeCreator initialized with paths: model_path='{self.model_path}', out_path='{self.out_path}'.")
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
        
        # После _ensure_analysis_result, self.result здесь гарантированно NetworkAnalysisResult
        # поэтому дополнительная проверка isinstance не обязательна, но может остаться для безопасности.
        if not isinstance(self.result, NetworkAnalysisResult) : # Should ideally not happen if _ensure_analysis_result works
             logger.critical("self.result не является NetworkAnalysisResult даже после _ensure_analysis_result. Логическая ошибка. / self.result is not NetworkAnalysisResult even after _ensure_analysis_result. Logical error.")
             return []


        tree_data: Dict[str, Dict[str, TypingList[str]]] = self.result.tree
        all_element_ids: TypingList[str] = self.result.nodes
        root_element_ids: TypingList[str] = self.result.roots

        if not tree_data and not all_element_ids : # Если и дерево и список узлов пусты (например, пустая модель)
            logger.warning("Данные дерева (tree) и список узлов (nodes) пусты в NetworkAnalysisResult. Возвращается пустое дерево. / Tree data and node list are empty in NetworkAnalysisResult. Returning an empty tree.")
            return []
        if not all_element_ids and tree_data: # Есть структура дерева, но нет списка узлов - странно
             logger.warning("Список узлов (all_node_ids) пуст, но есть данные дерева (tree_data) в NetworkAnalysisResult. Попытка построить дерево. / Node list (all_node_ids) is empty, but tree data exists in NetworkAnalysisResult. Attempting to build tree.")
             # Можно попробовать извлечь all_element_ids из ключей tree_data и всех children, но это может быть неполно.
             # Для большей надежности, если all_node_ids пуст, лучше вернуть [], если это не ожидается.
             # all_element_ids = list(tree_data.keys()) # Это будет неполно, если есть узлы без детей или только как дети.

        created_nodes: Dict[str, Node] = {}

        for node_id_str in all_element_ids:
            node = Node(str(node_id_str)) # Убедимся, что ID узла - строка
            created_nodes[str(node_id_str)] = node

        for parent_id_str_raw, connection_info in tree_data.items():
            parent_id_str = str(parent_id_str_raw)
            parent_node_obj = created_nodes.get(parent_id_str)

            if parent_node_obj:
                if isinstance(connection_info, dict) and 'child' in connection_info:
                    child_ids_list = connection_info['child']
                    if isinstance(child_ids_list, list):
                        for child_id_raw in child_ids_list:
                            child_id_str = str(child_id_raw)
                            child_node_obj = created_nodes.get(child_id_str)
                            if child_node_obj:
                                parent_node_obj.add_child(child_node_obj)
                            else:
                                logger.warning(f"Дочерний узел с ID '{child_id_str}' для родителя '{parent_id_str}' не найден в created_nodes. / Child node with ID '{child_id_str}' for parent '{parent_id_str}' not found in created_nodes.")
                    else:
                        logger.warning(f"Для родителя '{parent_id_str}' поле 'child' не является списком: {child_ids_list}. / For parent '{parent_id_str}', 'child' field is not a list: {child_ids_list}.")
                else:
                    logger.warning(f"Для родителя '{parent_id_str}' отсутствует ключ 'child' или данные не являются словарем: {connection_info}. / For parent '{parent_id_str}', 'child' key is missing or data is not a dictionary: {connection_info}.")
            elif parent_id_str in all_element_ids : # Если ID родителя был в общем списке, но узел не создался (не должно быть)
                 logger.error(f"Родительский узел с ID '{parent_id_str}' из tree_data не найден в created_nodes, хотя должен был быть создан. Логическая ошибка. / Parent node with ID '{parent_id_str}' from tree_data not found in created_nodes, though it should have been created. Logical error.")


        # Формируем список корневых узлов
        actual_roots: TypingList[Node] = [created_nodes[str(root_id)] for root_id in root_element_ids if str(root_id) in created_nodes]
        
        if not actual_roots and all_element_ids:
             logger.info("Корневые узлы не были предоставлены или не найдены в NetworkAnalysisResult. Попытка автоматического определения. / Root nodes were not provided or not found in NetworkAnalysisResult. Attempting automatic detection.")
             all_children_ids_set: TypingSet[str] = set()
             for parent_id_str_raw, connection_info in tree_data.items():
                 if isinstance(connection_info, dict) and 'child' in connection_info and isinstance(connection_info['child'], list):
                     for child_id_raw in connection_info['child']:
                         all_children_ids_set.add(str(child_id_raw))

             potential_roots = [created_nodes[node_id_str] for node_id_str in all_element_ids if node_id_str not in all_children_ids_set and node_id_str in created_nodes]

             if not potential_roots and all_element_ids: # Если все узлы являются чьими-то детьми или нет узлов вообще
                 logger.warning("Не удалось автоматически определить корневые узлы (возможно, циклическая структура или нет узлов). / Failed to automatically determine root nodes (possibly cyclic structure or no nodes).")
                 # Если есть узлы, но все они чьи-то дети, это может быть циклическая структура или один узел-корень, который также является чьим-то ребенком (что странно для дерева).
                 # В таком случае, можно вернуть первый узел из all_node_ids, если он есть, или пустой список.
                 # if all_element_ids and created_nodes: return [created_nodes[all_element_ids[0]]]
                 return []
             actual_roots = potential_roots
             logger.info(f"Автоматически определенные корневые узлы: {[r.value for r in actual_roots]} / Automatically determined root nodes: {[r.value for r in actual_roots]}")

        if not actual_roots: # Если и после автоматического определения корней нет
            logger.warning("Не удалось сформировать список корневых узлов ни из предоставленных, ни автоматически. / Failed to form list of root nodes either from provided or automatically.")

        return actual_roots
if __name__ == '__main__':
    model_path = 'C:\\Users\\Vlad Titov\\Desktop\\Work\\binary_tree\\model_processing\\available_modification\\converted.json'
    out_path = "output.json"
    tree = TreeCreator(model_path, out_path)
    #result = tree.model_to_tree()
    roots = tree.create_tree()