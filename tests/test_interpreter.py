from typing import Any

import pytest

from lox.expr import Binary, Grouping, Literal, Unary
from lox.interpreter import Interpreter, RuntimeError
from lox.token import Token
from lox.token_type import TokenType


# Use pytest fixture for getting a fresh copy each time
@pytest.fixture
def interpreter() -> Interpreter:
    """Provide a fresh interpreter instance for each test."""
    return Interpreter()


@pytest.fixture
def make_token() -> Any:
    """Helper to create tokens with less boilerplate."""

    # The nested _make_token follows the "fixture factory" pattern. If we
    # instead defined something like
    # def token():
    #   return Token(TokenType.NUMBER, "123", 123, 1)
    # we would only be able to use it like
    # def test_token(token):
    #   assert token.type == TokenType.NUMBER
    #   assert token.lexeme == "123"
    # With the factory, we get more flexibility:
    # def test_tokens(make_token):
    #   num_token = make_token(TokenType.NUMBER, "123", 123, 3)
    #   str_token = make_token(TokenType.STRING, "ab", "ab", 1)
    #   ret_token = make_token(TokenType.RETURN, "return", "return", 4)
    def _make_token(
        type_: TokenType, lexeme: str = "", literal: Any = None, line: int = 1
    ) -> Token:
        return Token(type_, lexeme, literal, line)

    return _make_token


def test_literal_expression(interpreter: Interpreter) -> None:
    """Test evaluation of literal expressions."""
    cases = [
        (None, "nil"),
        (123.0, "123"),
        (123.5, "123.5"),
        ("hello", "hello"),
        (True, "true"),
        (False, "false"),
    ]

    for value, expected in cases:
        # Check if expression evaluation works
        expr = Literal(value)
        result = interpreter._evaluate(expr)
        assert result == value

        # Check if stringification of evaluated expression works
        assert interpreter._stringify(result) == expected


def test_grouping_expression(interpreter: Interpreter) -> None:
    """Test evaluation of grouped expressions."""
    inner = Literal(42.0)
    expr = Grouping(inner)
    result = interpreter._evaluate(expr)
    assert result == 42.0
    assert interpreter._stringify(result) == "42"


@pytest.mark.parametrize(
    "operator_type,operand,expected",
    [
        (TokenType.MINUS, 42.0, -42.0),
        (TokenType.BANG, True, False),
        (TokenType.BANG, False, True),
        (TokenType.BANG, None, True),
        (TokenType.BANG, "hello", False),
        (TokenType.BANG, 123.0, False),
        (TokenType.BANG, 0.0, False),
    ],
)
def test_unary_expression(
    interpreter: Interpreter,
    make_token: Any,
    operator_type: TokenType,
    operand: Any,
    expected: Any,
) -> None:
    """Test evaluation of unary expressions."""
    operator = make_token(operator_type)
    expr = Unary(operator, Literal(operand))
    assert interpreter._evaluate(expr) == expected


def test_unary_minus_type_error(interpreter: Interpreter, make_token: Any) -> None:
    """Test that unary minus raises error for non-numeric operand."""
    operator = make_token(TokenType.MINUS)
    expr = Unary(operator, Literal("not a number"))
    with pytest.raises(RuntimeError) as exc_info:
        interpreter._evaluate(expr)
    assert "must be a number" in str(exc_info.value)


