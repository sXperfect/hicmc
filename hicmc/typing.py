from enum import Enum
from typing import Literal, Tuple, Union, Dict, Any, List, Callable
from numpy.typing import NDArray

Statistic = Callable[[NDArray], float]
Transform = Callable[[NDArray], NDArray]

class Axis(Enum):
    Row = 0
    Col = 1

    @property
    def other(self) -> 'Axis':
        if self is Axis.Row:
            return Axis.Col

        if self is Axis.Col:
            return Axis.Row

        raise RuntimeError()
