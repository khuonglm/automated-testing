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
    def base_test(self, random_generate, adaptive_generate, distance, N=10):
        adaptive_random_samples = [adaptive_generate() for _ in range(N)]
        random_samples = [random_generate() for _ in range(N)]
        random_distances = []
        adaptive_random_distances = []

        for i in range(N):
            for j in range(i, N):
                random_distances.append(distance(random_samples[i], random_samples[j]))
                adaptive_random_distances.append(distance(adaptive_random_samples[i], adaptive_random_samples[j])) 
        assert sum(random_distances) < sum(adaptive_random_distances)

    def test_random_strings(self, distance=levenshtein_distance):
        adaptive_random_string_generator = adaptive_random_generator.generate_random_string()
        self.base_test(lambda: random_generator.generate_random_string(), lambda: next(adaptive_random_string_generator), distance)
    
    def test_random_ints(self, distance=lambda i1, i2: abs(i1 - i2)):
        adaptive_random_int_generator = adaptive_random_generator.generate_random_int()
        self.base_test(lambda: random_generator.generate_random_int(), lambda: next(adaptive_random_int_generator), distance)
    
    def test_random_floats(self, distance=lambda i1, i2: abs(i1 - i2)):
        adaptive_random_float_generator = adaptive_random_generator.generate_random_float()
        self.base_test(lambda: random_generator.generate_random_float(), lambda: next(adaptive_random_float_generator), distance)
