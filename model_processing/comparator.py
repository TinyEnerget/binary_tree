from typing import Dict, Set, Any


class TreeComparator:
    @staticmethod
    def compare(result: Dict[str, Any], reference: Dict[str, Any]) -> bool:
        """Сравнивает дерево сети с эталонным."""
        print("=== СРАВНЕНИЕ РЕЗУЛЬТАТОВ ===")
        
        roots_match = set(result['roots']) == set(reference['roots'])
        print(f"✓ Корни совпадают: {roots_match}")
        
        nodes_match = len(result['nodes']) == len(reference['nodes'])
        print(f"✓ Количество узлов: {nodes_match} ({len(result['nodes'])}/{len(reference['nodes'])})")
        
        tree_matches = 0
        tree_total = len(reference['tree'])
        
        for node_id, node_data in reference['tree'].items():
            expected = set(node_data['child'])
            actual = set(result['tree'].get(node_id, {}).get('child', []))
            if expected == actual:
                tree_matches += 1
            else:
                print(f"✗ {node_id}: ожидается {sorted(expected)}, получено {sorted(actual)}")
        
        tree_structure_match = tree_matches == tree_total
        print(f"✓ Структура дерева: {tree_matches}/{tree_total} узлов совпадает")
        overall_match = roots_match and nodes_match and tree_structure_match
        print(f"\n{'🎉 ТЕСТ ПРОЙДЕН' if overall_match else '🔧 ТРЕБУЕТСЯ ДОРАБОТКА'}")
        return overall_match