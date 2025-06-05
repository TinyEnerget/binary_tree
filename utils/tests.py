import time
import random
import string
import psutil
import gc
from memory_profiler import profile

import sys
import os

# Add the parent directory to the path to allow imports from tree_analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tree_analyzer import Node, MultiRootAnalyzer # Assuming MultiRootAnalyzer is the non-optimized one for these tests
import numpy as np

# Import TreeGenerator from its new location
from .tree_generator import TreeGenerator

class PerformanceTester:
    """
    A class for testing the performance of the MultiRootAnalyzer.
    It includes tests for various scenarios like single trees, forests with shared nodes,
    and trees with cycles. It measures execution time and memory usage.
    """
    
    def __init__(self):
        """Initializes the PerformanceTester with a TreeGenerator instance."""
        self.generator = TreeGenerator()
        self.results = [] # Intended for storing results, though not actively used in current print-based output
    
    def measure_memory_usage(self) -> float:
        """
        Measures the current memory usage of the process.

        Returns:
            float: Memory usage in megabytes (MB).
        """
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def test_single_tree_performance(self, tree_sizes: list[int]):
        """
        Tests analyzer performance on single trees of various sizes.

        Args:
            tree_sizes (list[int]): A list of integers, where each integer is the number of nodes
                                    for a tree to be generated and tested.
        """
        print("=== Testing Single Tree Performance ===")
        
        for size in tree_sizes:
            print(f"\nTesting tree with {size} nodes:")
            
            # Create tree
            start_time = time.time()
            tree = self.generator.create_random_tree(size)
            creation_time = time.time() - start_time
            
            if tree is None:
                print(f"  Skipping analysis as tree generation returned None for size {size}")
                continue

            memory_before = self.measure_memory_usage()
            
            # Analyze tree
            analyzer = MultiRootAnalyzer([tree]) # Test with a list containing one tree
            
            start_time = time.time()
            stats = analyzer.get_forest_statistics()
            analysis_time = time.time() - start_time
            
            memory_after = self.measure_memory_usage()
            memory_used = memory_after - memory_before
            
            print(f"  Creation time: {creation_time:.4f} sec")
            print(f"  Analysis time: {analysis_time:.4f} sec")
            print(f"  Memory usage for analysis: {memory_used:.2f} MB")
            if stats['trees_info']: # Ensure there is info before accessing
                print(f"  Tree depth: {stats['trees_info'][0].get('depth', 'N/A')}")
                print(f"  Actual node count: {stats['trees_info'][0].get('nodes_count', 'N/A')}")
            else:
                print("  Could not retrieve tree statistics.")
            
            # Clean up memory
            del tree, analyzer, stats
            gc.collect()
    
    def test_forest_performance(self, forest_configs: list[tuple[int, int]]):
        """
        Tests analyzer performance on forests of trees with shared nodes.

        Args:
            forest_configs (list[tuple[int, int]]): A list of tuples, where each tuple
                                                    (num_trees, nodes_per_tree) specifies a forest configuration.
        """
        print("\n=== Testing Forest Performance ===")
        
        for config in forest_configs:
            num_trees, nodes_per_tree = config
            print(f"\nTesting forest: {num_trees} trees, ~{nodes_per_tree} nodes per tree:")
            
            # Create forest
            start_time = time.time()
            forest = self.generator.create_shared_nodes_forest(num_trees, nodes_per_tree)
            creation_time = time.time() - start_time
            
            memory_before = self.measure_memory_usage()
            
            # Analyze forest
            analyzer = MultiRootAnalyzer(forest)
            
            start_time_analysis = time.time()
            # Call analyze_forest() to populate shared_nodes, its return can be used for total_nodes
            all_nodes_map = analyzer.analyze_forest()
            analysis_specific_time = time.time() - start_time_analysis
            
            start_time_connections = time.time()
            connections = analyzer.find_connections_between_roots() # Populates analyzer.connections
            connections_specific_time = time.time() - start_time_connections
            
            start_time_stats = time.time()
            stats = analyzer.get_forest_statistics() # Uses populated shared_nodes
            stats_specific_time = time.time() - start_time_stats
            
            memory_after = self.measure_memory_usage()
            memory_used = memory_after - memory_before
            
            # Calculate total unique nodes from the map returned by analyze_forest
            total_unique_node_values = len(all_nodes_map)
            shared_node_values_count = len(analyzer.shared_nodes) # Access populated attribute

            print(f"  Forest creation time: {creation_time:.4f} sec")
            print(f"  analyze_forest() time: {analysis_specific_time:.4f} sec")
            print(f"  find_connections_between_roots() time: {connections_specific_time:.4f} sec")
            print(f"  get_forest_statistics() time: {stats_specific_time:.4f} sec")
            total_analysis_time = analysis_specific_time + connections_specific_time + stats_specific_time
            print(f"  Total analysis operations time: {total_analysis_time:.4f} sec")
            print(f"  Memory usage for analysis: {memory_used:.2f} MB")
            print(f"  Total unique node values in forest: {total_unique_node_values}")
            print(f"  Number of shared node values: {shared_node_values_count}")
            print(f"  Number of connections found: {len(connections)}")

            # Clean up memory
            del forest, analyzer, all_nodes_map, connections, stats
            gc.collect()
    
    def test_cyclic_trees_performance(self, sizes: list[int]):
        """
        Tests analyzer performance on trees containing cycles.

        Args:
            sizes (list[int]): A list of integers, where each integer is the number of unique nodes
                               for a cyclic tree to be generated and tested.
        """
        print("\n=== Testing Performance on Trees with Cycles ===")
        
        for size in sizes:
            print(f"\nTesting cyclic tree with {size} unique nodes:")
            
            # Create tree with cycles
            start_time = time.time()
            cyclic_tree = self.generator.create_cyclic_tree(size, cycle_probability=0.2)
            creation_time = time.time() - start_time

            if cyclic_tree is None:
                print(f"  Skipping analysis as cyclic tree generation returned None for size {size}")
                continue
            
            memory_before = self.measure_memory_usage()
            
            # Analyze tree
            analyzer = MultiRootAnalyzer([cyclic_tree]) # Test with a list containing one tree
            
            start_time = time.time()
            stats = analyzer.get_forest_statistics()
            # Test pathfinding on a potentially cyclic tree; .value of root is used as target
            paths_to_root = analyzer.find_all_paths_to_node(cyclic_tree.value)
            analysis_time = time.time() - start_time
            
            memory_after = self.measure_memory_usage()
            memory_used = memory_after - memory_before
            
            print(f"  Creation time: {creation_time:.4f} sec")
            print(f"  Analysis time (stats & pathfinding): {analysis_time:.4f} sec")
            print(f"  Memory usage for analysis: {memory_used:.2f} MB")
            if stats['trees_info']:
                print(f"  Tree depth: {stats['trees_info'][0].get('depth', 'N/A')}")
                print(f"  Node count: {stats['trees_info'][0].get('nodes_count', 'N/A')}")
            else:
                print("  Could not retrieve tree statistics.")
            print(f"  Paths found to root node '{cyclic_tree.value}': {len(paths_to_root.get(f'Tree_0_{cyclic_tree.value}', []))}")
            
            # Clean up memory
            del cyclic_tree, analyzer, stats, paths_to_root
            gc.collect()
    
    def run_comprehensive_test(self):
        """Runs a comprehensive suite of performance tests."""
        print("🚀 STARTING COMPREHENSIVE PERFORMANCE TESTING 🚀")
        print("=" * 70)
        
        # Test 1: Single trees of various sizes
        single_tree_sizes = [100, 500, 1000, 5000, 10000]
        self.test_single_tree_performance(single_tree_sizes)
        
        # Test 2: Forests of trees
        forest_configs = [
            (5, 100),    # 5 trees, ~100 nodes each
            (10, 200),   # 10 trees, ~200 nodes each
            (20, 500),   # 20 trees, ~500 nodes each
            #(50, 100), # Example of a larger configuration, commented out for brevity
        ]
        self.test_forest_performance(forest_configs)
              
        # Test 3: Trees with cycles (renamed from Test 4 for consistency)
        cyclic_sizes = [100, 200, 300, 500]
        self.test_cyclic_trees_performance(cyclic_sizes)
        
        print("\n" + "=" * 70)
        print("🎉 COMPREHENSIVE TESTING COMPLETE 🎉")


