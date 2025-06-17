"""
Этот модуль предоставляет класс `TreeComparator`, предназначенный для
сравнения двух древовидных структур сети. Основная задача - проверить,
соответствует ли сгенерированное дерево (результат анализа) эталонному
дереву, обычно загружаемому из файла.

This module provides the `TreeComparator` class, designed for
comparing two network tree structures. The main task is to check
if a generated tree (the result of an analysis) matches a reference
tree, typically loaded from a file.
"""
from typing import Dict, Set, Any, List # Добавлен List для sorted()

import logging # Добавлено логирование
logger = logging.getLogger(__name__)

class TreeComparator:
    """
    Класс `TreeComparator` предоставляет статический метод для сравнения двух
    древовидных представлений сети.
    The `TreeComparator` class provides a static method for comparing two
    tree-like representations of a network.

    Этот класс не хранит состояние и используется как пространство имен для
    логики сравнения.
    This class does not store state and is used as a namespace for
    the comparison logic.
    """
    @staticmethod
    def compare(result: Dict[str, Any], reference: Dict[str, Any]) -> bool:
        """
        Сравнивает сгенерированное дерево сети (`result`) с эталонным деревом (`reference`).
        Compares a generated network tree (`result`) with a reference tree (`reference`).

        Метод выполняет следующие проверки:
        1. Сравнение множеств корневых узлов.
        2. Сравнение общего количества узлов (элементов) в деревьях.
        3. Поэлементное сравнение списков дочерних узлов для каждого узла,
           присутствующего в эталонном дереве.

        Результаты сравнения выводятся в консоль, включая информацию о совпадении
        корней, количества узлов и детальное расхождение в структуре связей, если таковые имеются.
        The method performs the following checks:
        1. Comparison of root node sets.
        2. Comparison of the total number of nodes (elements) in the trees.
        3. Element-wise comparison of child node lists for each node present
           in the reference tree.

        Comparison results are printed to the console, including information about
        matching roots, node counts, and detailed discrepancies in connection structure, if any.

        Параметры / Parameters:
            result (Dict[str, Any]): Словарь, представляющий сгенерированное дерево.
                                     Ожидаются ключи 'roots' (список ID), 'nodes' (список ID),
                                     и 'tree' (словарь Dict[str, Dict[str, List[str]]],
                                     где 'tree[node_id]['child']' - список дочерних ID).
                                     A dictionary representing the generated tree.
                                     Expected keys are 'roots' (list of IDs), 'nodes' (list of IDs),
                                     and 'tree' (a Dict[str, Dict[str, List[str]]],
                                     where 'tree[node_id]['child']' is a list of child IDs).
            reference (Dict[str, Any]): Словарь, представляющий эталонное дерево.
                                        Имеет ту же структуру, что и `result`.
                                        A dictionary representing the reference tree.
                                        It has the same structure as `result`.

        Возвращает / Returns:
            bool: True, если все проверяемые аспекты (`roots`, количество `nodes`,
                  и структура `tree` для всех узлов из эталона) совпадают, иначе False.
                  True if all checked aspects (`roots`, `nodes` count, and `tree`
                  structure for all nodes from the reference) match, False otherwise.
        """
        logger.info("Начало сравнения результатов с эталоном. / Starting comparison of results with reference.")
        print("\n=== СРАВНЕНИЕ РЕЗУЛЬТАТОВ / RESULTS COMPARISON ===")
        
        # Проверка наличия ключей, чтобы избежать KeyError
        if not all(k in result for k in ['roots', 'nodes', 'tree']) or \
           not all(k in reference for k in ['roots', 'nodes', 'tree']):
            logger.error("Структура result или reference не соответствует ожиданиям (отсутствуют ключи 'roots', 'nodes' или 'tree'). / Result or reference structure does not match expectations (missing 'roots', 'nodes', or 'tree' keys).")
            print("✗ Ошибка: Неверная структура входных данных для сравнения. / Error: Invalid input data structure for comparison.")
            return False

        # 1. Сравнение корневых узлов
        # Приводим к множествам для сравнения без учета порядка
        result_roots = set(result['roots'])
        reference_roots = set(reference['roots'])
        roots_match = result_roots == reference_roots
        print(f"Корневые узлы: {'✓ Совпадают' if roots_match else '✗ НЕ совпадают'} / Root nodes: {'✓ Match' if roots_match else '✗ DO NOT match'}")
        if not roots_match:
            print(f"  Ожидалось / Expected: {sorted(list(reference_roots))}")
            print(f"  Получено / Actual:   {sorted(list(result_roots))}")
            logger.warning(f"Расхождение в корневых узлах. Ожидалось: {reference_roots}, получено: {result_roots}")

        # 2. Сравнение количества узлов
        # 'nodes' - это список всех элементов в модели
        nodes_count_match = len(result['nodes']) == len(reference['nodes'])
        print(f"Количество узлов: {'✓ Совпадает' if nodes_count_match else '✗ НЕ совпадает'} ({len(result['nodes'])}/{len(reference['nodes'])}) / Node count: {'✓ Matches' if nodes_count_match else '✗ DOES NOT match'} ({len(result['nodes'])}/{len(reference['nodes'])})")
        if not nodes_count_match:
             logger.warning(f"Расхождение в количестве узлов. Ожидалось: {len(reference['nodes'])}, получено: {len(result['nodes'])}")
             # Можно также сравнить множества узлов, если порядок не важен, а состав важен:
             # result_nodes_set = set(result['nodes'])
             # reference_nodes_set = set(reference['nodes'])
             # if result_nodes_set != reference_nodes_set:
             #     logger.warning(f"Различия в наборах узлов: лишние в результате {result_nodes_set - reference_nodes_set}, отсутствуют в результате {reference_nodes_set - result_nodes_set}")


        # 3. Сравнение структуры дерева (дочерних связей)
        tree_matches_count = 0
        # Итерируемся по узлам эталонного дерева, так как оно является "истиной"
        reference_tree_nodes_count = len(reference['tree'])
        
        comparison_details: List[str] = []

        for node_id, ref_node_data in reference['tree'].items():
            ref_children_set = set(ref_node_data.get('child', []))

            res_node_data = result['tree'].get(node_id, {}) # Получаем данные узла из результата, или пустой словарь
            res_children_set = set(res_node_data.get('child', [])) # Получаем детей, или пустой список -> пустое множество

            if ref_children_set == res_children_set:
                tree_matches_count += 1
            else:
                detail_msg = (f"  ✗ Узел '{node_id}': расхождение в дочерних элементах. "
                              f"Ожидалось: {sorted(list(ref_children_set))}, "
                              f"Получено: {sorted(list(res_children_set))}. / "
                              f"Node '{node_id}': mismatch in children. "
                              f"Expected: {sorted(list(ref_children_set))}, "
                              f"Actual: {sorted(list(res_children_set))}.")
                print(detail_msg)
                comparison_details.append(detail_msg)
                logger.warning(f"Расхождение в дочерних элементах для узла '{node_id}'. Ожидалось: {ref_children_set}, получено: {res_children_set}")

        # Проверка на наличие лишних узлов в result['tree'], которых нет в reference['tree']
        extra_nodes_in_result = set(result['tree'].keys()) - set(reference['tree'].keys())
        if extra_nodes_in_result:
            for extra_node_id in extra_nodes_in_result:
                extra_node_children = result['tree'][extra_node_id].get('child', [])
                detail_msg = (f"  ✗ Лишний узел в результате: '{extra_node_id}' с дочерними элементами {sorted(extra_node_children)}. / "
                              f"Extra node in result: '{extra_node_id}' with children {sorted(extra_node_children)}.")
                print(detail_msg)
                comparison_details.append(detail_msg)
                logger.warning(f"Лишний узел в result['tree']: {extra_node_id}")
        
        # Считаем, что структура дерева совпадает, если все узлы из эталона имеют совпадающих детей
        # и в результате нет лишних узлов.
        tree_structure_match = (tree_matches_count == reference_tree_nodes_count) and not extra_nodes_in_result
        
        print(f"Структура дерева (дочерние связи): {tree_matches_count}/{reference_tree_nodes_count} узлов из эталона совпадают. "
              f"Лишних узлов в результате: {len(extra_nodes_in_result)}. / "
              f"Tree structure (child connections): {tree_matches_count}/{reference_tree_nodes_count} nodes from reference match. "
              f"Extra nodes in result: {len(extra_nodes_in_result)}.")

        overall_match = roots_match and nodes_count_match and tree_structure_match
        
        summary_message = '🎉 ТЕСТ ПРОЙДЕН / TEST PASSED' if overall_match else '🔧 ТРЕБУЕТСЯ ДОРАБОТКА / NEEDS IMPROVEMENT'
        print(f"\n{summary_message}")
        logger.info(f"Общий результат сравнения: {summary_message} / Overall comparison result: {summary_message}")
        if not overall_match:
            logger.info("Детали расхождений: / Discrepancy details:\n" + "\n".join(comparison_details))

        return overall_match