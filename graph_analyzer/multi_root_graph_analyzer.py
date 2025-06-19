import concurrent.futures
from collections import defaultdict, deque
from typing import Dict, Set, List, Optional


class UndirectedGraphAnalyzer:
    def __init__(self, graph: Dict[str, Set[str]], max_workers: Optional[int] = None):
        self.graph = graph
        self.max_workers = max_workers or 8
        self.components = []
        self._paths_cache = {}

    def find_connected_components(self):
        visited = set()
        components = []

        for node in self.graph:
            if node not in visited:
                component = set()
                queue = deque([node])
                while queue:
                    current = queue.popleft()
                    if current not in visited:
                        visited.add(current)
                        component.add(current)
                        queue.extend(self.graph[current] - visited)
                components.append(component)

        self.components = components
        return components

    def find_all_paths(self, start: str, end: str) -> List[List[str]]:
        paths = []
        stack = [(start, [start], set([start]))]
        while stack:
            current, path, visited = stack.pop()
            if current == end:
                paths.append(path)
                continue
            for neighbor in self.graph.get(current, []):
                if neighbor not in visited:
                    stack.append((neighbor, path + [neighbor], visited | {neighbor}))

        return paths

    def find_shortest_path(self, start: str, end: str) -> Optional[List[str]]:
        visited = set()
        queue = deque([(start, [start])])

        while queue:
            current, path = queue.popleft()
            if current == end:
                return path
            if current in visited:
                continue
            visited.add(current)
            for neighbor in self.graph.get(current, []):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        return None
    
    def find_longest_path(self, start: str, end: str) -> List[str]:
        """Ищет самый длинный простой путь между start и end. Возвращает список узлов на этом пути."""
        max_path: List[str] = []

        def dfs(current: str, visited: Set[str], path: List[str]):
            nonlocal max_path
            if current == end:
                if len(path) > len(max_path):
                    max_path = path.copy()
                return

            for neighbor in self.graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(neighbor, visited, path)
                    path.pop()
                    visited.remove(neighbor)

        dfs(start, {start}, [start])
        return max_path
    
    def find_all_paths_parallel(self, start: str, end: str) -> List[List[str]]:
        paths = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.find_all_paths, start, end) for _ in range(self.max_workers)]
            for future in concurrent.futures.as_completed(futures):
                paths.extend(future.result())

        return paths

    def graph_statistics(self):
        num_nodes = len(self.graph)
        num_edges = sum(len(neighbors) for neighbors in self.graph.values()) // 2
        degrees = {node: len(neighbors) for node, neighbors in self.graph.items()}
        components = self.find_connected_components()

        return {
            "total_nodes": num_nodes,
            "total_edges": num_edges,
            "degree_distribution": degrees,
            "connected_components": [list(comp) for comp in components],
            "num_components": len(components)
        }

    def print_graph_statistics(self):
        stats = self.graph_statistics()
        print(f"Total Nodes: {stats['total_nodes']}")
        print(f"Total Edges: {stats['total_edges']}")
        print(f"Connected Components ({stats['num_components']}):")
        for idx, comp in enumerate(stats['connected_components'], 1):
            print(f"  Component {idx}: {comp}")
        print("Degree Distribution:")
        for node, degree in stats['degree_distribution'].items():
            print(f"  {node}: {degree}")

    def print_all_paths(self, start: str, end: str):
        paths = self.find_all_paths(start, end)
        print(f"All paths from {start} to {end}:")
        if not paths:
            print("  No paths found.")
        for i, path in enumerate(paths, 1):
            print(f"  Path {i}: {' -> '.join(path)}")

        print(f"Total paths: {len(paths)}")

    def print_shortest_path(self, start: str, end: str):
        path = self.find_shortest_path(start, end)
        print(f"Shortest path from {start} to {end}:")
        if path:
            print(f"  {' -> '.join(path)} (Length: {len(path)})")
        else:
            print("  No path found.")

    def print_longest_path(self, start: str, end: str):
        path = self.find_longest_path(start, end)
        print(f"Longest path from {start} to {end}:")
        if path:
            print(f"  {' -> '.join(path)} (Length: {len(path)})")
        else:
            print("  No path found.")
    
    def print_all_paths_parallel(self, start: str, end: str):
        paths = self.find_all_paths_parallel(start, end)
        print(f"All paths from {start} to {end}:")
        if not paths:
            print("  No paths found.")
        for i, path in enumerate(paths, 1):
            print(f"  Path {i}: {' -> '.join(path)}")
            print(f"  Path {i} length: {len(path)}")

    def print_all_connected_components(self):
        components = self.find_connected_components()
        print(f"Connected components: {components}")

if __name__ == "__main__":
    graph = {
        "A": {"B", "C"},
        "B": {"A", "D", "E"},
        "C": {"A", "F"},
        "D": {"B"},
        "E": {"B", "F"},
        "F": {"C", "E"}
    }

    analyzer = UndirectedGraphAnalyzer(graph)
    analyzer.print_graph_statistics()
    analyzer.print_all_paths("A", "F")
    analyzer.print_shortest_path("A", "F")
    analyzer.print_all_paths_parallel("A", "F")