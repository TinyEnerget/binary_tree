"""Примеры использования пакета model_processing.

Демонстрирует основные сценарии работы с классами и функциями пакета для анализа
электрической сети и построения ее дерева.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional # Added Optional
from model_processing import (
    NetworkAnalyzer
)
from model_processing.models import NetworkAnalysisResult # Added NetworkAnalysisResult

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_model():
    logger.info("Запуск примера 0: загрузка модели")
    from model_processing import load_json, save_json
    input_file_1 = Path('C:\\Users\\Vlad Titov\\Desktop\\Work\\binary_tree\\model_processing\\available_modification\\converted.json')
    input_file_2 = Path('model.json')
    model_1 = load_json(input_file_1)
    
    with open(input_file_2, 'r', encoding='utf-8') as file:
        model_2 = json.load(file)
    if model_1 != model_2:
        logger.error("Модели не совпадают")
        save_json('model_1.json', model_1)
        save_json('model_2.json', model_2)
    else:
        logger.info("Модели совпадают")

   

def example_1_analyze_network() -> None:
    """Пример 1: Анализ сети с использованием NetworkAnalyzer.

    Загружает модель сети из JSON-файла, выполняет анализ и сравнивает с эталоном.
    """
    logger.info("Запуск примера 1: Анализ сети")
    
    input_file = Path('C:\\Users\\Vlad Titov\\Desktop\\Work\\binary_tree\\model_processing\\available_modification\\converted.json')#Path('model.json')
    output_file = Path("output.json")
    
    if not input_file.exists():
        logger.error("Входной файл %s не найден", input_file)
        return
    
    try:
        # Анализируем сеть
        result: Optional[NetworkAnalysisResult] = None # Initialize with None
        result = NetworkAnalyzer.analyze_network(str(input_file), str(output_file))
        logger.info("Анализ завершен. Результаты сохранены в %s", output_file)
        
        if result is None: # Should not happen if analyze_network raises on critical errors
            logger.error("Анализ сети не вернул результат.")
            return

        # Сравниваем с эталоном
        reference_file = Path("example.json")
        if reference_file.exists():
            is_match = NetworkAnalyzer.compare_with_reference(result, str(reference_file))
            logger.info("Результаты соответствуют эталону: %s", is_match)
        else:
            logger.warning("Эталонный файл %s не найден", reference_file)
    except Exception as e:
        logger.error("Ошибка при анализе сети: %s", e)

def main() -> None:
    """Запускает все примеры последовательно."""
    logger.info("Запуск всех примеров использования пакета model_processing")
    check_model()
    example_1_analyze_network()
    
    logger.info("Все примеры завершены")

if __name__ == '__main__':
    main()