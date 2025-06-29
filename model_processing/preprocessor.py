from typing import Dict, Any

class ModelPreprocessor:
    """
    Handles preprocessing of the raw network model data.
    This includes restructuring nodes and identifying root elements.
    """

    @staticmethod
    def rewrite_nodes(model: dict) -> dict:
        """
        Rewrites the node structure in the model, focusing on 'bus' type elements.
        The logic aims to consolidate connections around 'bus' elements and then
        clean these connections by removing self-references.

        Args:
            model (dict): The network model data.

        Returns:
            dict: The model data with a rewritten 'nodes' section.
        """
        # This logic seems complex and might benefit from further clarification
        # of its original intent for specific edge cases.
        # Current behavior is preserved with added English comments.

        # Step 1: Collect connections related to 'bus' elements.
        # If a key is a 'bus', its connections are taken.
        # If a key is not a 'bus' but connects to a 'bus', that 'bus' inherits
        # the connections of the original key.
        bus_related_connections = {}
        if 'nodes' in model and isinstance(model['nodes'], dict):
            for key, value in model['nodes'].items():
                is_key_bus = model.get('elements', {}).get(key, {}).get('Type') == 'bus'

                if is_key_bus: # If the key is a 'bus'
                    bus_related_connections[key] = value
                else: # If the key is not a 'bus', but connects to a 'bus' in its list of connections
                    for item_id in value: # Iterate through items connected to the current key
                        # If a connected item is a 'bus'
                        if model.get('elements', {}).get(item_id, {}).get('Type') == 'bus':
                            # The connections of the original non-bus key are attributed to this bus.
                            # This might overwrite if multiple non-bus keys point to the same bus,
                            # unless the bus was already a primary key.
                            if item_id not in bus_related_connections:
                                bus_related_connections[item_id] = value

        # Step 2: Clean the connections for the identified 'bus'-related entries.
        # For each 'bus' (now a key in bus_related_connections), create a new list
        # of its connections, excluding any self-references.
        clear_nodes = {}
        for key, value in bus_related_connections.items():
            new_value = []
            for item in value:
                if key != item: # Exclude self-reference
                    new_value.append(item)
            clear_nodes[key] = new_value

        model['nodes'] = clear_nodes # Update the model's 'nodes' section
        return model

    @staticmethod
    def find_root_nodes(model: dict) -> dict:
        """
        Identifies root nodes (elements of type 'system') within the model
        and adds them to model['roots']. Also compiles a list of all unique
        node identifiers involved in connections into model['nodes_id'].

        Args:
            model (dict): The network model data.

        Returns:
            dict: The model data updated with 'roots' and 'nodes_id' lists.
        """
        all_connected_nodes = set()
        if 'nodes' in model and isinstance(model['nodes'], dict):
            for key, connected_list in model['nodes'].items():
                all_connected_nodes.add(key)
                all_connected_nodes.update(connected_list)

        roots = []
        if 'elements' in model and isinstance(model['elements'], dict):
            # Iterate over all nodes participating in connections to find systems
            for node_id in all_connected_nodes:
                element_details = model['elements'].get(node_id)
                if element_details and element_details.get('Type') == 'system':
                    roots.append(node_id)

        model['roots'] = sorted(list(set(roots))) # Sort for consistency
        model['nodes_id'] = sorted(list(all_connected_nodes)) # Sort for consistency
        return model

    def preprocess(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies all preprocessing steps to the model data.
        """
        model_data = self.rewrite_nodes(model_data)
        model_data = self.find_root_nodes(model_data)
        return model_data
