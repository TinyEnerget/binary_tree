"""
Этот модуль определяет основные структуры данных, используемые для представления
и обработки моделей электрических сетей. Он включает перечисление типов элементов,
датакласс для представления самих элементов сети, пользовательское исключение
для ошибок модели и основной класс `NetworkModel`, который управляет парсингом,
хранением и анализом данных модели.

This module defines the core data structures used for representing and processing
electrical network models. It includes an enumeration for element types,
a dataclass for representing network elements themselves, a custom exception
for model-related errors, and the main `NetworkModel` class that manages
parsing, storage, and analysis of model data.
"""
from functools import lru_cache
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass

if TYPE_CHECKING:
    from .registry import AnalyzerRegistry # Для проверки типов, избегая циклических импортов во время выполнения
    from .analyzers import ElementAnalyzer # For type checking, avoiding circular imports at runtime

import logging
logger = logging.getLogger(__name__)

# TODO: Дополнить элементы схемы из ЛабРЗА / TODO: Supplement schema elements from LabRZA
class ElementType(Enum):
    """
    Перечисление стандартных типов элементов электрической сети.
    Enumeration of standard electrical network element types.

    Каждый член перечисления представляет собой определенный тип оборудования,
    используемый в моделях электрических сетей.
    Each member of the enumeration represents a specific type of equipment
    used in electrical network models.
    """
    SYSTEM = "system"  # Энергосистема (эквивалент, источник бесконечной мощности) / Power system (equivalent, infinite power source)
    BUS = "bus"  # Шина или сборная шина / Busbar or bus
    OVERHEAD_LINE = "overhead_line"  # Воздушная линия электропередачи / Overhead transmission line
    TRANSFORMER2 = "transformer2"  # Двухобмоточный трансформатор / Two-winding transformer
    TRANSFORMER2SW = "transformer2sw" # Двухобмоточный трансформатор с РПН или переключателем отпаек / Two-winding transformer with OLTC or tap changer
    TRANSFORMER3 = "transformer3"  # Трехобмоточный трансформатор / Three-winding transformer
    AUTOTRANSFORMER = "autotransformer"  # Автотрансформатор / Autotransformer
    SWITCH = "switch"  # Коммутационный аппарат (выключатель, разъединитель) / Switching device (circuit breaker, disconnector)
    GENERATOR = "generator"  # Генератор / Generator
    LOAD = "load"  # Нагрузка / Load


@dataclass
class NetworkElement:
    """
    Представляет базовый элемент электрической сети.
    Represents a basic element of an electrical network.

    Этот датакласс используется для хранения общей информации о любом элементе сети.
    This dataclass is used to store common information about any network element.

    Атрибуты / Attributes:
        id (str): Уникальный идентификатор элемента в модели.
                  Unique identifier of the element in the model.
        name (str): Имя элемента (может быть не уникальным).
                    Name of the element (may not be unique).
        element_type (ElementType): Тип элемента, член перечисления `ElementType`.
                                    Type of the element, a member of the `ElementType` enum.
        nodes (List[int]): Список идентификаторов узлов (обычно числовых), к которым
                           подключен данный элемент. Порядок узлов может быть важен
                           для некоторых типов элементов (например, для линий или трансформаторов).
                           List of node identifiers (usually numerical) to which this
                           element is connected. The order of nodes can be important
                           for some element types (e.g., lines or transformers).
        data (Dict[str, Any]): Словарь, содержащий дополнительные, специфичные для данного
                               типа элемента, параметры и данные.
                               A dictionary containing additional parameters and data specific
                               to this type of element.
    """
    id: str
    name: str
    element_type: ElementType # Должен быть ElementType после успешного парсинга
    nodes: List[int] # ID узлов, к которым подключен элемент
    data: Dict[str, Any] # Остальные данные из JSON для этого элемента


class NetworkModelError(Exception):
    """
    Пользовательское исключение для ошибок, специфичных для обработки или структуры модели электрической сети.
    Custom exception for errors specific to the processing or structure of an electrical network model.
    """
    pass


