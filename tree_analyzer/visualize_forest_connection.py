# Description: This class works in conjunction with a MultiRootAnalyzer instance
# and uses its data for visualization purposes.
#
# Key functionalities:
# 1. (Removed) Static print_tree() method - Tree printing is now handled by Node.print_tree().
# 2. visualize_forest_connections() - The main method for visualizing the forest,
#    displaying each tree structure and the connections between them based on shared nodes.

# Imports
# (No specific imports are listed, but would typically include MultiRootAnalyzer types if type hinting was more extensive)
# from .multi_root_analyzer import BaseMultiRootAnalyzer # Example

class VisualizeForest:
    """
    A class responsible for visualizing a forest of trees, including their structures
    and connections, based on data from a MultiRootAnalyzer instance.
    """
    def __init__(self, analyzer):
        """
        Initializes the VisualizeForest instance.

        Args:
            analyzer: An instance of a class compatible with BaseMultiRootAnalyzer,
                      which has already processed a list of root nodes. This analyzer
                      instance should provide access to `roots` and `connections`
                      (or a method to generate connections like `find_connections_between_roots`).
        """
        self.analyzer = analyzer

    # The static print_tree method was removed. Node's instance method (Node.print_tree) is now used.

    def visualize_forest_connections(self): # Removed unused level and prefix parameters
        """
        Visualizes the entire forest structure and the connections between trees.

        This method iterates through each tree in the forest, printing its structure
        using the `Node.print_tree()` method. It then lists the connections
        (based on shared nodes) found between different trees in the forest.
        """
        print("=== FOREST VISUALIZATION ===\n")
        roots = self.analyzer.roots

        # Ensure connections are populated if the analyzer hasn't run the relevant method yet.
        # The `connections` attribute is expected to be populated by `find_connections_between_roots`.
        if not hasattr(self.analyzer, 'connections') or not self.analyzer.connections:
            if hasattr(self.analyzer, 'find_connections_between_roots'):
                self.analyzer.find_connections_between_roots() # Populate connections if possible

        connections = getattr(self.analyzer, 'connections', [])

        # Print each tree structure
        for i, root_node in enumerate(roots):
            if root_node is None:
                print(f"Warning: Tree {i+1} has a None root and will be skipped.")
                print()
                continue

            print(f"Tree {i+1} (Root: {root_node.value}):")
            # Call the Node's instance method print_tree.
            # It uses its own default parameters for level and prefix for a root.
            root_node.print_tree()
            print() # Adds a blank line for better separation between trees

        # Print the analysis of connections
        if connections:
            print("FOUND CONNECTIONS:")
            for conn in connections:
                print(f"  {conn.get('root1', 'N/A')} ↔ {conn.get('root2', 'N/A')}") # Using .get for safer access
                print(f"  Shared nodes: {', '.join(map(str, conn.get('common_nodes', [])))}")
                print()
        else:
            print("No connections found between trees.")

