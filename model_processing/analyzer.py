"""
Этот модуль предоставляет основной класс `NetworkAnalyzer`, который выступает
в качестве координатора для загрузки, предварительной обработки, анализа
(построения древовидной структуры) и сравнения моделей электрических сетей.

`NetworkAnalyzer` использует другие компоненты из пакета `model_processing`,
такие как `NetworkModel` и `NetworkTreeBuilder`, для выполнения своих задач.
Он также включает статические методы для утилитных операций, таких как
загрузка модели и сохранение результатов анализа.

This module provides the main `NetworkAnalyzer` class, which acts as a
coordinator for loading, preprocessing, analyzing (building a tree-like structure),
and comparing electrical network models.

`NetworkAnalyzer` utilizes other components from the `model_processing` package,
such as `NetworkModel` and `NetworkTreeBuilder`, to perform its tasks.
It also includes static methods for utility operations like loading models
and saving analysis results.
"""
from typing import Dict, Any, Optional, List, Set, Type # Added Type for class methods
import json # Для json.JSONDecodeError в docstring load_model
from dataclasses import asdict # Для преобразования NetworkAnalysisResult в dict

from .utils import load_json, save_json
from .comparator import TreeComparator
from .models import NetworkModel, NetworkAnalysisResult
from .tree_builder import NetworkTreeBuilder

import logging
logger = logging.getLogger(__name__)

