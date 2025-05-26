import random
from collections.abc import Callable

from .random_generator import RandomGenerator
from .datatypes import *

# String distances
def hamming_distance(s1: str, s2: str) -> float:
    """Number of positions where the corresponding symbols differ between 2 strings of equal length."""
    if len(s1) != len(s2):
        raise ValueError("Strings are required to be of same length in Hamming distance.")
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

# todo!
def levenshtein_distance(s1: str, s2: str) -> float:
    """
    The minimum number of edits (insertions, deletions, and substitutions)
    required to change s1 into s2.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

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
        distance: Callable[[str, str], float] = levenshtein_distance
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