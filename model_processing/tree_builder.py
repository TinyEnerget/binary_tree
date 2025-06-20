"""
Этот модуль предоставляет класс `NetworkTreeBuilder`, предназначенный для
построения первоначального древовидного (или лесовидного, если есть несколько корней)
представления электрической сети на основе обработанной `NetworkModel`.

Модуль использует анализаторы элементов из `NetworkModel` для определения
иерархических связей (родитель-потомок) между элементами сети.
Результатом является словарь, описывающий корневые узлы, все узлы (элементы)
и структуру связей "родитель-потомок".

This module provides the `NetworkTreeBuilder` class, designed for
constructing an initial tree-like (or forest-like, if there are multiple roots)
representation of an electrical network based on a processed `NetworkModel`.

The module uses element analyzers from the `NetworkModel` to determine
hierarchical relationships (parent-child) between network elements.
The result is a dictionary describing root nodes, all nodes (elements),
and the parent-child relationship structure.
"""
from typing import Dict, Any, List
from .models import NetworkModel, NetworkAnalysisResult # Импортируем NetworkAnalysisResult

import logging
logger = logging.getLogger(__name__)

class NetworkTreeBuilder:
    """
    Класс `NetworkTreeBuilder` отвечает за построение древовидного представления электрической сети.
    The `NetworkTreeBuilder` class is responsible for building a tree-like representation of an electrical network.

    Он принимает экземпляр `NetworkModel`, который уже содержит проанализированные данные
    об элементах сети и их соединениях, а также зарегистрированные анализаторы для каждого типа элемента.
    `NetworkTreeBuilder` использует эти анализаторы для определения иерархических связей
    (родитель-потомок) и идентификации корневых элементов.
    It takes an instance of `NetworkModel`, which already contains analyzed data
    about network elements and their connections, as well as registered analyzers for each element type.
    `NetworkTreeBuilder` uses these analyzers to determine hierarchical relationships
    (parent-child) and identify root elements.

    Атрибуты / Attributes:
        model (NetworkModel): Обработанная модель сети, содержащая элементы, их типы,
                              соединения и анализаторы.
                              The processed network model containing elements, their types,
                              connections, and analyzers.
    """

    def __init__(self, model: NetworkModel):
        """
        Инициализирует `NetworkTreeBuilder` с предоставленной моделью сети.
        Initializes the `NetworkTreeBuilder` with the provided network model.

        Параметры / Parameters:
            model (NetworkModel): Экземпляр `NetworkModel`, который будет использоваться
                                  для построения дерева. Модель должна быть уже загружена
                                  и содержать необходимые элементы и анализаторы.
                                  An instance of `NetworkModel` that will be used
                                  for building the tree. The model should already be loaded
                                  and contain the necessary elements and analyzers.
        """
        if not isinstance(model, NetworkModel):
            # Логируем ошибку и выбрасываем исключение, если тип model некорректен
            logger.error("Переданный аргумент 'model' не является экземпляром NetworkModel. / Provided 'model' argument is not an instance of NetworkModel.")
            raise TypeError("Аргумент 'model' должен быть экземпляром NetworkModel. / 'model' argument must be an instance of NetworkModel.")
        self.model = model
        logger.info("NetworkTreeBuilder инициализирован с моделью. / NetworkTreeBuilder initialized with a model.")

    def build_tree(self) -> NetworkAnalysisResult:
        """
        Строит и возвращает древовидное представление сети в виде объекта `NetworkAnalysisResult`.
        Builds and returns a tree-like representation of the network as a `NetworkAnalysisResult` object.

        Процесс включает:
        1. Получение списка ID всех элементов из модели.
        2. Определение корневых элементов с помощью метода `self.model.get_root_elements()`.
        3. Итерацию по каждому элементу модели для определения его дочерних элементов
           с использованием соответствующего анализатора (`analyzer.get_children()`).
        4. Формирование и возврат экземпляра `NetworkAnalysisResult`, содержащего
           списки ID корневых элементов, всех элементов и словарь связей "родитель-потомок".

        Если для элемента не найден анализатор или элемент отсутствует (хотя он есть в общем списке ID),
        он будет включен в результирующую структуру `tree` с пустым списком дочерних элементов.
        The process includes:
        1. Getting a list of IDs of all elements from the model.
        2. Identifying root elements using `self.model.get_root_elements()`.
        3. Iterating through each element in the model to determine its children
           using the appropriate analyzer (`analyzer.get_children()`).
        4. Forming and returning a `NetworkAnalysisResult` instance containing
           lists of root element IDs, all element IDs, and a dictionary of parent-child relationships.

        If no analyzer is found for an element or an element is missing (though present in the overall ID list),
        it will be included in the resulting `tree` structure with an empty list of children.

        Возвращает / Returns:
            NetworkAnalysisResult: Экземпляр `NetworkAnalysisResult`, содержащий
                                   `roots` (List[str]), `nodes` (List[str]),
                                   и `tree` (Dict[str, Dict[str, List[str]]]).
                                   An instance of `NetworkAnalysisResult` containing
                                   `roots` (List[str]), `nodes` (List[str]),
                                   and `tree` (Dict[str, Dict[str, List[str]]]).
        """
        logger.info("Начало построения дерева сети... / Starting to build the network tree...")

        tree_connections: Dict[str, Dict[str, List[str]]] = {}
        all_element_ids: List[str] = list(self.model.elements.keys())

        if not all_element_ids:
            logger.warning("В модели нет элементов для построения дерева. / No elements in the model to build a tree.")
            return NetworkAnalysisResult(roots=[], nodes=[], tree={})

        root_ids: List[str] = self.model.get_root_elements()
        logger.debug(f"Обнаружены корневые элементы: {root_ids} / Root elements detected: {root_ids}")

        for element_id in all_element_ids:
            element = self.model.get_element(element_id)

            if not element:
                logger.warning(f"Элемент с ID '{element_id}' не найден в модели во время построения дерева. Он будет иметь пустой список дочерних элементов. / Element with ID '{element_id}' not found in model during tree building. It will have an empty child list.")
                tree_connections[element_id] = {"child": []}
                continue
                
            analyzer = self.model.get_analyzer(element.element_type)

            children_ids: List[str]
            if not analyzer:
                logger.warning(f"Анализатор для элемента '{element_id}' (тип: {element.element_type}) не найден. Дочерние элементы не будут определены. / Analyzer for element '{element_id}' (type: {element.element_type}) not found. Children will not be determined.")
                children_ids = []
            else:
                try:
                    children_ids = analyzer.get_children(element, self.model)
                    logger.debug(f"Для элемента '{element_id}' (тип: {element.element_type}) найдены дочерние элементы: {children_ids} / For element '{element_id}' (type: {element.element_type}) found children: {children_ids}")
                except Exception as e:
                    logger.exception(f"Ошибка при получении дочерних элементов для '{element_id}' (тип: {element.element_type}): {e} / Error getting children for '{element_id}' (type: {element.element_type}): {e}")
                    children_ids = []

            tree_connections[element_id] = {"child": children_ids}

        logger.info(f"Построение дерева завершено. Найдено {len(root_ids)} корней, обработано {len(all_element_ids)} узлов. / Tree building finished. Found {len(root_ids)} roots, processed {len(all_element_ids)} nodes.")

        return NetworkAnalysisResult(
            roots=root_ids,
            nodes=all_element_ids,
            tree=tree_connections
        )