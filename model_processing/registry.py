from typing import List, Type, TYPE_CHECKING
import importlib
import inspect
from .analyzers import ElementAnalyzer

#from .analyzers import (
#    SystemAnalyzer, BusAnalyzer, OverheadLineAnalyzer,
#    TransformerAnalyzer, GeneratorAnalyzer, LoadAnalyzer
#)

import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .analyzers import ElementAnalyzer

class AnalyzerRegistry:
    """Реестр анализаторов элементов электрической сети.

    Предоставляет централизованный механизм для регистрации и получения анализаторов,
    избегая циклических импортов между модулями.

    Attributes:
        _analyzers (List[ElementAnalyzer]): Список зарегистрированных анализаторов.
    """

    _analyzers: List['ElementAnalyzer'] = []

    @classmethod
    def register_analyzer(cls, analyzer_class: Type['ElementAnalyzer']) -> None:
        """Регистрирует класс анализатора.

        Args:
            analyzer_class (Type[ElementAnalyzer]): Класс анализатора, производный от ElementAnalyzer.
        Raises:
            ValueError: Если класс не является производным от ElementAnalyzer.
        """
        if not issubclass(analyzer_class, ElementAnalyzer) or analyzer_class is ElementAnalyzer:
            raise ValueError(f"Класс {analyzer_class.__name__} должен быть производным от ElementAnalyzer")
        logger.info("Регистрация анализатора: %s", analyzer_class.__name__)
        cls._analyzers.append(analyzer_class())

    @classmethod
    def get_analyzers(cls) -> List['ElementAnalyzer']:
        """Возвращает список всех зарегистрированных анализаторов.

        Returns:
            List[ElementAnalyzer]: Список экземпляров анализаторов.
        """
        return cls._analyzers

    @classmethod
    def register_default_analyzers(cls) -> None: 
                                   #module_name: str = "network_analyzer.analyzers") -> None:
        """Динамически регистрирует анализаторы из указанного модуля.

        Автоматически обнаруживает все классы, наследующиеся от ElementAnalyzer, в указанном модуле
        и регистрирует их.

        Args:
            module_name (str): Имя модуля, из которого загружаются анализаторы
                              (по умолчанию "network_analyzer.analyzers").

        Raises:
            ImportError: Если модуль не может быть импортирован.
            ValueError: Если обнаруженный класс не является производным от ElementAnalyzer.
        """
        try:
            import model_processing.analyzers as analyzers_module
            excluded_analyzer_bases_names = {"DirectionalElementAnalyzer", "TerminalElementAnalyzer"}
            excluded_classes = {ElementAnalyzer}
            for name_to_exclude in excluded_analyzer_bases_names:
                if hasattr(analyzers_module, name_to_exclude):
                    excluded_classes.add(getattr(analyzers_module, name_to_exclude))

        except ImportError as e:
            logger.error("Failed to import .analyzers module or ElementAnalyzer: %s", str(e))
            raise 

        for name, obj_type in inspect.getmembers(analyzers_module, inspect.isclass):
            if (issubclass(obj_type, ElementAnalyzer) and
                    obj_type.__module__ == analyzers_module.__name__ and
                    obj_type not in excluded_classes):
                try:
                    cls.register_analyzer(obj_type) # Register the class itself
                    logger.debug("Dynamically registered analyzer: %s", name)
                except ValueError as e: # Catch potential errors from register_analyzer
                    logger.error("Failed to register analyzer %s: %s", name, e)
        

        