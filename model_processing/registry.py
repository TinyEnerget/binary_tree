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
from typing import List, Type, TYPE_CHECKING, Set as TypingSet # Добавлен Set для excluded_classes
# import importlib # Закомментировано, т.к. import model_processing.analyzers используется напрямую
import inspect
from .analyzers import ElementAnalyzer # Базовый класс для проверки типов

# Закомментированные импорты конкретных анализаторов не нужны здесь,
# так как register_default_analyzers будет импортировать модуль analyzers целиком.
# from .analyzers import (
#    SystemAnalyzer, BusAnalyzer, OverheadLineAnalyzer,
#    TransformerAnalyzer, GeneratorAnalyzer, LoadAnalyzer
# )

import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # Этот импорт остается здесь для поддержки проверки типов, если ElementAnalyzer используется в аннотациях напрямую.
    from .analyzers import ElementAnalyzer # pragma: no cover

class AnalyzerRegistry:
    """
    Реестр для управления анализаторами элементов электрической сети.
    Registry for managing electrical network element analyzers.

    Этот класс использует статические методы и атрибуты класса для хранения
    и предоставления доступа к экземплярам анализаторов. Он обеспечивает:
    - Регистрацию отдельных классов анализаторов.
    - Автоматическое обнаружение и регистрацию всех анализаторов по умолчанию из модуля `model_processing.analyzers`.
    - Получение списка всех зарегистрированных экземпляров анализаторов.

    Такая централизация упрощает управление зависимостями и расширение системы новыми типами анализаторов.
    `NetworkModel` использует этот реестр для получения необходимых анализаторов для обработки элементов сети.

    This class uses static methods and class attributes to store and provide
    access to analyzer instances. It provides:
    - Registration of individual analyzer classes.
    - Automatic discovery and registration of all default analyzers from the `model_processing.analyzers` module.
    - Retrieval of a list of all registered analyzer instances.

    This centralization simplifies dependency management and system extension with new analyzer types.
    `NetworkModel` uses this registry to obtain the necessary analyzers for processing network elements.

    Атрибуты класса / Class Attributes:
        _analyzers (List['ElementAnalyzer']): Приватный список, хранящий экземпляры
                                             всех зарегистрированных анализаторов.
                                             A private list storing instances of all
                                             registered analyzers.
    """

    _analyzers: List['ElementAnalyzer'] = [] # Список для хранения экземпляров анализаторов

    @classmethod
    def register_analyzer(cls, analyzer_class: Type['ElementAnalyzer']) -> None:
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
        # Для простоты, если один и тот же КЛАСС регистрируется дважды, будет два ЭКЗЕМПЛЯРА.
        # Если нужно гарантировать уникальность по типу элемента, логика должна быть сложнее.

        logger.info("Регистрация анализатора: %s / Registering analyzer: %s", analyzer_class.__name__)
        try:
            # Создаем экземпляр и добавляем в список
            cls._analyzers.append(analyzer_class())
        except Exception as e:
            logger.error(f"Не удалось создать экземпляр или зарегистрировать анализатор {analyzer_class.__name__}: {e} / Failed to instantiate or register analyzer {analyzer_class.__name__}: {e}")
            # Можно перевыбросить как ValueError или специфическое исключение реестра
            raise ValueError(f"Ошибка при инстанцировании анализатора {analyzer_class.__name__}: {e}")


    @classmethod
    def get_analyzers(cls) -> List['ElementAnalyzer']:
        """
        Возвращает список всех зарегистрированных экземпляров анализаторов.
        Returns a list of all registered analyzer instances.

        Этот список используется `NetworkModel` для получения доступа к логике анализа
        различных типов элементов сети.
        This list is used by `NetworkModel` to access the analysis logic
        for different types of network elements.

        Возвращает / Returns:
            List['ElementAnalyzer']: Список экземпляров анализаторов.
                                     A list of analyzer instances.
        """
        if not cls._analyzers:
            logger.warning("Список зарегистрированных анализаторов пуст. Возможно, register_default_analyzers не был вызван или не нашел анализаторы. / List of registered analyzers is empty. Perhaps register_default_analyzers was not called or found no analyzers.")
        return cls._analyzers

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
        # Очищаем список перед повторной регистрацией, чтобы избежать дубликатов при многократных вызовах
        # (хотя обычно этот метод вызывается один раз при инициализации).
        # Если это нежелательно, эту строку можно убрать.
        if cls._analyzers:
            logger.debug("Очистка ранее зарегистрированных анализаторов перед регистрацией по умолчанию. / Clearing previously registered analyzers before default registration.")
            cls._analyzers = []

        try:
            # Импортируем модуль, где определены конкретные анализаторы
            import model_processing.analyzers as analyzers_module

            # Определяем базовые/абстрактные классы, которые не должны регистрироваться как конкретные анализаторы
            excluded_analyzer_base_names: TypingSet[str] = {"DirectionalElementAnalyzer", "TerminalElementAnalyzer"}
            excluded_classes: TypingSet[Type[ElementAnalyzer]] = {ElementAnalyzer} # Исключаем сам ElementAnalyzer

            for name_to_exclude in excluded_analyzer_base_names:
                if hasattr(analyzers_module, name_to_exclude):
                    excluded_classes.add(getattr(analyzers_module, name_to_exclude))

        except ImportError as e:
            logger.error("Не удалось импортировать модуль .analyzers или базовый ElementAnalyzer: %s / Failed to import .analyzers module or base ElementAnalyzer: %s", str(e), e)
            # Перевыбрасываем, так как это критическая ошибка для работы реестра
            raise ImportError(f"Ошибка импорта модуля анализаторов: {e}") from e

        # Итерируем по всем членам модуля analyzers_module
        for name, member_type in inspect.getmembers(analyzers_module, inspect.isclass):
            # Проверяем, что это класс, он является подклассом ElementAnalyzer,
            # он определен в модуле analyzers_module (а не импортирован туда),
            # и он не входит в список исключенных классов.
            if (issubclass(member_type, ElementAnalyzer) and
                    member_type.__module__ == analyzers_module.__name__ and
                    member_type not in excluded_classes):
                try:
                    # Регистрируем сам класс (экземпляр будет создан в register_analyzer)
                    cls.register_analyzer(member_type)
                    logger.debug("Автоматически зарегистрирован анализатор: %s / Automatically registered analyzer: %s", name)
                except ValueError as e:
                    # Логируем ошибку, если register_analyzer вызвал исключение
                    logger.error("Не удалось зарегистрировать анализатор '%s': %s / Failed to register analyzer '%s': %s", name, e, name, e)
        logger.info(f"Регистрация анализаторов по умолчанию завершена. Зарегистрировано: {len(cls._analyzers)} анализаторов. / Default analyzers registration finished. Registered: {len(cls._analyzers)} analyzers.")