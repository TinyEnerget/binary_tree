import concurrent.futures
import multiprocessing as mp
from functools import lru_cache
#import numpy as np
from typing import Set, List as TypingList, Dict as TypingDict, Tuple, Optional
#import threading
from collections import defaultdict, deque
#import time

# Assuming BaseMultiRootAnalyzer is in multi_root_analyzer.py in the same directory
from .multi_root_analyzer import BaseMultiRootAnalyzer


class MultiRootAnalyzerOpt(BaseMultiRootAnalyzer):
    """
    Optimized forest analyzer with multithreading and caching capabilities.
    Inherits core logic from BaseMultiRootAnalyzer and overrides key methods
    for performance enhancement.

    This class is designed for analyzing large forests or complex tree structures
    where performance is a concern. It uses ThreadPoolExecutor for parallel processing
    of operations on multiple trees and LRU caching for memoizing results of
    computationally intensive tasks like node collection and depth calculation.

    Attributes:
        roots (list[Node]): Inherited. List of root nodes for analysis.
        max_workers (int): Maximum number of threads for parallel processing.
        _node_cache (dict): Instance cache for `_get_all_nodes_in_tree` results.
                            Keyed by (id(root_node), tree_idx).
        _depth_cache (dict): Instance cache for `_get_tree_depth` results.
                             Keyed by id(root_node). This is used by the original optimized
                             `_get_tree_depth` if lru_cache is not used directly on the method.
                             Note: The current implementation of `_get_tree_depth` uses @lru_cache,
                             making this attribute redundant for that specific method.
        # forest_map, shared_nodes, connections are inherited and managed by BaseMultiRootAnalyzer.
    """
        
    def __init__(self, roots: list, max_workers: Optional[int] = None):
        """
        Initializes the MultiRootAnalyzerOpt.

        Args:
            roots (list[Node]): A list of root Node objects.
            max_workers (Optional[int]): The maximum number of worker threads for concurrent operations.
                                         If None, it defaults to a value based on CPU count.
        """
        super().__init__(roots)
        self.max_workers = max_workers or min(32, (mp.cpu_count() or 1) + 4)
        self._node_cache = {}
        self._depth_cache = {} # Redundant if all relevant methods are @lru_cache decorated

    def analyze_forest(self) -> dict:
        """
        Analyzes the forest in parallel to identify all nodes and shared nodes.
        Overrides the base class method.

        Returns:
            dict: A map where keys are node values and values are lists of tree identifiers
                  (e.g., "Tree_0_RootValue") indicating which trees each node belongs to.
        """
        all_nodes_in_trees_map = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_tree_info = {
                executor.submit(self._get_all_nodes_in_tree_cached, root_node, i): (root_node, i)
                for i, root_node in enumerate(self.roots) if root_node is not None # Skip None roots
            }
            
            for future in concurrent.futures.as_completed(future_to_tree_info):
                root_node, tree_index = future_to_tree_info[future]
                try:
                    nodes_set = future.result()
                    tree_identifier = f"Tree_{tree_index}_{root_node.value}" # root_node here is guaranteed not None
                    
                    for node_val in nodes_set:
                        if node_val not in all_nodes_in_trees_map:
                            all_nodes_in_trees_map[node_val] = []
                        all_nodes_in_trees_map[node_val].append(tree_identifier)
                        
                except Exception as e:
                    # Log this error appropriately in a real application
                    print(f"Error processing tree {root_node.value if root_node else 'Unknown'} in analyze_forest: {e}")
        
        self.shared_nodes.clear()
        for node_val, tree_list in all_nodes_in_trees_map.items():
            if len(tree_list) > 1:
                self.shared_nodes[node_val] = tree_list
        
        return all_nodes_in_trees_map

    @lru_cache(maxsize=1000) # Decorating this method, uses its own shared cache across instances if not careful.
                             # However, as an instance method, args (like self) make it instance-specific effectively.
    def _get_all_nodes_in_tree_cached(self, root_node, tree_idx: int) -> set:
        """
        Cached retrieval of all nodes in a tree using the instance's `_node_cache`.
        The `@lru_cache` decorator provides an additional layer of caching if this method
        is called with the same `root_node` and `tree_idx` multiple times.

        Args:
            root_node (Node): The root node of the tree.
            tree_idx (int): The index of the tree, used for cache key uniqueness.

        Returns:
            set: A set of node values in the tree.
        """
        # Instance cache check (manual)
        cache_key = (id(root_node), tree_idx)
        if cache_key in self._node_cache:
            return self._node_cache[cache_key]
            
        # If not in instance cache, compute, then store in instance cache.
        # Calls the overridden _get_all_nodes_in_tree of this class.
        nodes = self._get_all_nodes_in_tree(root_node)
        self._node_cache[cache_key] = nodes
        return nodes

    def _get_all_nodes_in_tree(self, root_node) -> set:
        """
        Optimized retrieval of all nodes in a tree using iterative BFS (deque) with cycle protection.
        Overrides the base class method.

        Args:
            root_node (Node): The root node of the tree.

        Returns:
            set: A set of node values in the tree.
        """
        if not root_node:
            return set()
            
        nodes_set = set()
        visited_values = set()
        processing_queue = deque()
        
        if root_node:
            processing_queue.append(root_node)

        while processing_queue:
            current_node = processing_queue.popleft()
            if current_node and current_node.value not in visited_values:
                visited_values.add(current_node.value)
                nodes_set.add(current_node.value)
                
                if hasattr(current_node, 'children') and current_node.children:
                    for child in current_node.children:
                        if child:
                            processing_queue.append(child)
        return nodes_set

    def find_connections_between_roots(self) -> list:
        """
        Finds connections between root nodes in parallel using shared nodes.
        Overrides the base class method.

        Returns:
            list[dict]: A list of connection dictionaries, same format as base class.
        """
        all_tree_nodes_map = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_tree_index = {
                executor.submit(self._get_all_nodes_in_tree_cached, root_node, i): i
                for i, root_node in enumerate(self.roots) if root_node is not None
            }
            
            for future in concurrent.futures.as_completed(future_to_tree_index):
                tree_idx = future_to_tree_index[future]
                try:
                    all_tree_nodes_map[tree_idx] = future.result()
                except Exception as e:
                    print(f"Error getting nodes for tree index {tree_idx} in find_connections: {e}")
                    all_tree_nodes_map[tree_idx] = set()

        root_indices = [i for i, r in enumerate(self.roots) if r is not None] # Consider only non-None roots
        tree_pairs = [(i, j) for idx, i in enumerate(root_indices) for j in root_indices[idx + 1:]]
        
        found_connections = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_pair_indices = {
                executor.submit(self._find_connection_for_pair, pair_indices[0], pair_indices[1], all_tree_nodes_map): pair_indices
                for pair_indices in tree_pairs
            }
            
            for future in concurrent.futures.as_completed(future_to_pair_indices):
                try:
                    connection_result = future.result()
                    if connection_result:
                        found_connections.append(connection_result)
                except Exception as e:
                    # pair_idx_tuple = future_to_pair_indices[future]
                    # print(f"Error finding connection for pair {pair_idx_tuple}: {e}")
                    pass

        self.connections = found_connections
        return self.connections

    def _find_connection_for_pair(self, tree_idx1: int, tree_idx2: int, all_tree_nodes_map: TypingDict[int, set]) -> Optional[dict]:
        """
        Helper method to find shared node connections between a single pair of trees.

        Args:
            tree_idx1 (int): Index of the first tree's root in `self.roots`.
            tree_idx2 (int): Index of the second tree's root in `self.roots`.
            all_tree_nodes_map (TypingDict[int, set]): A map of tree index to its set of node values.

        Returns:
            Optional[dict]: A connection dictionary if common nodes are found, else None.
        """
        nodes_for_tree1 = all_tree_nodes_map.get(tree_idx1, set())
        nodes_for_tree2 = all_tree_nodes_map.get(tree_idx2, set())
        
        common_nodes_set = nodes_for_tree1.intersection(nodes_for_tree2)
        
        if common_nodes_set:
            # self.roots[tree_idx1] and self.roots[tree_idx2] are guaranteed to be non-None by caller logic
            return {
                'root1': self.roots[tree_idx1].value,
                'root2': self.roots[tree_idx2].value,
                'common_nodes': list(common_nodes_set),
                'connection_type': 'shared_nodes'
            }
        return None

    def get_forest_statistics(self) -> dict:
        """
        Calculates and returns statistics for the forest in parallel.
        Overrides the base class method.

        Returns:
            dict: A dictionary containing forest statistics, same format as base class.
        """
        if not self.shared_nodes and self.roots:
             self.analyze_forest() # Populates self.shared_nodes

        stats_dict = {
            'total_roots': len(self.roots),
            'trees_info': [None] * len(self.roots),
            'shared_nodes': self.shared_nodes
        }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_tree_index = {
                executor.submit(self._get_tree_stats, root_node, i): i
                for i, root_node in enumerate(self.roots) # _get_tree_stats will handle None root_node
            }
            
            for future in concurrent.futures.as_completed(future_to_tree_index):
                tree_idx = future_to_tree_index[future]
                try:
                    tree_stat_result = future.result()
                    stats_dict['trees_info'][tree_idx] = tree_stat_result
                except Exception as e:
                    root_val = self.roots[tree_idx].value if self.roots[tree_idx] else "Unknown (None root)"
                    print(f"Error getting stats for tree index {tree_idx} (root: {root_val}): {e}")
                    stats_dict['trees_info'][tree_idx] = {'root': root_val, 'error': str(e)}
        return stats_dict

    def _get_tree_stats(self, root_node, tree_idx: int) -> TypingDict:
        """
        Helper method to get statistics for a single tree.

        Args:
            root_node (Node): The root node of the tree.
            tree_idx (int): The index of the tree (for caching purposes).

        Returns:
            TypingDict: A dictionary with statistics for the tree.
        """
        if root_node is None: # Handle None root gracefully
            return {
                'root': None,
                'nodes_count': 0,
                'depth': 0,
                'nodes': []
            }

        nodes_in_tree = self._get_all_nodes_in_tree_cached(root_node, tree_idx)
        depth_of_tree = self._get_tree_depth(root_node) # Relies on @lru_cache on _get_tree_depth
        
        return {
            'root': root_node.value,
            'nodes_count': len(nodes_in_tree),
            'depth': depth_of_tree,
            'nodes': list(nodes_in_tree)
        }

    @lru_cache(maxsize=500)
    def _get_tree_depth(self, root_node) -> int:
        """
        Optimized calculation of tree depth using iterative DFS with cycle protection.
        Overrides the base class method. Decorated with @lru_cache for memoization.

        Args:
            root_node (Node): The root node of the tree.

        Returns:
            int: The depth of the tree. Returns 0 if root_node is None.
        """
        if not root_node:
            return 0
        
        current_max_depth = 0
        processing_stack = [(root_node, 1, frozenset([root_node.value]))]
        
        while processing_stack:
            current_node, depth_at_node, visited_on_path = processing_stack.pop()
            current_max_depth = max(current_max_depth, depth_at_node)
            
            if hasattr(current_node, 'children') and current_node.children:
                for child_node in current_node.children:
                    if child_node and child_node.value not in visited_on_path:
                        new_visited_on_path = visited_on_path | {child_node.value}
                        processing_stack.append((child_node, depth_at_node + 1, new_visited_on_path))
        return current_max_depth

    def find_all_paths_to_node(self, target_value) -> dict:
        """
        Finds all paths to a target node in parallel across all trees.
        Overrides the base class method.

        Args:
            target_value: The value of the node to find paths to.

        Returns:
            dict: A map of tree identifiers to lists of paths, same format as base.
        """
        all_found_paths = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_tree_index_map = {
                executor.submit(self._find_paths_in_tree, root_node, target_value): i
                for i, root_node in enumerate(self.roots) if root_node is not None
            }
            
            for future in concurrent.futures.as_completed(future_to_tree_index_map):
                tree_idx = future_to_tree_index_map[future]
                try:
                    paths_in_tree = future.result()
                    if paths_in_tree: # self.roots[tree_idx] is not None due to filter above
                        tree_name = f"Tree_{tree_idx}_{self.roots[tree_idx].value}"
                        all_found_paths[tree_name] = paths_in_tree
                except Exception as e:
                    root_val = self.roots[tree_idx].value if self.roots[tree_idx] else "Unknown (None root)"
                    print(f"Error finding paths to {target_value} in tree index {tree_idx} (root {root_val}): {e}")
        return all_found_paths

    def _find_paths_in_tree(self, root_node, target_value) -> TypingList[TypingList]:
        """
        Optimized path finding within a single tree using iterative DFS.
        Overrides the base class method.

        Args:
            root_node (Node): The root of the tree to search.
            target_value: The value of the target node.

        Returns:
            TypingList[TypingList]: A list of paths, where each path is a list of node values.
        """
        if not root_node:
            return []
        
        found_paths_list = []
        # Stack stores: (current_node_object, current_path_list_of_values, visited_on_path_set_of_values)
        processing_stack = [(root_node, [root_node.value], {root_node.value})]
        
        while processing_stack:
            current_node, path_list, visited_on_path_set = processing_stack.pop()
            
            if current_node.value == target_value:
                found_paths_list.append(list(path_list)) # Store a copy
            
            if hasattr(current_node, 'children') and current_node.children:
                # Iterate in reverse to mimic recursive DFS call order more closely if desired,
                # though for finding all paths, order of exploring children doesn't change the final set of paths.
                for child_node in reversed(current_node.children):
                    if child_node and child_node.value not in visited_on_path_set:
                        new_path_list = path_list + [child_node.value]
                        new_visited_on_path_set = visited_on_path_set | {child_node.value}
                        processing_stack.append((child_node, new_path_list, new_visited_on_path_set))
        return found_paths_list

    def find_shortest_path_to_node(self, target_value) -> Optional[dict]:
        # Inherited from BaseMultiRootAnalyzer, calls self.find_all_paths_to_node (which is overridden here).
        return super().find_shortest_path_to_node(target_value)

    def find_all_paths_between_nodes(self, start_value, end_value) -> dict:
        """
        Finds all paths between two nodes in parallel across all trees.
        Overrides the base class method.

        Args:
            start_value: The value of the starting node.
            end_value: The value of the ending node.

        Returns:
            dict: A map of tree identifiers to lists of paths, same format as base.
        """
        all_found_paths = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_tree_index_map = {
                executor.submit(self._find_paths_between_nodes_in_tree, root_node, start_value, end_value): i
                for i, root_node in enumerate(self.roots) if root_node is not None
            }
            
            for future in concurrent.futures.as_completed(future_to_tree_index_map):
                tree_idx = future_to_tree_index_map[future]
                try:
                    paths_in_tree = future.result()
                    if paths_in_tree: # self.roots[tree_idx] is not None
                        tree_name = f"Tree_{tree_idx}_{self.roots[tree_idx].value}"
                        all_found_paths[tree_name] = paths_in_tree
                except Exception as e:
                    root_val = self.roots[tree_idx].value if self.roots[tree_idx] else "Unknown (None root)"
                    print(f"Error finding paths between {start_value}-{end_value} in tree index {tree_idx} (root {root_val}): {e}")
        return all_found_paths

    def _find_paths_between_nodes_in_tree(self, root_node, start_value, end_value) -> TypingList[TypingList]:
        """
        Optimized path finding between two nodes in a single tree using iterative DFS.
        Paths collected are segments from `start_value` to `end_value`.
        Overrides the base class method.

        Args:
            root_node (Node): The root of the tree.
            start_value: The value of the starting node.
            end_value: The value of the ending node.

        Returns:
            TypingList[TypingList]: A list of paths, each path a list of node values.
        """
        if not root_node:
            return []
        
        found_paths_list = []
        initial_found_start = (root_node.value == start_value)
        # Stack: (current_node, current_path_list, visited_on_path_set, found_start_in_current_path_bool)
        processing_stack = [(root_node, [root_node.value], {root_node.value}, initial_found_start)]
        
        while processing_stack:
            current_node, path_list, visited_on_path_set, found_start_in_path = processing_stack.pop()
            current_val = current_node.value
            
            if not found_start_in_path and current_val == start_value:
                found_start_in_path = True
                # The path now effectively starts from here for path segment extraction purposes.
                # If current_val is start_value, path_list up to this point is the prefix from root.
                # We want the segment from start_value.

            if current_val == end_value and found_start_in_path:
                try:
                    # Find the first index of start_value in the current accumulated path_list.
                    path_start_index = -1
                    for i in range(len(path_list)):
                        if path_list[i] == start_value:
                            path_start_index = i
                            break

                    if path_start_index != -1: # If start_value was indeed found in the path
                        path_segment = path_list[path_start_index:] # Slice from start_value to current (end_value)
                        if path_segment not in found_paths_list:
                             found_paths_list.append(path_segment)
                except ValueError:
                    pass # Should not occur if logic is sound
            
            if hasattr(current_node, 'children') and current_node.children:
                for child_node in reversed(current_node.children):
                    if child_node and child_node.value not in visited_on_path_set:
                        new_path_list = path_list + [child_node.value] # Extend current path
                        new_visited_on_path_set = visited_on_path_set | {child_node.value}
                        processing_stack.append((child_node, new_path_list, new_visited_on_path_set, found_start_in_path))
        return found_paths_list

    # Print methods were removed in a previous refactoring step.
    # The __main__ block below is for testing this file directly.

# The if __name__ == '__main__' block has been moved to examples/example_multi_root_analyzer_optimized.py