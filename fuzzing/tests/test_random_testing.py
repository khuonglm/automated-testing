from ..utils.random_generator import *
from ..utils.adaptive_random_generator import *
import random

random_generator = RandomGenerator()
adaptive_random_generator = AdaptiveRandomGenerator(random_generator, 3)

random.seed(123)

class TestRandomGenerator:
    def test_generate_random_int(self):
        assert random_generator.generate_random_int() == 4164106

class TestDistances:
    def test_random_string(self):
        distance = levenshtein_distance
        N = 10
        adaptive_random_string_generator = adaptive_random_generator.generate_random_string()

        adaptive_random_samples = [next(adaptive_random_string_generator) for _ in range(10)]
        random_samples = [random_generator.generate_random_string() for _ in range(10)]
        random_distances = []
        adaptive_random_distances = []

        for i in range(N):
            for j in range(i, N):
                random_distances.append(distance(random_samples[i], random_samples[j]))
                adaptive_random_distances.append(distance(adaptive_random_samples[i], adaptive_random_samples[j])) 
        assert sum(random_distances) < sum(adaptive_random_distances)
