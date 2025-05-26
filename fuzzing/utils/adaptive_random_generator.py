import random
from collections.abc import Callable

from .random_generator import RandomGenerator
from .datatypes import *

# String distances
def hamming_distance(s1: str, s2: str) -> float:
    """Compute normalized Hamming distance between two strings of equal length."""
    if len(s1) != len(s2):
        raise ValueError("Strings are required to be of same length in Hamming distance.")
    return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2)) / len(s1)

# todo!
def levenshtein_distance(s1: str, s2: str) -> float:
    pass

class AdaptiveRandomGenerator:
    def __init__(
        self,
        generator: type[RandomGenerator],
        candidates_per_round: int = 3,
    ):
        self.generator = generator
        self.candidates_per_round = candidates_per_round
        self.string_reference_set = []
    
    def generate_random_string(
        self,
        length: int | None = None,
        chars: str = STR_CHARS,
        distance: Callable[[str, str], float] = hamming_distance
    ):
        # Seed element
        seed = self.generator.generate_random_string(length, chars)
        self.string_reference_set.append(seed)
        yield seed

        # Generate the rest adaptively
        while True:
            candidates = [self.generator.generate_random_string(length, chars) for _ in range(self.candidates_per_round)]
            # Find the candidate that is the furthest away from the reference set
            best_candidate = max(
                candidates,
                key=lambda c: min(distance(c, reference) for reference in self.string_reference_set)
            )
            self.string_reference_set.append(best_candidate)
            yield best_candidate