class NetworkAnalyzer:
    """
    Основной класс для анализа моделей электрической сети.
    Main class for analyzing electrical network models.

    Этот класс координирует полный процесс анализа сети:
    1. Загрузка данных модели из файла (обычно JSON).
    2. Предварительная обработка данных модели (например, `rewrite_nodes`, `find_root_nodes`).
    3. Создание экземпляра `NetworkModel` для представления модели в памяти.
    4. Построение древовидной структуры сети с помощью `NetworkTreeBuilder`.
    5. Опциональное сохранение результатов анализа.
    6. Предоставление возможности сравнения полученной структуры с эталонным результатом.

    This class coordinates the complete network analysis process:
    1. Loading model data from a file (usually JSON).
    2. Preprocessing the model data (e.g., `rewrite_nodes`, `find_root_nodes`).
    3. Creating a `NetworkModel` instance to represent the model in memory.
    4. Building a tree-like structure of the network using `NetworkTreeBuilder`.
    5. Optionally saving the analysis results.
    6. Providing functionality to compare the resulting structure with a reference result.
    """

    @staticmethod
    def load_model(file_path: str) -> Dict[str, Any]:
        """
        Загружает модель сети из JSON-файла.
        Loads a network model from a JSON file.

        Использует утилиту `load_json` из `.utils`.
        Uses the `load_json` utility from `.utils`.

        Параметры / Parameters:
            file_path (str): Путь к JSON-файлу с моделью.
                             Path to the JSON file with the model.

        Возвращает / Returns:
            Dict[str, Any]: Данные модели сети в виде словаря.
                            Network model data as a dictionary.

        Выбрасывает / Raises:
            FileNotFoundError: Если файл по указанному пути не найден.
                               If the file at the specified path is not found.
            json.JSONDecodeError: Если содержимое файла не является корректным JSON.
                                  If the file content is not valid JSON.
        """
        logger.info(f"Загрузка модели из файла: {file_path} / Loading model from file: {file_path}")
        return load_json(file_path)

    @staticmethod
    def save_tree(tree_data: NetworkAnalysisResult, file_path: str) -> None:
        """
        Сохраняет построенное дерево сети (объект `NetworkAnalysisResult`) в JSON-файл.
        Saves the constructed network tree (`NetworkAnalysisResult` object) to a JSON file.

        Перед сохранением объект `NetworkAnalysisResult` преобразуется в словарь
        с помощью `dataclasses.asdict()`. Использует утилиту `save_json` из `.utils`.
        Before saving, the `NetworkAnalysisResult` object is converted to a dictionary
        using `dataclasses.asdict()`. Uses the `save_json` utility from `.utils`.

        Параметры / Parameters:
            tree_data (NetworkAnalysisResult): Данные дерева сети в виде объекта `NetworkAnalysisResult`.
                                               Network tree data as a `NetworkAnalysisResult` object.
            file_path (str): Путь для сохранения JSON-файла.
                             Path to save the JSON file.

        Выбрасывает / Raises:
            OSError: Если возникает ошибка при записи файла (например, проблемы с правами доступа).
                     If an error occurs while writing the file (e.g., permission issues).
            TypeError: Если `tree_data` не является экземпляром `NetworkAnalysisResult`.
                       If `tree_data` is not an instance of `NetworkAnalysisResult`.
        """
        if not isinstance(tree_data, NetworkAnalysisResult):
            msg = "Данные для сохранения дерева должны быть экземпляром NetworkAnalysisResult. / Data for saving tree must be an instance of NetworkAnalysisResult."
            logger.error(msg)
            raise TypeError(msg)
        logger.info(f"Сохранение дерева NetworkAnalysisResult в файл: {file_path} / Saving NetworkAnalysisResult tree to file: {file_path}")
        save_json(file_path, asdict(tree_data)) # Преобразуем датакласс в словарь для save_json

    @classmethod
    def analyze_network(cls, model_path: str, output_path: Optional[str] = None) -> NetworkAnalysisResult:
        """
        Выполняет полный цикл анализа сети: загрузка, предварительная обработка,
        построение `NetworkModel`, построение дерева и опциональное сохранение.
        Performs a full network analysis cycle: loading, preprocessing,
        `NetworkModel` construction, tree building, and optional saving.

        Последовательность операций / Sequence of operations:
        1. Загрузка данных модели из `model_path` с помощью `cls.load_model()`.
           Перехватывает `FileNotFoundError` и `json.JSONDecodeError`.
        2. Предварительная обработка узлов модели с помощью `cls.rewrite_nodes()`.
           Перехватывает возможные `KeyError` или `TypeError`, если структура `model_data` некорректна.
        3. Идентификация и добавление корневых узлов в данные модели с помощью `cls.find_root_nodes()`.
           Аналогично, перехватывает `KeyError` или `TypeError`.
        4. Создание экземпляра `NetworkModel` на основе обработанных данных.
           Перехватывает `NetworkModelError` от конструктора `NetworkModel`.
        5. Создание экземпляра `NetworkTreeBuilder` с созданной `NetworkModel`.
        6. Построение древовидной структуры с помощью `tree_builder.build_tree()`.
           Перехватывает возможные ошибки этапа построения дерева.
        7. Если указан `output_path`, результат сохраняется с помощью `cls.save_tree()`.
           Перехватывает `OSError` при сохранении.

        Параметры / Parameters:
            model_path (str): Путь к JSON-файлу с исходной моделью сети.
                              Path to the JSON file with the source network model.
            output_path (Optional[str]): Необязательный путь для сохранения результирующего
                                         дерева в формате JSON. Если None, результат не сохраняется.
                                         Optional path to save the resulting tree in JSON format.
                                         If None, the result is not saved.

        Возвращает / Returns:
            NetworkAnalysisResult: Экземпляр датакласса `NetworkAnalysisResult`, содержащий
                                   результаты анализа: 'roots' (список ID корневых элементов),
                                   'nodes' (список ID всех элементов) и 'tree' (словарь
                                   связей "родитель-потомок").
                                   An instance of the `NetworkAnalysisResult` dataclass containing
                                   the analysis results: 'roots' (list of root element IDs),
                                   'nodes' (list of all element IDs), and 'tree' (a dictionary
                                   of parent-child relationships).

        Выбрасывает / Raises:
            FileNotFoundError: Если входной файл модели `model_path` не найден.
                               If the input model file `model_path` is not found.
            json.JSONDecodeError: Если входной файл модели содержит некорректный JSON.
                                  If the input model file contains invalid JSON.
            ValueError: Если структура данных модели некорректна для обработки (например, отсутствуют ожидаемые ключи).
                        If the model data structure is incorrect for processing (e.g., missing expected keys).
            NetworkModelError: Если возникают ошибки при создании или парсинге `NetworkModel`.
                               If errors occur during `NetworkModel` creation or parsing.
            Exception: Любые другие непредвиденные исключения, которые могут возникнуть в процессе обработки.
                       Any other unexpected exceptions that may occur during processing.
        """
        logger.info(f"Начало анализа сети для модели: {model_path} / Starting network analysis for model: {model_path}")
        
        try:
            model_data = cls.load_model(model_path)

            logger.info("Предварительная обработка узлов... / Preprocessing nodes...")
            model_data = cls.rewrite_nodes(model_data) # Ожидаем, что rewrite_nodes теперь более устойчив или выбрасывает ValueError/KeyError

            logger.info("Поиск корневых узлов... / Finding root nodes...")
            model_data = cls.find_root_nodes(model_data) # Аналогично для find_root_nodes

            logger.info("Создание NetworkModel... / Creating NetworkModel...")
            network_model = NetworkModel(model_data) # NetworkModel должен сам обрабатывать ошибки в своих данных через NetworkModelError

            logger.info("Построение дерева сети с помощью NetworkTreeBuilder... / Building network tree using NetworkTreeBuilder...")
            tree_builder = NetworkTreeBuilder(network_model)
            tree_result_dict = tree_builder.build_tree()

            analysis_result = NetworkAnalysisResult(
                roots=tree_result_dict.roots, # Используем прямой доступ к атрибутам, т.к. build_tree теперь возвращает NetworkAnalysisResult
                nodes=tree_result_dict.nodes,
                tree=tree_result_dict.tree
            )

            if output_path:
                cls.save_tree(analysis_result, output_path) # Передаем объект NetworkAnalysisResult
                logger.info(f"Результат анализа сохранен в: {output_path} / Analysis result saved to: {output_path}")
            else:
                logger.info("Output_path не указан, результат анализа не будет сохранен в файл. / Output_path not specified, analysis result will not be saved to a file.")

            logger.info(f"Анализ сети для модели {model_path} завершен. / Network analysis for model {model_path} completed.")
            return analysis_result

        except FileNotFoundError: # Уже логируется в load_model, но перехватываем для возможной специфической обработки здесь
            logger.error(f"Критическая ошибка: Файл модели {model_path} не найден. / Critical error: Model file {model_path} not found.")
            raise # Перевыбрасываем, чтобы вызывающий код знал
        except json.JSONDecodeError: # Уже логируется в load_model
            logger.error(f"Критическая ошибка: Не удалось декодировать JSON из файла модели {model_path}. / Critical error: Failed to decode JSON from model file {model_path}.")
            raise
        except (KeyError, TypeError, ValueError) as e: # Ошибки структуры данных от rewrite_nodes/find_root_nodes или при создании NetworkAnalysisResult
            logger.error(f"Критическая ошибка: Некорректная структура данных в модели {model_path} или результате построения дерева: {e} / Critical error: Incorrect data structure in model {model_path} or tree building result: {e}")
            raise ValueError(f"Некорректная структура данных в модели {model_path}: {e}") from e
        except NetworkModelError as e: # Ошибки от NetworkModel
            logger.error(f"Критическая ошибка при обработке модели {model_path}: {e} / Critical error processing model {model_path}: {e}")
            raise
        except OSError as e: # Ошибки при сохранении файла
            logger.error(f"Критическая ошибка: Ошибка при сохранении файла дерева для модели {model_path} в {output_path}: {e} / Critical error: Error saving tree file for model {model_path} to {output_path}: {e}")
            raise
        except Exception as e: # Все остальные непредвиденные ошибки
            logger.error(f"Непредвиденная критическая ошибка при анализе сети {model_path}: {type(e).__name__} - {e} / Unexpected critical error analyzing network {model_path}: {type(e).__name__} - {e}")
            raise


    @classmethod
    def compare_with_reference(cls, result: NetworkAnalysisResult, reference_path: str) -> bool:
        """
        Сравнивает полученный результат построения дерева с эталонным JSON-файлом.
        Compares the obtained tree construction result with a reference JSON file.

        Использует `TreeComparator.compare` для выполнения сравнения. `result` (типа `NetworkAnalysisResult`)
        конвертируется в словарь перед передачей в `TreeComparator`.
        Uses `TreeComparator.compare` to perform the comparison. The `result` (of type `NetworkAnalysisResult`)
        is converted to a dictionary before being passed to `TreeComparator`.

        Параметры / Parameters:
            result (NetworkAnalysisResult): Результат построения дерева в виде объекта `NetworkAnalysisResult`.
                                            The tree construction result as a `NetworkAnalysisResult` object.
            reference_path (str): Путь к JSON-файлу, содержащему эталонное дерево.
                                  Path to the JSON file containing the reference tree.

        Возвращает / Returns:
            bool: True, если результат `result` полностью совпадает с эталоном `reference_path`,
                  иначе False.
                  True if the `result` fully matches the reference from `reference_path`,
                  False otherwise.

        Выбрасывает / Raises:
            FileNotFoundError: Если эталонный файл `reference_path` не найден.
                               If the reference file `reference_path` is not found.
        """
        logger.info(f"Сравнение результата с эталоном из файла: {reference_path} / Comparing result with reference from file: {reference_path}")
        reference_data = cls.load_model(reference_path) # Загружаем эталонные данные
        are_identical = TreeComparator.compare(result, reference_data)
        logger.info(f"Результат сравнения: {'совпадают' if are_identical else 'НЕ совпадают'} / Comparison result: {'identical' if are_identical else 'NOT identical'}")
        # Для сравнения TreeComparator ожидает Dict, поэтому преобразуем NetworkAnalysisResult в словарь,
        # если это необходимо, или обновим TreeComparator.
        # Текущий TreeComparator.compare ожидает Dict[str, Any].
        # Используем dataclasses.asdict, если бы он был импортирован, или создадим словарь вручную.
        from dataclasses import asdict # Импортируем здесь для преобразования
        result_dict = asdict(result)

        logger.info(f"Сравнение результата с эталоном из файла: {reference_path} / Comparing result with reference from file: {reference_path}")
        reference_data = cls.load_model(reference_path) # Загружаем эталонные данные
        are_identical = TreeComparator.compare(result_dict, reference_data)
        logger.info(f"Результат сравнения: {'совпадают' if are_identical else 'НЕ совпадают'} / Comparison result: {'identical' if are_identical else 'NOT identical'}")
        return are_identical

    @classmethod
    def rewrite_nodes(cls, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Предварительно обрабатывает раздел 'nodes' в данных модели.
        Preprocesses the 'nodes' section in the model data.

        Цель этого метода — реструктурировать информацию о соединениях узлов (шин)
        в `model_data['nodes']`. Изначально `model_data['nodes']` может иметь ключи,
        не являющиеся шинами, но содержащие шины в своих значениях (списках подключенных элементов).
        Метод перестраивает `model_data['nodes']` так, чтобы ключами становились
        идентификаторы элементов типа 'bus', а значениями — списки подключенных к ним
        элементов, исключая самоподключения шины к себе.

        The purpose of this method is to restructure the node (bus) connection
        information in `model_data['nodes']`. Initially, `model_data['nodes']`
        might have keys that are not buses but contain buses in their values
        (lists of connected elements). This method rebuilds `model_data['nodes']`
        so that the keys are identifiers of 'bus' type elements, and the values
        are lists of elements connected to them, excluding bus self-connections.

        Этапы обработки / Processing steps:
        1. Создается временный словарь `bus_centric_nodes`. Исходный `model_data['nodes']`
           (предположительно `Dict[str, List[str]]`) итерируется. Если какой-либо элемент (`id`)
           из списка подключенных элементов (`value`) является шиной ('bus'), то этот `id` шины
           становится ключом в `bus_centric_nodes`, а весь исходный список `value` — его значением.
           Это гарантирует, что ключами в `bus_centric_nodes` будут ID шин.
           A temporary dictionary `bus_centric_nodes` is created. The original
           `model_data['nodes']` (presumably `Dict[str, List[str]]`) is iterated.
           If any element (`id`) from the list of connected elements (`value`)
           is a bus ('bus'), then this bus `id` becomes a key in `bus_centric_nodes`,
           and the entire original list `value` becomes its value. This ensures
           that keys in `bus_centric_nodes` are bus IDs.
        2. Создается итоговый словарь `final_bus_connections`. Он итерируется по
           `bus_centric_nodes`. Для каждой шины (ключа) ее список подключенных элементов
           фильтруется: из списка удаляется ID самой шины (если он там был),
           предотвращая самоподключения.
           A final dictionary `final_bus_connections` is created. It iterates through
           `bus_centric_nodes`. For each bus (key), its list of connected elements
           is filtered: the bus's own ID is removed from the list (if it was there),
           preventing self-connections.
        3. Раздел `model_data['nodes']` заменяется на `final_bus_connections`.
           The `model_data['nodes']` section is replaced with `final_bus_connections`.

        Параметры / Parameters:
            model_data (Dict[str, Any]): Словарь с данными модели сети.
                                         Dictionary with network model data.

        Возвращает / Returns:
            Dict[str, Any]: Модифицированный словарь `model_data` с обновленным разделом 'nodes'.
                            The modified `model_data` dictionary with an updated 'nodes' section.
        """
        if 'nodes' not in model_data or not isinstance(model_data['nodes'], dict):
            logger.warning("Раздел 'nodes' отсутствует или имеет неверный формат в model_data. rewrite_nodes не будет выполнен. / 'nodes' section is missing or has incorrect format in model_data. rewrite_nodes will not be executed.")
            return model_data
        if 'elements' not in model_data or not isinstance(model_data['elements'], dict):
            logger.warning("Раздел 'elements' отсутствует или имеет неверный формат в model_data. rewrite_nodes не может проверить типы элементов. / 'elements' section is missing or has incorrect format in model_data. rewrite_nodes cannot check element types.")
            return model_data

        bus_centric_nodes: Dict[str, List[str]] = {}
        for _original_node_key, connected_ids_list in model_data['nodes'].items():
            if not isinstance(connected_ids_list, list):
                logger.warning(f"Значение для ключа '{_original_node_key}' в 'nodes' не является списком. Пропуск. / Value for key '{_original_node_key}' in 'nodes' is not a list. Skipping.")
                continue
            for element_id_str in connected_ids_list:
                element_id = str(element_id_str) # Убедимся, что ID - строка
                element_details = model_data['elements'].get(element_id)
                if element_details and isinstance(element_details, dict) and element_details.get('Type') == 'bus':
                    # Если этот элемент - шина, он становится ключом.
                    # Значением становится исходный список соединений, из которого он был взят.
                    bus_centric_nodes[element_id] = [str(eid) for eid in connected_ids_list]


        final_bus_connections: Dict[str, List[str]] = {}
        for bus_id_key, original_connections_list in bus_centric_nodes.items():
            # Фильтруем список, удаляя самоподключения (bus_id_key из списка своих же соединений)
            filtered_connections = [conn_id for conn_id in original_connections_list if conn_id != bus_id_key]
            final_bus_connections[bus_id_key] = filtered_connections

        model_data['nodes'] = final_bus_connections
        logger.debug(f"Раздел 'nodes' перестроен. Количество узлов-шин: {len(final_bus_connections)}. / 'nodes' section rewritten. Number of bus nodes: {len(final_bus_connections)}.")
        return model_data

    @classmethod
    def find_root_nodes(cls, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Идентифицирует корневые узлы (элементы типа 'system') в модели и обновляет
        словарь модели, добавляя списки корневых узлов и всех узлов.
        Identifies root nodes (elements of type 'system') in the model and updates
        the model dictionary by adding lists of root nodes and all nodes.

        Процесс / Process:
        1. Собирает все уникальные идентификаторы элементов, упомянутые в разделе
           `model_data['nodes']` (как ключи, так и значения в списках соединений).
           Collects all unique element identifiers mentioned in the `model_data['nodes']`
           section (both as keys and as values in connection lists).
           (Примечание: текущая реализация кода собирает ID только из значений списков соединений,
           а не из ключей `model_data['nodes']`. Это может быть неполным, если ключи `model_data['nodes']`
           также являются ID элементов, которые должны быть учтены. Однако, после `rewrite_nodes`
           ключами становятся ID шин, которые также должны быть в `model_data['elements']`.)
           (Note: The current code implementation collects IDs only from the values of
           connection lists, not from the keys of `model_data['nodes']`. This might be
           incomplete if the keys of `model_data['nodes']` are also element IDs that
           should be considered. However, after `rewrite_nodes`, keys become bus IDs,
           which should also be in `model_data['elements']`.)

        2. Итерирует по этим уникальным идентификаторам. Если элемент с таким ID
           в `model_data['elements']` имеет тип 'system', он добавляется в список `roots`.
           Iterates through these unique identifiers. If an element with such an ID
           in `model_data['elements']` has the type 'system', it is added to the `roots` list.
        3. Добавляет/обновляет два ключа в словаре `model_data`:
           - `'roots'`: список ID идентифицированных корневых элементов.
           - `'nodes_id'`: список всех уникальных ID элементов, найденных на шаге 1.
                           (Название `nodes_id` может вводить в заблуждение, т.к. это ID элементов, а не узлов в общем смысле).
           Adds/updates two keys in the `model_data` dictionary:
           - `'roots'`: a list of IDs of identified root elements.
           - `'nodes_id'`: a list of all unique element IDs found in step 1.
                           (The name `nodes_id` might be misleading as these are element IDs,
                           not nodes in a general sense).


        Параметры / Parameters:
            model_data (Dict[str, Any]): Словарь с данными модели сети.
                                         Dictionary with network model data.

        Возвращает / Returns:
            Dict[str, Any]: Модифицированный словарь `model_data` с добавленными ключами
                            `'roots'` и `'nodes_id'`.
                            The modified `model_data` dictionary with added `'roots'`
                            and `'nodes_id'` keys.
        """
        if 'nodes' not in model_data or not isinstance(model_data['nodes'], dict):
            logger.warning("Раздел 'nodes' отсутствует или имеет неверный формат в model_data. find_root_nodes не может определить все узлы. / 'nodes' section is missing or has incorrect format. find_root_nodes cannot determine all nodes.")
            model_data['roots'] = []
            model_data['nodes_id'] = []
            return model_data
        if 'elements' not in model_data or not isinstance(model_data['elements'], dict):
            logger.warning("Раздел 'elements' отсутствует или имеет неверный формат в model_data. find_root_nodes не может проверить типы элементов. / 'elements' section is missing or has incorrect format. find_root_nodes cannot check element types.")
            model_data['roots'] = []
            # Попытаемся собрать 'nodes_id' хотя бы из ключей 'nodes', если 'elements' недоступен для проверки типов
            model_data['nodes_id'] = list(model_data['nodes'].keys())
            return model_data

        all_involved_element_ids: Set[str] = set()
        # Собираем ID из ключей и значений раздела 'nodes'
        for node_key, connected_list in model_data['nodes'].items():
            all_involved_element_ids.add(str(node_key)) # Ключи тоже могут быть ID элементов (шин)
            if isinstance(connected_list, list):
                for item_id in connected_list:
                    all_involved_element_ids.add(str(item_id))

        list_of_all_ids = list(all_involved_element_ids)
        root_ids: List[str] = []

        for element_id_str in list_of_all_ids:
            element_details = model_data['elements'].get(element_id_str)
            if element_details and isinstance(element_details, dict) and element_details.get('Type') == 'system':
                root_ids.append(element_id_str)

        model_data['roots'] = root_ids
        # 'nodes_id' здесь - это все уникальные ID, упомянутые в связях или как ключи узлов.
        # Это не обязательно все элементы из 'model_data['elements']', а те, что участвуют в связях.
        model_data['nodes_id'] = list_of_all_ids
        logger.debug(f"Поиск корневых узлов завершен. Найдено корней: {len(root_ids)}. Общее количество ID узлов/элементов в связях: {len(list_of_all_ids)}. / Root node search completed. Roots found: {len(root_ids)}. Total unique node/element IDs in connections: {len(list_of_all_ids)}.")
        return model_data
