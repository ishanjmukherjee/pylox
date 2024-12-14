from dataclasses import dataclass
from typing import Any

from lox.token_type import TokenType


# @dataclass automatically generates __init__ for initialization and __eq__ for
# equality comparison. It also lets you make Tokens immutable via frozen=True.
@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str  # The actual source text this token represents
    literal: Any  # Runtime value for literals (strings, numbers)
    line: int  # Line where the token appears in source

    def __str__(self) -> str:
        return f"{self.type} {self.lexeme} {self.literal}"