class NetworkModel:
    """
    Представляет модель электрической сети.
    Represents an electrical network model.

    Этот класс является центральным для работы с данными модели сети. Он отвечает за:
    - Парсинг исходных данных модели (обычно из словаря, полученного из JSON).
    - Хранение элементов сети (`NetworkElement`) и их соединений.
    - Управление анализаторами элементов (`ElementAnalyzer`), которые предоставляют
      специфичную для каждого типа элемента логику (например, определение, является ли элемент корневым).
    This class is central to working with network model data. It is responsible for:
    - Parsing raw model data (usually from a dictionary obtained from JSON).
    - Storing network elements (`NetworkElement`) and their connections.
    - Managing element analyzers (`ElementAnalyzer`) that provide element-type-specific
      logic (e.g., determining if an element is a root).

    Атрибуты / Attributes:
        raw_data (Dict[str, Any]): Исходные, необработанные данные модели.
                                   Raw, unprocessed model data.
        elements (Dict[str, NetworkElement]): Словарь элементов сети, где ключ - ID элемента.
                                              Dictionary of network elements, where the key is the element ID.
        node_connections (Dict[str, List[str]]): Словарь, отображающий ID узла на список ID элементов,
                                                 подключенных к этому узлу.
                                                 Dictionary mapping a node ID to a list of element IDs
                                                 connected to that node.
        analyzers (Dict[Union[ElementType, str], 'ElementAnalyzer']): Словарь зарегистрированных анализаторов,
                                                                    где ключ - тип элемента.
                                                                    Dictionary of registered analyzers,
                                                                    where the key is the element type.
    """

    def __init__(self, model_data: Dict[str, Any]):
        """
        Инициализирует модель электрической сети.
        Initializes the electrical network model.

        При инициализации происходит:
        1. Сохранение исходных данных (`model_data`).
        2. Инициализация внутренних структур для хранения элементов, соединений и анализаторов.
        3. Регистрация стандартных анализаторов элементов с помощью `_register_default_analyzers()`.
        4. Полный парсинг модели (элементов и их соединений) с помощью `_parse_model()`.

        Параметры / Parameters:
            model_data (Dict[str, Any]): Входные данные модели в формате словаря.
                                         Должны содержать ключи 'elements' и 'nodes'.
                                         Input model data as a dictionary.
                                         Must contain 'elements' and 'nodes' keys.
        Выбрасывает / Raises:
            NetworkModelError: Если `model_data` имеет неверную структуру или отсутствуют
                               ключевые секции 'elements' или 'nodes', или при ошибках
                               во время регистрации анализаторов или парсинга.
                               If `model_data` has an invalid structure or key sections
                               'elements' or 'nodes' are missing, or if errors occur
                               during analyzer registration or parsing.
        """
        if not isinstance(model_data, dict):
            msg = "Входные данные model_data должны быть словарем. / Input model_data must be a dictionary."
            logger.error(msg)
            raise NetworkModelError(msg)

        self.raw_data: Dict[str, Any] = model_data
        self.elements: Dict[str, NetworkElement] = {}
        self.node_connections: Dict[str, List[str]] = {} # Ключ: ID узла (строка), Значение: список ID элементов (строки)
        self.analyzers: Dict[ElementType, 'ElementAnalyzer'] = {} # Ключ - ElementType enum

        try:
            self._register_default_analyzers()
            self._parse_model()
        except NetworkModelError:
            raise
        except Exception as e:
            msg = f"Непредвиденная ошибка при инициализации NetworkModel: {type(e).__name__} - {e} / Unexpected error during NetworkModel initialization: {type(e).__name__} - {e}"
            logger.exception(msg) # Используем exception для полного стека вызовов
            raise NetworkModelError(msg) from e
        
        logger.debug("Модель инициализирована: %d элементов, %d узлов с соединениями / Model initialized: %d elements, %d nodes with connections",
                     len(self.elements), len(self.node_connections))

    def _register_default_analyzers(self) -> None:
        """
        Регистрирует стандартные (по умолчанию) анализаторы для известных типов элементов.
        Registers default analyzers for known element types.

        Использует `AnalyzerRegistry` для получения списка стандартных анализаторов.
        Каждый анализатор связывается с соответствующим `ElementType` в словаре `self.analyzers`.
        Выполняет отложенный импорт `AnalyzerRegistry` для предотвращения циклических зависимостей.
        Uses `AnalyzerRegistry` to get a list of standard analyzers.
        Each analyzer is associated with its corresponding `ElementType` in the `self.analyzers` dictionary.
        Performs a lazy import of `AnalyzerRegistry` to prevent circular dependencies.

        Выбрасывает / Raises:
            NetworkModelError: Если происходит ошибка импорта `AnalyzerRegistry` или его зависимостей,
                               или если анализатор не может быть инстанциирован или не имеет
                               метода `get_element_type`.
                               If an error occurs importing `AnalyzerRegistry` or its dependencies,
                               or if an analyzer cannot be instantiated or lacks the
                               `get_element_type` method.
        """
        try:
            from .registry import AnalyzerRegistry  # Отложенный импорт / Lazy import
            # Убеждаемся, что анализаторы в реестре инициализированы (если это еще не сделано)
            # AnalyzerRegistry.register_default_analyzers() # Этот вызов должен быть здесь, если он не гарантирован ранее
            # В текущей структуре AnalyzerRegistry.register_default_analyzers() сам заполняет свой список.
            # А NetworkModel получает этот список и строит свой словарь self.analyzers.
            # Если AnalyzerRegistry.register_default_analyzers() не был вызван извне до инициализации NetworkModel,
            # то его нужно вызвать здесь, чтобы _analyzers в AnalyzerRegistry был заполнен.
            # Предположим, что AnalyzerRegistry инициализирует свои анализаторы самостоятельно при первом обращении или статически.
            # Если же AnalyzerRegistry.register_default_analyzers() должен быть вызван здесь для заполнения _analyzers:
            if not AnalyzerRegistry.get_analyzers(): # Проверка, есть ли уже анализаторы в реестре
                 AnalyzerRegistry.register_default_analyzers()


            registered_analyzer_instances = AnalyzerRegistry.get_analyzers()
            if not registered_analyzer_instances:
                # Это может быть проблемой, если ожидаются анализаторы.
                logger.warning("Не найдено ни одного анализатора в AnalyzerRegistry после попытки регистрации по умолчанию. / No analyzers found in AnalyzerRegistry after attempting default registration.")
                # Не выбрасываем ошибку здесь, так как модель может работать с элементами без анализаторов (хотя и с ограничениями).

            for analyzer_instance in registered_analyzer_instances:
                if not hasattr(analyzer_instance, 'get_element_type') or not callable(analyzer_instance.get_element_type):
                    err_msg = f"Зарегистрированный анализатор {type(analyzer_instance).__name__} не имеет метода get_element_type. / Registered analyzer {type(analyzer_instance).__name__} lacks get_element_type method."
                    logger.error(err_msg)
                    raise NetworkModelError(err_msg)

                element_type = analyzer_instance.get_element_type()
                self.analyzers[element_type] = analyzer_instance
                logger.debug("Зарегистрирован анализатор для типа: %s / Registered analyzer for type: %s", element_type, element_type)

        except ImportError as e:
            logger.error("Ошибка импорта при регистрации анализаторов (AnalyzerRegistry или его зависимости): %s / Import error during analyzer registration (AnalyzerRegistry or its dependencies): %s", e, e)
            raise NetworkModelError(f"Не удалось импортировать AnalyzerRegistry или его зависимости: {e}") from e
        except Exception as e:
            logger.error("Непредвиденная ошибка при регистрации анализаторов: {type(e).__name__} - {e} / Unexpected error during analyzer registration: {type(e).__name__} - {e}")
            raise NetworkModelError(f"Не удалось зарегистрировать анализаторы: {e}") from e

    @lru_cache(maxsize=None)
    def get_analyzer(self, element_type: ElementType) -> Optional['ElementAnalyzer']:
        """
        Возвращает зарегистрированный анализатор для указанного типа элемента `ElementType`.
        Returns the registered analyzer for the specified `ElementType`.

        Использует кэширование `@lru_cache` для быстрого повторного доступа.
        Uses `@lru_cache` for fast repeated access.

        Параметры / Parameters:
            element_type (ElementType): Тип элемента (объект `ElementType`).
                                        The element type (`ElementType` object).

        Возвращает / Returns:
            Optional['ElementAnalyzer']: Экземпляр анализатора для данного типа элемента
                                         или None, если анализатор не найден.
                                         An analyzer instance for the given element type,
                                         or None if no analyzer is found.
        """
        # Ключом в self.analyzers теперь всегда является ElementType
        analyzer = self.analyzers.get(element_type)
        if not analyzer:
            logger.warning("Анализатор для типа ElementType '%s' не найден. / Analyzer for ElementType '%s' not found.", element_type.value if isinstance(element_type, Enum) else element_type)
        return analyzer

    def _parse_model(self) -> None:
        """
        Выполняет основной парсинг данных модели, инициализируя элементы и их соединения.
        Performs the main parsing of model data, initializing elements and their connections.

        Этот метод последовательно вызывает `_parse_elements()` для создания объектов
        `NetworkElement` и `_parse_connections()` для установления связей между ними
        на основе информации об узлах. Обернут в блок try-except для перехвата
        и логирования общих ошибок парсинга.
        This method sequentially calls `_parse_elements()` to create `NetworkElement` objects
        and `_parse_connections()` to establish links between them based on node information.
        It is wrapped in a try-except block to catch and log general parsing errors.

        Выбрасывает / Raises:
            NetworkModelError: Если во время парсинга элементов или соединений возникает ошибка,
                               или если отсутствуют ключевые разделы 'elements' или 'nodes' в `raw_data`.
                               If an error occurs during element or connection parsing,
                               or if key sections 'elements' or 'nodes' are missing in `raw_data`.
        """
        if 'elements' not in self.raw_data or not isinstance(self.raw_data['elements'], dict):
            msg = "Раздел 'elements' отсутствует или имеет неверный формат в исходных данных модели. / 'elements' section is missing or has incorrect format in raw model data."
            logger.error(msg)
            raise NetworkModelError(msg)

        if 'nodes' not in self.raw_data or not isinstance(self.raw_data['nodes'], dict):
            # 'nodes' может быть некритичным для некоторых моделей, но для построения связей он нужен.
            # Если он не обязателен для всех сценариев, можно заменить на logger.warning.
            # Но для полной модели с соединениями он, скорее всего, необходим.
            msg = "Раздел 'nodes' отсутствует или имеет неверный формат в исходных данных модели. / 'nodes' section is missing or has incorrect format in raw model data."
            logger.warning(msg) # Изменено на warning, т.к. модель элементов может быть полезна и без явных соединений.
            # raise NetworkModelError(msg) # Закомментировано, чтобы не прерывать, если нужны только элементы

        try:
            logger.info("Начало парсинга элементов модели. / Starting model elements parsing.")
            self._parse_elements()
            logger.info("Завершение парсинга элементов. Начало парсинга соединений. / Finished elements parsing. Starting connections parsing.")
            if 'nodes' in self.raw_data and isinstance(self.raw_data['nodes'], dict): # Парсим соединения только если секция 'nodes' валидна
                self._parse_connections()
            else:
                logger.info("Пропуск парсинга соединений из-за отсутствия или неверного формата секции 'nodes'. / Skipping connections parsing due to missing or incorrect 'nodes' section.")
            logger.info("Парсинг модели успешно завершен. / Model parsing completed successfully.")
        except (KeyError, TypeError, ValueError) as e: # Ловим специфичные ошибки при доступе к данным
            msg = f"Ошибка структуры данных при парсинге модели: {type(e).__name__} - {e}. / Data structure error during model parsing: {type(e).__name__} - {e}."
            logger.error(msg)
            raise NetworkModelError(msg) from e
        except Exception as e: # Другие неожиданные ошибки парсинга
            msg = f"Критическая ошибка при парсинге модели: {type(e).__name__} - {e} / Critical error during model parsing: {type(e).__name__} - {e}"
            logger.error(msg)
            raise NetworkModelError(msg) from e

    def _parse_elements(self) -> None:
        """
        Парсит информацию об элементах из `self.raw_data['elements']`.
        Parses element information from `self.raw_data['elements']`.

        Создает объекты `NetworkElement` для каждой валидной записи элемента.
        Пропускает элементы с отсутствующим или некорректным типом, или с неверным форматом данных.
        Логирует предупреждения или ошибки для пропущенных или некорректно определенных элементов.
        Creates `NetworkElement` objects for each valid element entry.
        Skips elements with missing or incorrect types, or with invalid data format.
        Logs warnings or errors for skipped or incorrectly defined elements.

        Выбрасывает / Raises:
            KeyError, TypeError, ValueError: при некорректной структуре данных элемента,
                                             которые должны быть пойманы в `_parse_model`.
                                             For incorrect element data structure,
                                             which should be caught in `_parse_model`.
        """
        elements_data = self.raw_data.get('elements', {}) # elements_data уже проверен на dict в _parse_model

        for element_id, element_data_raw in elements_data.items():
            if not isinstance(element_data_raw, dict):
                logger.warning(f"Данные для элемента ID '{element_id}' не являются словарем. Пропуск. / Data for element ID '{element_id}' is not a dictionary. Skipping.")
                continue

            # Гарантируем, что element_data является словарем для дальнейшей безопасной работы с .get()
            element_data: Dict[str, Any] = element_data_raw

            element_type_str = element_data.get('Type') # Тип должен быть строкой
            if not isinstance(element_type_str, str) or not element_type_str:
                logger.warning(f"Тип элемента не указан или имеет неверный формат для ID '{element_id}'. Пропуск. / Element type not specified or has incorrect format for ID '{element_id}'. Skipping.")
                continue

            element_type: ElementType
            try:
                element_type = ElementType(element_type_str)
            except ValueError:
                logger.error(f"Неизвестный тип элемента '{element_type_str}' для ID '{element_id}'. Элемент не будет создан. / Unknown element type '{element_type_str}' for ID '{element_id}'. Element will not be created.")
                continue

            nodes_raw = element_data.get('Nodes', []) # Ожидаем список или int
            nodes: List[int] = []
            if isinstance(nodes_raw, int):
                nodes = [nodes_raw]
            elif isinstance(nodes_raw, list) and all(isinstance(n, int) for n in nodes_raw):
                nodes = nodes_raw
            elif isinstance(nodes_raw, list) and not all(isinstance(n, int) for n in nodes_raw):
                 logger.warning(f"Список узлов для элемента '{element_id}' содержит нечисловые значения: {nodes_raw}. Попытка отфильтровать. / Nodes list for element '{element_id}' contains non-integer values: {nodes_raw}. Attempting to filter.")
                 nodes = [n for n in nodes_raw if isinstance(n, int)]
                 if not nodes and nodes_raw : # Если после фильтрации ничего не осталось, а что-то было
                      logger.warning(f"После фильтрации список узлов для '{element_id}' пуст. / After filtering, nodes list for '{element_id}' is empty.")
            else: # Не int и не list, или пустой список по умолчанию
                logger.debug(f"Узлы для элемента '{element_id}' не указаны или имеют неверный формат: {nodes_raw}. Используется пустой список. / Nodes for element '{element_id}' not specified or have incorrect format: {nodes_raw}. Using empty list.")
                nodes = []


            element_name_raw = element_data.get('Name', f'Element_{str(element_id)[:8]}')
            element_name = str(element_name_raw) if element_name_raw is not None else f'Element_{str(element_id)[:8]}'

            element = NetworkElement(
                id=str(element_id),
                name=element_name,
                element_type=element_type,
                nodes=nodes,
                data=element_data
            )
            self.elements[element.id] = element
            logger.debug("Добавлен элемент: ID=%s, Тип=%s, Узлы=%s / Added element: ID=%s, Type=%s, Nodes=%s",
                         element.id, element.element_type.value, element.nodes)

    def _parse_connections(self) -> None:
        """
        Парсит информацию о соединениях из `self.raw_data['nodes']`.
        Parses connection information from `self.raw_data['nodes']`.

        Формирует `self.node_connections`, связывая ID узлов (строки) со списками
        ID элементов, которые к ним подключены. Пропускает некорректные записи.
        Forms `self.node_connections`, linking node IDs (strings) to lists of
        element IDs connected to them. Skips incorrect entries.
        """
        nodes_data = self.raw_data.get('nodes', {}) # nodes_data уже проверен на dict в _parse_model

        for node_id_str_raw, connected_element_ids_raw in nodes_data.items():
            node_id_str = str(node_id_str_raw) # Ключ узла должен быть строкой

            if not isinstance(connected_element_ids_raw, list):
                logger.warning(f"Для узла '{node_id_str}' список подключенных элементов не является списком ({type(connected_element_ids_raw).__name__}). Пропуск. / For node '{node_id_str}', connected elements list is not a list ({type(connected_element_ids_raw).__name__}). Skipping.")
                continue

            valid_elements_for_node: List[str] = []
            for elem_id_raw in connected_element_ids_raw:
                elem_id = str(elem_id_raw)
                if elem_id in self.elements:
                    valid_elements_for_node.append(elem_id)
                else:
                    logger.debug(f"Элемент с ID '{elem_id}', указанный в соединениях узла '{node_id_str}', не найден в self.elements. / Element with ID '{elem_id}' in connections of node '{node_id_str}' not found in self.elements.")

            if valid_elements_for_node:
                self.node_connections[node_id_str] = valid_elements_for_node
                logger.debug("Узел '%s': установлены соединения с %s / Node '%s': established connections with %s", node_id_str, valid_elements_for_node)

        if not self.node_connections:
            logger.warning("Соединения узлов (self.node_connections) не были сформированы. Проверьте раздел 'nodes' в модели. / Node connections (self.node_connections) were not formed. Check 'nodes' section in the model.")

    def get_element(self, element_id: str) -> Optional[NetworkElement]:
        """
        Возвращает объект `NetworkElement` по его уникальному идентификатору.
        Returns the `NetworkElement` object by its unique identifier.

        Параметры / Parameters:
            element_id (str): Уникальный идентификатор запрашиваемого элемента.
                              The unique identifier of the requested element.

        Возвращает / Returns:
            Optional[NetworkElement]: Объект `NetworkElement`, если элемент с таким ID существует,
                                      иначе None.
                                      The `NetworkElement` object if an element with such ID exists,
                                      otherwise None.
        """
        element = self.elements.get(element_id)
        if not element:
            logger.debug("Элемент с ID '%s' не найден в модели. / Element with ID '%s' not found in model.", element_id)
        return element

    def get_root_elements(self) -> List[str]:
        """
        Определяет и возвращает список идентификаторов корневых элементов в модели.
        Identifies and returns a list of root element identifiers in the model.

        Корневым считается элемент, для которого соответствующий анализатор типа
        (полученный через `get_analyzer`) возвращает `True` из метода `is_root()`.
        An element is considered a root if its corresponding type analyzer
        (obtained via `get_analyzer`) returns `True` from its `is_root()` method.

        Возвращает / Returns:
            List[str]: Список строковых идентификаторов корневых элементов.
                       A list of string identifiers of root elements.
        """
        root_element_ids: List[str] = []
        for element_id, element in self.elements.items():
            analyzer = self.get_analyzer(element.element_type)
            # Проверяем, что анализатор существует и имеет метод is_root
            if analyzer and hasattr(analyzer, 'is_root') and callable(analyzer.is_root):
                if analyzer.is_root(element): # Передаем сам элемент в is_root
                    root_element_ids.append(element_id)
                    logger.debug("Найден корневой элемент: ID=%s, Тип=%s / Found root element: ID=%s, Type=%s",
                                 element_id, element.element_type)
            #else:
                # Логировать отсутствие анализатора или метода is_root здесь может быть слишком многословно,
                # т.к. get_analyzer уже выводит предупреждение.

        if not root_element_ids:
            logger.warning("Корневые элементы не найдены в модели. / No root elements found in the model.")
        return root_element_ids

