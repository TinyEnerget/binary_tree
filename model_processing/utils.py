import json
from typing import Dict, Any
from pathlib import Path

def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Loads JSON data from a specified file path.

    Args:
        file_path (Path): The path to the JSON file.

    Returns:
        Dict[str, Any]: The data loaded from the JSON file.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """
    Saves the given data to a JSON file at the specified path.
    Ensures the parent directory for the file exists before writing.

    Args:
        file_path (Path): The path where the JSON file will be saved.
        data (Dict[str, Any]): The data to save.

    Raises:
        OSError: If there is an issue writing the file (e.g., permissions).
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=6, ensure_ascii=False)

# rewrite_nodes and find_root_nodes have been moved to ModelPreprocessor
