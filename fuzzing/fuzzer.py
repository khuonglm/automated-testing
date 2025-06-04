import json
from typing import Any
from utils.random_generator import RandomGenerator
from sequencer import MyAPISequencer

class Fuzzer:
    def __init__(self, apis: list[Any], graph: dict[str, list[dict[str, Any]]], random_generator=RandomGenerator()):
        self.apis = apis
        self.graph = graph
        self.random_generator = random_generator

    def _set_nested_field(self, data: dict, field_path: str, value: Any) -> None:
        keys = field_path.split(".")
        current = data
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value

    def _get_nested_field(self, data: dict, field_path: str) -> Any:
        keys = field_path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    def _fill_body(self, schema: dict, replaces: dict, call_id: int, simulated_data: dict) -> dict:
        body = {}
        for param, value in schema.items():
            if isinstance(value, dict):
                body[param] = self._fill_body(value, replaces, call_id, simulated_data)
            else:
                field_path = f"body.{param}" if param not in body else f"{param}"
                if value == "<string>":
                    body[param] = simulated_data.get(field_path, self.random_generator.generate_random_string())
                    replaces[field_path] = f"response.{call_id}.{param}"
                elif value == "<integer>":
                    body[param] = self.random_generator.generate_random_int()
                else:
                    body[param] = value
        return body

    def _build_endpoint(self, url: str, path_params: dict, query_params: dict) -> str:
        endpoint = url
        for param, value in path_params.items():
            endpoint = endpoint.replace(f"<{param}>", str(value))
        if query_params:
            query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
            endpoint += f"?{query_string}"
        return endpoint

    def _get_dependency_mapping(self, sequence: list[str]) -> dict[str, list[dict]]:
        dependency_map = {}
        for target_idx in sequence:
            dependency_map[target_idx] = []
            for source_idx, dependencies in self.graph.items():
                for dep in dependencies:
                    if dep.get("related", False) and dep["relation"]["to"] == target_idx:
                        dependency_map[target_idx].append({
                            "source_idx": source_idx,
                            "field_mappings": dep["fieldMappings"]
                        })
        return dependency_map

    def _simulate_response(self, api_idx: str, request_body: dict) -> dict:
        # Simulate a response based on the API index and request body
        simulated_response = {}
        if api_idx == "0":  # POST /api/users/login
            simulated_response = {
                "user": {
                    "token": self.random_generator.generate_random_string(32),
                    "email": self._get_nested_field(request_body, "user.email"),
                    "username": self.random_generator.generate_random_string()
                }
            }
        elif api_idx == "1":  # POST /api/users
            simulated_response = {
                "user": {
                    "username": self._get_nested_field(request_body, "user.username"),
                    "email": self._get_nested_field(request_body, "user.email"),
                    "password": self._get_nested_field(request_body, "user.password")
                }
            }
        elif api_idx == "2":  # GET /api/user
            simulated_response = {
                "user": {
                    "username": self.random_generator.generate_random_string(),
                    "email": self.random_generator.generate_random_string()
                }
            }
        elif api_idx == "3":  # PUT /api/user
            simulated_response = {
                "user": {
                    "username": self._get_nested_field(request_body, "user.username"),
                    "email": self._get_nested_field(request_body, "user.email"),
                    "bio": self._get_nested_field(request_body, "user.bio")
                }
            }
        elif api_idx == "4":  # GET /api/profiles/<username>
            simulated_response = {
                "profile": {
                    "username": self._get_nested_field(request_body, "path.username")
                }
            }
        elif api_idx == "5":  # POST /api/profiles/<username>/follow
            simulated_response = {
                "profile": {
                    "username": self._get_nested_field(request_body, "path.username"),
                    "following": True
                }
            }
        return simulated_response

    def fuzz_single_sequence(self, sequence: list[str]) -> list[dict]:
        """
        Generate fuzzed API call inputs for a single sequence, feeding data from previous calls.
        Returns a list of fuzzed API call dictionaries.
        """
        fuzzed_sequence = []
        dependency_map = self._get_dependency_mapping(sequence)
        simulated_data = {}  # Store request/response data for the sequence
        call_data = {}  # Store call-specific data for replacements

        for call_id, api_idx in enumerate(sequence):
            api = self.apis[int(api_idx)]
            if api["method"] not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                raise ValueError(f"Invalid method {api['method']}!")
            
            path_params = {}
            query_params = {}
            headers = {}
            replaces = {}

            # Populate path parameters
            for param, param_type in api["path_parameters"].items():
                if param_type == "<string>":
                    path_params[param] = self.random_generator.generate_random_string()
                elif param_type == "<integer>":
                    path_params[param] = self.random_generator.generate_random_int()
                else:
                    path_params[param] = param_type

            # Populate query parameters
            for param, param_type in api["query_parameters"].items():
                if param_type == "<string>":
                    query_params[param] = self.random_generator.generate_random_string()
                elif param_type == "<integer>":
                    query_params[param] = self.random_generator.generate_random_int()
                else:
                    query_params[param] = param_type

            # Populate headers
            for param, value in api["headers"].items():
                if value == "Token <token>":
                    headers[param] = f"Token {self.random_generator.generate_random_string(32)}"
                    replaces[f"headers.{param}"] = f"response.{call_id}.user.token"
                else:
                    headers[param] = value

            # Populate body with simulated data
            body = self._fill_body(api["body"], replaces, call_id, simulated_data)

            # Apply field mappings from dependencies
            for dep in dependency_map.get(api_idx, []):
                source_idx = dep["source_idx"]
                source_call_id = sequence.index(source_idx) if source_idx in sequence[:call_id] else -1
                if source_call_id >= 0:  # Source API is called before target
                    for mapping in dep["field_mappings"]:
                        source_field = mapping["source"]["fieldPath"]
                        source_phase = mapping["source"]["phase"]
                        target_field = mapping["target"]["fieldPath"]
                        target_location = mapping["target"]["location"]
                        target_key = f"{target_location}.{target_field}"

                        # Get source data from request or response
                        source_data = call_data[source_call_id]["request"] if source_phase == "request" else call_data[source_call_id]["response"]
                        value = self._get_nested_field(source_data, source_field)
                        if value is None:
                            value = self.random_generator.generate_random_string()

                        # Update target field
                        if target_location == "path":
                            path_params[target_field] = value
                        elif target_location == "query":
                            query_params[target_field] = value
                        elif target_location == "header":
                            headers[target_field] = f"Token {value}" if target_field == "Authorization" else value
                        elif target_location == "body":
                            self._set_nested_field(body, target_field, value)
                        replaces[target_key] = f"response.{source_call_id}.{source_field}"

            endpoint = self._build_endpoint(api["url"], path_params, query_params)
            
            # Simulate response for this API call
            request_data = {"body": body, "path": path_params, "query": query_params, "headers": headers}
            simulated_response = self._simulate_response(api_idx, request_data)
            
            # Store call data for future dependencies
            call_data[call_id] = {
                "request": request_data,
                "response": simulated_response
            }
            
            # Store simulated data for body fields
            for key, value in body.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        simulated_data[f"body.{key}.{subkey}"] = subvalue
                else:
                    simulated_data[f"body.{key}"] = value

            fuzzed_call = {
                "method": api["method"],
                "endpoint": endpoint,
                "request": {
                    "body": body,
                    "path_params": path_params,
                    "query_params": query_params,
                    "headers": headers,
                    "replaces": replaces
                }
            }
            fuzzed_sequence.append(fuzzed_call)
        
        return fuzzed_sequence

    def fuzz_sequences(self, sequences: list[list[str]]) -> list[list[dict]]:
        """
        Generate fuzzed API call inputs for each sequence, feeding data from previous calls.
        Returns a list of sequences, each containing a list of fuzzed API call dictionaries.
        """
        return [self.fuzz_single_sequence(sequence) for sequence in sequences]

    def fuzz_all_paths_to_leaves(self, start_node: str) -> list[list[dict]]:
        """
        Find all paths from start_node to leaf nodes and fuzz each path immediately as it is found.
        Returns a list of fuzzed sequences, each containing a list of fuzzed API call dictionaries.
        """
        fuzzed_results = []
        self.sequencer.find_all_paths_to_leaves_with_fuzzing(start_node, self, fuzzed_results)
        return fuzzed_results
    

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
            "Authorization": "<token>"
        },
        "path_parameters": {},
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "PUT",
        "url": "/api/user",
        "headers": {
            "Authorization": "<token>"
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
            "Authorization": "<token>"
        },
        "path_parameters": {
            "username": "<string>"
        },
        "query_parameters": {},
        "body": {}
    },
]


if __name__ == "__main__":
    with open('relations.json') as json_file:
        dependencies = json.load(json_file)

    sequencer = MyAPISequencer(dependencies, example_apis)
    sequences = sequencer.find_all_paths_to_leaves("1")

    fuzzer = Fuzzer(example_apis, dependencies)

    inputs = fuzzer.fuzz_sequences(['1', '0', '2', '3', '4', '5'])

    print(inputs)