@dataclass
class NetworkAnalysisResult:
    """
    Структура данных для хранения результатов анализа топологии сети.
    Data structure for storing the results of network topology analysis.

    Этот датакласс инкапсулирует основные компоненты, описывающие
    древовидное или лесовидное представление сети, полученное в результате
    работы `NetworkTreeBuilder` (и, следовательно, `NetworkAnalyzer`).
    This dataclass encapsulates the main components that describe
    the tree-like or forest-like representation of the network, obtained
    as a result of `NetworkTreeBuilder`'s work (and therefore `NetworkAnalyzer`).

    Атрибуты / Attributes:
        roots (List[str]): Список идентификаторов (ID) корневых элементов сети.
                           A list of identifiers (IDs) of the root elements of the network.
        nodes (List[str]): Список ID всех элементов (узлов), присутствующих в анализируемой модели.
                           A list of IDs of all elements (nodes) present in the analyzed model.
        tree (Dict[str, Dict[str, List[str]]]): Словарь, представляющий структуру связей "родитель-потомок".
                                                Ключ - ID родительского элемента.
                                                Значение - словарь с одним ключом 'child', значение которого -
                                                список ID прямых дочерних элементов этого родителя.
                                                A dictionary representing the parent-child relationship structure.
                                                The key is the parent element's ID.
                                                The value is a dictionary with a single key 'child', whose value
                                                is a list of IDs of the direct children of that parent.
                                                Пример / Example: `{'parent_id': {'child': ['child1_id', 'child2_id']}}`
    """
    roots: List[str]
    nodes: List[str]
    tree: Dict[str, Dict[str, List[str]]]