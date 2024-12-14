import time
from typing import Any, List

from lox.environment import Environment
from lox.expr import (
    Assign,
    Binary,
    Call,
    Expr,
    ExprVisitor,
    Grouping,
    Literal,
    Logical,
    Unary,
    Variable,
)
from lox.lox_callable import LoxCallable, LoxFunction, Return
from lox.stmt import (
    Block,
    Expression,
    Function,
    If,
    Print,
    Stmt,
    StmtVisitor,
    Var,
    While,
)
from lox.token import Token
from lox.token_type import TokenType


class RuntimeError(Exception):
    """Lox runtime error with associated token for error reporting."""

    def __init__(self, token: Token, message: str):
        super().__init__(message)
        self.token = token


class Interpreter(ExprVisitor[Any], StmtVisitor[None]):
    """Evaluates Lox expressions."""

    def __init__(self):
        self.globals = Environment()
        self.environment = self.globals

        class ClockFunction(LoxCallable):
            def call(self, interpreter: Interpreter, arguments: List[Any]) -> float:
                return float(time.time())

            def arity(self) -> int:
                return 0

            def __str__(self) -> str:
                return "<native fn>"

        self.globals.define("clock", ClockFunction())

    def interpret(self, statements: List[Stmt]) -> None:
        try:
            for statement in statements:
                self._execute(statement)
        except RuntimeError as error:
            from lox.lox import Lox

            Lox.runtime_error(error)

    def visit_literal(self, expr: Literal) -> Any:
        """Return the literal's value directly."""
        return expr.value

    def visit_logical(self, expr: Logical) -> Any:
        """Evaluate logical expressions (or, and)."""
        left = self._evaluate(expr.left)

        # Short circuiting logic
        # Return the last value the program actually evaluates. Examples:
        # OR: if left is true, right no longer needs to be evaluated, and left
        # is returned
        # AND: if left is false, right no longer needs to be evaluated, and left
        # is returned
        if expr.operator.type == TokenType.OR:
            if self._is_truthy(left):
                return left
        else:  # TokenType.AND
            if not self._is_truthy(left):
                return left

        return self._evaluate(expr.right)

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

    def visit_variable_expr(self, expr: Variable) -> Any:
        return self.environment.get(expr.name)

    def visit_assign_expr(self, expr: Assign) -> Any:
        value = self._evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value

    def visit_call(self, expr: Call) -> Any:
        callee = self._evaluate(expr.callee)

        arguments = []
        for argument in expr.arguments:
            arguments.append(self._evaluate(argument))

        if not isinstance(callee, LoxCallable):
            raise RuntimeError(expr.paren, "Can only call functions and classes.")

        function = callee
        if len(arguments) != function.arity():
            raise RuntimeError(
                expr.paren,
                f"Expected {function.arity()} arguments but got {len(arguments)}.",
            )

        return function.call(self, arguments)

    def visit_function_stmt(self, stmt: Function) -> None:
        function = LoxFunction(stmt, self.environment)
        self.environment.define(stmt.name.lexeme, function)
        return None

    def visit_return_stmt(self, stmt: Return) -> None:
        value = None
        if stmt.value is not None:
            value = self._evaluate(stmt.value)
        raise Return(value)

    def visit_expression_stmt(self, stmt: Expression) -> None:
        self._evaluate(stmt.expression)

    def visit_if_stmt(self, stmt: If) -> None:
        if self._is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self._execute(stmt.else_branch)
        return None

    def visit_print_stmt(self, stmt: Print) -> None:
        value = self._evaluate(stmt.expression)
        print(self._stringify(value))

    def visit_var_stmt(self, stmt: Var) -> None:
        value = None
        if stmt.initializer is not None:
            value = self._evaluate(stmt.initializer)
        self.environment.define(stmt.name.lexeme, value)

    def visit_while_stmt(self, stmt: While) -> None:
        while self._is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.body)

    def visit_block_stmt(self, stmt: Block) -> None:
        self._execute_block(stmt.statements, Environment(self.environment))

    def _execute_block(self, statements: List[Stmt], environment: Environment) -> None:
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = previous

    def _execute(self, stmt: Stmt) -> None:
        stmt.accept(self)

    def _evaluate(self, expr: Expr) -> Any:
        return expr.accept(self)

    def _is_truthy(self, obj: Any) -> bool:
        # None and False are falsey, everything else is truthy.
        if obj is None:
            return False
        if isinstance(obj, bool):
            return obj
        return True

    def _is_equal(self, a: Any, b: Any) -> bool:
        # None is only equal to None
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b

    def _check_number_operand(self, operator: Token, operand: Any) -> None:
        if isinstance(operand, float):
            return
        raise RuntimeError(operator, "Operand must be a number.")

    def _check_number_operands(self, operator: Token, left: Any, right: Any) -> None:
        if isinstance(left, float) and isinstance(right, float):
            return
        raise RuntimeError(operator, "Operands must be numbers.")

    def _stringify(self, obj: None | float | bool | str) -> str:
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
