# This module implements a forest analyzer (MultiRootAnalyzer)
# that works with multiple root nodes simultaneously.
#
# How it works:
# The class accepts a list of root nodes and creates structures
# to track relationships between trees.
#
# 1. analyze_forest(): Analyzes the entire forest.
#    - Iterates through each tree and collects all its nodes.
#    - Tracks in which trees each node appears.
#    - Identifies nodes that are present in multiple trees (shared nodes).
#
# 2. find_connections_between_roots(): Finds connections between roots.
#    - Compares each pair of trees.
#    - Finds common nodes between these trees.
#    - Creates a map of connections through these shared nodes.
#
# 3. get_forest_statistics(): Gathers statistics for the forest.
#    - Counts the number of nodes in each tree.
#    - Calculates the depth of each tree.
#    - Collects overall statistics for the forest.
#    - Returns these statistics.

# Imports
# (No specific imports are used in this snippet, but typically Node would be imported if not in the same file)
# from .tree_construction import Node # Example if Node is in tree_construction.py

class BaseMultiRootAnalyzer:
    """
    Base class for multi-root tree forest analyzers.
    Provides core logic for analyzing forests composed of multiple tree structures,
    including finding shared nodes, connections between trees, and gathering statistics.

    Attributes:
        roots (list[Node]): A list of root Node objects to be analyzed.
        forest_map (dict): A mapping of node values to the root Node of the tree(s) they belong to.
                           Note: This attribute is initialized but not actively used in the current base methods.
                           It might be intended for more advanced value-based lookups.
        shared_nodes (dict): A dictionary where keys are node values and values are lists of tree identifiers
                             (e.g., "Tree_0_RootValue") indicating which trees contain that node.
                             Populated by `analyze_forest()`.
        connections (list[dict]): A list of dictionaries, where each dictionary represents a connection
                                  between two roots through shared nodes. Populated by `find_connections_between_roots()`.
    """
    def __init__(self, roots: list):
        """
        Initializes the BaseMultiRootAnalyzer with a list of root nodes.

        Args:
            roots (list[Node]): A list of root Node objects representing the trees in the forest.
                                Expected to be a list of objects compatible with the Node structure
                                (having .value and .children attributes).
        """
        self.roots = roots  # List of root nodes
        self.forest_map = {}  # Intended for: node_value -> root_node mapping (currently not fully utilized)
        self.shared_nodes = {}  # Stores: node_value -> [list_of_trees_containing_it]
        self.connections = [] # Stores: list of connection dicts between roots

    def analyze_forest(self) -> dict:
        """
        Analyzes the forest of trees to identify all nodes and shared nodes.

        Iterates through each tree starting from its root, collects all unique node values within that tree,
        and maps each node value to all trees it appears in. Populates `self.shared_nodes`
        with nodes found in more than one tree.

        Returns:
            dict: A dictionary where keys are node values and values are lists of tree identifiers
                  (e.g., "Tree_0_RootValue") indicating which trees each node belongs to.
                  This map includes all nodes, not just shared ones.
        """
        all_nodes_in_trees = {}
        
        for i, root_node in enumerate(self.roots): # Renamed root to root_node for clarity
            if root_node is None: # Safety check for None roots
                continue
            tree_nodes = self._get_all_nodes_in_tree(root_node)
            
            for node_value in tree_nodes:
                if node_value not in all_nodes_in_trees:
                    all_nodes_in_trees[node_value] = []
                all_nodes_in_trees[node_value].append(f"Tree_{i}_{root_node.value}")
        
        # Identify nodes that appear in multiple trees
        self.shared_nodes.clear() # Clear previous results
        for node_value, trees in all_nodes_in_trees.items():
            if len(trees) > 1:
                self.shared_nodes[node_value] = trees
        
        return all_nodes_in_trees

    def _get_all_nodes_in_tree(self, root_node) -> set:
        """
        Retrieves all unique node values in a single tree starting from the given root node.
        Uses a depth-first traversal with cycle detection.

        Args:
            root_node (Node): The root node of the tree to traverse.

        Returns:
            set: A set of unique node values found in the tree.
        """
        nodes = set()
        visited_values = set()  # Tracks visited node values to prevent reprocessing and handle cycles.

        def traverse(node):
            if node and node.value not in visited_values:
                visited_values.add(node.value)  # Mark node value as visited
                nodes.add(node.value)
                if hasattr(node, 'children') and node.children: # Check if node has children attribute
                    for child in node.children:
                        traverse(child)
        
        if root_node: # Ensure root_node is not None
            traverse(root_node)
        return nodes

    def find_connections_between_roots(self) -> list:
        """
        Finds and records connections between pairs of root nodes based on shared nodes.

        Iterates through all unique pairs of trees in the forest, gets all nodes for each tree in a pair,
        and finds their intersection (common nodes). If common nodes exist, a connection record
        is created and stored in `self.connections`.

        Returns:
            list[dict]: A list of connection dictionaries. Each dictionary contains:
                        - 'root1': Value of the first root node in the connected pair.
                        - 'root2': Value of the second root node in the connected pair.
                        - 'common_nodes': A list of values of the shared nodes.
                        - 'connection_type': A string indicating the type of connection (e.g., 'shared_nodes').
        """
        connections_list = [] # Local list for current findings
        self.connections.clear() # Clear previous results from the instance attribute

        num_roots = len(self.roots)
        for i in range(num_roots):
            for j in range(i + 1, num_roots):
                root1 = self.roots[i]
                root2 = self.roots[j]

                if root1 is None or root2 is None: # Skip if either root is None
                    continue
                
                nodes1 = self._get_all_nodes_in_tree(root1)
                nodes2 = self._get_all_nodes_in_tree(root2)
                
                common_nodes = nodes1.intersection(nodes2)
                
                if common_nodes:
                    connections_list.append({
                        'root1': root1.value,
                        'root2': root2.value,
                        'common_nodes': list(common_nodes),
                        'connection_type': 'shared_nodes' # Type of connection
                    })
        self.connections = connections_list
        return self.connections

    def get_forest_statistics(self) -> dict:
        """
        Calculates and returns statistics for the forest.

        This includes the total number of roots, and for each tree: its root value,
        node count, depth, and a list of its node values. Also includes the shared nodes
        information populated by `analyze_forest()`. If `analyze_forest()` has not been
        called yet (i.e., `self.shared_nodes` is empty), this method will call it.

        Returns:
            dict: A dictionary containing forest statistics with keys:
                  - 'total_roots': Total number of trees (roots).
                  - 'trees_info': A list of dictionaries, each with info for a single tree
                                  ('root', 'nodes_count', 'depth', 'nodes').
                  - 'shared_nodes': The `self.shared_nodes` dictionary.
        """
        stats = {
            'total_roots': len(self.roots),
            'trees_info': [],
            'shared_nodes': self.shared_nodes
        }
        
        if not self.shared_nodes and self.roots: # Avoid calling analyze_forest if no roots
            self.analyze_forest()
            stats['shared_nodes'] = self.shared_nodes # Update with results from analyze_forest

        for i, root_node in enumerate(self.roots): # Renamed root to root_node
            if root_node is None: # Handle None roots
                stats['trees_info'].append({
                    'root': None,
                    'nodes_count': 0,
                    'depth': 0,
                    'nodes': []
                })
                continue

            tree_nodes = self._get_all_nodes_in_tree(root_node)
            tree_depth = self._get_tree_depth(root_node)
            
            stats['trees_info'].append({
                'root': root_node.value,
                'nodes_count': len(tree_nodes),
                'depth': tree_depth,
                'nodes': list(tree_nodes)
            })
        
        return stats

    def _get_tree_depth(self, root_node) -> int:
        """
        Calculates the depth of a single tree starting from the given root node.
        The depth is defined as the number of nodes along the longest path from the root node
        down to the farthest leaf node. A tree with only a root node has depth 1.
        Uses a depth-first traversal with cycle detection for path uniqueness.

        Args:
            root_node (Node): The root node of the tree.

        Returns:
            int: The calculated depth of the tree. Returns 0 if root_node is None.
        """
        if not root_node:
            return 0
        
        max_depth_found = 0
        # Stores tuples of (path_tuple_of_values) to detect repeated paths in cyclic graphs
        visited_paths_set = set()

        def dfs(node, current_depth, path_values): # path_values is a list of node values in current DFS path
            nonlocal max_depth_found

            if not node:
                return

            # Create a unique key for the current path to this node
            # This helps in scenarios with complex cycles where just visiting a node isn't enough,
            # but visiting a node via the same path is.
            current_path_key = tuple(path_values + [node.value])

            # Cycle detection: if this exact path to this node's value has been seen, or
            # if the node's value itself is in the current path list leading up to it (excluding current node).
            if current_path_key in visited_paths_set or node.value in path_values:
                return

            visited_paths_set.add(current_path_key)
            max_depth_found = max(max_depth_found, current_depth + 1) # current_depth is 0-indexed

            if hasattr(node, 'children') and node.children:
                for child in node.children:
                    dfs(child, current_depth + 1, path_values + [node.value]) # Pass new path list
    
        dfs(root_node, 0, []) # Initial call: depth 0, empty path list
        return max_depth_found

    def find_all_paths_to_node(self, target_value) -> dict:
        """
        Finds all possible paths from any root in the forest to a node with the target value.

        Args:
            target_value: The value of the node to find paths to.

        Returns:
            dict: A dictionary where keys are tree identifiers (e.g., "Tree_0_RootValue")
                  and values are lists of paths. Each path is a list of node values
                  from the root to the target node in that tree.
                  Returns an empty dictionary if the target is not found in any tree.
        """
        all_paths_map = {} # Use a more descriptive name
        
        for i, root_node in enumerate(self.roots): # Renamed root to root_node
            if root_node is None: # Skip None roots
                continue
            tree_name = f"Tree_{i}_{root_node.value}"
            paths_in_tree = self._find_paths_in_tree(root_node, target_value)
            
            if paths_in_tree:
                all_paths_map[tree_name] = paths_in_tree
        
        return all_paths_map
    
    def _find_paths_in_tree(self, root_node, target_value) -> list:
        """
        Finds all paths from a given root node to a node with the target value within a single tree.
        Uses a recursive DFS approach. Cycle detection is handled by passing a copy of the visited set for each path.

        Args:
            root_node (Node): The root node of the tree to search within.
            target_value: The value of the node to find.

        Returns:
            list[list[str]]: A list of paths, where each path is a list of node values.
                             Returns an empty list if the target is not found or root_node is None.
        """
        if not root_node: # Handle None root_node explicitly
            return []

        all_paths_list = [] # Use a more descriptive name
        
        # visited_in_path tracks nodes visited in the current specific DFS path to handle cycles within that path
        def dfs(node, current_path_values, visited_on_current_path):
            if not node:
                return
            
            if node.value in visited_on_current_path: # Cycle detected in current path
                return
            
            # Add current node to path and visited set for this specific DFS traversal
            current_path_values.append(node.value)
            new_visited_on_current_path = visited_on_current_path | {node.value}
            
            if node.value == target_value:
                all_paths_list.append(list(current_path_values)) # Store a copy of the found path
            
            if hasattr(node, 'children') and node.children:
                for child in node.children:
                    # Each DFS branch gets its own copy of visited_on_current_path implicitly by passing a new set
                    # or by managing additions/removals carefully if passing the same set object.
                    # Here, new_visited_on_current_path is passed, but current_path_values is modified and popped.
                    dfs(child, current_path_values, new_visited_on_current_path)
            
            current_path_values.pop() # Backtrack: remove current node from path
            # No need to remove from new_visited_on_current_path as it's local to the deeper recursion stack
        
        dfs(root_node, [], set()) # Initial call with empty path and visited set for the path
        return all_paths_list
    
    def find_shortest_path_to_node(self, target_value) -> dict | None:
        """
        Finds the shortest path to a node with the target value from any root in the forest.

        Args:
            target_value: The value of the node to find the shortest path to.

        Returns:
            dict or None: A dictionary containing information about the shortest path, including:
                          - 'tree': The identifier of the tree where the shortest path was found.
                          - 'path': The shortest path as a list of node values.
                          - 'length': The length of the shortest path (number of nodes).
                          Returns `None` if the target node is not found in any tree.
        """
        all_paths_data = self.find_all_paths_to_node(target_value) # Calls the overridden version if in subclass
        
        if not all_paths_data:
            return None
        
        shortest_path_info = None # Use a more descriptive name
        current_shortest_length = float('inf')
        
        for tree_name, paths_list in all_paths_data.items():
            for path in paths_list:
                if len(path) < current_shortest_length:
                    current_shortest_length = len(path)
                    shortest_path_info = {
                        'tree': tree_name,
                        'path': path,
                        'length': current_shortest_length
                    }
        
        return shortest_path_info    
    def find_all_paths_between_nodes(self, start_value, end_value) -> dict:
        """
        Finds all paths between two nodes (identified by start_value and end_value)
        across all trees in the forest.

        Args:
            start_value: The value of the starting node of the paths.
            end_value: The value of the ending node of the paths.

        Returns:
            dict: A dictionary where keys are tree identifiers (e.g., "Tree_0_RootValue")
                  and values are lists of paths. Each path is a list of node values
                  from start_value to end_value in that tree.
                  Returns an empty dictionary if no such paths are found.
        """
        all_paths_map = {} # Use a more descriptive name
        
        for i, root_node in enumerate(self.roots): # Renamed root to root_node
            if root_node is None: # Skip None roots
                continue
            tree_name = f"Tree_{i}_{root_node.value}"
            paths_in_tree = self._find_paths_between_nodes_in_tree(root_node, start_value, end_value)
            
            if paths_in_tree:
                all_paths_map[tree_name] = paths_in_tree
        
        return all_paths_map
    
    def _find_paths_between_nodes_in_tree(self, root_node, start_value, end_value) -> list:
        """
        Finds all paths between a start_value node and an end_value node within a single tree.
        Paths are collected starting from the node that matches `start_value`.
        Uses a recursive DFS approach with cycle detection.

        Args:
            root_node (Node): The root node of the tree to search.
            start_value: The value of the starting node for the paths.
            end_value: The value of the ending node for the paths.

        Returns:
            list[list[str]]: A list of paths, where each path is a list of node values from
                             `start_value` to `end_value`. Returns an empty list if no such
                             paths are found or if `root_node` is None.
        """
        if not root_node: # Handle None root_node explicitly
            return []

        collected_paths = [] # Use a more descriptive name
        
        # visited_in_path tracks nodes in the current DFS path to avoid cycles within this path.
        def dfs(node, current_path_values, visited_on_current_path, start_node_found_in_path):
            if not node:
                return
            
            if node.value in visited_on_current_path: # Cycle in current path
                return
            
            current_path_values.append(node.value)
            new_visited_on_current_path = visited_on_current_path | {node.value}
            
            # Update status if current node is the start_value
            if node.value == start_value:
                start_node_found_in_path = True
            
            # If current node is the end_value and start_value was found earlier in this path
            if node.value == end_value and start_node_found_in_path:
                try:
                    # Extract the path segment from the first occurrence of start_value
                    start_index = current_path_values.index(start_value)
                    path_segment = current_path_values[start_index:]
                    if path_segment not in collected_paths: # Avoid duplicate path segments
                        collected_paths.append(path_segment)
                except ValueError:
                    # Should not happen if start_node_found_in_path is True.
                    # This means start_value was not in current_path_values, which contradicts logic.
                    pass

            if hasattr(node, 'children') and node.children:
                for child in node.children:
                    dfs(child, current_path_values, new_visited_on_current_path, start_node_found_in_path)
            
            current_path_values.pop() # Backtrack
        
        # Initial call to DFS. The search for start_value begins from the root_node.
        # The 'found_start' flag is initially False.
        dfs(root_node, [], set(), False)
        return collected_paths


