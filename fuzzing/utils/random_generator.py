import random

from .datatypes import *
    
class RandomGenerator:
    MIN_LENGTH = 1
    MAX_LENGTH = 100

    def __init__(self):
        pass

    def generate_random_length(self) -> int:
        return random.randint(self.MIN_LENGTH, self.MAX_LENGTH)

    def generate_random_bool(self) -> bool:
        return random.choice(BOOL_CHARS)

    def generate_random_string(self, length: int | None = None, chars: str = STR_CHARS) -> str:
        if length is None:
            length = self.generate_random_length()
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_random_int(self, length: int | None = None, chars: str = INT_CHARS) -> int:
        if length is None:
            length = self.generate_random_length()
        return int(''.join(random.choice(chars) for _ in range(length)))

    def generate_random_float(self, length: int | None = None, chars: str = INT_CHARS) -> float:
        if length is None:
            length = self.generate_random_length()
        point = random.randint(1, length)
        return float(''.join(random.choice(chars) for _ in range(point)) + '.' + ''.join(random.choice(chars) for _ in range(length - point)))

    def generate_random_list(self, length: int | None = None, obj: any = None) -> list[any]:
        value = []
        if length is None:
            length = self.generate_random_length()
        for _ in range(length):
            if isinstance(obj, str):
                value.append(self.generate_random_string(None, STR_CHARS_NO_SPECIAL))
            elif isinstance(obj, int):
                value.append(self.generate_random_int(None, INT_CHARS))
            elif isinstance(obj, float):
                value.append(self.generate_random_float(None, INT_CHARS))
            elif isinstance(obj, list):
                value.append(self.generate_random_list(None, obj[0]))
            elif isinstance(obj, dict):
                value.append(self.generate_random_dict(obj))
            elif isinstance(obj, bool):
                value.append(self.generate_random_bool())
        return value

    def generate_random_dict(self, obj: dict[str, any]) -> dict[str, any]:
        dic = {}
        for key, value in obj.items():
            if isinstance(value, str):
                dic[key] = self.generate_random_string(None, STR_CHARS_NO_SPECIAL)
            elif isinstance(value, int):
                dic[key] = self.generate_random_int(None, INT_CHARS)
            elif isinstance(value, float):
                dic[key] = self.generate_random_float(None, INT_CHARS)
            elif isinstance(value, list):
                dic[key] = self.generate_random_list(None, value[0])
            elif isinstance(value, dict):
                dic[key] = self.generate_random_dict(value)
            elif isinstance(value, bool):
                dic[key] = self.generate_random_bool()
        return dic

    def sample_from_list(self, length: int | None = None, population: list[any] = None) -> any:
        """
        sample a list of unique random numbers from a population
        """
        if length is None:
            length = self.generate_random_length()
        return random.sample(population, length)
