import json
from typing import Any
from utils.random_generator import RandomGenerator
from sequencer import Sequencer
import datetime
import random

FAULT_INJECTION_THRESHOLD = 0.2

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

    def _fill_body(self, schema: dict) -> dict:
        """Populate the request body based on schema, handling register special case."""
        body = {}
        for param, value in schema.items():
            if isinstance(value, dict):
                body[param] = self._fill_body(value)
            elif isinstance(value, list):
                body[param] = [self.random_generator.generate_random_string() for _ in range(2)]
            else:
                if param == "email":
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

    def fuzz_single_sequence(self, sequence: list[str], fault_injection: bool = False) -> list[dict]:
        """Generate fuzzed API call inputs for a single sequence."""
        fuzzed_sequence = []
        call_data = {}  # Store request/response data for dependencies
        used_values = {}

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
                if fault_injection and rand < FAULT_INJECTION_THRESHOLD and param in used_values:
                    if param_type == "<string>":
                        path_params[param] = random.choice(used_values[param])
                    elif param_type == "<integer>":
                        path_params[param] = random.choice(used_values[param])
                else:
                    if param_type == "<string>":
                        path_params[param] = self.random_generator.generate_random_string()
                    elif param_type == "<integer>":
                        path_params[param] = self.random_generator.generate_random_int()

                    if param not in used_values:
                        used_values[param] = []
                    used_values[param].append(path_params[param])

            # Populate query parameters
            for param, param_type in api["query_parameters"].items():
                rand = random.random() 
                if fault_injection and rand < FAULT_INJECTION_THRESHOLD and param in used_values:
                    if param_type == "<string>":
                        query_params[param] = random.choice(used_values[param])
                    elif param_type == "<integer>":
                        query_params[param] = random.choice(used_values[param])
                else:   
                    if param_type == "<string>":
                        query_params[param] = self.random_generator.generate_random_string()
                    elif param_type == "<integer>":
                        query_params[param] = self.random_generator.generate_random_int()

                    if param not in used_values:
                        used_values[param] = []
                    used_values[param].append(query_params[param])

            # Populate headers
            for param, value in api["headers"].items():
                if value == "<token>":
                    headers[param] = self.random_generator.generate_random_jwt_token()
                else:
                    headers[param] = value

            # Populate body
            body = self._fill_body(api["body"])

            # Apply dependencies for non-first calls
            if call_id > 0:
                found = False
                for idx, prev_api_idx in enumerate(sequence[:call_id][::-1]):
                    for dep in self.graph[prev_api_idx]:
                        if dep["related"] and dep["relation"]["to"] == api_idx:
                            # print(prev_api_idx, api_idx)
                            for mapping in dep["fieldMappings"]:
                                target_field = mapping["target"]["fieldPath"]
                                target_location = mapping["target"]["location"]
                                target_key = f"{target_location}.{target_field}"
                                source_key = f"{mapping['source']['phase']}.{{{call_id - idx - 1}}}.{mapping['source']['location']}.{mapping['source']['fieldPath']}"

                                if (not fault_injection) or random.random() > FAULT_INJECTION_THRESHOLD:
                                    replaces[target_key] = source_key
                                    # print(target_key, source_key)

                            found = True
                            break

                    if found:
                        break

            # Store request data
            request_data = {
                "body": body,
                "path": path_params,
                "query": query_params,
                "header": headers
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
                "endpoint": api["url"],
                "request": {
                    "body": body,
                    "header": headers,
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
    with open(os.path.join(PATH, "preprocessing", "docs", "output", "relations.json")) as json_file:
        dependencies = json.load(json_file)

    if os.path.exists(os.path.join(PATH, "test_cov", "stats_summary.json")):
        os.remove(os.path.join(PATH, "test_cov", "stats_summary.json"))

    curr_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    N   = 1000
    mod = 100
    for i in range(N):
        sequencer = Sequencer(dependencies, example_apis)
        sequence = sequencer.random_sequence(200)
        fuzzer = Fuzzer(example_apis, dependencies)
        inputs = fuzzer.fuzz_single_sequence(sequence, fault_injection=False)

        # Write inputs to a JSON file
        with open(os.path.join(PATH, "test", f'fuzzed_inputs.json'), 'w') as f:
            json.dump(inputs, f, indent=4)

        subprocess.run(["python", "linecoverage.py"], cwd=os.path.join(PATH, "evaluation"))

        if i % mod == 0 or i == N - 1:
            with open(os.path.join(PATH, "test_cov", "stats_summary.json")) as f:
                data = json.load(f)
            with open(os.path.join(PATH, "test_cov", f"stats_summary_{curr_time}_{i}.json"), 'w') as f:
                json.dump(data, f, indent=4)