def stress_test_extreme_cases():
    """Runs stress tests with extreme tree/forest configurations."""
    print("\n🔥 EXTREME STRESS TESTING 🔥")
    print("=" * 50)
    
    generator = TreeGenerator()
    
    # Test 1: Very deep tree
    print("\n1. Testing very deep tree (depth 10, branching 5):") # Reduced depth for practical reasons
    start_time = time.time()
    deep_tree = generator.create_balanced_tree(depth=10, branching_factor=5)
    creation_time = time.time() - start_time
    
    analyzer_deep = MultiRootAnalyzer([deep_tree])
    start_time_analysis = time.time()
    stats_deep = analyzer_deep.get_forest_statistics()
    analysis_time_deep = time.time() - start_time_analysis

    print(f"  Creation time: {creation_time:.4f} sec")
    print(f"  Analysis time: {analysis_time_deep:.4f} sec")
    if stats_deep['trees_info']:
        print(f"  Depth: {stats_deep['trees_info'][0].get('depth', 'N/A')}")
        print(f"  Nodes: {stats_deep['trees_info'][0].get('nodes_count', 'N/A')}")
    del deep_tree, analyzer_deep, stats_deep
    gc.collect()

    # Test 2: Very wide tree
    print("\n2. Testing very wide tree (500 children at root, depth 2):")
    start_time = time.time()
    wide_tree = generator.create_wide_tree(width=500, depth=2)
    creation_time = time.time() - start_time
    
    analyzer_wide = MultiRootAnalyzer([wide_tree])
    start_time_analysis = time.time()
    stats_wide = analyzer_wide.get_forest_statistics()
    analysis_time_wide = time.time() - start_time_analysis

    print(f"  Creation time: {creation_time:.4f} sec")
    print(f"  Analysis time: {analysis_time_wide:.4f} sec")
    if stats_wide['trees_info']:
        print(f"  Depth: {stats_wide['trees_info'][0].get('depth', 'N/A')}")
        print(f"  Nodes: {stats_wide['trees_info'][0].get('nodes_count', 'N/A')}")
    del wide_tree, analyzer_wide, stats_wide
    gc.collect()

    # Test 3: Huge forest (adjust numbers for reasonable execution time)
    print("\n3. Testing huge forest (e.g., 50 trees, ~500 nodes each):") # Adjusted from 100x1000
    start_time = time.time()
    # Using smaller numbers than original example for quicker test runs: 50 trees, 500 nodes/tree
    huge_forest = generator.create_shared_nodes_forest(num_trees=50, nodes_per_tree=500, shared_ratio=0.2)
    creation_time = time.time() - start_time
    
    analyzer_huge = MultiRootAnalyzer(huge_forest)
    start_time_analysis = time.time()
    forest_analysis_map = analyzer_huge.analyze_forest() # Populates .shared_nodes
    connections_huge = analyzer_huge.find_connections_between_roots() # Populates .connections
    analysis_time_huge = time.time() - start_time_analysis

    print(f"  Creation time: {creation_time:.4f} sec")
    print(f"  Analysis time (analyze_forest & find_connections): {analysis_time_huge:.4f} sec")
    print(f"  Number of trees: {len(huge_forest)}")
    print(f"  Unique node values: {len(forest_analysis_map)}")
    print(f"  Shared node values: {len(analyzer_huge.shared_nodes)}")
    print(f"  Connections between trees: {len(connections_huge)}")
    del huge_forest, analyzer_huge, forest_analysis_map, connections_huge
    gc.collect()
    print("=" * 50)


