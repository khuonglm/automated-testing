from fuzzing.utils.random_generator import RandomGenerator
from fuzzing.utils.adaptive_random_generator import AdaptiveRandomGenerator
from typing import Literal

example_graph = {
   "0": [
        {
            "api": "1",
            "related_fields": [
                {
                    "field_name1": "slug",
                    "where_to_take": "path_variable",
                    "where_to_put": "path_variable"
                }
            ]
        }
    ],
    "1": [
        {
            "api": "2",
            "related_fields": []
        },
        {
            "api": "3",
            "related_fields": []
        },
    ],
    "2": [
        {
            "api": "4",
            "related_fields": []
        },
    ],
}

class APISequencer:
    def __init__(self, graph: dict[str, list[dict[str, str]]]):
        self.graph = graph

    # Helper method for Depth-first Search
    def _dfs(self, node: str, visited: set[str], stack: list[str]):
        stack.append(node)
        visited.add(node)

        for dependency in self.graph.get(node, []):
            dep_api = dependency["api"]
            if dep_api not in visited:
                self._dfs(dep_api, visited, stack)
        
    # Depth-first Search
    def dfs(self) -> list[str]:
        visited = set()
        stack = []

        for node in self.graph:
            if node not in visited:
                self._dfs(node, visited, stack) 
        # Reverse so that dependent APIs are called last
        return stack[::-1]

    def bfs(self) -> list[str]:
        visited = set()
        queue = []
        stack = []

        for node in self.graph:
            queue.append(node)
            visited.add(node)
        while queue:
            node = queue.pop(0)
            stack.append(node)
            for dependency in self.graph.get(node, []):
                dep_api = dependency["api"]
                if dep_api not in visited:
                    queue.append(dep_api)
                    visited.add(dep_api)
        
        # Reverse so that dependent APIs are called last
        return stack[::-1]

    def sequence(self, method: Literal["dfs"] | Literal["bfs"] ="dfs"):
        if method == "dfs":
            ordered_sequence = self.dfs()
        elif method == "bfs":
            ordered_sequence = self.bfs()
        else:
            raise TypeError("method should be 'dfs' or 'bfs'.")

        print("call order: ", ordered_sequence)
        return ordered_sequence

if __name__ == '__main__':
    print("hello world")
    sequencer = APISequencer(example_graph)
    sequencer.sequence("bfs")

    