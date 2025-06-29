import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

# sys.path.append removed, assuming project is run from root or PYTHONPATH is set
# For direct execution or package context, relative imports are preferred.
from model_processing import NetworkAnalyzer # NetworkModel and NetworkGraphBuilder are used by NetworkAnalyzer

import logging
# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GraphCreator:
    """
    Class for creating an undirected graph from an electrical network model.
    It orchestrates the process by using NetworkAnalyzer to parse and build the graph.

    Attributes:
        model_path (Path): Path to the input JSON model file.
        out_path (Path): Path where NetworkAnalyzer saves the processed graph data.
        result (Dict[str, Any]): The resulting graph (adjacency list).
        roots (List[str]): List of root node IDs identified in the graph.
    """
    def __init__(self, model_path: str | Path, out_path: str | Path):
        """
        Initializes the GraphCreator.

        Args:
            model_path (str | Path): Path to the JSON model file.
            out_path (str | Path): Path for saving the processed graph data by NetworkAnalyzer.

        Raises:
            FileNotFoundError: If the input model file does not exist.
        """
        self.model_path = Path(model_path)
        self.out_path = Path(out_path)

        if not self.model_path.exists():
            logger.error("Input file %s not found", self.model_path) # Translated logger message
            raise FileNotFoundError(f"Input file {self.model_path} not found")

        self.result: Dict[str, Any] = {} # Stores the graph (adjacency list)
        self.roots: List[str] = []      # Stores the root nodes
    
    @staticmethod
    def save_graph_to_json(file_path: Path, graph_data: Dict[str, Any]) -> None:
        """
        Saves graph data (adjacency list) to a JSON file named 'output_graph.json'.
        The file is saved in the parent directory of the provided `file_path`.
        This is a utility method and may not be used in the primary graph creation flow.

        Args:
            file_path (Path): A path determining the output directory.
                              The output file will be `file_path.parent / "output_graph.json"`.
            graph_data (Dict[str, Any]): The graph data (adjacency list) to save.
                                         Neighbor lists (if sets) are converted to lists.
        """
        # Convert sets to lists for JSON serialization if necessary
        adjacency_serializable = {
            node: list(neighbors) if isinstance(neighbors, set) else neighbors
            for node, neighbors in graph_data.items()
        }
        
        output_filename = file_path.parent / "output_graph.json"

        output_filename.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists

        with open(output_filename, 'w', encoding='utf-8') as file:
            json.dump(adjacency_serializable, file, indent=6, ensure_ascii=False)
        logger.info("Graph utility save: graph data saved to %s", output_filename) # Translated logger

    def load_graph_from_json(self, file_path: Path) -> Dict[str, set]:
        """
        Loads a graph (adjacency list) from a JSON file.
        Converts lists of neighbors from the JSON into sets for internal use.

        Args:
            file_path (Path): The path to the JSON file containing the graph.

        Returns:
            Dict[str, set]: The loaded graph as an adjacency list with sets of neighbors.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            adjacency_list_from_json = json.load(file)
        # Convert lists of neighbors back to sets
        graph = {node: set(neighbors) for node, neighbors in adjacency_list_from_json.items()}
        return graph

    def model_to_graph(self) -> Tuple[Dict[str, Any], List[str]]:
        """
        Converts the input model into an undirected graph by using NetworkAnalyzer.
        This method populates `self.result` (the graph) and `self.roots`.

        Returns:
            Tuple[Dict[str, Any], List[str]]: A tuple containing the graph
                                              (adjacency list) and a list of root node IDs.
        Raises:
            Exception: If an error occurs during model analysis or graph construction.
        """
        try:
            logger.info("Analyzing model %s to build graph structure", self.model_path) # Translated

            # NetworkAnalyzer is instantiated here.
            # Its build_network_structure method handles loading, preprocessing, and graph building.
            # self.out_path is used by build_network_structure to save its own output.
            analyzer_instance = NetworkAnalyzer()
            # processed_model_data is expected to be like:
            # {'graph': adj_list, 'roots': list_of_roots, 'all_nodes': ...}
            processed_model_data = analyzer_instance.build_network_structure(self.model_path, self.out_path)

            if 'graph' not in processed_model_data or 'roots' not in processed_model_data:
                logger.error( # Translated
                    "Analysis result from NetworkAnalyzer is missing 'graph' or 'roots' keys. Received: %s",
                    list(processed_model_data.keys())
                )
                # Original Russian error message was "Некорректный формат результата от NetworkAnalyzer.analyze_network"
                raise ValueError("Invalid format from NetworkAnalyzer.build_network_structure")

            self.result = processed_model_data['graph'] # This is the adjacency list
            self.roots = processed_model_data['roots']

            logger.info( # Translated
                "Graph construction complete. Main processed data (from NetworkAnalyzer) saved to %s",
                self.out_path
            )

        except Exception as e: # Catching a broad exception, consider more specific ones if possible
            logger.error("Error during graph construction from model: %s", e, exc_info=True) # Translated
            raise # Re-raise the exception after logging
        finally:
            logger.info("Model-to-graph conversion process finished for %s.", self.model_path) # Translated
        
        return self.result, self.roots
    
    def create_graph(self) -> Tuple[Dict[str, Any], List[str]]:
        """
        Creates and returns the undirected graph structure from the model.
        If the graph has not been created yet (i.e., self.result is empty),
        it calls `model_to_graph()` to build it.

        Returns:
            Tuple[Dict[str, Any], List[str]]: The graph (adjacency list) and a list of root node IDs.
        """
        if not self.result: # Check if self.result (graph) is empty
            self.model_to_graph()
        return self.result, self.roots
    
    def visualize_graph_with_print(self, graph_data: Dict[str, Any] | None = None) -> None:
        """
        Visualizes the graph in the console by printing its edges.
        Uses `self.result` if `graph_data` is not provided.

        Args:
            graph_data (Dict[str, Any] | None, optional): Adjacency list of the graph to visualize.
                                                          Defaults to None (uses self.result).
        """
        target_graph = graph_data if graph_data is not None else self.result
        if not target_graph:
            logger.warning("Graph for console visualization not found or is empty.") # Translated
            return

        printed_edges = set()
        logger.info("Console Graph Visualization (Edges):") # Translated
        for node, neighbors in target_graph.items():
            for neighbor in neighbors:
                # Sort to ensure uniqueness of edges like (A,B) vs (B,A) for printing
                edge = tuple(sorted((str(node)[:8], str(neighbor)[:8]))) # Show first 8 chars for brevity
                if edge not in printed_edges:
                    print(f"{edge[0]} --- {edge[1]}")
                    printed_edges.add(edge)

    def visualize_graph_with_plot(self, graph_data: Dict[str, Any] | None = None) -> None:
        """
        Visualizes the graph using networkx and matplotlib.
        Uses `self.result` if `graph_data` is not provided.

        Args:
            graph_data (Dict[str, Any] | None, optional): Adjacency list of the graph to visualize.
                                                          Defaults to None (uses self.result).
        """
        target_graph = graph_data if graph_data is not None else self.result
        if not target_graph:
            logger.warning("Graph for plotting not found or is empty.") # Translated
            return

        try:
            import networkx as nx
            import matplotlib.pyplot as plt
        except ImportError:
            logger.error("Libraries networkx or matplotlib are not installed. Visualization is not possible.") # Translated
            print("Please install networkx and matplotlib: `pip install networkx matplotlib`") # Translated
            return

        graph_nx = nx.Graph() # Create a new NetworkX graph
        for node, neighbors in target_graph.items():
            for neighbor in neighbors:
                graph_nx.add_edge(str(node), str(neighbor)) # Ensure nodes are strings for NetworkX

        if not graph_nx.nodes():
            logger.warning("Graph is empty after NetworkX conversion, nothing to visualize.") # Translated
            return

        plt.figure(figsize=(16, 12)) # Slightly larger figure size
        try:
            # k parameter adjusts distance between nodes, iterations for layout stability
            pos = nx.spring_layout(graph_nx, seed=42, k=0.20, iterations=30)
        except nx.NetworkXError: # Fallback for very small or specific graph types
            logger.warning("Spring layout failed, trying Kamada-Kawai layout.")
            pos = nx.kamada_kawai_layout(graph_nx)

        nx.draw(
            graph_nx, pos, with_labels=True,
            node_size=1200, node_color="skyblue",
            font_size=10, font_weight="bold",
            edge_color="gray", width=1.5,
            alpha=0.9 # Slight transparency
        )
        plt.title("Undirected Graph Visualization", fontsize=18) # Translated
        plt.axis("off") # Turn off axis numbers and ticks
        plt.tight_layout() # Adjust plot to ensure everything fits without overlapping
        plt.show()


if __name__ == "__main__":
    # Example usage when running this file directly (e.g., python -m graph_analyzer.graph_creator).
    # Ensure paths are correct relative to your execution location or use absolute paths.

    # Determine project root assuming this script is in graph_analyzer/
    current_script_path = Path(__file__).resolve()
    project_root = current_script_path.parent.parent

    # Example paths relative to the project root
    # Try to use the same default model as in main.py for consistency
    default_model_name = "three_system_model_with_orphans_nodes_and_connected_system_converted.json"
    fallback_model_name = "converted_three_system_model.json" # Fallback if primary default is missing

    default_model_path = project_root / 'example_data' / default_model_name
    if not default_model_path.exists():
        logger.info("Default model '%s' not found, trying fallback '%s'", default_model_name, fallback_model_name)
        default_model_path = project_root / 'example_data' / fallback_model_name

    # Define where GraphCreator (via NetworkAnalyzer) should save its primary output for this script run
    default_out_path_for_analyzer = project_root / 'results' / 'from_graph_creator_script' / 'processed_model_output.json'

    model_path_for_script = default_model_path
    if not default_model_path.exists():
        print(f"WARNING: Neither default model '{default_model_name}' nor fallback '{fallback_model_name}' found in example_data. "
              f"Please place a model file at {default_model_path} or edit the script.")
        # model_path_for_script = "path/to/your/model.json" # Placeholder if needed
        exit(1) # Exit if no model can be found for the test script

    out_path_for_script = default_out_path_for_analyzer

    print(f"Using model for script execution: {model_path_for_script}")
    print(f"Output path for NetworkAnalyzer's processed data (this script run): {out_path_for_script}")

    try:
        graph_creator_instance = GraphCreator(model_path_for_script, out_path_for_script)
        created_graph, graph_roots = graph_creator_instance.create_graph()

        if created_graph:
            print(f"Graph created successfully: {len(created_graph)} nodes, {len(graph_roots)} roots.")
            # Example: print first 5 roots if many
            # print(f"Roots: {graph_roots[:5]}{'...' if len(graph_roots) > 5 else ''}")
            # Example: print a sample of the graph
            if created_graph.items(): # Check if graph is not empty
               sample_node = list(created_graph.keys())[0]
               print(f"Sample node '{sample_node}': connected to {list(created_graph[sample_node])[:5]}")

            # Visualize using the built-in method
            print("Attempting to visualize the graph...")
            graph_creator_instance.visualize_graph_with_plot()
        else:
            print("Graph was not created or is empty.")

    except FileNotFoundError as e:
        print(f"ERROR: Model file not found. {e}")
    except Exception as e:
        print(f"An error occurred during graph creation or visualization: {e}")
        import traceback
        traceback.print_exc()

        