@pytest.mark.parametrize(
    "operator_type,left,right,expected",
    [
        # Arithmetic
        (TokenType.PLUS, 2.0, 3.0, 5.0),
        (TokenType.MINUS, 5.0, 3.0, 2.0),
        (TokenType.STAR, 4.0, 3.0, 12.0),
        (TokenType.SLASH, 10.0, 2.0, 5.0),
        # String concatenation
        (TokenType.PLUS, "Hello, ", "World!", "Hello, World!"),
        # Comparison
        (TokenType.GREATER, 5.0, 3.0, True),
        (TokenType.GREATER, 3.0, 3.0, False),
        (TokenType.GREATER_EQUAL, 3.0, 3.0, True),
        (TokenType.GREATER_EQUAL, 2.0, 3.0, False),
        (TokenType.LESS, 2.0, 3.0, True),
        (TokenType.LESS, 3.0, 3.0, False),
        (TokenType.LESS_EQUAL, 3.0, 3.0, True),
        (TokenType.LESS_EQUAL, 4.0, 3.0, False),
        # Equality
        (TokenType.EQUAL_EQUAL, 3.0, 3.0, True),
        (TokenType.EQUAL_EQUAL, "hello", "hello", True),
        (TokenType.EQUAL_EQUAL, True, True, True),
        (TokenType.EQUAL_EQUAL, None, None, True),
        (TokenType.EQUAL_EQUAL, 3.0, 4.0, False),
        (TokenType.EQUAL_EQUAL, "hello", "world", False),
        (TokenType.EQUAL_EQUAL, True, False, False),
        (TokenType.EQUAL_EQUAL, None, False, False),
        (TokenType.BANG_EQUAL, 3.0, 4.0, True),
        (TokenType.BANG_EQUAL, "hello", "world", True),
        (TokenType.BANG_EQUAL, True, False, True),
        (TokenType.BANG_EQUAL, None, False, True),
        (TokenType.BANG_EQUAL, 3.0, 3.0, False),
        (TokenType.BANG_EQUAL, "hello", "hello", False),
    ],
)
def test_binary_expression(
    interpreter: Interpreter,
    make_token: Any,
    operator_type: TokenType,
    left: Any,
    right: Any,
    expected: Any,
) -> None:
    """Test evaluation of binary expressions."""
    operator = make_token(operator_type)
    expr = Binary(Literal(left), operator, Literal(right))
    assert interpreter._evaluate(expr) == expected


@pytest.mark.parametrize(
    "operator_type,left,right,error_message",
    [
        (TokenType.MINUS, "naht", "numbers", "must be numbers"),
        (TokenType.SLASH, "naht", "numbers", "must be numbers"),
        (TokenType.STAR, "naht", "numbers", "must be numbers"),
        (TokenType.GREATER, "naht", "numbers", "must be numbers"),
        (TokenType.GREATER_EQUAL, "naht naht", "numbers", "must be numbers"),
        (TokenType.LESS, "naht naht naht", "numbers", "must be numbers"),
        (TokenType.LESS_EQUAL, "naht naht naht naht", "numbers", "must be numbers"),
        (TokenType.PLUS, "oiler", 2.72, "must be two numbers or two strings"),
        (TokenType.PLUS, 3.14, "pie", "must be two numbers or two strings"),
    ],
)
def test_binary_type_errors(
    interpreter: Interpreter,
    make_token: Any,
    operator_type: TokenType,
    left: Any,
    right: Any,
    error_message: str,
) -> None:
    """Test that binary operations raise appropriate type errors."""
    operator = make_token(operator_type)
    expr = Binary(Literal(left), operator, Literal(right))
    with pytest.raises(RuntimeError) as exc_info:
        interpreter._evaluate(expr)
    assert error_message in str(exc_info.value)


def test_interpret_method_handles_runtime_error(
    interpreter: Interpreter,
    make_token: Any,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """Test that interpret() method properly handles and reports runtime errors."""
    # Create an expression that will cause a runtime error
    operator = make_token(TokenType.MINUS)
    expr = Unary(operator, Literal("naht a number"))

    # Capture stdout/stderr
    interpreter.interpret(expr)
    captured = capfd.readouterr()

    # Verify error was reported
    assert "must be a number" in captured.err
    assert "[line 1]" in captured.err


def test_truthy_values(interpreter: Interpreter) -> None:
    """Test truthiness rules."""
    # Falsey values
    assert not interpreter._is_truthy(None)
    assert not interpreter._is_truthy(False)

    # Truthy values
    assert interpreter._is_truthy(True)
    assert interpreter._is_truthy(0.0)
    assert interpreter._is_truthy("")
    assert interpreter._is_truthy("false")
    # Implementation detail, but important for extensibility: even non-Lox types
    # should be truthy
    assert interpreter._is_truthy([])
