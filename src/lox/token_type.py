from enum import Enum, auto, unique


# The @unique decorator catches enum members which have the same value during
# definition time. While not necessary here since we use auto() for each member,
# it's better to be explicit about it.
# A design note on the Python language: why is @unique opt-in instead of the
# default? Because some use cases legitimately want duplicate values (like
# aliases). Making it opt-in follows the PEP20 principle of "Explicit is better
# than implicit." See https://peps.python.org/pep-0020/.
@unique
class TokenType(Enum):
    # Single-character tokens
    # Use auto() for automatic value assignment, see
    # https://docs.python.org/3/library/enum.html#enum.auto.
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    SEMICOLON = auto()
    SLASH = auto()
    STAR = auto()

    # One or two character tokens
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()

    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Keywords
    AND = auto()
    CLASS = auto()
    ELSE = auto()
    FALSE = auto()
    FUN = auto()
    FOR = auto()
    IF = auto()
    NIL = auto()
    OR = auto()
    PRINT = auto()
    RETURN = auto()
    SUPER = auto()
    THIS = auto()
    TRUE = auto()
    VAR = auto()
    WHILE = auto()

    EOF = auto()
