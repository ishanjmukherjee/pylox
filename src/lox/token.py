from dataclasses import dataclass
from typing import Any

from lox.token_type import TokenType


@dataclass
class Token:
    """A token in the Lox language.

    The token stores both the type of token and the source text that created it.
    For literals, it also stores the actual runtime value. Line numbers are
    tracked for error reporting.
    """

    type: TokenType
    lexeme: str  # The actual source text this token represents
    literal: Any  # Runtime value for literals (strings, numbers)
    line: int  # Line where the token appears in source

    def __str__(self) -> str:
        return f"{self.type} {self.lexeme} {self.literal}"
