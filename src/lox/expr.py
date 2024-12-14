from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from lox.token import Token

# Use Generic type for visitor pattern
R = TypeVar("R")


# Jupiter; the Platonic ideal to inherit from
class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: "ExprVisitor[R]") -> R:
        pass


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: "ExprVisitor[R]") -> R:
        # Every accept() method has the same story:
        # visitor.visit_relevant_expr()
        return visitor.visit_binary(self)


class Logical(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: "ExprVisitor[R]") -> R:
        return visitor.visit_logical(self)


class Grouping(Expr):
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept(self, visitor: "ExprVisitor[R]") -> R:
        return visitor.visit_grouping(self)


class Literal(Expr):
    def __init__(self, value: Any):
        self.value = value

    def accept(self, visitor: "ExprVisitor[R]") -> R:
        return visitor.visit_literal(self)


class Unary(Expr):
    def __init__(self, operator: Token, right: Expr):
        self.operator = operator
        self.right = right

    def accept(self, visitor: "ExprVisitor[R]") -> R:
        return visitor.visit_unary(self)


class Variable(Expr):
    def __init__(self, name: Token):
        self.name = name

    def accept(self, visitor: "ExprVisitor[R]") -> R:
        return visitor.visit_variable_expr(self)


class Assign(Expr):
    def __init__(self, name: Token, value: Expr):
        self.name = name
        self.value = value

    def accept(self, visitor: "ExprVisitor[R]") -> R:
        return visitor.visit_assign_expr(self)


class ExprVisitor(Generic[R], ABC):
    @abstractmethod
    def visit_binary(self, expr: Binary) -> R:
        pass

    @abstractmethod
    def visit_grouping(self, expr: Grouping) -> R:
        pass

    @abstractmethod
    def visit_literal(self, expr: Literal) -> R:
        pass

    @abstractmethod
    def visit_unary(self, expr: Unary) -> R:
        pass
