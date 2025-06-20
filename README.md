# Project Title: Network Graph Analyzer

## Description
This project is designed to analyze and visualize network graphs, with a specific focus on electrical networks. It takes a network model as input (in JSON format), builds a graph or tree representation, performs various analyses (such as finding paths and checking connectivity), and can visualize the graph.

## Project Structure

The project is organized into the following main directories:

- **`graph_analyzer/`**: Contains modules for creating, visualizing, and analyzing graphs.
  - `graph_creator.py`: Defines `GraphCreator` for building graph representations from network models.
  - `graph_visualizer.py`: Provides functionality to visualize graphs.
  - `multi_root_graph_analyzer.py`: Contains logic for analyzing graphs that may have multiple root nodes or be disconnected.
  - `connecting_graphs_checker.py`: Implements checks for connectivity between different parts of a graph or multiple graphs.
- **`model_processing/`**: Includes modules for loading, parsing, and processing the initial network model data.
  - `analyzer.py` / `analyzers.py`: Defines `NetworkAnalyzer` for parsing the input model and preparing it for graph/tree construction.
  - `models.py`: Likely contains data structures or classes representing the network model elements.
  - `tree_builder.py`: Defines `NetworkTreeBuilder` for constructing a tree structure from the processed model.
  - `comparator.py`: Possibly used for comparing different graph/tree structures.
  - `registry.py`: Might be used for managing or registering different types of model components or analyzers.
  - `utils.py`: Utility functions for model processing.
- **`tree_analyzer/`**: Contains modules specifically for creating and analyzing tree structures derived from the network model.
  - `tree_creator.py`: Defines `TreeCreator` for generating tree representations.
  - `multi_root_analyzer.py` / `multi_root_analyzer_optimazed.py`: Specialized analysis for tree structures, potentially handling forests or multiple trees.
  - `tree_construction.py`: Contains the `Node` class and logic for building the tree.
  - `visualize_forest_connection.py`: Tools for visualizing connections within a forest of trees.
- **`utils/`**: General utility modules used across the project.
  - `generate_init.py`: Possibly a script to auto-generate `__init__.py` files.
  - `tests.py`: Utility functions related to testing.
- **`example_data/`**: Contains example JSON files that can be used as input models.

**Key Files:**

- `main.py`: The main entry point for running analyses.
- `convert.py` / `example_data/convert.py`: Scripts likely used for converting data formats or preparing models.
- `examples.py`: May contain example usage of the project's functionalities.

## Main Functionality

This project provides a suite of tools to analyze electrical network models. Here's an overview of its capabilities:

- **Loading Network Models**: The system loads network configurations from JSON files. These files describe the components of the electrical network and their interconnections.
- **Graph/Tree Representation**: It processes the input model to build a graph (specifically, an undirected graph) or a tree structure. This representation is then used for further analysis.
    - The `model_processing` modules handle the initial parsing and conversion.
    - `graph_analyzer` and `tree_analyzer` then use this data to construct their respective graph or tree structures.
- **Network Analysis**:
    - **Pathfinding**: The system can find and display all paths, the shortest path, and the longest path between two specified nodes in the graph (as seen in `main.py` using `UndirectedGraphAnalyzer`).
    - **Connectivity Analysis**: It can analyze the connectivity of the graph, particularly for identifying how different systems or components are connected, especially in scenarios with multiple roots or disconnected subgraphs (using `UndirectedGraphConnectingAnalyzer`).
    - **Orphan Node Identification**: The analysis can identify nodes that are not connected to the main graph (orphan nodes).
- **Visualization**: The project includes capabilities to visualize the generated graphs, helping in understanding the network structure.
    - `GraphVisualizer` uses libraries like `networkx` and `matplotlib` to draw the graph.
    - `tree_analyzer/visualize_forest_connection.py` suggests capabilities for visualizing connections in tree/forest structures.

### How to Run

The primary way to run an analysis is by executing the `main.py` script.

```bash
python main.py
```

You would typically modify `main.py` to specify:
- `model_path`: The path to the input JSON model file.
- `out_path`: The path where output data (like the generated graph structure) should be saved.
- Specific nodes for pathfinding or other analysis parameters.

The script uses the `logging` module to output information about its progress and results.

## Input and Output

### Input
- **JSON Model File**: The primary input is a JSON file representing the electrical network model.
    - This file contains definitions of `elements` (like buses, lines, transformers, switches, systems, etc.) and their `connections`.
    - The structure typically includes:
        - `elements`: A dictionary where keys are element IDs and values are objects describing the element's `Type` and other properties.
        - `nodes` (or similar field): A structure describing how elements are interconnected, often forming a list of adjacencies or connections for each bus/node.
        - `roots` (or identified by the system): Specifies the root nodes or main systems in the model.
    - Example model files can be found in the `example_data/` directory.

