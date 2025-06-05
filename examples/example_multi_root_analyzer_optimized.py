import sys
import os
import time # Ensure time is imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tree_analyzer.tree_construction import Node
from tree_analyzer.multi_root_analyzer_optimazed import MultiRootAnalyzerOpt
# Assuming visualize_forest_connection might be in the tree_analyzer package directory
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
    # node_o = Node("O") # Defined but not used in original example

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

    start_time = time.time()
    # Initialize the optimized analyzer
    multi_analyzer_opt = MultiRootAnalyzerOpt([root_1, root_2, root_3])

    # --- Get and print forest statistics (first call) ---
    print("Optimized Forest Statistics (1st call):")
    stats_opt = multi_analyzer_opt.get_forest_statistics()
    print(f"  Total Roots: {stats_opt.get('total_roots', 'N/A')}")
    if 'trees_info' in stats_opt:
        for tree_info in stats_opt.get('trees_info', []):
            if tree_info:
                print(f"  Tree {tree_info.get('root', 'N/A')}: "
                      f"Nodes - {tree_info.get('nodes_count', 'N/A')}, "
                      f"Depth - {tree_info.get('depth', 'N/A')}")
    print("Shared Nodes Data (from get_forest_statistics - 1st call):")
    if 'shared_nodes' in stats_opt and stats_opt.get('shared_nodes'):
        for node_value, in_trees in stats_opt['shared_nodes'].items():
            print(f"  Node '{node_value}': found in {in_trees}")
    else:
        print("  No shared nodes found.")
    print("-" * 30)

    # --- Explicitly call analyze_forest and print shared nodes ---
    # (get_forest_statistics would have already called analyze_forest if shared_nodes was empty)
    multi_analyzer_opt.analyze_forest() # Ensure shared_nodes are populated
    print("Shared Nodes (after explicit analyze_forest call on optimized analyzer):")
    if multi_analyzer_opt.shared_nodes:
        for node_value, in_trees in multi_analyzer_opt.shared_nodes.items():
            print(f"  Node '{node_value}': found in {in_trees}")
    else:
        print("  No shared nodes found.")
    print("-" * 30)

    # --- Find and print connections between roots (first call) ---
    print("Optimized Connections Between Roots (1st call):")
    connections_opt = multi_analyzer_opt.find_connections_between_roots()
    if connections_opt:
        for conn in connections_opt:
            print(f"  Connection between {conn.get('root1','N/A')} and {conn.get('root2','N/A')}: "
                  f"Common nodes - {conn.get('common_nodes',[])}")
    else:
        print("  No direct connections found.")
    print("-" * 30)

    # --- Get and print forest statistics (second call - to check caching/repeated calls) ---
    print("Optimized Forest Statistics (2nd call):")
    stats_opt_repeat = multi_analyzer_opt.get_forest_statistics()
    print(f"  Total Roots: {stats_opt_repeat.get('total_roots', 'N/A')}")
    # (Can add more detailed printout if desired for verification)
    print("-" * 30)

    # --- Find and print connections (second call) ---
    print("Optimized Connections Between Roots (2nd call):")
    connections_opt_repeat = multi_analyzer_opt.find_connections_between_roots()
    if connections_opt_repeat:
         for conn in connections_opt_repeat: # Basic print to show it ran
            print(f"  Connection: {conn.get('root1','N/A')} - {conn.get('root2','N/A')}")
    else:
        print("  No direct connections found on repeat call.")
    print("-" * 30)

    # --- Find and print all paths between "A" and "G" ---
    print("Optimized All paths from 'A' to 'G':")
    paths_a_g_opt = multi_analyzer_opt.find_all_paths_between_nodes("A", "G")
    if paths_a_g_opt:
        for tree_name, path_list in paths_a_g_opt.items():
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
    print("Optimized Shortest path to 'G':")
    shortest_path_g_opt = multi_analyzer_opt.find_shortest_path_to_node("G")
    if shortest_path_g_opt:
        print(f"  In Tree: {shortest_path_g_opt.get('tree', 'N/A')}")
        print(f"  Path: {' -> '.join(map(str, shortest_path_g_opt.get('path', [])))}")
        print(f"  Length: {shortest_path_g_opt.get('length', 'N/A')}")
    else:
        print("  No path found to 'G' in any tree.")
    print("\n")

    end_time = time.time()
    print(f"Total execution time for optimized analysis example: {end_time - start_time:.4f} seconds")
    print("\n")

    # --- Visualize the forest ---
    print("Visualizing forest (optimized analyzer)...")
    try:
        visualizer_opt = VisualizeForest(multi_analyzer_opt)
        visualizer_opt.visualize_forest_connections()
    except Exception as e_viz:
        print(f"Visualization module error or issue during visualization: {e_viz}")
