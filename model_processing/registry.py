"""
Этот модуль предоставляет класс `AnalyzerRegistry`, который служит централизованным
механизмом для регистрации и доступа к различным анализаторам элементов сети
(`ElementAnalyzer`). Использование реестра позволяет избежать жестко закодированных
связей и циклических импортов между модулем `NetworkModel` и конкретными
реализациями анализаторов. Это способствует модульности и расширяемости системы,
позволяя легко добавлять новые типы анализаторов.

This module provides the `AnalyzerRegistry` class, which serves as a centralized
mechanism for registering and accessing various network element analyzers
(`ElementAnalyzer`). Using a registry helps avoid hard-coded dependencies and
circular imports between the `NetworkModel` module and specific analyzer
implementations. This promotes modularity and extensibility of the system,
allowing new analyzer types to be easily added.
"""
from typing import List, Type, TYPE_CHECKING, Set as TypingSet, Dict, Optional as TypingOptional
# import importlib # Закомментировано, т.к. import model_processing.analyzers используется напрямую
import inspect
# ElementAnalyzer импортируется ниже, после if TYPE_CHECKING, чтобы избежать проблем при инициализации
# from .analyzers import ElementAnalyzer
from .models import ElementType # ElementType нужен для ключей словаря и аннотаций

import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .analyzers import ElementAnalyzer # pragma: no cover

# Импортируем ElementAnalyzer здесь, чтобы он был доступен во время выполнения
from .analyzers import ElementAnalyzer

