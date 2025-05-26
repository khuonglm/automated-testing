from utils.random_generator import RandomGenerator


class APISequencer:
    def __init__(self, graph: dict[str, list[dict[str, str]]]):
        self.graph = graph

    def sequence(self):
        pass