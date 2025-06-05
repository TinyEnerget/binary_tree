import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree_analyzer.tree_construction import Node

if __name__ == '__main__':
    root = Node('root')
    child1 = Node('child1')
    child2 = Node('child2')
    grandchild1_1 = Node('grandchild1_1')
    grandchild1_2 = Node('grandchild1_2')

    child1.add_child(grandchild1_1)
    child1.add_child(grandchild1_2)

    root.add_child(child1)
    root.add_child(child2)

    print("--- Printing tree (acyclic) ---")
    root.print_tree()
    print(f"Value of first child of root: {root.children[0].value}")
    print("-" * 30)

    # Add a cycle for demonstration: grandchild1_2 -> child1
    print("\n--- Adding a cycle: grandchild1_2 points back to child1 ---")
    grandchild1_2.add_child(child1)

    print("--- Printing tree (with cycle) ---")
    # The print_tree method should now detect and indicate the cycle.
    root.print_tree()
    print("-" * 30)

    # Another cyclic example: child2 points to root
    child3 = Node('child3_loops_to_root')
    root.add_child(child3)
    child3.add_child(root) # child3 -> root (cycle)

    print("\n--- Printing tree (with another cycle: child3 points to root) ---")
    root.print_tree()
    print("-" * 30)

    # Example of a deeper cycle
    node_a = Node('A')
    node_b = Node('B')
    node_c = Node('C')
    node_d = Node('D')
    node_e_loops_to_b = Node('E_loops_to_B')

    node_a.add_child(node_b)
    node_b.add_child(node_c)
    node_c.add_child(node_d)
    node_d.add_child(node_e_loops_to_b)
    node_e_loops_to_b.add_child(node_b) # Cycle E -> B

    print("\n--- Printing tree with deeper cycle (E loops to B) ---")
    node_a.print_tree()
    print("-" * 30)
