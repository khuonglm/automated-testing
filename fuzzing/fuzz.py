from utils.random_generator import RandomGenerator
import random
from typing import Any

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

class APISequencer:
    def __init__(self, apis: list[Any]):
        self.apis = apis

    def sequence(self, length: int):
        apis = []
        for _ in range(length):
            apis.append(random.choice(list(range(len(self.apis)))))
        return apis

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

        url = url_template
        path_params = {}
        # Populate path parameters
        for param in path_params_schema:
            param_type = path_params_schema[param]
            if param_type == "<string>":
                path_params[param] = str(random_generator.generate_random_string())
            elif param_type == "<integer>":
                path_params[param] = str(random_generator.generate_random_int())
        
        # Populate query parameters
        query_params = {}
        for param in query_params_schema:
            param_type = query_params_schema[param]
            if param_type == "<string>":
                query_params[param] = str(random_generator.generate_random_string())
            elif param_type == "<integer>":
                query_params[param] = str(random_generator.generate_random_int())
            
        def fill_body(schema, current): 
            for param in schema:
                value = schema[param]
                if isinstance(value, dict):
                    current[param] = {}
                    fill_body(value, current[param])
                else:    
                    if value == "<string>":
                        current[param] = str(random_generator.generate_random_string())
                    elif value == "<integer>":
                        current[param] = str(random_generator.generate_random_int())

        body = {}
        fill_body(body_schema, body)

        # Populate headers parameters
        headers = {}
        for param in headers_schema:
            value = headers_schema[param]
            if value == "Token <token>":
                headers[param] = random_generator.generate_random_jwt_token()
            else:
                headers[param] = value
        
        return {
            "method": api["method"],
            "endpoint": url,
            "request": {
                "header": headers,
                "body": body,
                "path": path_params,
                "query": query_params
            },
            "replaces": {}
        }

    def fuzz_sequence(self, sequence: list[str]):
        fuzzed_sequence = []
        for idx in sequence:
            fuzzed_sequence.append(self.fuzz_api(self.apis[int(idx)]))
        return fuzzed_sequence

if __name__ == '__main__':
    import os
    import time
    import subprocess
    import json
    PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if os.path.exists(os.path.join(PATH, "test_cov", "stats_summary.json")):
        os.remove(os.path.join(PATH, "test_cov", "stats_summary.json"))

    curr_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    N   = 1000
    mod = 100
    for i in range(N):
        sequencer = APISequencer(example_apis)
        sequence = sequencer.sequence(200)
        fuzzer = Fuzzer(example_apis)
        fuzzed_sequence = fuzzer.fuzz_sequence(sequence)
        with open(os.path.join(PATH, "test", f'fuzzed_inputs.json'), 'w') as f:
            json.dump(fuzzed_sequence, f, indent=4)
        
        subprocess.run(["python", "linecoverage.py"], cwd=os.path.join(PATH, "evaluation"))

        if i % mod == 0 or i == N - 1:
            with open(os.path.join(PATH, "test_cov", "stats_summary.json")) as f:
                data = json.load(f)
            with open(os.path.join(PATH, "test_cov", f"stats_summary_{curr_time}_{i}.json"), 'w') as f:
                json.dump(data, f, indent=4)