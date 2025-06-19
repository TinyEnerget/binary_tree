import concurrent.futures
from typing import Dict, Set, List, Optional

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UndirectedGraphConnectingAnalyzer:
    def __init__(self, graph: Dict[str, Set[str]], systems:List[str], max_workers: Optional[int] = None):
        self.graph = graph
        self.systems = set(systems)
        self.max_workers = max_workers or 8
        self.components = []
        self._paths_cache = {}

    def find_all_components(self) -> List[Set[str]]:
        visited = set()
        components = []
        for node in self.graph:
            if node not in visited:
                component = set()
                self.dfs(node, component, visited)
                components.append(component)
        logger.info("Finding all components")
        return components

    def dfs(self, node: str, component: Set[str], visited: Set[str]) -> None:
        component.add(node)
        visited.add(node)
        for neighbor in self.graph[node]:
            if neighbor not in visited:
                self.dfs(neighbor, component, visited)

    def classify_components(self,components: list[set[str]], system_nodes: set[str]) -> tuple[list[set[str]], list[set[str]]]:
        system_components = []
        orphan_components = []

        for comp in components:
            if comp & system_nodes:
                system_components.append(comp)
            else:
                orphan_components.append(comp)
        logger.info("Classifying components by system nodes ")
        return system_components, orphan_components
    
    def analyze(self) -> None:
        logger.info("Analyzing graph...")
        self.components = self.find_all_components()
        self.system_components, self.orphan_components = self.classify_components(self.components, self.systems)
        logger.info("Found %d components", len(self.components))
        logger.info("Found %d system components", len(self.system_components))
        logger.info("Found %d orphan components", len(self.orphan_components))
        self.print_components()
        self.print_system_components()
        logger.info("Analyzing graph done")

    def print_components(self) -> None:
        logger.info("Printing components...")
        for i, comp in enumerate(self.components):
            logger.info(f"Component {i+1}: {comp}")
        logger.info("Printing components done")
    
    def print_system_components(self) -> None:
        logger.info("Printing system components...")
        for i, comp in enumerate(self.system_components):
            logger.info(f"System component {i+1}: {comp}")
        logger.info("Printing system components done")


