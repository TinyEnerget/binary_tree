import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree_analyzer.tree_construction import Node
from tree_analyzer.multi_root_analyzer import MultiRootAnalyzer
from tree_analyzer.visualize_forest_connection import VisualizeForest

if __name__ == '__main__':
    # Setup from the original __main__ block
    root_1 = Node("A")
    root_2 = Node("B")
    root_3 = Node("C")

    node_d = Node("D")
    node_e = Node("E")
    node_f = Node("F")
    node_g = Node("G")
    node_k = Node("K")
    node_l = Node("L")
    node_m = Node("M")
    node_n = Node("N")
    # node_o = Node("O") # This node was defined but not used in original example, can be omitted or kept

    root_1.add_child(node_d)
    root_2.add_child(node_k)
    root_3.add_child(node_l)
    root_3.add_child(node_m)
    root_3.add_child(node_n)

    node_d.add_child(node_e)
    node_e.add_child(node_f)
    node_f.add_child(node_g)
    node_f.add_child(node_d) # Cycle D -> E -> F -> D
    node_e.add_child(node_g)

    # Initialize the analyzer
    multi_analyzer = MultiRootAnalyzer([root_1, root_2, root_3])

    # --- Get and print forest statistics ---
    stats = multi_analyzer.get_forest_statistics()
    print("Forest Statistics:")
    print(f"  Total Roots: {stats.get('total_roots', 'N/A')}")
    if 'trees_info' in stats:
        for tree_info in stats.get('trees_info', []):
            if tree_info: # Check if tree_info is not None
                print(f"  Tree {tree_info.get('root', 'N/A')}: "
                      f"Nodes - {tree_info.get('nodes_count', 'N/A')}, "
                      f"Depth - {tree_info.get('depth', 'N/A')}")
    print("Shared Nodes Data (from get_forest_statistics):")
    if 'shared_nodes' in stats and stats.get('shared_nodes'):
        for node_value, in_trees in stats['shared_nodes'].items():
            print(f"  Node '{node_value}': found in {in_trees}")
    else:
        print("  No shared nodes found via get_forest_statistics.")
    print("-" * 30)

    # --- Analyze forest to populate shared_nodes explicitly and print them ---
    # Note: analyze_forest() is called by get_forest_statistics if shared_nodes is empty.
    # Calling it here again ensures it's fresh or if direct access to its return (all_nodes_map) is needed.
    all_nodes_map = multi_analyzer.analyze_forest()
    print("Shared Nodes (after explicit analyze_forest call):")
    if multi_analyzer.shared_nodes:
        for node_value, in_trees in multi_analyzer.shared_nodes.items():
            print(f"  Node '{node_value}': found in {in_trees}")
    else:
        print("  No shared nodes found.")
    # print("All nodes map from analyze_forest:", all_nodes_map) # Optional: print full map for debugging
    print("-" * 30)

    # --- Find and print connections between roots ---
    connections = multi_analyzer.find_connections_between_roots()
    print("Connections Between Roots:")
    if connections:
        for conn in connections:
            print(f"  Connection between {conn.get('root1','N/A')} and {conn.get('root2','N/A')}: "
                  f"Common nodes - {conn.get('common_nodes',[])}")
    else:
        print("  No direct connections found.")
    print("-" * 30)

    # --- Find and print all paths between "A" and "G" ---
    paths_a_g = multi_analyzer.find_all_paths_between_nodes("A", "G")
    print("All paths from 'A' to 'G':")
    if paths_a_g:
        for tree_name, path_list in paths_a_g.items():
            print(f"  In {tree_name}:")
            if path_list:
                for i, path in enumerate(path_list, 1):
                    print(f"    Path {i}: {' -> '.join(map(str, path))}")
            else:
                print("    No paths found in this tree for A -> G.")
    else:
        print("  No paths found between 'A' and 'G' in any tree.")
    print("-" * 30)

    # --- Find and print shortest path to "G" ---
    shortest_path_g = multi_analyzer.find_shortest_path_to_node("G")
    print("Shortest path to 'G':")
    if shortest_path_g:
        print(f"  In Tree: {shortest_path_g.get('tree', 'N/A')}")
        print(f"  Path: {' -> '.join(map(str, shortest_path_g.get('path', [])))}")
        print(f"  Length: {shortest_path_g.get('length', 'N/A')}")
    else:
        print("  No path found to 'G' in any tree.")
    print("\n")

    # --- Visualize the forest ---
    print("Visualizing forest connections...")
    visualizer = VisualizeForest(multi_analyzer)
    visualizer.visualize_forest_connections()
