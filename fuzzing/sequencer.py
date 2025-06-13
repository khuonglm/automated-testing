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



class Sequencer:
    def __init__(self, graph: dict[str, list[dict[str, Any]]], apis: list[Any]):
        # Dependencies graph
        self.graph = graph
        # APIs list
        self.apis = apis
        # Build simplified adjacency list: {node: [dependent_api_indices]}
        self.adj_list = self._build_adjacency_list()

    def _build_adjacency_list(self) -> dict[str, list[str]]:
        adj_list = {}
        for node, dependencies in self.graph.items():
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
                else:
                    all_paths.append(current_path[:] + [dep_api])

        # Validate start_node
        if start_node not in self.adj_list:
            return []

        all_paths = []
        visited = {start_node}
        current_path = [start_node]
        _find_paths(start_node, visited, current_path, all_paths)
        return all_paths

    def _sample_path(self) -> list[str]:
        # Get all possible nodes (API indices)
        nodes = list(self.adj_list.keys())
        if not nodes:
            return []

        in_deg = {node: 0 for node in nodes}
        for node in nodes:
            for dep in self.adj_list[node]:
                in_deg[dep] += 1

        def _find_paths(node: str, visited: set[str], current_path: list[str], start_node: str):
            adj_list = self.adj_list.get(node, [])
            if node != start_node or random.random() < 0.05:
                random.shuffle(adj_list)

            for dep_api in adj_list:
                if dep_api not in visited:
                    visited.add(dep_api)
                    return _find_paths(dep_api, visited, current_path + [dep_api], start_node)
                if random.random() < 0.05:
                    return current_path[:] + [dep_api]

            return current_path[:]
 
        path = []
        for node in nodes:
            if in_deg[node] == 0:
                path += _find_paths(node, set(), [node], node)[:]
        return path

    def random_sequence(self, min_length: int, random_generator=RandomGenerator()) -> list[str]:
        """
        Generate a random sequence of APIs with a maximum length of max_length, allowing duplicates.
        The sequence always start with register and login, so max_length must be at least 3
        """
        assert min_length > 0, "min_length must be at least 1"
        path = []
        while len(path) < min_length:
            path = path + self._sample_path()
        visited_nodes = set(path)
        for node in list(self.adj_list.keys()):
            if node not in visited_nodes:
                path = path + [str(node)]
        return path


if __name__ == "__main__":
    with open('../preprocessing/docs/output/relations.json') as json_file:
        dependencies = json.load(json_file)
    
    sequencer = Sequencer(dependencies, example_apis)
    
    keys = sequencer.adj_list.keys()
    keys = sorted(keys)
    for key in keys:
        print(key, sequencer.adj_list[key])

    print("----------------------------------------------")

    for _ in range(3):
        sequence = sequencer.random_sequence(100)
        print(sequence)