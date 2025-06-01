from fuzzing.fuzz import *

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

class TestSequencer:
    def test_sequencer(self):
        sequencer = APISequencer(example_graph, example_apis)
        assert sequencer.sequence("dfs") == ['3', '4', '2', '1', '0']
        assert sequencer.sequence("bfs") == ['4', '3', '2', '1', '0']