@profile
def memory_profiling_test():
    """Performs memory profiling for key analyzer operations."""
    print("\n📊 MEMORY PROFILING 📊")
    
    generator = TreeGenerator()
    
    # Create a moderately large forest
    print("  Creating forest for memory profiling (10 trees, 100 nodes each)...")
    forest = generator.create_shared_nodes_forest(num_trees=10, nodes_per_tree=100, shared_ratio=0.3)
    
    # Analyze
    print("  Analyzing forest...")
    analyzer = MultiRootAnalyzer(forest)
    _ = analyzer.analyze_forest() # Ensure shared_nodes is populated
    _ = analyzer.find_connections_between_roots() # Ensure connections is populated
    _ = analyzer.get_forest_statistics()

    # Pathfinding
    if forest and forest[0] is not None: # Ensure forest and first root are not None
        print(f"  Performing pathfinding in first tree (root: {forest[0].value})...")
        _ = analyzer.find_all_paths_to_node(forest[0].value)
        _ = analyzer.find_shortest_path_to_node(forest[0].value)

    print("Memory profiling tasks complete. Check profiler output.")
    del forest, analyzer # Explicit cleanup
    gc.collect()


if __name__ == '__main__':
    # Main testing sequence
    tester = PerformanceTester()
    tester.run_comprehensive_test()
    
    # Extreme cases testing
    stress_test_extreme_cases()
    
    # Memory profiling
    try:
        print("\nAttempting memory profiling (requires memory_profiler package)...")
        memory_profiling_test()
    except Exception as e:
        print(f"Memory profiling could not be run or failed: {e}")
    
    # Demonstration with a specific large tree and forest
    print("\n" + "=" * 70)
    print("🌳 DEMONSTRATION WITH A LARGE TREE AND FOREST 🌳")
    print("=" * 70)
    
    generator = TreeGenerator()
    
    # Create a large tree with cycles
    print("Creating a large tree with 5000 nodes and cycles...")
    start_time = time.time()
    big_tree = generator.create_cyclic_tree(num_nodes=5000, cycle_probability=0.15)
    creation_time = time.time() - start_time
    print(f"Tree created in {creation_time:.4f} seconds.")
    # Optionally, analyze this single large tree if needed for specific demo
    # analyzer_single_big = MultiRootAnalyzer([big_tree])
    # ... analysis calls ...
    del big_tree # Clean up if not used further
    gc.collect()

    # Create a forest of several large trees
    print("\nCreating a forest of 10 large trees (1000 nodes each)...")
    start_time = time.time()
    big_forest = []
    for i in range(10): # Corrected loop variable if 'i' is not used inside
        tree = generator.create_random_tree(1000)
        if tree: # Ensure tree is not None
            big_forest.append(tree)
    creation_time = time.time() - start_time
    print(f"Forest created in {creation_time:.4f} seconds.")

    if not big_forest:
        print("Skipping analysis of big_forest as it's empty.")
    else:
        # Analyze the large forest
        print("\nAnalyzing the large forest...")
        analyzer = MultiRootAnalyzer(big_forest)
        
        start_time = time.time()
        stats_big = analyzer.get_forest_statistics()
        # --- Mimic print_forest_statistics ---
        print("Big Forest Statistics:")
        print(f"  Total Roots: {stats_big.get('total_roots', 'N/A')}")
        if 'trees_info' in stats_big:
            for tree_info in stats_big['trees_info']:
                if tree_info: # Check for None if a tree root was None
                    print(f"  Tree {tree_info.get('root', 'N/A')}: Nodes - {tree_info.get('nodes_count', 'N/A')}, Depth - {tree_info.get('depth', 'N/A')}")
        print(f"\nStatistics gathered in {time.time() - start_time:.4f} seconds.")

        start_time = time.time()
        analyzer.analyze_forest() # Ensure shared_nodes is populated
        # --- Mimic print_shared_nodes ---
        print("Big Forest Shared Nodes:")
        if analyzer.shared_nodes:
            for node_value, in_trees in analyzer.shared_nodes.items():
                print(f"  Node '{node_value}': found in {in_trees}")
        else:
            print("  No shared nodes found.")
        print(f"Shared nodes identified in {time.time() - start_time:.4f} seconds.")

        start_time = time.time()
        connections_big = analyzer.find_connections_between_roots()
        # --- Mimic print_connections_between_roots ---
        print("Big Forest Connections Between Roots:")
        if connections_big:
            for conn in connections_big:
                print(f"  Connection between {conn.get('root1','N/A')} and {conn.get('root2','N/A')}: Common nodes - {conn.get('common_nodes',[])}")
        else:
            print("  No direct connections found.")
        print(f"Connections found in {time.time() - start_time:.4f} seconds.")

        # Pathfinding in the large forest (example with the first tree's root)
        if big_forest[0]: # Ensure the first tree exists and is not None
            target_node_example = None
            # Attempt to find a valid target node more robustly
            if big_forest[0].children:
                if big_forest[0].children[0].children:
                    target_node_example = big_forest[0].children[0].children[0].value
                else:
                    target_node_example = big_forest[0].children[0].value
            else: # Fallback if no grandchildren or children
                target_node_example = big_forest[0].value

            if target_node_example:
                print(f"\nFinding shortest path to node '{target_node_example}' in the large forest...")
                start_time = time.time()
                shortest_path_big = analyzer.find_shortest_path_to_node(target_value=target_node_example)
                # --- Mimic print_shortest_path_to_node ---
                print(f"Shortest path to node '{target_node_example}':")
                if shortest_path_big:
                    print(f"  Tree: {shortest_path_big.get('tree','N/A')}")
                    print(f"  Path: {' -> '.join(map(str, shortest_path_big.get('path',[])))}")
                    print(f"  Length: {shortest_path_big.get('length','N/A')} nodes")
                else:
                    print(f"  Node '{target_node_example}' not found in any tree.")
                print(f"Shortest path found in {time.time() - start_time:.4f} seconds.")
        del analyzer, big_forest, stats_big, connections_big # Explicit cleanup
        if 'shortest_path_big' in locals(): del shortest_path_big
        gc.collect()

    print("\n🎯 DEMONSTRATION COMPLETE 🎯")
