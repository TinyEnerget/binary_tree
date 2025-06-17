import sys
import os

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем необходимые классы
from model_processing.analyzer import NetworkAnalyzer
from model_processing.models import NetworkAnalysisResult
from tree_analyzer import MultiRootAnalyzer, VisualizeForest, TreeCreator
from graph_analyzer import GraphCreator, GraphVisualizer, UndirectedGraphAnalyzer

# Пути к файлам модели и для выходных данных
# TODO: Замените на актуальные пути или используйте относительные пути / переменные окружения
# model_path = 'C:\\Users\\Vlad Titov\\Desktop\\Work\\binary_tree\\model_processing\\available_modification\\converted.json'
# out_path = "output.json" # Это будет использоваться для сохранения NetworkAnalyzer промежуточного файла и графа

# Используем относительные пути для примера
project_root = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(project_root, 'model_processing', 'available_modification', 'converted.json')
# out_path теперь должен указывать на директорию, куда будут сохраняться файлы
# или полный путь к файлу, из которого директория будет извлечена.
# Для NetworkAnalyzer.analyze_network, output_path - это путь к файлу дерева.
# Для GraphCreator.save_json, out_path - это путь к файлу, из которого извлекается директория для output_graph.json.
# Сделаем out_path директорией для простоты.
results_dir = os.path.join(project_root, "analysis_results")
os.makedirs(results_dir, exist_ok=True)

# Путь для сохранения промежуточного дерева от NetworkAnalyzer
network_analyzer_output_tree_path = os.path.join(results_dir, "network_analysis_tree.json")
# Путь (директория) для GraphCreator, куда он сохранит output_graph.json
graph_creator_output_dir = Path(results_dir)


# 1. Выполняем анализ сети ОДИН РАЗ
print(f"Анализ модели из: {model_path}")
try:
    analysis_result: NetworkAnalysisResult = NetworkAnalyzer.analyze_network(model_path, network_analyzer_output_tree_path)
    print(f"Анализ сети завершен. Промежуточное дерево сохранено в: {network_analyzer_output_tree_path}")
except FileNotFoundError:
    print(f"ОШИБКА: Файл модели не найден по пути: {model_path}")
    sys.exit(1)
except Exception as e:
    print(f"ОШИБКА: Произошла ошибка во время анализа сети: {e}")
    sys.exit(1)

# 2. Создаем дерево Node-объектов, передавая результат анализа
# TreeCreator теперь может не нуждаться в model_path и out_path, если ему передан analysis_result
# out_path для TreeCreator был для NetworkAnalyzer, который теперь вызывается отдельно.
print("\nСоздание структуры дерева Node...")
tree_creator = TreeCreator(analysis_result=analysis_result) # model_path и out_path не обязательны
tree_nodes_list = tree_creator.create_tree() # create_tree() теперь использует self.result
print(f"Структура дерева Node создана. Количество корневых узлов: {len(tree_nodes_list)}")

# 3. Создаем граф, передавая результат анализа
# GraphCreator все еще нужен out_path для сохранения своего output_graph.json
print("\nСоздание структуры графа...")
graph_creator = GraphCreator(out_path=str(graph_creator_output_dir), analysis_result=analysis_result) # model_path не обязателен
# graph_creator.model_to_tree() # Этот вызов больше не нужен, так как result передан
graph_adj_list = graph_creator.create_graph()
print(f"Структура графа создана и сохранена в директории: {graph_creator_output_dir}")

# Далее используется tree_nodes_list (список объектов Node) и graph_adj_list (словарь смежности)
# Убедимся, что MultiRootAnalyzer ожидает список Node, а UndirectedGraphAnalyzer - словарь смежности.

# Анализ дерева (списка Node)
print("\nАнализ дерева (MultiRootAnalyzer)...")
analyzer_tree = MultiRootAnalyzer(tree_nodes_list) # MultiRootAnalyzer ожидает список корней Node
stats_tree = analyzer_tree.get_forest_statistics()
# forest_analysis = analyzer_tree.analyze_forest() # analyze_forest вызывается в __init__ или get_forest_statistics
connections_tree = analyzer_tree.find_connections_between_roots()
# Вывод статистики (пример)
if stats_tree['trees_info']:
    print(f"  Статистика по первому дереву: Глубина: {stats_tree['trees_info'][0]['depth']}, Количество узлов: {stats_tree['trees_info'][0]['nodes_count']}")
