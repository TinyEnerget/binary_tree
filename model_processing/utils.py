"""
Этот модуль предоставляет вспомогательные (утилитные) функции, используемые
в различных частях пакета `model_processing`. В настоящее время он включает
функции для загрузки данных из JSON-файлов и сохранения данных в JSON-файлы.

This module provides utility functions used in various parts of the
`model_processing` package. Currently, it includes functions for loading data
from JSON files and saving data to JSON files.
"""
import json
from typing import Dict, Any
import logging # Добавлено логирование

logger = logging.getLogger(__name__) # Инициализация логгера для этого модуля

def load_json(file_path: str) -> Dict[str, Any]:
    """
    Загружает данные из файла формата JSON.
    Loads data from a JSON formatted file.

    Эта функция является оберткой над `json.load()`, обеспечивая
    чтение файла с кодировкой UTF-8.
    This function is a wrapper around `json.load()`, ensuring
    the file is read with UTF-8 encoding.

    Параметры / Parameters:
        file_path (str): Строковый путь к JSON-файлу.
                         String path to the JSON file.

    Возвращает / Returns:
        Dict[str, Any]: Словарь с данными, загруженными из файла.
                        A dictionary with the data loaded from the file.

    Выбрасывает / Raises:
        FileNotFoundError: Если файл по указанному пути не найден.
                           If the file at the specified path is not found.
        json.JSONDecodeError: Если содержимое файла не является корректным JSON.
                              If the file content is not valid JSON.
        Exception: Другие возможные исключения, связанные с операциями файлового ввода-вывода.
                   Other potential exceptions related to file I/O operations.
    """
    logger.debug(f"Загрузка JSON из файла: {file_path} / Loading JSON from file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Файл не найден при загрузке: {file_path} / File not found during load: {file_path}")
        raise
    except PermissionError as e:
        logger.error(f"Ошибка прав доступа при загрузке файла: {file_path} - {e} / Permission error during file load: {file_path} - {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON в файле {file_path}: {e.message} (строка {e.lineno}, столбец {e.colno}) / JSON decoding error in file {file_path}: {e.message} (line {e.lineno}, column {e.colno})")
        raise
    except IOError as e: # Более общая ошибка ввода-вывода, если не FileNotFoundError или PermissionError
        logger.error(f"Ошибка ввода-вывода при загрузке JSON из {file_path}: {e} / IO error loading JSON from {file_path}: {e}")
        raise
    except Exception as e: # Для других непредвиденных ошибок
        logger.error(f"Непредвиденная ошибка при загрузке JSON из {file_path}: {type(e).__name__} - {e} / Unexpected error loading JSON from {file_path}: {type(e).__name__} - {e}")
        raise

def save_json(file_path: str, data: Dict[str, Any]) -> None:
    """
    Сохраняет предоставленные данные (словарь) в файл формата JSON.
    Saves the provided data (dictionary) to a JSON formatted file.

    Данные сохраняются с кодировкой UTF-8, с отступом в 6 пробелов для
    читаемости и с параметром `ensure_ascii=False` для корректной записи
    не-ASCII символов (например, кириллицы).
    The data is saved with UTF-8 encoding, an indent of 6 spaces for
    readability, and the `ensure_ascii=False` parameter for correct
    writing of non-ASCII characters (e.g., Cyrillic).

    Параметры / Parameters:
        file_path (str): Строковый путь к файлу, в который будут сохранены данные.
                         String path to the file where the data will be saved.
        data (Dict[str, Any]): Словарь с данными для сохранения.
                               A dictionary containing the data to save.

    Выбрасывает / Raises:
        OSError: Если происходит ошибка при записи в файл (например, из-за
                 проблем с правами доступа или если путь недействителен).
                 If an error occurs while writing to the file (e.g., due to
                 permission issues or if the path is invalid).
        Exception: Другие возможные исключения, связанные с операциями файлового ввода-вывода.
                   Other potential exceptions related to file I/O operations.
    """
    logger.debug(f"Сохранение данных в JSON-файл: {file_path} / Saving data to JSON file: {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False) # Изменен отступ на 4 для большей распространенности
        logger.info(f"Данные успешно сохранены в {file_path} / Data successfully saved to {file_path}")
    except PermissionError as e:
        logger.error(f"Ошибка прав доступа при сохранении файла: {file_path} - {e} / Permission error during file save: {file_path} - {e}")
        raise
    except TypeError as e: # Может возникнуть, если `data` несериализуемо в JSON
        logger.error(f"Ошибка типа данных при сериализации в JSON для файла {file_path}: {e} / Data type error during JSON serialization for file {file_path}: {e}")
        raise
    except OSError as e: # Более общая ошибка ввода-вывода, если не PermissionError
        logger.error(f"Ошибка ввода-вывода при сохранении JSON в файл {file_path}: {e} / OS error while saving JSON to file {file_path}: {e}")
        raise
    except Exception as e: # Для других непредвиденных ошибок
        logger.error(f"Непредвиденная ошибка при сохранении JSON в {file_path}: {type(e).__name__} - {e} / Unexpected error saving JSON to {file_path}: {type(e).__name__} - {e}")
        raise

def rewrite_nodes(model: dict) -> dict:
    nodes = {}
    for key, value in model['nodes'].items():
        #print(f'Key: {key}, Value: {value}')
        for id in value:
            if 'bus' == model['elements'][id]['Type']:
                nodes[id] = value
                #print(f'Node: {id}, Value: {value}')
                           
    clear_nodes = {}
    for key, value in nodes.items():
        new_value = []
        #print(f'Key: {key}, Value: {value}')
        for item in value:
            if key != item:
                new_value.append(item)
        clear_nodes[key] = new_value
        #print(f'New Key: {key}, New Value: {new_value}')
    model['nodes'] = clear_nodes
    return model

def find_root_nodes(model):
    nodes = []
    roots = []
    for key, node in model['nodes'].items():
        nodes.extend(node)
        #nodes.append(key)

    nodes = list(set(nodes))

    for node in nodes: 
        if model['elements'][node]['Type'] == 'system':
            roots.append(node)

    model['roots'] = roots
    model['nodes_id'] = nodes
    return model     
