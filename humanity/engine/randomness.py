"""The version-1 Mulberry32 stream, including JavaScript's 32-bit semantics.

Using the same stream preserves existing save files and lets us compare the
Python engine against the original implementation. Rendering never calls it.
"""

from typing import Sequence, TypeVar

from .models import World

T = TypeVar("T")
MASK = 0xFFFFFFFF


def hash_seed(seed: str) -> int:
    value = 2166136261
    for char in str(seed):
        code = ord(char)
        # The original JS iterates code points, then reads their first UTF-16 unit.
        if code > 0xFFFF:
            code = 0xD800 + ((code - 0x10000) >> 10)
        value = ((value ^ code) * 16777619) & MASK
    return value


def random(world: World) -> float:
    world.rng = (world.rng + 0x6D2B79F5) & MASK
    value = world.rng
    value = ((value ^ (value >> 15)) * (value | 1)) & MASK
    product = ((value ^ (value >> 7)) * (value | 61)) & MASK
    value = (value ^ ((value + product) & MASK)) & MASK
    return ((value ^ (value >> 14)) & MASK) / 4294967296


def between(world: World, minimum: float, maximum: float) -> float:
    return minimum + random(world) * (maximum - minimum)


def pick(world: World, items: Sequence[T]) -> T:
    return items[int(random(world) * len(items))]


def shuffle(world: World, items: Sequence[T]) -> list[T]:
    result = list(items)
    for index in range(len(result) - 1, 0, -1):
        other = int(random(world) * (index + 1))
        result[index], result[other] = result[other], result[index]
    return result


def clamp(value: float, minimum: float = 0, maximum: float = 1) -> float:
    return max(minimum, min(maximum, value))


def mean(values) -> float:
    # Explicit left-to-right addition also stays consistent on Python 3.12+.
    total = 0.0
    count = 0
    for value in values:
        total += value
        count += 1
    return total / count if count else 0.0
