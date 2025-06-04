import json
from typing import Any
from utils.random_generator import RandomGenerator
from sequencer import Sequencer
import datetime
import random

REUSE_THRESHOLD = 0.3
MAPPING_THRESHOLD = 0.8

class Fuzzer:
    def __init__(self, apis: list[Any], graph: dict[str, list[dict[str, Any]]], random_generator=RandomGenerator()):
        self.apis = apis
        self.random_generator = random_generator
        self.graph = graph

    def _set_nested_field(self, data: dict, field_path: str, value: Any) -> None:
        """Set a value in a nested dictionary using a dot-separated field path."""
        keys = field_path.split(".")
        current = data
        for key in keys[:-1]:
            # Handle array indexing like articles.[0]
            if key.startswith("[") and key.endswith("]"):
                index = int(key[1:-1])
                current = current.setdefault(index, {})
            else:
                current = current.setdefault(key, {})
        last_key = keys[-1]
        if last_key.startswith("[") and last_key.endswith("]"):
            index = int(last_key[1:-1])
            current[index] = value
        else:
            current[last_key] = value

    def _get_nested_field(self, data: dict, field_path: str) -> Any:
        """Get a value from a nested dictionary using a dot-separated field path."""
        keys = field_path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                if key.startswith("[") and key.endswith("]"):
                    index = int(key[1:-1])
                    current = current.get(list(current.keys())[index]) if index < len(current.keys()) else None
                else:
                    current = current.get(key)
            elif isinstance(current, list) and key.startswith("[") and key.endswith("]"):
                index = int(key[1:-1])
                current = current[index] if index < len(current) else None
            else:
                return None
        return current

    def _fill_body(self, schema: dict, is_register_start: bool = False) -> dict:
        """Populate the request body based on schema, handling register special case."""
        body = {}
        for param, value in schema.items():
            if isinstance(value, dict):
                body[param] = self._fill_body(value, is_register_start)
            elif isinstance(value, list):
                body[param] = [self.random_generator.generate_random_string() for _ in range(2)]
            else:
                if is_register_start and param in ["email", "password"]:
                    body[param] = "john.doe@example.com" if param == "email" else "password"
                elif param == "email":
                    body[param] = self.random_generator.generate_random_email()
                elif value == "<string>":
                    body[param] = self.random_generator.generate_random_string()
                elif value == "<integer>":
                    body[param] = self.random_generator.generate_random_int()
                else:
                    body[param] = value
        return body

    def _build_endpoint(self, url: str, path_params: dict, query_params: dict, replaces: dict) -> tuple[str, dict]:
        """Construct the full API endpoint URL"""
        endpoint = url

        # Replace path parameters and track which ones were used
        for param, value in path_params.items():
            if f"path.{param}" in replaces:
                continue
            placeholder = f"<{param}>"
            if placeholder in endpoint:
                endpoint = endpoint.replace(placeholder, str(value))
        
        for param, value in query_params.items():
            if f"query.{param}" in replaces:
                query_params[param] = f"<{param}>"
        
        if query_params:
            query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
            endpoint += f"?{query_string}"

        return endpoint

    def _get_dependency_mapping(self, sequence: list[str]) -> dict[str, list[dict]]:
        """Map each API index to dependencies from the previous API in the sequence."""
        dependency_map = {}
        for call_id, target_idx in enumerate(sequence):
            dependency_map[target_idx] = []
            if call_id == 0:
                continue  # First API has no predecessor
            source_idx = sequence[call_id - 1]
            dependencies = self.graph.get(source_idx, [])
            for dep in dependencies:
                if dep.get("related", False) and dep.get("relation", {}).get("to") == target_idx:
                    dependency_map[target_idx].append({
                        "source_idx": source_idx,
                        "field_mappings": dep.get("fieldMappings", [])
                    })
        return dependency_map

    def _simulate_response(self, api_idx: str, request_data: dict) -> dict:
        """Simulate an API response based on the API index and request data."""
        now = datetime.datetime.now().isoformat()
        simulated_response = {}
        if api_idx == "0":  # POST /api/users/login
            simulated_response = {
                "user": {
                    "bio": None,
                    "createdAt": now,
                    "email": self._get_nested_field(request_data, "body.user.email"),
                    "image": None,
                    "token": self.random_generator.generate_random_string(32),
                    "updatedAt": now,
                    "username": self.random_generator.generate_random_string()
                }
            }
        elif api_idx == "1":  # POST /api/users
            simulated_response = {
                "user": {
                    "bio": None,
                    "createdAt": now,
                    "email": self._get_nested_field(request_data, "body.user.email"),
                    "image": None,
                    "token": self.random_generator.generate_random_string(32),
                    "updatedAt": now,
                    "username": self._get_nested_field(request_data, "body.user.username")
                }
            }
        elif api_idx == "2":  # GET /api/user
            simulated_response = {
                "user": {
                    "bio": None,
                    "createdAt": now,
                    "email": self.random_generator.generate_random_string(),
                    "image": None,
                    "token": self.random_generator.generate_random_string(32),
                    "updatedAt": now,
                    "username": self.random_generator.generate_random_string()
                }
            }
        elif api_idx == "3":  # PUT /api/user
            simulated_response = {
                "user": {
                    "bio": self._get_nested_field(request_data, "body.user.bio") or None,
                    "createdAt": now,
                    "email": self._get_nested_field(request_data, "body.user.email"),
                    "image": None,
                    "token": "",
                    "updatedAt": now,
                    "username": self._get_nested_field(request_data, "body.user.username")
                }
            }
        elif api_idx == "4":  # GET /api/profiles/<username>
            simulated_response = {
                "profile": {
                    "bio": self.random_generator.generate_random_string(),
                    "email": self.random_generator.generate_random_string(),
                    "following": False,
                    "image": None,
                    "username": self._get_nested_field(request_data, "path.username")
                }
            }
        elif api_idx == "5":  # POST /api/profiles/<username>/follow
            simulated_response = {
                "profile": {
                    "bio": self.random_generator.generate_random_string(),
                    "email": self.random_generator.generate_random_string(),
                    "following": True,
                    "image": None,
                    "username": self._get_nested_field(request_data, "path.username")
                }
            }
        elif api_idx == "6":  # DELETE /api/profiles/<username>/follow
            simulated_response = {
                "profile": {
                    "bio": self.random_generator.generate_random_string(),
                    "email": self.random_generator.generate_random_string(),
                    "following": False,
                    "image": None,
                    "username": self._get_nested_field(request_data, "path.username")
                }
            }
        elif api_idx == "7":  # GET /api/articles
            simulated_response = {
                "articles": [
                    {
                        "author": {
                            "bio": None,
                            "email": self.random_generator.generate_random_string(),
                            "following": False,
                            "image": None,
                            "username": self.random_generator.generate_random_string()
                        },
                        "body": self.random_generator.generate_random_string(),
                        "createdAt": now,
                        "description": self.random_generator.generate_random_string(),
                        "favorited": False,
                        "favoritesCount": 0,
                        "slug": self.random_generator.generate_random_string(),
                        "tagList": [self.random_generator.generate_random_string() for _ in range(3)],
                        "title": self.random_generator.generate_random_string(),
                        "updatedAt": now
                    }
                ],
                "articlesCount": 1
            }
        elif api_idx == "8":  # GET /api/articles/feed
            simulated_response = {
                "articles": [
                    {
                        "author": {
                            "bio": None,
                            "email": self.random_generator.generate_random_string(),
                            "following": True,
                            "image": None,
                            "username": self.random_generator.generate_random_string()
                        },
                        "body": self.random_generator.generate_random_string(),
                        "createdAt": now,
                        "description": self.random_generator.generate_random_string(),
                        "favorited": True,
                        "favoritesCount": 0,
                        "slug": self.random_generator.generate_random_string(),
                        "tagList": [self.random_generator.generate_random_string() for _ in range(3)],
                        "title": self.random_generator.generate_random_string(),
                        "updatedAt": now
                    }
                ],
                "articlesCount": 1
            }
        elif api_idx == "9":  # GET /api/articles/<slug>
            simulated_response = {
                "article": {
                    "author": {
                        "bio": None,
                        "email": self.random_generator.generate_random_string(),
                        "following": False,
                        "image": None,
                        "username": self.random_generator.generate_random_string()
                    },
                    "body": self.random_generator.generate_random_string(),
                    "createdAt": now,
                    "description": self.random_generator.generate_random_string(),
                    "favorited": False,
                    "favoritesCount": 0,
                    "slug": self._get_nested_field(request_data, "path.slug"),
                    "tagList": [self.random_generator.generate_random_string() for _ in range(3)],
                    "title": self.random_generator.generate_random_string(),
                    "updatedAt": now
                }
            }
        elif api_idx == "10":  # POST /api/articles
            simulated_response = {
                "article": {
                    "author": {
                        "bio": None,
                        "email": self.random_generator.generate_random_string(),
                        "following": False,
                        "image": None,
                        "username": self.random_generator.generate_random_string()
                    },
                    "body": self._get_nested_field(request_data, "body.article.body"),
                    "createdAt": now,
                    "description": self._get_nested_field(request_data, "body.article.description"),
                    "favorited": False,
                    "favoritesCount": 0,
                    "slug": self.random_generator.generate_random_string(),
                    "tagList": self._get_nested_field(request_data, "body.article.tagList") or [self.random_generator.generate_random_string() for _ in range(3)],
                    "title": self._get_nested_field(request_data, "body.article.title"),
                    "updatedAt": now
                }
            }
        elif api_idx == "11":  # PUT /api/articles/<slug>
            simulated_response = {
                "article": {
                    "author": {
                        "bio": None,
                        "email": self.random_generator.generate_random_string(),
                        "following": False,
                        "image": None,
                        "username": self.random_generator.generate_random_string()
                    },
                    "body": self._get_nested_field(request_data, "body.article.body") or self.random_generator.generate_random_string(),
                    "createdAt": now,
                    "description": self._get_nested_field(request_data, "body.article.description") or self.random_generator.generate_random_string(),
                    "favorited": False,
                    "favoritesCount": 0,
                    "slug": self._get_nested_field(request_data, "path.slug"),
                    "tagList": [self.random_generator.generate_random_string() for _ in range(3)],
                    "title": self._get_nested_field(request_data, "body.article.title") or self.random_generator.generate_random_string(),
                    "updatedAt": now
                }
            }
        elif api_idx == "12":  # DELETE /api/articles/<slug>
            simulated_response = {}
        elif api_idx == "13":  # POST /api/articles/<slug>/comments
            simulated_response = {
                "comment": {
                    "author": {
                        "bio": None,
                        "email": self.random_generator.generate_random_string(),
                        "following": False,
                        "image": None,
                        "username": self.random_generator.generate_random_string()
                    },
                    "body": self._get_nested_field(request_data, "body.comment.body"),
                    "createdAt": now,
                    "id": self.random_generator.generate_random_int(),
                    "updatedAt": now
                }
            }
        elif api_idx == "14":  # GET /api/articles/<slug>/comments
            simulated_response = {
                "comments": [
                    {
                        "author": {
                            "bio": None,
                            "email": self.random_generator.generate_random_string(),
                            "following": False,
                            "image": None,
                            "username": self.random_generator.generate_random_string()
                        },
                        "body": self.random_generator.generate_random_string(),
                        "createdAt": now,
                        "id": self.random_generator.generate_random_int(),
                        "updatedAt": now
                    }
                ]
            }
        elif api_idx == "15":  # DELETE /api/articles/<slug>/comments/<cid>
            simulated_response = {}
        elif api_idx == "16":  # POST /api/articles/<slug>/favorite
            simulated_response = {
                "article": {
                    "author": {
                        "bio": None,
                        "email": self.random_generator.generate_random_string(),
                        "following": False,
                        "image": None,
                        "username": self.random_generator.generate_random_string()
                    },
                    "body": self.random_generator.generate_random_string(),
                    "createdAt": now,
                    "description": self.random_generator.generate_random_string(),
                    "favorited": True,
                    "favoritesCount": 1,
                    "slug": self._get_nested_field(request_data, "path.slug"),
                    "tagList": [self.random_generator.generate_random_string() for _ in range(3)],
                    "title": self.random_generator.generate_random_string(),
                    "updatedAt": now
                }
            }
        elif api_idx == "17":  # DELETE /api/articles/<slug>/favorite
            simulated_response = {
                "article": {
                    "author": {
                        "bio": None,
                        "email": self.random_generator.generate_random_string(),
                        "following": False,
                        "image": None,
                        "username": self.random_generator.generate_random_string()
                    },
                    "body": self.random_generator.generate_random_string(),
                    "createdAt": now,
                    "description": self.random_generator.generate_random_string(),
                    "favorited": False,
                    "favoritesCount": 0,
                    "slug": self._get_nested_field(request_data, "path.slug"),
                    "tagList": [self.random_generator.generate_random_string() for _ in range(3)],
                    "title": self.random_generator.generate_random_string(),
                    "updatedAt": now
                }
            }
        elif api_idx == "18":  # GET /api/tags
            simulated_response = {
                "tags": [self.random_generator.generate_random_string() for _ in range(3)]
            }
        return simulated_response

    def fuzz_single_sequence(self, sequence: list[str]) -> list[dict]:
        """Generate fuzzed API call inputs for a single sequence."""
        fuzzed_sequence = []
        dependency_map = self._get_dependency_mapping(sequence)
        call_data = {}  # Store request/response data for dependencies
        string_values = []
        int_values = []

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
                rand = random.random() 
                if rand < REUSE_THRESHOLD and len(string_values) > 0 and len(int_values) > 0:
                    if param_type == "<string>":
                        path_params[param] = string_values[random.randint(0, len(string_values) - 1)]
                    elif param_type == "<integer>":
                        path_params[param] = int_values[random.randint(0, len(int_values) - 1)]
                else:
                    if param_type == "<string>":
                        path_params[param] = self.random_generator.generate_random_string()
                        string_values.append(path_params[param])
                    elif param_type == "<integer>":
                        path_params[param] = self.random_generator.generate_random_int()
                        int_values.append(path_params[param])

            # Populate query parameters
            for param, param_type in api["query_parameters"].items():
                rand = random.random() 
                if rand < REUSE_THRESHOLD and len(string_values) > 0 and len(int_values) > 0:
                    if param_type == "<string>":
                        query_params[param] = string_values[random.randint(0, len(string_values) - 1)]
                    elif param_type == "<integer>":
                        query_params[param] = int_values[random.randint(0, len(int_values) - 1)]
                else:
                    if param_type == "<string>":
                        query_params[param] = self.random_generator.generate_random_string()
                        string_values.append(query_params[param])
                    elif param_type == "<integer>":
                        query_params[param] = self.random_generator.generate_random_int()
                        int_values.append(query_params[param])

            # Populate headers
            for param, value in api["headers"].items():
                if value == "<token>":
                    headers[param] = self.random_generator.generate_random_jwt_token()
                else:
                    headers[param] = value

            # Populate body
            is_register_start = api_idx == "1" and call_id == 0
            body = self._fill_body(api["body"], is_register_start)

            # Apply dependencies for non-first calls
            if call_id > 0:
                for dep in dependency_map.get(api_idx, []):
                    prev_api_idx = [t for t in range(call_id) if sequence[t] == dep["source_idx"]]
                    if len(prev_api_idx) > 0:
                        prev_api_idx = random.choice(prev_api_idx)
                        for mapping in dep["field_mappings"]:
                            source_field = mapping["source"]["fieldPath"]
                            source_phase = mapping["source"]["phase"]
                            target_field = mapping["target"]["fieldPath"]
                            target_location = mapping["target"]["location"]
                            target_key = f"{target_location}.{target_field}"

                            source_data = call_data[prev_api_idx]["request"] if source_phase == "request" else call_data[prev_api_idx]["response"]
                            value = self._get_nested_field(source_data, source_field)
                            if value is None:
                                value = self.random_generator.generate_random_string()

                            if target_location == "path":
                                # Remove < and > from target_field if present
                                clean_field = target_field.strip("<>")
                                path_params[clean_field] = value
                            elif target_location == "query":
                                query_params[target_field] = value
                            elif target_location == "header":
                                headers[target_field] = f"Bearer {value}" if target_field == "Authorization" else value
                            elif target_location == "body":
                                self._set_nested_field(body, target_field, value)
                            rand = random.random()
                            if rand < MAPPING_THRESHOLD:
                                replaces[target_key] = f"response.{{{prev_api_idx}}}.{source_field}"

            endpoint = self._build_endpoint(api["url"], path_params, query_params, replaces)

            # Store request data
            request_data = {
                "body": body,
                "path": path_params,
                "query": query_params,
                "headers": headers
            }

            # Simulate response
            simulated_response = self._simulate_response(api_idx, request_data)

            # Store call data
            call_data[call_id] = {
                "request": request_data,
                "response": simulated_response
            }

            # Construct fuzzed call
            fuzzed_call = {
                "method": api["method"],
                "endpoint": endpoint,
                "request": {
                    "body": body,
                    "headers": headers,
                    "path": path_params,
                    "query": query_params,
                    "replaces": replaces
                }
            }
            fuzzed_sequence.append(fuzzed_call)

        return fuzzed_sequence


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
        "headers": {
            "Content-Type": "application/json"
        },
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
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {},
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "PUT",
        "url": "/api/user",
        "headers": {
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {},
        "query_parameters": {},
        "body": {
            "user": {
                "username": "<string>",
                "email": "<string>",
                "bio": "<string>",
                "password": "<string>",
                "image": "<string>"
            }
        }
    },
    {
        "method": "GET",
        "url": "/api/profiles/<username>",
        "headers": {
            "Content-Type": "application/json"
        },
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
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {
            "username": "<string>"
        },
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "DELETE",
        "url": "/api/profiles/<username>/follow",
        "headers": {
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {
            "username": "<string>"
        },
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "GET",
        "url": "/api/articles",
        "headers": {
            "Content-Type": "application/json"
        },
        "path_parameters": {},
        "query_parameters": {
            "tag": "<string>",
            "author": "<string>",
            "favorited": "<string>",
            "limit": "<integer>",
            "offset": "<integer>"
        },
        "body": {}
    },
    {
        "method": "GET",
        "url": "/api/articles/feed",
        "headers": {
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {},
        "query_parameters": {
            "limit": "<integer>",
            "offset": "<integer>"
        },
        "body": {}
    },
    {
        "method": "GET",
        "url": "/api/articles/<slug>",
        "headers": {
            "Content-Type": "application/json"
        },
        "path_parameters": {
            "slug": "<string>"
        },
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "POST",
        "url": "/api/articles",
        "headers": {
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {},
        "query_parameters": {},
        "body": {
            "article": {
                "title": "<string>",
                "description": "<string>",
                "body": "<string>",
                "tagList": ["<string>"]
            }
        }
    },
    {
        "method": "PUT",
        "url": "/api/articles/<slug>",
        "headers": {
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {
            "slug": "<string>"
        },
        "query_parameters": {},
        "body": {
            "article": {
                "title": "<string>",
                "description": "<string>",
                "body": "<string>",
                "tagList": ["<string>"]
            }
        }
    },
    {
        "method": "DELETE",
        "url": "/api/articles/<slug>",
        "headers": {
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {
            "slug": "<string>"
        },
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "POST",
        "url": "/api/articles/<slug>/comments",
        "headers": {
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {
            "slug": "<string>"
        },
        "query_parameters": {},
        "body": {
            "comment": {
                "body": "<string>"
            }
        }
    },
    {
        "method": "GET",
        "url": "/api/articles/<slug>/comments",
        "headers": {
            "Content-Type": "application/json"
        },
        "path_parameters": {
            "slug": "<string>"
        },
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "DELETE",
        "url": "/api/articles/<slug>/comments/<cid>",
        "headers": {
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {
            "slug": "<string>",
            "cid": "<integer>"
        },
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "POST",
        "url": "/api/articles/<slug>/favorite",
        "headers": {
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {
            "slug": "<string>"
        },
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "DELETE",
        "url": "/api/articles/<slug>/favorite",
        "headers": {
            "Authorization": "<token>",
            "Content-Type": "application/json"
        },
        "path_parameters": {
            "slug": "<string>"
        },
        "query_parameters": {},
        "body": {}
    },
    {
        "method": "GET",
        "url": "/api/tags",
        "headers": {
            "Content-Type": "application/json"
        },
        "path_parameters": {},
        "query_parameters": {},
        "body": {}
    }
]

if __name__ == "__main__":
    import os
    import time
    import subprocess
    PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(PATH, "preprocessing", "docs", "output", "relations_2025-06-01_13-38-34.json")) as json_file:
        dependencies = json.load(json_file)

    if os.path.exists(os.path.join(PATH, "test_cov", "stats_summary.json")):
        os.remove(os.path.join(PATH, "test_cov", "stats_summary.json"))

    curr_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    N   = 100000
    mod = 5000
    for i in range(N):
        sequencer = Sequencer(dependencies, example_apis)
        sequence = sequencer.random_sequence(22)
        fuzzer = Fuzzer(example_apis, dependencies)
        inputs = fuzzer.fuzz_single_sequence(sequence)

        # Write inputs to a JSON file
        with open(os.path.join(PATH, "test", f'fuzzed_inputs.json'), 'w') as f:
            json.dump(inputs, f, indent=4)
        
        subprocess.run(["python", "linecoverage.py"], cwd=os.path.join(PATH, "evaluation"))

        if i % mod == 0 or i == N - 1:
            with open(os.path.join(PATH, "test_cov", "stats_summary.json")) as f:
                data = json.load(f)
            with open(os.path.join(PATH, "test_cov", f"stats_summary_{curr_time}_{i}.json"), 'w') as f:
                json.dump(data, f, indent=4)