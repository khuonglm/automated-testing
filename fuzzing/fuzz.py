from utils.random_generator import RandomGenerator
from utils.adaptive_random_generator import AdaptiveRandomGenerator
from typing import Literal, Any
import random
import requests
from os import path
import re

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
    def __init__(self, graph: dict[str, list[dict[str, str]]], apis: list[Any]):
        self.graph = graph
        self.apis = apis

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
    
    # def random(self) -> list[str]:
    #     apis = [str(x) for x in range(len(self.apis))]
    #     random.shuffle(apis)
    #     return apis

    def sequence(self, method: Literal["dfs"] | Literal["bfs"] = "dfs"):
        match method:
            case "dfs":
                ordered_sequence = self.dfs()
            case "bfs":
                ordered_sequence = self.bfs()
            # case "random":
            #     ordered_sequence = self.random()
            case _:
                raise TypeError("invalid method.")

        # print("call order: ", ordered_sequence)
        return ordered_sequence

class Fuzzer:
    def __init__(self, apis):
        self.apis = apis

    def fuzz_api(self, api, random_generator = RandomGenerator()):
        if api["method"] not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            raise ValueError("Invalid method {method}!")  
        method = api["method"].lower()
        path_params_schema = api["path_parameters"]
        query_params_schema = api["query_parameters"]
        url_template = api["url"]
        body_schema = api["body"]
        headers_schema = api["headers"]

        while True:
            url = url_template
            # Populate path parameters
            for param in path_params_schema:
                param_type = path_params_schema[param]
                match param_type:
                    case "<string>":
                        url = url.replace("<{param}>", random_generator.generate_random_string())
                    case "<integer>":
                        url = url.replace("<{param}>", random_generator.generate_random_int())
            
            # Populate query parameters
            query_params = {}
            for param in query_params_schema:
                param_type = path_params_schema[param]
                match param_type:
                    case "<string>":
                        query_params[param] = random_generator.generate_random_string()
                    case "<integer>":
                        query_params[param] = random_generator.generate_random_int()
             

            # Fuzz a dictionary. 
            # Example: body_schema = {
            #     "article": {
            #         "slug": "<string>",
            #         "date": {
            #             "month": "<string>",
            #             "day": "<integer>",
            #         }
            #     },
            #     "content": "<string>"
            # }
            def fill_body(schema, current): 
                for param in schema:
                    value = schema[param]
                    if isinstance(value, dict):
                        current[param] = {}
                        fill_body(value, current[param])
                    else:    
                        match value:
                            case "<string>":
                                current[param] = random_generator.generate_random_string()
                            case "<integer>":
                                current[param] = random_generator.generate_random_int()

            body = {}
            fill_body(body_schema, body)

             # Populate headers parameters
            headers = {}
            for param in headers_schema:
                value = headers_schema[param]
                match value:
                    case "Token <token>":
                        headers[param] = "Token " + random_generator.generate_random_string()
                    case _:
                        headers[param] = value

            self.call_api(method, url, headers=headers, body=body)         

    def call_api(self, method: str, url: str, headers, body, baseurl="http://localhost:5000"):
        url = path.join(baseurl, url.lstrip('/'))
        request = getattr(requests, method)
        return request(url, headers=headers, data=body)

    def fuzz_sequence(self, sequence: list[str]):
        sequence = [int(idx) for idx in sequence]
        for idx in sequence:
            self.fuzz_api(self.apis[idx])

if __name__ == '__main__':
    sequencer = APISequencer(example_graph, example_apis)
    sequencer.sequence("dfs")
    fuzzer = Fuzzer(example_apis)
    print(fuzzer.fuzz_api(example_apis[2]))
    # print(fuzzer.call_api(example_apis[0], "http://localhost:5000"))

