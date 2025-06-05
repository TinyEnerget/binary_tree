# This code implements the basic structure of a tree node (Node)
# with methods for building and displaying tree-like structures.
# How it works:
# Node Class - The foundation of the tree structure
# Features:
#   Each node stores a value and a list of children.
#   This is not a binary tree - a node can have any number of children.
#   The structure supports n-ary trees.
# Structure Management Methods:
# 1. add_child() - Adds a child node to the current node.
# 2. remove_child() - Removes a child node from the current node.
# 3. print_tree() - Outputs the tree structure to the console.
#   How print_tree works:
#       Recursive depth-first traversal of the tree.
#       Indentation: level * 4 spaces for each level.
#       ASCII graphics:
#       ├── for intermediate nodes
#       └── for the last node at a level
#       Prefixes: "Root: " for the root, then branch symbols.
## TODO: Add methods for input validation and error handling.

# Imports

class Node:
    """
    Represents a node in a tree data structure. Each node has a value and can have multiple children.

    This class provides basic functionalities to manipulate tree structures, such as adding
    and removing child nodes, and printing the tree structure to the console.
    The tree can be n-ary, meaning a node can have any number of children.
    
    Attributes:
        value (str): The value stored in the node. This is expected to be a string,
                     but other types can be used if string conversion is appropriate for printing.
        children (list[Node]): A list of child `Node` objects connected to this node.
    """
        
    def __init__(self, value: str):
        """
        Initializes a Node object.

        Args:
            value (str): The value to be stored in the node.
        """
        self.value = value  # Node's identifier or content
        self.children = []  # List of child nodes

    def add_child(self, child_node: 'Node'):
        """
        Adds a child node to this node.

        Args:
            child_node (Node): The Node object to be added as a child.
                               It's expected that child_node is an instance of Node.
        """
        # TODO: Consider adding a check to ensure child_node is an instance of Node
        # and not already present if duplicates are not desired.
        self.children.append(child_node)

    def remove_child(self, child_node: 'Node'):
        """
        Removes a specified child node from this node's children.

        Args:
            child_node (Node): The Node object to be removed from the children.
                               If the node is not found, a ValueError might be raised by list.remove().

        Raises:
            ValueError: If `child_node` is not found in the children list.
        """
        # TODO: Consider adding a check if child_node exists to provide a custom error or handle silently.
        self.children.remove(child_node)

    def print_tree(self, level: int = 0, prefix: str = "Root: ", path: list = None):
        """
        Prints the tree structure starting from this node to the console.

        Uses ASCII graphics to represent the tree hierarchy and includes cycle detection
        to prevent infinite loops when printing trees with circular references.

        Args:
            level (int, optional): The current depth level of the node in the tree.
                                   Used for indentation. Defaults to 0.
            prefix (str, optional): The prefix string to display before the node's value.
                                    Indicates the node's relationship to its parent (e.g., "Root: ", "├── ").
                                    Defaults to "Root: ".
            path (list, optional): A list of node values representing the current path from the root
                                   to this node in the traversal. Used for cycle detection.
                                   Should generally be left as None for external calls; it's managed internally
                                   by the recursion. Defaults to None.
        """
        # Initialize path as an empty list if it's the first call (None).
        # This list stores the values of nodes in the current traversal path to detect cycles.
        current_path = path or []

        if self.value is not None:
            print(" " * (level * 4) + prefix + str(self.value), end="")  # Keep print on one line initially

            # Check for cycles: if the current node's value is already in the path, it's a cycle.
            if self.value in current_path:
                print(f" [CYCLE DETECTED back to node '{self.value}']")
                return  # Stop recursion for this branch to prevent infinite loop
            else:
                print()  # Newline if not a cycle and the node's value has been printed

            if self.children:
                # Add current node's value to the path for recursive calls to children
                new_path_for_children = current_path + [self.value]
                for i, child in enumerate(self.children):
                    # Determine the correct prefix for child nodes based on whether it's the last child
                    extension = "├── " if i < len(self.children) - 1 else "└── "
                    # Recursively call print_tree for each child
                    child.print_tree(level + 1, extension, new_path_for_children)
        else:  # Handle the unlikely case where self.value is None
            print(" " * (level * 4) + prefix + "[None Value Node]")


# The if __name__ == '__main__' block has been moved to examples/example_tree_construction.py

