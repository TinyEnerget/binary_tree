from typing import Dict, Any
from pathlib import Path
from .utils import load_json, save_json
from .preprocessor import ModelPreprocessor
from .comparator import TreeComparator
from .models import NetworkModel
from .graph_builder import NetworkGraphBuilder # Updated import


class NetworkAnalyzer:
    """
    Core class for analyzing electrical networks and building their graph structure.
    It orchestrates model loading, preprocessing, graph construction, and optional saving.
    """
    
    def __init__(self):
        """Initializes the NetworkAnalyzer with a ModelPreprocessor."""
        self.preprocessor = ModelPreprocessor()

    def load_and_preprocess_model(self, file_path: Path) -> Dict[str, Any]:
        """
        Loads a network model from a JSON file and applies preprocessing steps.

        Args:
            file_path (Path): The path to the JSON model file.

        Returns:
            Dict[str, Any]: The preprocessed model data.
        """
        model_data = load_json(file_path)
        # Apply transformations to the model via ModelPreprocessor
        processed_model_data = self.preprocessor.preprocess(model_data)
        return processed_model_data
    
    @staticmethod
    def save_processed_model(processed_data: Dict[str, Any], file_path: Path) -> None:
        """
        Saves the processed model data (including the graph structure) to a JSON file.

        Args:
            processed_data (Dict[str, Any]): The data to save.
            file_path (Path): The path where the JSON file will be saved.
        """
        save_json(file_path, processed_data)
    
    def build_network_structure(self, model_path: Path, output_path: Path | None = None) -> Dict[str, Any]:
        """
        Performs the full cycle: loading, preprocessing the model, and building its graph structure.
        Optionally saves the result.

        Args:
            model_path (Path): Path to the JSON model file.
            output_path (Path | None, optional): Path to save the resulting structure.
                                                 If None, the result is not saved. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary describing the network structure, typically including
                            'graph' (adjacency list), 'roots' (list of root IDs),
                            and 'all_nodes' (list of all node IDs).
        """
        # Load and preprocess the model
        processed_model_data = self.load_and_preprocess_model(model_path)

        # Create a NetworkModel object from the preprocessed data
        network_model_obj = NetworkModel(processed_model_data)
        
        # Build the graph structure using NetworkGraphBuilder
        builder = NetworkGraphBuilder(network_model_obj)
        
        # The primary path for GraphCreator uses an undirected graph representation.
        graph_adj_list, roots_list = builder.build_undirected_graph()

        # Construct the result dictionary.
        # 'graph' holds the adjacency list.
        # 'roots' holds the list of root node IDs.
        # 'all_nodes' can be sourced from preprocessed data or graph keys.
        result_structure = {
            'graph': graph_adj_list,
            'roots': roots_list,
            'all_nodes': processed_model_data.get('nodes_id', list(graph_adj_list.keys()))
        }

        # Save the result if an output path is provided
        if output_path:
            # Save the structure that will be returned
            self.save_processed_model(result_structure, output_path)
        
        return result_structure
    
    def compare_with_reference(self, result_structure: Dict[str, Any], reference_path: Path) -> bool:
        """
        Compares the resulting network structure with a reference JSON file.

        Args:
            result_structure (Dict[str, Any]): The generated network structure.
            reference_path (Path): Path to the JSON file containing the reference structure.

        Returns:
            bool: True if the structures are identical, False otherwise.
        """
        # Load reference data
        reference_data = load_json(reference_path)
        # Note: The reference data might need the same preprocessing if it's in raw format.
        # For a direct structural comparison, the reference should be in the processed format.
        return TreeComparator.compare(result_structure, reference_data)

# Note: The class method `analyze_network` has been effectively replaced by the instance method `build_network_structure`.
# Static methods for loading/saving are now primarily handled by `load_and_preprocess_model` (instance method)
# and `save_processed_model` (static method, but called by instance method), or directly via `utils.py`.
# NetworkAnalyzer now requires instantiation to be used.
