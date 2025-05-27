from utils.random_generator import RandomGenerator
from utils.adaptive_random_generator import AdaptiveRandomGenerator

class APISequencer:
    def __init__(self, graph: dict[str, list[dict[str, str]]]):
        self.graph = graph

    def sequence(self):
        pass