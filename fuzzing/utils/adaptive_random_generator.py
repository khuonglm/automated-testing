from collections.abc import Callable
from collections import deque
from typing import Any

from .random_generator import RandomGenerator
from .datatypes import *

import random

# String distances
def hamming_distance(s1: str, s2: str) -> int:
    """Number of positions where the corresponding symbols differ between 2 strings of equal length."""
    if len(s1) != len(s2):
        raise ValueError("Strings are required to be of same length in Hamming distance.")
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

def levenshtein_distance(s1: str, s2: str) -> int:
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
    MIN_LENGTH = 1
    MAX_LENGTH = 100
    
    def __init__(
        self,
        generator: type[RandomGenerator],
        candidates_per_round: int = 5,
        max_reference_set_size = 10
    ):
        self.generator = generator
        # Number of candidates to choose the next input from
        self.candidates_per_round = candidates_per_round
        # Maximum size of reference set. If set to `None`, the reference set may grow to an arbitrary length.
        self.max_reference_set_size = max_reference_set_size
    
    def generate_random_length(self) -> int:
        return random.randint(self.MIN_LENGTH, self.MAX_LENGTH)

    # Primitives

    def generate_random_bool(self):
        while True:
            yield self.generator.generate_random_bool()
    
    def generate_random_string(
        self,
        length: int | None = None,
        chars: str = STR_CHARS,
        distance: Callable[[str, str], int] = levenshtein_distance,
    ):
        return self.generate_random(lambda: self.generator.generate_random_string(length, chars), distance, deque([], maxlen=self.max_reference_set_size))
    
    def generate_random_int(
        self,
        length: int | None = None,
        chars: str = INT_CHARS,
        distance: Callable[[int, int], int] = lambda i1, i2: abs(i1 - i2),
    ):
        return self.generate_random(lambda: self.generator.generate_random_int(length, chars), distance, deque([], maxlen=self.max_reference_set_size))
    
    def generate_random_float(
        self,
        length: int | None = None,
        chars: str = INT_CHARS,
        distance: Callable[[int, int], int] = lambda i1, i2: abs(i1 - i2),
    ):
        return self.generate_random(lambda: self.generator.generate_random_float(length, chars), distance, deque([], maxlen=self.max_reference_set_size))
    
    # Objects

    def generate_random_list(self, length: int | None = None, obj: any = None):
        if isinstance(obj, str):
            generator = self.generate_random_string(None, STR_CHARS_NO_SPECIAL)
        elif isinstance(obj, int):
            generator = self.generate_random_int(None, INT_CHARS)
        elif isinstance(obj, float):
            generator = self.generate_random_float(None, INT_CHARS)
        elif isinstance(obj, list):
            generator = self.generate_random_list(None, obj[0])
        elif isinstance(obj, dict):
            generator = self.generate_random_dict(obj)
        elif isinstance(obj, bool):
            generator = self.generate_random_bool()
        else:
            raise TypeError("obj must have a valid type")

        while True:
            if length is None:
                length = self.generate_random_length() 

            yield [next(generator) for _ in range(length)]
    
    def generate_random_dict(self, obj: dict[str, any]):
        if not isinstance(obj, dict):
            raise TypeError("obj must be a dictionary.")

        generator_map = {}
        for key, value in obj.items():
            if isinstance(value, str):
                generator_map[key] = self.generate_random_string(None, STR_CHARS_NO_SPECIAL)
            elif isinstance(value, int):
                generator_map[key] = self.generate_random_int(None, INT_CHARS)
            elif isinstance(value, float):
                generator_map[key] = self.generate_random_float(None, INT_CHARS)
            elif isinstance(value, list):
                generator_map[key] = self.generate_random_list(None, value[0])
            elif isinstance(value, dict):
                generator_map[key] = self.generate_random_dict(value)
            elif isinstance(value, bool):
                generator_map[key] = self.generate_random_bool()
            else:
                raise TypeError("obj must have a valid type")
            
        while True:
            dic = {}
            for key, value in obj.items():
                dic[key] = next(generator_map[key])
            yield dic

    def generate_random(self, generate: Callable[[], Any], distance: Callable[[Any, Any], float | int], reference_set: deque[Any]):
        # Seed element
        seed = generate()
        reference_set.append(seed)
        yield seed

        # Generate the rest adaptively
        while True:
            candidates = [generate() for _ in range(self.candidates_per_round)]
            # Find the candidate that is the furthest away from the reference set
            best_candidate = max(
                candidates,
                key=lambda c: min(distance(c, reference) for reference in reference_set)
            )
            reference_set.append(best_candidate)
            yield best_candidate