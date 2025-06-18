#!/usr/bin/env python3
import json
import argparse
import sys
from collections import defaultdict

def convert_elements(input_path: str, output_path: str):
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Ошибка при чтении '{input_path}': {e}", file=sys.stderr)
        sys.exit(1)

    elements_list = data.get("elements", [])
    result = {"elements": {}, "nodes": defaultdict(list)}

    for el in elements_list:
        el_id = el.get("id")
        if not el_id:
            continue

        result["elements"][el_id] = el

        nodes = el.get("Nodes")
        if isinstance(nodes, int):
            nodes = [nodes]
        elif not isinstance(nodes, list):
            continue

        for node in nodes:
            result["nodes"][node].append(el_id)

    # Преобразуем defaultdict в обычный dict перед сериализацией
    result["nodes"] = dict(result["nodes"])

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Ошибка при записи '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Преобразование завершено, результат сохранён в '{output_path}'")

def main():
    parser = argparse.ArgumentParser(
        description="Преобразует структуру JSON: elements → {elements: {id: el}, nodes: {node: [ids]}}"
    )
    parser.add_argument("input", metavar="INPUT", help="входной JSON-файл (с ключом 'elements')")
    parser.add_argument("-o", "--output", metavar="OUTPUT", default="converted.json",
                        help="выходной JSON-файл (по умолчанию 'converted.json')")

    args = parser.parse_args()
    convert_elements(args.input, args.output)

if __name__ == "__main__":
    main()
