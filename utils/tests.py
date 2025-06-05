import time
import random
import string
import psutil
import gc
from memory_profiler import profile

import sys
import os

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tree_analyzer import Node, MultiRootAnalyzer
import numpy as np

class TreeGenerator:
    """Генератор больших деревьев для тестирования производительности"""
    
    def __init__(self, seed=42):
        random.seed(seed)
        np.random.seed(seed)
    
    def generate_random_value(self, length=3):
        """Генерирует случайное значение для узла"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    def create_balanced_tree(self, depth, branching_factor=3):
        """Создает сбалансированное дерево заданной глубины"""
        root = Node(self.generate_random_value())
        
        def build_level(node, current_depth):
            if current_depth >= depth:
                return
            
            for _ in range(branching_factor):
                child = Node(self.generate_random_value())
                node.add_child(child)
                build_level(child, current_depth + 1)
        
        build_level(root, 0)
        return root
    
    def create_wide_tree(self, width, depth=3):
        """Создает широкое дерево с большим количеством детей на каждом уровне"""
        root = Node(self.generate_random_value())
        
        def build_wide_level(node, current_depth, current_width):
            if current_depth >= depth:
                return
            
            for _ in range(current_width):
                child = Node(self.generate_random_value())
                node.add_child(child)
                # Уменьшаем ширину на следующем уровне
                build_wide_level(child, current_depth + 1, max(1, current_width // 2))
        
        build_wide_level(root, 0, width)
        return root
    
    def create_random_tree(self, num_nodes):
        """Создает случайное дерево с заданным количеством узлов"""
        if num_nodes <= 0:
            return None
        
        root = Node(self.generate_random_value())
        nodes = [root]
        created_nodes = 1
        
        while created_nodes < num_nodes:
            # Выбираем случайный существующий узел как родителя
            parent = random.choice(nodes)
            
            # Создаем от 1 до 5 детей
            children_count = min(random.randint(1, 5), num_nodes - created_nodes)
            
            for _ in range(children_count):
                child = Node(self.generate_random_value())
                parent.add_child(child)
                nodes.append(child)
                created_nodes += 1
        
        return root
    
    def create_cyclic_tree(self, num_nodes, cycle_probability=0.1):
        """Создает дерево с циклами для тестирования защиты от циклов"""
        if num_nodes <= 0:
            return None
        
        root = Node(self.generate_random_value())
        all_nodes = [root]
        created_nodes = 1
        
        while created_nodes < num_nodes:
            parent = random.choice(all_nodes)
            
            # Создаем обычного ребенка
            if random.random() > cycle_probability or created_nodes == 1:
                child = Node(self.generate_random_value())
                parent.add_child(child)
                all_nodes.append(child)
                created_nodes += 1
            else:
                # Создаем цикл, добавляя существующий узел как ребенка
                if len(all_nodes) > 1:
                    cycle_node = random.choice(all_nodes[:-1])  # Исключаем последний узел
                    parent.add_child(cycle_node)
        
        return root
    
    def create_shared_nodes_forest(self, num_trees, nodes_per_tree, shared_ratio=0.3):
        """Создает лес с общими узлами между деревьями"""
        # Создаем пул общих узлов
        shared_nodes_count = int(nodes_per_tree * shared_ratio)
        shared_nodes = [Node(f"SHARED_{i}") for i in range(shared_nodes_count)]
        
        trees = []
        
        for tree_idx in range(num_trees):
            root = Node(f"ROOT_{tree_idx}")
            tree_nodes = [root]
            
            # Добавляем уникальные узлы
            unique_nodes_count = nodes_per_tree - shared_nodes_count
            for i in range(unique_nodes_count):
                node = Node(f"T{tree_idx}_N{i}")
                tree_nodes.append(node)
            
            # Добавляем некоторые общие узлы
            num_shared_to_add = random.randint(1, shared_nodes_count)
            selected_shared = random.sample(shared_nodes, num_shared_to_add)
            tree_nodes.extend(selected_shared)
            
            # Случайно соединяем узлы
            for node in tree_nodes[1:]:  # Исключаем корень
                parent = random.choice(tree_nodes[:tree_nodes.index(node)])
                parent.add_child(node)
            
            trees.append(root)
        
        return trees

class PerformanceTester:
    """Класс для тестирования производительности анализатора"""
    
    def __init__(self):
        self.generator = TreeGenerator()
        self.results = []
    
    def measure_memory_usage(self):
        """Измеряет использование памяти"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def test_single_tree_performance(self, tree_sizes):
        """Тестирует производительность на одиночных деревьях разного размера"""
        print("=== Тестирование производительности одиночных деревьев ===")
        
        for size in tree_sizes:
            print(f"\nТестирование дерева с {size} узлами:")
            
            # Создаем дерево
            start_time = time.time()
            tree = self.generator.create_random_tree(size)
            creation_time = time.time() - start_time
            
            memory_before = self.measure_memory_usage()
            
            # Анализируем дерево
            analyzer = MultiRootAnalyzer([tree])
            
            start_time = time.time()
            stats = analyzer.get_forest_statistics()
            analysis_time = time.time() - start_time
            
            memory_after = self.measure_memory_usage()
            memory_used = memory_after - memory_before
            
            print(f"  Время создания: {creation_time:.4f} сек")
            print(f"  Время анализа: {analysis_time:.4f} сек")
            print(f"  Использование памяти: {memory_used:.2f} MB")
            print(f"  Глубина дерева: {stats['trees_info'][0]['depth']}")
            print(f"  Фактическое количество узлов: {stats['trees_info'][0]['nodes_count']}")
            
            # Очищаем память
            del tree, analyzer, stats
            gc.collect()
    
    def test_forest_performance(self, forest_configs):
        """Тестирует производительность на лесах деревьев"""
        print("\n=== Тестирование производительности лесов ===")
        
        for config in forest_configs:
            num_trees, nodes_per_tree = config
            print(f"\nТестирование леса: {num_trees} деревьев по {nodes_per_tree} узлов:")
            
            # Создаем лес
            start_time = time.time()
            forest = self.generator.create_shared_nodes_forest(num_trees, nodes_per_tree)
            creation_time = time.time() - start_time
            
            memory_before = self.measure_memory_usage()
            
            # Анализируем лес
            analyzer = MultiRootAnalyzer(forest)
            
            start_time = time.time()
            forest_analysis = analyzer.analyze_forest()
            analysis_time = time.time() - start_time
            
            start_time = time.time()
            connections = analyzer.find_connections_between_roots()
            connections_time = time.time() - start_time
            
            start_time = time.time()
            stats = analyzer.get_forest_statistics()
            stats_time = time.time() - start_time
            
            memory_after = self.measure_memory_usage()
            memory_used = memory_after - memory_before
            
            total_nodes = sum(len(nodes) for nodes in forest_analysis.values())
            shared_nodes_count = len(analyzer.shared_nodes)
            
            print(f"  Время создания леса: {creation_time:.4f} сек")
            print(f"  Время анализа леса: {analysis_time:.4f} сек")
            print(f"  Время поиска связей: {connections_time:.4f} сек")
            print(f"  Время сбора статистики: {stats_time:.4f} сек")
            print(f"  Общее время анализа: {analysis_time + connections_time + stats_time:.4f} сек")
            print(f"  Использование памяти: {memory_used:.2f} MB")
            print(f"  Общее количество уникальных узлов: {total_nodes}")
            print(f"  Количество общих узлов: {shared_nodes_count}")
            print(f"  Количество связей между деревьями: {len(connections)}")
            
            # Очищаем память
            del forest, analyzer, forest_analysis, connections, stats
            gc.collect()
    
    def test_cyclic_trees_performance(self, sizes):
        """Тестирует производительность на деревьях с циклами"""
        print("\n=== Тестирование деревьев с циклами ===")
        
        for size in sizes:
            print(f"\nТестирование циклического дерева с {size} узлами:")
            
            # Создаем дерево с циклами
            start_time = time.time()
            cyclic_tree = self.generator.create_cyclic_tree(size, cycle_probability=0.2)
            creation_time = time.time() - start_time
            
            memory_before = self.measure_memory_usage()
            
            # Анализируем дерево
            analyzer = MultiRootAnalyzer([cyclic_tree])
            
            start_time = time.time()
            stats = analyzer.get_forest_statistics()
            paths = analyzer.find_all_paths_to_node(cyclic_tree.value)
            analysis_time = time.time() - start_time
            
            memory_after = self.measure_memory_usage()
            memory_used = memory_after - memory_before
            
            print(f"  Время создания: {creation_time:.4f} сек")
            print(f"  Время анализа: {analysis_time:.4f} сек")
            print(f"  Использование памяти: {memory_used:.2f} MB")
            print(f"  Глубина дерева: {stats['trees_info'][0]['depth']}")
            print(f"  Количество узлов: {stats['trees_info'][0]['nodes_count']}")
            print(f"  Найдено путей до корня: {len(paths.get(f'Tree_0_{cyclic_tree.value}', []))}")
            
            # Очищаем память
            del cyclic_tree, analyzer, stats, paths
            gc.collect()
    
    def run_comprehensive_test(self):
        """Запускает комплексное тестирование производительности"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ ПРОИЗВОДИТЕЛЬНОСТИ 🚀")
        print("=" * 70)
        
        # Тест 1: Одиночные деревья разного размера
        single_tree_sizes = [100, 500, 1000, 5000, 10000]
        self.test_single_tree_performance(single_tree_sizes)
        
        # Тест 2: Леса деревьев
        forest_configs = [
            (5, 100),    # 5 деревьев по 100 узлов
            (10, 200),   # 10 деревьев по 200 узлов
            (20, 500),   # 20 деревьев по 500 узлов
            #(50, 100),   # 50 деревьев по 100 узлов
        ]
        self.test_forest_performance(forest_configs)
              
        # Тест 4: Деревья с циклами
        cyclic_sizes = [100, 200, 300, 500]
        self.test_cyclic_trees_performance(cyclic_sizes)
        
        print("\n" + "=" * 70)
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО 🎉")


def stress_test_extreme_cases():
    """Экстремальное стресс-тестирование"""
    print("\n🔥 ЭКСТРЕМАЛЬНОЕ СТРЕСС-ТЕСТИРОВАНИЕ 🔥")
    print("=" * 50)
    
    generator = TreeGenerator()
    
    # Тест 1: Очень глубокое дерево
    print("\n1. Тестирование очень глубокого дерева (глубина 100):")
    start_time = time.time()
    deep_tree = generator.create_balanced_tree(depth=10, branching_factor=5)
    creation_time = time.time() - start_time
    
    analyzer = MultiRootAnalyzer([deep_tree])
    start_time = time.time()
    stats = analyzer.get_forest_statistics()
    analysis_time = time.time() - start_time
    
    print(f"  Время создания: {creation_time:.4f} сек")
    print(f"  Время анализа: {analysis_time:.4f} сек")
    print(f"  Глубина: {stats['trees_info'][0]['depth']}")
    print(f"  Узлов: {stats['trees_info'][0]['nodes_count']}")
    
    # Тест 2: Очень широкое дерево
    print("\n2. Тестирование очень широкого дерева (500 детей у корня):")
    start_time = time.time()
    wide_tree = generator.create_wide_tree(width=500, depth=2)
    creation_time = time.time() - start_time
    
    analyzer = MultiRootAnalyzer([wide_tree])
    start_time = time.time()
    stats = analyzer.get_forest_statistics()
    analysis_time = time.time() - start_time
    
    print(f"  Время создания: {creation_time:.4f} сек")
    print(f"  Время анализа: {analysis_time:.4f} сек")
    print(f"  Глубина: {stats['trees_info'][0]['depth']}")
    print(f"  Узлов: {stats['trees_info'][0]['nodes_count']}")
    
    # Тест 3: Огромный лес
    print("\n3. Тестирование огромного леса (100 деревьев по 1000 узлов):")
    start_time = time.time()
    huge_forest = generator.create_shared_nodes_forest(100, 1000, shared_ratio=0.5)
    creation_time = time.time() - start_time
    
    analyzer = MultiRootAnalyzer(huge_forest)
    start_time = time.time()
    forest_analysis = analyzer.analyze_forest()
    connections = analyzer.find_connections_between_roots()
    analysis_time = time.time() - start_time
    
    print(f"  Время создания: {creation_time:.4f} сек")
    print(f"  Время анализа: {analysis_time:.4f} сек")
    print(f"  Деревьев: {len(huge_forest)}")
    print(f"  Уникальных узлов: {len(forest_analysis)}")
    print(f"  Общих узлов: {len(analyzer.shared_nodes)}")
    print(f"  Связей между деревьями: {len(connections)}")


@profile
def memory_profiling_test():
    """Тест с профилированием памяти"""
    print("\n📊 ПРОФИЛИРОВАНИЕ ПАМЯТИ 📊")
    
    generator = TreeGenerator()
    
    # Создаем большой лес
    forest = generator.create_shared_nodes_forest(10, 100, shared_ratio=0.3)
    
    # Анализируем
    analyzer = MultiRootAnalyzer(forest)
    forest_analysis = analyzer.analyze_forest()
    connections = analyzer.find_connections_between_roots()
    stats = analyzer.get_forest_statistics()
    
    # Поиск путей
    if forest:
        paths = analyzer.find_all_paths_to_node(forest[0].value)
        shortest = analyzer.find_shortest_path_to_node(forest[0].value)
    
    print("Профилирование памяти завершено")


if __name__ == '__main__':
    # Основное тестирование
    tester = PerformanceTester()
    tester.run_comprehensive_test()
    
    # Экстремальное тестирование
    stress_test_extreme_cases()
    
    # Профилирование памяти
    try:
        memory_profiling_test()
    except Exception as e:
        print(f"Профилирование памяти недоступно: {e}")
    
    # Демонстрация работы с конкретным большим деревом
    print("\n" + "=" * 70)
    print("🌳 ДЕМОНСТРАЦИЯ РАБОТЫ С БОЛЬШИМ ДЕРЕВОМ 🌳")
    print("=" * 70)
    
    generator = TreeGenerator()
    
    # Создаем большое дерево с циклами
    print("Создание большого дерева с 5000 узлами и циклами...")
    start_time = time.time()
    big_tree = generator.create_cyclic_tree(5000, cycle_probability=0.15)
    creation_time = time.time() - start_time
    print(f"Дерево создано за {creation_time:.4f} секунд")
    
    # Создаем лес из нескольких больших деревьев
    print("\nСоздание леса из 10 больших деревьев...")
    start_time = time.time()
    big_forest = []
    for i in range(10):
        tree = generator.create_random_tree(1000)
        big_forest.append(tree)
    creation_time = time.time() - start_time
    print(f"Лес создан за {creation_time:.4f} секунд")
    
    # Анализируем большой лес
    print("\nАнализ большого леса...")
    analyzer = MultiRootAnalyzer(big_forest)
    
    start_time = time.time()
    analyzer.print_forest_statistics()
    print(f"\nСтатистика получена за {time.time() - start_time:.4f} секунд")
    
    start_time = time.time()
    analyzer.print_shared_nodes()
    print(f"Общие узлы найдены за {time.time() - start_time:.4f} секунд")
    
    start_time = time.time()
    analyzer.print_connections_between_roots()
    print(f"Связи найдены за {time.time() - start_time:.4f} секунд")
    
    # Поиск путей в большом дереве
    if big_forest:
        target_node = None
        # Найдем случайный узел для поиска
        for node in big_forest[0].children if big_forest[0].children else []:
            if node.children:
                target_node = node.children[0].value
                break
        
        if target_node:
            print(f"\nПоиск путей до узла '{target_node}'...")
            start_time = time.time()
            analyzer.print_shortest_path_to_node(target_node)
            print(f"Кратчайший путь найден за {time.time() - start_time:.4f} секунд")
    
    print("\n🎯 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА 🎯")
