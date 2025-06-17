import json
from typing import Dict, Any

def load_json(file_path: str) -> Dict[str, Any]:
    """Загружает JSON из файла."""
    with open(file_path, 'r', encoding='utf-8') as file:
        #model = rewrite_nodes(json.load(file))
        #model = find_root_nodes(model)
        return json.load(file)

def save_json(file_path: str, data: Dict[str, Any]) -> None:
    """Сохраняет данные в JSON-файл."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=6, ensure_ascii=False)

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