else:
    print("  Информация о деревьях отсутствует в статистике.")

# Анализ графа (словаря смежности)
print("\nАнализ графа (UndirectedGraphAnalyzer)...")
analyzer_graph = UndirectedGraphAnalyzer(graph_adj_list) # UndirectedGraphAnalyzer ожидает словарь смежности
stats_graph = analyzer_graph.graph_statistics()
print(f"  Статистика по графу: Всего узлов: {stats_graph['total_nodes']}, Всего ребер: {stats_graph['total_edges']}")

# Пример поиска путей (если узлы существуют в созданных структурах)
# Используем ID из analysis_result.nodes, если они там есть, или примеры
if analysis_result.nodes and len(analysis_result.nodes) >= 2:
    # Для примера возьмем первые два узла из общего списка узлов модели,
    # предполагая, что они могут быть в дереве/графе.
    # В реальном сценарии ID узлов для поиска путей должны быть известны заранее или получены осмысленно.
    # node_A = analysis_result.nodes[0]
    # node_B = analysis_result.nodes[1]
    # Захардкоженные ID для примера, если они существуют в вашей модели
    node_A = 'ebe34ba8-6a85-416d-884e-f81ac31e3d72'
    node_B = 'c287dc60-661f-4e21-87c7-2b6366b25f8f'

    # Проверка наличия узлов перед поиском путей
    # Для tree_nodes_list (список Node объектов), нужно найти узлы по ID
    # Для graph_adj_list (словарь), ключи - это ID узлов

    # Проверка для дерева:
    # Это упрощенная проверка; в реальности нужно обойти tree_nodes_list и проверить analyzer_tree.roots
    # или все узлы в деревьях на наличие node_A и node_B.
    # Здесь мы предполагаем, что если они есть в исходной модели, то анализаторы их обработают.

    print(f"\nПоиск путей в дереве между '{node_A}' и '{node_B}':")
    analyzer_tree.print_paths_between_nodes(node_A, node_B)
    # analyzer_tree.print_paths_between_nodes(node_B, node_A) # Для дерева пути обычно направленные от корня

    if node_A in graph_adj_list and node_B in graph_adj_list:
        print(f"\nПоиск путей в графе между '{node_A}' и '{node_B}':")
        analyzer_graph.print_all_paths(node_A, node_B)
        # analyzer_graph.print_all_paths(node_B, node_A) # Для неориентированного графа пути симметричны
    else:
        print(f"\nУзлы '{node_A}' или '{node_B}' отсутствуют в созданном графе для поиска путей.")

else:
    print("\nНедостаточно узлов в модели для примера поиска путей.")


# Визуализация дерева
print("\nВизуализация леса (дерева)...")
visualizer_tree = VisualizeForest(analyzer_tree) # VisualizeForest ожидает MultiRootAnalyzer
visualizer_tree.visualize_forest_connections()

# Визуализация графа
print("\nВизуализация графа...")
visualizer_graph = GraphVisualizer(graph_adj_list) # GraphVisualizer ожидает словарь смежности
visualizer_graph.draw_graph()

print("\nЗавершено.")
forest_analysis = analyzer_tree.analyze_forest()
connections_tree = analyzer_tree.find_connections_between_roots()
print(stats_tree)
print(f"  Глубина дерева: {stats_tree['trees_info'][0]['depth']}")
print(f"  Фактическое количество узлов: {stats_tree['trees_info'][0]['nodes_count']}")

analyzer_graph = UndirectedGraphAnalyzer(graph)
stats_graph = analyzer_graph.graph_statistics()
print(stats_graph)

node_A = 'ebe34ba8-6a85-416d-884e-f81ac31e3d72'
node_B = 'c287dc60-661f-4e21-87c7-2b6366b25f8f'

print(f"  Количество путей от {node_A} до {node_B}:")
analyzer_tree.print_paths_between_nodes(node_A, node_B)
analyzer_tree.print_paths_between_nodes(node_B, node_A)

print(f"  Количество путей от {node_A} до {node_B}:")
analyzer_graph.print_all_paths(node_A, node_B)
analyzer_graph.print_all_paths(node_B, node_A)

visualizer = VisualizeForest(analyzer_tree)
visualizer.visualize_forest_connections()

visualizer = GraphVisualizer(graph)
visualizer.draw_graph()