class AnalyzerRegistry:
    """
    Реестр для управления анализаторами элементов электрической сети.
    Registry for managing electrical network element analyzers.

    Этот класс использует статические методы и атрибуты класса для хранения
    и предоставления доступа к экземплярам анализаторов. Он обеспечивает:
    - Регистрацию отдельных классов анализаторов.
    - Автоматическое обнаружение и регистрацию всех анализаторов по умолчанию из модуля `model_processing.analyzers`.
    - Получение словаря всех зарегистрированных экземпляров анализаторов, индексированных по `ElementType`.
    - Получение конкретного анализатора по его `ElementType`.

    Такая централизация упрощает управление зависимостями и расширение системы новыми типами анализаторов.
    `NetworkModel` использует этот реестр для получения необходимых анализаторов для обработки элементов сети.

    This class uses static methods and class attributes to store and provide
    access to analyzer instances. It provides:
    - Registration of individual analyzer classes.
    - Automatic discovery and registration of all default analyzers from the `model_processing.analyzers` module.
    - Retrieval of a dictionary of all registered analyzer instances, indexed by `ElementType`.
    - Retrieval of a specific analyzer by its `ElementType`.

    This centralization simplifies dependency management and system extension with new analyzer types.
    `NetworkModel` uses this registry to obtain the necessary analyzers for processing network elements.

    Атрибуты класса / Class Attributes:
        _analyzers_dict (Dict[ElementType, ElementAnalyzer]): Приватный словарь, хранящий экземпляры
                                                              всех зарегистрированных анализаторов,
                                                              ключом является `ElementType`.
                                                              A private dictionary storing instances of all
                                                              registered analyzers, keyed by `ElementType`.
    """

    _analyzers_dict: Dict[ElementType, ElementAnalyzer] = {} # Словарь для хранения экземпляров анализаторов

    @classmethod
    def register_analyzer(cls, analyzer_class: Type[ElementAnalyzer]) -> None:
        """
        Регистрирует предоставленный класс анализатора в реестре.
        Registers the provided analyzer class in the registry.

        Перед регистрацией выполняется проверка, что `analyzer_class` является
        подклассом `ElementAnalyzer` и не является самим `ElementAnalyzer` (т.е. должен быть конкретным анализатором).
        Если класс валиден, создается его экземпляр и добавляется в список `_analyzers`.
        Before registration, a check is performed to ensure that `analyzer_class` is a
        subclass of `ElementAnalyzer` and not `ElementAnalyzer` itself (i.e., it must be a concrete analyzer).
        If the class is valid, an instance of it is created and added to the `_analyzers` list.

        Параметры / Parameters:
            analyzer_class (Type['ElementAnalyzer']): Класс анализатора для регистрации,
                                                      должен быть унаследован от `ElementAnalyzer`.
                                                      The analyzer class to register, must be
                                                      a subclass of `ElementAnalyzer`.
        Выбрасывает / Raises:
            ValueError: Если `analyzer_class` не является допустимым подклассом `ElementAnalyzer`.
                        If `analyzer_class` is not a valid subclass of `ElementAnalyzer`.
        """
        # Проверяем, что это действительно класс, а не экземпляр, и что он наследуется от ElementAnalyzer,
        # но не является самим ElementAnalyzer (т.к. ElementAnalyzer абстрактный).
        if not inspect.isclass(analyzer_class) or \
           not issubclass(analyzer_class, ElementAnalyzer) or \
           analyzer_class is ElementAnalyzer:
            raise ValueError(
                f"Класс '{analyzer_class.__name__}' должен быть конкретным подклассом ElementAnalyzer. / "
                f"Class '{analyzer_class.__name__}' must be a concrete subclass of ElementAnalyzer."
            )

        # Проверяем, не зарегистрирован ли уже анализатор такого же типа (основываясь на классе)
        # Это предотвращает дублирование, если метод регистрации вызывается несколько раз с тем же классом.
        # Однако, get_element_type() вызывается на экземпляре, так что эта проверка здесь может быть избыточна,
        # если логика в NetworkModel.get_analyzer корректно обрабатывает типы.
        # Проверяем, не зарегистрирован ли уже анализатор для данного типа элемента.
        # Это требует инстанцирования для вызова get_element_type().
        temp_instance = analyzer_class()
        analyzer_type = temp_instance.get_element_type()

        if analyzer_type in cls._analyzers_dict:
            logger.warning(f"Анализатор для типа {analyzer_type} уже зарегистрирован ({cls._analyzers_dict[analyzer_type].__class__.__name__}). Новый анализатор {analyzer_class.__name__} не будет зарегистрирован. / Analyzer for type {analyzer_type} is already registered ({cls._analyzers_dict[analyzer_type].__class__.__name__}). New analyzer {analyzer_class.__name__} will not be registered.")
            return

        logger.info("Регистрация анализатора: %s для типа %s / Registering analyzer: %s for type %s", analyzer_class.__name__, analyzer_type, analyzer_class.__name__, analyzer_type)
        cls._analyzers_dict[analyzer_type] = temp_instance


    @classmethod
    def get_analyzer_by_type(cls, element_type: ElementType) -> TypingOptional[ElementAnalyzer]:
        """
        Возвращает экземпляр анализатора для указанного `ElementType`.
        Returns an analyzer instance for the specified `ElementType`.

        Параметры / Parameters:
            element_type (ElementType): Тип элемента, для которого запрашивается анализатор.
                                        The element type for which an analyzer is requested.

        Возвращает / Returns:
            Optional[ElementAnalyzer]: Экземпляр анализатора или None, если анализатор
                                       для данного типа не зарегистрирован.
                                       An analyzer instance or None if no analyzer is
                                       registered for the given type.
        """
        analyzer = cls._analyzers_dict.get(element_type)
        if not analyzer:
            logger.warning(f"Анализатор для типа ElementType '{element_type.value if isinstance(element_type, Enum) else element_type}' не найден в реестре. / Analyzer for ElementType '{element_type.value if isinstance(element_type, Enum) else element_type}' not found in registry.")
        return analyzer

    @classmethod
    def get_analyzers(cls) -> List[ElementAnalyzer]: # Возвращает список значений словаря
        """
        Возвращает список всех зарегистрированных экземпляров анализаторов.
        Returns a list of all registered analyzer instances.

        Этот список может быть использован для итерации по всем доступным анализаторам,
        например, в `NetworkModel` для построения своего внутреннего отображения.
        This list can be used to iterate over all available analyzers,
        for example, in `NetworkModel` to build its internal mapping.

        Возвращает / Returns:
            List[ElementAnalyzer]: Список экземпляров анализаторов.
                                     A list of analyzer instances.
        """
        if not cls._analyzers_dict:
            logger.warning("Словарь зарегистрированных анализаторов пуст. Возможно, register_default_analyzers не был вызван или не нашел анализаторы. / Dictionary of registered analyzers is empty. Perhaps register_default_analyzers was not called or found no analyzers.")
        return list(cls._analyzers_dict.values())

    @classmethod
    def register_default_analyzers(cls) -> None:
        """
        Автоматически обнаруживает и регистрирует все классы анализаторов по умолчанию
        из модуля `model_processing.analyzers`.
        Automatically discovers and registers all default analyzer classes
        from the `model_processing.analyzers` module.

        Метод импортирует модуль `model_processing.analyzers`, итерирует по всем его членам,
        являющимся классами, и фильтрует те, которые:
        1. Являются подклассами `ElementAnalyzer`.
        2. Определены непосредственно в модуле `model_processing.analyzers` (а не импортированы в него).
        3. Не входят в список исключенных базовых или абстрактных классов (таких как
           `ElementAnalyzer` сам, `DirectionalElementAnalyzer`, `TerminalElementAnalyzer`).
        Каждый подходящий класс анализатора затем регистрируется с помощью `cls.register_analyzer()`.

        The method imports the `model_processing.analyzers` module, iterates through all its
        class members, and filters those that:
        1. Are subclasses of `ElementAnalyzer`.
        2. Are defined directly in the `model_processing.analyzers` module (not imported into it).
        3. Are not in the list of excluded base or abstract classes (such as
           `ElementAnalyzer` itself, `DirectionalElementAnalyzer`, `TerminalElementAnalyzer`).
        Each suitable analyzer class is then registered using `cls.register_analyzer()`.

        Выбрасывает / Raises:
            ImportError: Если модуль `model_processing.analyzers` не может быть импортирован.
                         If the `model_processing.analyzers` module cannot be imported.
            ValueError: Если обнаруженный класс не является допустимым для регистрации (например, ошибка в `register_analyzer`).
                        If a discovered class is not valid for registration (e.g., an error in `register_analyzer`).
        """
        logger.info("Начало регистрации анализаторов по умолчанию... / Starting registration of default analyzers...")
        # Очищаем словарь перед повторной регистрацией, чтобы избежать дубликатов или старых записей
        # при многократных вызовах (хотя обычно этот метод вызывается один раз).
        if cls._analyzers_dict:
            logger.debug("Очистка ранее зарегистрированных анализаторов (в словаре) перед регистрацией по умолчанию. / Clearing previously registered analyzers (in dictionary) before default registration.")
            cls._analyzers_dict = {}

        try:
            import model_processing.analyzers as analyzers_module # Модуль, где определены классы анализаторов

            excluded_analyzer_base_names: TypingSet[str] = {"DirectionalElementAnalyzer", "TerminalElementAnalyzer"}
            excluded_classes: TypingSet[Type[ElementAnalyzer]] = {ElementAnalyzer}

            for name_to_exclude in excluded_analyzer_base_names:
                if hasattr(analyzers_module, name_to_exclude):
                    analyzer_attr = getattr(analyzers_module, name_to_exclude)
                    if inspect.isclass(analyzer_attr) and issubclass(analyzer_attr, ElementAnalyzer):
                        excluded_classes.add(analyzer_attr)

        except ImportError as e:
            logger.error("Не удалось импортировать модуль .analyzers или базовый ElementAnalyzer: %s / Failed to import .analyzers module or base ElementAnalyzer: %s", str(e), e)
            raise ImportError(f"Ошибка импорта модуля анализаторов: {e}") from e

        for name, member_class in inspect.getmembers(analyzers_module, inspect.isclass):
            if (issubclass(member_class, ElementAnalyzer) and
                    member_class.__module__ == analyzers_module.__name__ and # Убеждаемся, что класс определен в этом модуле
                    member_class not in excluded_classes):
                try:
                    cls.register_analyzer(member_class) # Регистрируем класс
                    logger.debug("Автоматически зарегистрирован анализатор: %s / Automatically registered analyzer: %s", name)
                except ValueError as e:
                    logger.error("Не удалось зарегистрировать анализатор '%s': %s / Failed to register analyzer '%s': %s", name, e, name, e)
        logger.info(f"Регистрация анализаторов по умолчанию завершена. Зарегистрировано: {len(cls._analyzers_dict)} типов анализаторов. / Default analyzers registration finished. Registered: {len(cls._analyzers_dict)} analyzer types.")