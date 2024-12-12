from typing import Any

from lox.expr import Binary, Expr, ExprVisitor, Grouping, Literal, Unary
from lox.token import Token
from lox.token_type import TokenType


class RuntimeError(Exception):
    """Lox runtime error with associated token for error reporting."""

    def __init__(self, token: Token, message: str):
        super().__init__(message)
        self.token = token


class Interpreter(ExprVisitor[Any]):
    """Evaluates Lox expressions."""

    def interpret(self, expression: Expr) -> None:
        """
        Evaluate an expression and print the result.
        Handle runtime errors by reporting them through the Lox class.
        """
        try:
            value = self._evaluate(expression)
            print(self._stringify(value))
        except RuntimeError as error:
            from lox.lox import Lox

            Lox.runtime_error(error)

    def visit_literal(self, expr: Literal) -> Any:
        """Return the literal's value directly."""
        return expr.value

    def visit_grouping(self, expr: Grouping) -> Any:
        """Evaluate the expression inside the grouping."""
        return self._evaluate(expr.expression)

    def visit_unary(self, expr: Unary) -> Any:
        """Evaluate unary operations (-, !)."""
        right = self._evaluate(expr.right)

        match expr.operator.type:
            case TokenType.MINUS:
                self._check_number_operand(expr.operator, right)
                return -float(right)
            case TokenType.BANG:
                return not self._is_truthy(right)

        # Unreachable
        return None

    def visit_binary(self, expr: Binary) -> Any:
        """Evaluate binary operations (+, -, *, /, >, >=, <, <=, ==, !=)."""
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)

        match expr.operator.type:
            case TokenType.GREATER:
                self._check_number_operands(expr.operator, left, right)
                return float(left) > float(right)
            case TokenType.GREATER_EQUAL:
                self._check_number_operands(expr.operator, left, right)
                return float(left) >= float(right)
            case TokenType.LESS:
                self._check_number_operands(expr.operator, left, right)
                return float(left) < float(right)
            case TokenType.LESS_EQUAL:
                self._check_number_operands(expr.operator, left, right)
                return float(left) <= float(right)
            case TokenType.BANG_EQUAL:
                return not self._is_equal(left, right)
            case TokenType.EQUAL_EQUAL:
                return self._is_equal(left, right)
            case TokenType.MINUS:
                self._check_number_operands(expr.operator, left, right)
                return float(left) - float(right)
            case TokenType.PLUS:
                # Handle both number addition and string concatenation
                if isinstance(left, float) and isinstance(right, float):
                    return left + right
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                raise RuntimeError(
                    expr.operator, "Operands must be two numbers or two strings."
                )
            case TokenType.SLASH:
                self._check_number_operands(expr.operator, left, right)
                return float(left) / float(right)
            case TokenType.STAR:
                self._check_number_operands(expr.operator, left, right)
                return float(left) * float(right)

        # Unreachable
        return None

    def _evaluate(self, expr: Expr) -> Any:
        """Helper method to evaluate an expression."""
        return expr.accept(self)

    def _is_truthy(self, obj: Any) -> bool:
        """
        Determine the truthiness of a value.
        None and False are falsey, everything else is truthy.
        """
        if obj is None:
            return False
        if isinstance(obj, bool):
            return obj
        return True

    def _is_equal(self, a: Any, b: Any) -> bool:
        """
        Check equality of two values.
        None is only equal to None.
        """
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b

    def _check_number_operand(self, operator: Token, operand: Any) -> None:
        """Verify that an operand is a number."""
        if isinstance(operand, float):
            return
        raise RuntimeError(operator, "Operand must be a number.")

    def _check_number_operands(self, operator: Token, left: Any, right: Any) -> None:
        """Verify that both operands are numbers."""
        if isinstance(left, float) and isinstance(right, float):
            return
        raise RuntimeError(operator, "Operands must be numbers.")

    def _stringify(self, obj: None | float | bool | str) -> str:
        """Convert a Python value to a Lox value string representation."""
        if obj is None:
            return "nil"

        if isinstance(obj, float):
            text = str(obj)
            # Show integer values without decimal point
            if text.endswith(".0"):
                text = text[:-2]
            return text

        if isinstance(obj, bool):
            # str(True) evaluates to "True"
            return str(obj).lower()

        return obj  # must be str at this point