class MultiRootAnalyzer(BaseMultiRootAnalyzer):
    """
    A standard multi-root tree forest analyzer.
    It inherits core analysis capabilities from `BaseMultiRootAnalyzer` and can be used for
    analyzing multiple tree structures, tracking shared nodes, finding connections,
    and generating statistics. This version does not add further optimizations on top of the base.
    
    This class enables advanced forest analysis by:
    - Tracking shared nodes across multiple trees
    - Finding connections between root nodes
    - Generating detailed forest and tree statistics
    
    Attributes:
        roots (list): A collection of root nodes to be analyzed
        forest_map (dict): Mapping of node values to their root nodes
        shared_nodes (dict): Tracks node values that appear in multiple trees
    """
    def __init__(self, roots: list):
        super().__init__(roots)
        # Any additional initialization specific to MultiRootAnalyzer can go here
        # For now, it seems the base __init__ is sufficient.

    # Methods like analyze_forest, _get_all_nodes_in_tree, find_connections_between_roots,
    # get_forest_statistics, _get_tree_depth, and pathfinding methods
    # are inherited from BaseMultiRootAnalyzer.

    # Print methods are removed as per refactoring plan.
    # Users should call data-gathering methods and print the results as needed.

# The if __name__ == '__main__' block has been moved to examples/example_multi_root_analyzer.py