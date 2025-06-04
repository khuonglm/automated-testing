import random
from typing import Literal, Any
import json

from utils.random_generator import RandomGenerator

example_apis = [
    {
        "method": "POST",
        "url": "/api/users/login",
        "headers": {
            "Content-Type": "application/json"
        },
        "path_parameters": {},
        "query_parameters": {},
        "body": {
            "user": {
                "email": "<string>",
                "password": "<string>"
            }
        }
    },
    {
        "method": "POST",
        "url": "/api/users",
        "headers": {},
        "path_parameters": {},
        "query_parameters": {},
        "body": {
            "user": {
                "username": "<string>",
                "email": "<string>",
                "password": "<string>"
            }
        }
    },
    {
        "method": "GET",
        "url": "/api/user",
        "headers": {
            "Authorization": "Token <token>"
        },
        "path_parameters": {},
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "PUT",
        "url": "/api/user",
        "headers": {
            "Authorization": "Token <token>"
        },
        "path_parameters": {},
        "query_parameters": {},
        "body": {
            "user": {
                "username": "<string>",
                "email": "<string>",
                "bio": "<string>",
                "password": "<string>"
            }
        }
    },
    {
        "method": "GET",
        "url": "/api/profiles/<username>",
        "headers": {},
        "path_parameters": {
            "username": "<string>"
        },
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "POST",
        "url": "/api/profiles/<username>/follow",
        "headers": {
            "Authorization": "Token <token>"
        },
        "path_parameters": {
            "username": "<string>"
        },
        "query_parameters": {},
        "body": {}
    },
]



class MyAPISequencer:
    def __init__(self, graph: dict[str, list[dict[str, Any]]], apis: list[Any]):
        self.graph = graph
        self.apis = apis
        # Build simplified adjacency list: {node: [dependent_api_indices]}
        self.adj_list = self._build_adjacency_list()

    def _build_adjacency_list(self) -> dict[str, list[str]]:
        adj_list = {}
        for node, dependencies in self.graph.items():
            # Only include nodes that have dependencies or are dependencies
            adj_list[node] = []
            for dep in dependencies:
                if dep.get("related", False):
                    dep_api = dep["relation"]["to"]
                    if dep["relation"]["from"] == node and dep_api != node:
                        adj_list[node].append(dep_api)
                    # Ensure the dependent API is in the adjacency list
                    if dep_api not in adj_list:
                        adj_list[dep_api] = []
        return adj_list

    def find_all_paths_to_leaves(self, start_node: str) -> list[list[str]]:
        """
        Find all possible paths from start_node to leaf nodes using DFS.
        A leaf node is a node with no unvisited outgoing dependencies.
        Returns a list of paths, where each path is a list of API indices.
        """
        def _find_paths(node: str, visited: set[str], current_path: list[str], all_paths: list[list[str]]):
            # Check if node is a leaf (no unvisited dependents)
            has_unvisited = False
            for dep_api in self.adj_list.get(node, []):
                if dep_api not in visited:
                    has_unvisited = True
                    break
            if not has_unvisited:
                all_paths.append(current_path[:])
                return

            # Explore each unvisited dependent API
            for dep_api in self.adj_list.get(node, []):
                if dep_api not in visited:
                    visited.add(dep_api)
                    current_path.append(dep_api)
                    _find_paths(dep_api, visited, current_path, all_paths)
                    current_path.pop()
                    visited.remove(dep_api)

        # Validate start_node
        if start_node not in self.adj_list:
            return []

        all_paths = []
        visited = {start_node}
        current_path = [start_node]
        _find_paths(start_node, visited, current_path, all_paths)
        return all_paths
    
    def random_sequence(self, max_length: int, random_generator=RandomGenerator()) -> list[str]:
        """
        Generate a random sequence of APIs with a maximum length of max_length, allowing duplicates.
        """
        if max_length < 1:
            raise ValueError("max_length must be at least 1")

        # Get all possible nodes (API indices)
        nodes = list(self.adj_list.keys())
        if not nodes:
            return []

        # Initialize the sequence with register and login
        sequence = ['1', '0']

        # Generate sequence up to max_length
        for _ in range(max_length - 2):
            # Randomly select a node
            selected_node = random.choice(self.adj_list[sequence[-1]])
            sequence.append(selected_node)

            # Optionally allow duplicates by not removing the selected node from available_nodes
            # Since duplicates are allowed, we don't modify available_nodes
        return sequence
    

if __name__ == "__main__":
    with open('relations_2025-06-01_13-38-34.json') as json_file:
        dependencies = json.load(json_file)
    
    sequencer = MyAPISequencer(dependencies, example_apis)
    
    keys = sequencer.adj_list.keys()
    keys = sorted(keys)
    for key in keys:
        print(key, sequencer.adj_list[key])

    print("----------------------------------------------")

    for _ in range(20):
        sequence = sequencer.random_sequence(20)
        print(sequence)