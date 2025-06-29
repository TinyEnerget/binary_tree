from pathlib import Path
import logging

# Assuming main.py is in the project root, sys.path modifications are not needed
# for imports from sub-packages like graph_analyzer.
from graph_analyzer import GraphCreator, UndirectedGraphAnalyzer, UndirectedGraphConnectingAnalyzer
# from graph_analyzer import GraphVisualizer # Uncomment if direct visualization from main is needed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration Constants ---
DEFAULT_MODEL_FILENAME = "three_system_model_with_orphans_nodes_and_connected_system_converted.json"
FALLBACK_MODEL_FILENAME = "converted_three_system_model.json" # Common example
DEFAULT_EXAMPLE_DATA_DIR = "example_data"
DEFAULT_OUTPUT_DIR_NAME = "results_from_main"

# Example Node IDs for path analysis (can be made configurable too)
EXAMPLE_NODE_A_ID = 'a9f8bc28-8b2f-4f4d-bb11-a76205ba5c07'
EXAMPLE_NODE_B_ID = '7911384c-1671-4ea0-a002-cdaa840e5c65'


def setup_paths(base_dir: Path, model_filename: str, example_data_dir: str, output_dir_name: str) -> tuple[Path | None, Path]:
    """
    Sets up and validates input model path and output path.
    Tries a fallback model if the primary one is not found.
    Returns (model_path, out_path). model_path can be None if no model is found.
    """
    model_path = base_dir / example_data_dir / model_filename
    out_path = base_dir / output_dir_name / model_filename # Output file named same as model

    logger.info(f"Attempting to use model: {model_path}")
    logger.info(f"Output path for NetworkAnalyzer result: {out_path}")

    if not model_path.exists():
        logger.error(f"Model file not found at {model_path}.")
        fallback_model_path = base_dir / example_data_dir / FALLBACK_MODEL_FILENAME
        if fallback_model_path.exists():
            logger.warning(f"Specified model not found. Trying fallback: {fallback_model_path}")
            model_path = fallback_model_path
        else:
            logger.error(f"Fallback model {fallback_model_path} also not found. Cannot proceed.")
            return None, out_path # Return None for model_path
    return model_path, out_path


def create_graph_from_model(model_path: Path, out_path: Path) -> tuple[GraphCreator | None, dict | None, list | None]:
    """
    Creates the graph using GraphCreator.
    Returns the graph_creator instance, the graph dictionary, and roots list.
    Returns (None, None, None) on failure.
    """
    logger.info(f"Starting graph creation process from model: {model_path}")
    graph_creator = GraphCreator(model_path, out_path)
    graph, roots = graph_creator.create_graph()

    if not graph:
        logger.error("Graph creation failed or resulted in an empty graph.")
        return None, None, None

    logger.info(f"Graph created successfully: {len(graph)} nodes, {len(roots)} roots identified.")
    logger.info(f"Identified roots: {roots}")
    return graph_creator, graph, roots


def perform_path_analysis(graph: dict, node_a_id: str, node_b_id: str):
    """
    Performs and prints path analyses (all paths, shortest, longest) between two nodes.
    """
    if not graph:
        logger.warning("Path analysis skipped: graph is empty or not provided.")
        return

    path_analyzer = UndirectedGraphAnalyzer(graph)

    if node_a_id not in graph or node_b_id not in graph:
        logger.warning(f"Path analysis: One or both nodes ({node_a_id}, {node_b_id}) not in graph.")
        logger.warning(f"Available nodes example: {list(graph.keys())[:5]}")
        return

    logger.info(f"Analyzing paths between {node_a_id} and {node_b_id}")
    path_analyzer.print_all_paths(node_a_id, node_b_id)

    # logger.info(f"Shortest path between {node_a_id} and {node_b_id}:")
    # path_analyzer.print_shortest_path(node_a_id, node_b_id)
    # logger.info(f"Longest path between {node_a_id} and {node_b_id}:")
    # path_analyzer.print_longest_path(node_a_id, node_b_id)


def perform_connectivity_analysis(graph: dict, roots: list):
    """
    Performs and prints connectivity analysis.
    """
    if not graph or not roots:
        logger.warning("Connectivity analysis skipped: graph or roots are empty/not provided.")
        return

    logger.info(f"Analyzing connectivity of systems based on roots: {roots}")
    connecting_analyzer = UndirectedGraphConnectingAnalyzer(graph, roots)
    connection_results = connecting_analyzer.analyze() # analyze() typically prints its findings
    # logger.info(f"Connectivity analysis results: {connection_results}") # If analyze returns structured data


def visualize_graph_interactive(graph_creator_instance: GraphCreator | None):
    """
    Uses GraphCreator's built-in plotting method for visualization if available.
    """
    if graph_creator_instance:
        logger.info("Attempting to display graph using GraphCreator's built-in plotter...")
        try:
            graph_creator_instance.visualize_graph_with_plot()
        except Exception as e:
            logger.error(f"Error during visualization with GraphCreator: {e}")
    else:
        logger.warning("Visualization skipped: GraphCreator instance not available.")


def run_analysis_workflow(
    model_filename: str,
    example_data_dir: str,
    output_dir: str,
    node_a: str,
    node_b: str,
    visualize: bool
    ):
    """
    Main workflow orchestrator.
    """
    base_path = Path(__file__).resolve().parent # Project root

    model_path, out_path = setup_paths(base_path, model_filename, example_data_dir, output_dir)

    if not model_path: # setup_paths returns None for model_path if it fails
        return

    graph_creator, graph, roots = create_graph_from_model(model_path, out_path)

    if not graph or not roots: # Check if graph creation was successful
        logger.error("Halting analysis due to graph creation failure.")
        return

    perform_path_analysis(graph, node_a, node_b)
    perform_connectivity_analysis(graph, roots)

    if visualize:
        visualize_graph_interactive(graph_creator)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Network Graph Analyzer")
    parser.add_argument(
        "--model_file",
        type=str,
        default=DEFAULT_MODEL_FILENAME,
        help=f"Filename of the model in the example_data directory (default: {DEFAULT_MODEL_FILENAME})"
    )
    parser.add_argument(
        "--example_dir",
        type=str,
        default=DEFAULT_EXAMPLE_DATA_DIR,
        help=f"Directory containing example model files, relative to project root (default: {DEFAULT_EXAMPLE_DATA_DIR})"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR_NAME,
        help=f"Directory where processed graph data will be saved, relative to project root (default: {DEFAULT_OUTPUT_DIR_NAME})"
    )
    parser.add_argument("--node_a", type=str, default=EXAMPLE_NODE_A_ID, help="ID of the first node for path analysis")
    parser.add_argument("--node_b", type=str, default=EXAMPLE_NODE_B_ID, help="ID of the second node for path analysis")
    parser.add_argument("--visualize", action="store_true", help="Enable interactive graph visualization")

    args = parser.parse_args()

    logger.info("Application started with arguments: %s", args)

    run_analysis_workflow(
        model_filename=args.model_file,
        example_data_dir=args.example_dir,
        output_dir=args.output_dir,
        node_a=args.node_a,
        node_b=args.node_b,
        visualize=args.visualize
    )

    logger.info("Application finished.")