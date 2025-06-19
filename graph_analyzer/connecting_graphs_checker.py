import concurrent.futures
from typing import Dict, Set, Tuple, Optional, List
from collections import defaultdict
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class UndirectedGraphConnectingAnalyzer:
    """Класс для анализа неориентированного графа и связей с системными узлами."""
    
    def __init__(self, graph: Dict[str, List[str]], systems: List[str], max_workers: Optional[int] = None):
        """
        Инициализация анализатора графа.
        
        Args:
            graph: Словарь, представляющий граф (ключ - узел, значение - список соседей).
            systems: Список системных узлов.
            max_workers: Максимальное количество рабочих потоков (по умолчанию 8).
        
        Raises:
            ValueError: Если граф или системные узлы некорректны.
        """
        if not graph or not isinstance(graph, dict):
            raise ValueError("Граф должен быть непустым словарем.")
        if not systems or not isinstance(systems, list):
            raise ValueError("Список системных узлов должен быть непустым.")
        
        # Преобразование списков соседей в множества
        self.graph = {node: set(neighbors) for node, neighbors in graph.items()}
        self.systems = set(systems)
        self.max_workers = max_workers or 8
        self.components: List[Set[str]] = []
        self.system_components: List[Set[str]] = []
        self.orphan_components: List[Set[str]] = []
        self._paths_cache: Dict[Tuple[str, str], List[str]] = {}
        
        # Проверка корректности графа и системных узлов
        self._validate_graph()

    def _validate_graph(self) -> None:
        """Проверяет корректность графа и системных узлов."""
        for node in self.graph:
            for neighbor in self.graph[node]:
                if neighbor not in self.graph:
                    raise ValueError(f"Узел {neighbor} отсутствует в графе.")
                if node not in self.graph[neighbor]:
                    raise ValueError(f"Граф не является неориентированным: связь {node} -> {neighbor} не симметрична.")
        for system_node in self.systems:
            if system_node not in self.graph:
                raise ValueError(f"Системный узел {system_node} отсутствует в графе.")

    def find_all_components(self) -> List[Set[str]]:
        """Находит все связанные компоненты графа с помощью DFS."""
        visited = set()
        components = []
        for node in self.graph:
            if node not in visited:
                component = set()
                self._dfs(node, component, visited)
                components.append(component)
        logger.info("Найдено %d связанных компонент", len(components))
        return components

    def _dfs(self, node: str, component: Set[str], visited: Set[str]) -> None:
        """Вспомогательный метод для DFS."""
        component.add(node)
        visited.add(node)
        for neighbor in self.graph[node]:
            if neighbor not in visited:
                self._dfs(neighbor, component, visited)

    def classify_components(self, components: List[Set[str]]) -> Tuple[List[Set[str]], List[Set[str]]]:
        """Классифицирует компоненты на системные и орфанные."""
        system_components = []
        orphan_components = []
        for comp in components:
            if comp & self.systems:
                system_components.append(comp)
            else:
                orphan_components.append(comp)
        logger.info("Классифицировано %d системных и %d орфанных компонент", 
                    len(system_components), len(orphan_components))
        return system_components, orphan_components

    def find_connecting_elements(self) -> Dict[Tuple[str, str], List[List[str]]]:
        """Находит системные узлы, соединённые через общие элементы, и пути между ними."""
        logger.info("Поиск соединяющих элементов между системными узлами...")
        system_pairs_paths = {}
        
        def bfs(start: str, end: str) -> List[List[str]]:
            """Поиск всех кратчайших путей между двумя узлами с помощью BFS."""
            if start == end:
                return [[start]]
            queue = [(start, [start])]
            visited = {start}
            paths = []
            min_length = float('inf')
            
            while queue:
                node, path = queue.pop(0)
                if len(path) > min_length:
                    break
                for neighbor in self.graph[node]:
                    if neighbor not in visited:
                        new_path = path + [neighbor]
                        if neighbor == end:
                            paths.append(new_path)
                            min_length = len(new_path)
                        else:
                            queue.append((neighbor, new_path))
                            visited.add(neighbor)
            return paths

        system_nodes = sorted(list(self.systems))
        for i in range(len(system_nodes)):
            for j in range(i + 1, len(system_nodes)):
                start, end = system_nodes[i], system_nodes[j]
                if any(start in comp and end in comp for comp in self.system_components):
                    paths = bfs(start, end)
                    if paths:
                        system_pairs_paths[(start, end)] = paths
        logger.info("Найдено %d пар системных узлов с путями", len(system_pairs_paths))
        return system_pairs_paths

    def find_unconnected_elements(self) -> Set[str]:
        """Находит узлы, не связанные с системными узлами."""
        system_nodes = set()
        for comp in self.system_components:
            system_nodes.update(comp)
        unconnected = set(self.graph.keys()) - system_nodes
        logger.info("Найдено %d непривязанных узлов", len(unconnected))
        return unconnected

    def analyze(self) -> None:
        """Выполняет полный анализ графа."""
        logger.info("Начало анализа графа...")
        self.components = self.find_all_components()
        self.system_components, self.orphan_components = self.classify_components(self.components)
        self.print_components()
        self.print_system_components()
        self.print_connecting_elements()
        self.print_unconnected_elements()
        logger.info("Анализ графа завершён")

    def print_components(self) -> None:
        """Выводит все связанные компоненты."""
        logger.info("Вывод связанных компонент...")
        for i, comp in enumerate(self.components, 1):
            logger.info(f"Компонента {i}: {comp}")
        logger.info("Вывод компонент завершён")

    def print_system_components(self) -> None:
        """Выводит системные компоненты."""
        logger.info("Вывод системных компонент...")
        for i, comp in enumerate(self.system_components, 1):
            logger.info(f"Системная компонента {i}: {comp}")
        logger.info("Вывод системных компонент завершён")

    def print_connecting_elements(self) -> None:
        """Выводит системные узлы с общими элементами и пути между ними."""
        logger.info("Вывод соединяющих элементов...")
        paths = self.find_connecting_elements()
        if not paths:
            logger.info("Нет системных узлов с общими элементами.")
        for (start, end), path_list in paths.items():
            logger.info(f"Системные узлы {start} и {end} соединены через пути:")
            for path in path_list:
                logger.info(f"  Путь: {' -> '.join(path)}")
        logger.info("Вывод соединяющих элементов завершён")

    def print_unconnected_elements(self) -> None:
        """Выводит непривязанные узлы."""
        logger.info("Вывод непривязанных узлов...")
        unconnected = self.find_unconnected_elements()
        if not unconnected:
            logger.info("Нет непривязанных узлов.")
        else:
            logger.info(f"Непривязанные узлы: {unconnected}")
        logger.info("Вывод непривязанных узлов завершён")