### Output
- **Log Files/Console Output**: The script logs its operations and analysis results to the console. This includes information about the created graph, number of nodes, roots, and results of specific analyses like pathfinding.
- **JSON Output File**:
    - The `GraphCreator` (via `NetworkAnalyzer.save_tree`) saves the processed graph/tree structure to a JSON file specified by the `out_path` in `main.py`. This file typically contains:
        - `nodes`: A list of all node identifiers in the graph.
        - `roots`: A list of identified root nodes.
        - `tree` (or `graph`): An adjacency list representation of the graph, where each node maps to a list of its neighbors or children.
- **Graph Visualizations**:
    - If visualization functions are called (e.g., `GraphVisualizer.draw_graph()`), the project can generate and display plots of the network graph using `matplotlib`. These are typically shown in a new window or saved to a file if the code is modified to do so.

## How to Use the Code (Library Components)

While `main.py` provides a primary execution script, the components of this project can also be used programmatically.

### Example: Creating and Analyzing a Graph

Here's a conceptual example of how you might use `GraphCreator` and an analyzer:

```python
from graph_analyzer import GraphCreator, UndirectedGraphAnalyzer, GraphVisualizer

# Define paths for the model and output
model_path = 'example_data/your_model.json'
output_graph_path = 'results/your_model_graph.json'

# 1. Create the graph
graph_creator = GraphCreator(model_path, output_graph_path)
graph, roots = graph_creator.create_graph()
print(f"Graph created with {len(graph)} nodes and {len(roots)} roots: {roots}")

# 2. Analyze the graph
analyzer = UndirectedGraphAnalyzer(graph)

# Example: Find paths between two nodes
node1_id = "some_node_id_from_your_model" # Replace with actual ID
node2_id = "another_node_id_from_your_model" # Replace with actual ID

if node1_id in graph and node2_id in graph:
    print(f"Analyzing paths between {node1_id} and {node2_id}:")
    analyzer.print_all_paths(node1_id, node2_id)
    # analyzer.print_shortest_path(node1_id, node2_id)
    # analyzer.print_longest_path(node1_id, node2_id)
else:
    print(f"One or both nodes not found in the graph. Available nodes: {list(graph.keys())[:5]}")


# 3. Analyze connectivity (if applicable)
# from graph_analyzer import UndirectedGraphConnectingAnalyzer
# connecting_analyzer = UndirectedGraphConnectingAnalyzer(graph, roots)
# analysis_results = connecting_analyzer.analyze()
# print("Connectivity Analysis Results:", analysis_results)


# 4. Visualize the graph
# visualizer = GraphVisualizer(graph)
# visualizer.draw_graph() # This will typically show a plot
```

### Key Classes and Usage

- **`GraphCreator(model_path, out_path)`**:
    - `create_graph()`: Loads the model, processes it, and returns the graph (adjacency list) and list of root nodes. Saves the graph to `out_path`.
- **`UndirectedGraphAnalyzer(graph)`**:
    - `print_all_paths(node_A, node_B)`: Prints all paths between `node_A` and `node_B`.
    - `get_shortest_path(node_A, node_B)`: Returns the shortest path.
    - `get_longest_path(node_A, node_B)`: Returns the longest path.
- **`UndirectedGraphConnectingAnalyzer(graph, roots)`**:
    - `analyze()`: Performs connectivity analysis based on the provided roots and graph.
- **`GraphVisualizer(graph)`**:
    - `draw_graph()`: Renders a visual representation of the graph.
- **`model_processing.NetworkAnalyzer`**:
    - `analyze_network(model_path, output_path)`: Core function to load a model and build the tree/graph structure.
- **`tree_analyzer.TreeCreator(model_path, out_path)`**:
    - `create_tree()`: Creates a tree structure (list of `Node` objects) from the model.

Refer to the specific modules and classes for more detailed API information. The `examples.py` file might also contain usage demonstrations.

## Dependencies

Based on the source code, the project likely depends on the following Python libraries:

- **`networkx`**: Used for graph creation, manipulation, and algorithms (e.g., in `GraphVisualizer` and potentially underlying graph analysis).
- **`matplotlib`**: Used for plotting and visualizing graphs (e.g., in `GraphVisualizer`).

You may need to install these libraries if they are not already in your Python environment. You can typically install them using pip:

```bash
pip install networkx matplotlib
```

Other standard Python libraries are used but do not require separate installation. The project also relies heavily on the `json` module for data handling.
