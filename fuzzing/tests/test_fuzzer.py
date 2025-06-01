from fuzzing.fuzz import *

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
        sequencer = APISequencer(example_graph)
        assert sequencer.sequence("dfs") == ['3', '4', '2', '1', '0']
        assert sequencer.sequence("bfs") == ['4', '3', '2', '1', '0']