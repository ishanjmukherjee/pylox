from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from lox.expr import Expr
from lox.token import Token

R = TypeVar("R")


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: "StmtVisitor[R]") -> R:
        pass


class Expression(Stmt):
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept(self, visitor: "StmtVisitor[R]") -> R:
        return visitor.visit_expression_stmt(self)


class Print(Stmt):
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept(self, visitor: "StmtVisitor[R]") -> R:
        return visitor.visit_print_stmt(self)


class If(Stmt):
    def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Stmt):
        self.condition = condition
        self.else_branch = else_branch
        self.then_branch = then_branch

    def accept(self, visitor: "StmtVisitor[R]") -> R:
        return visitor.visit_if_stmt(self)


class While(Stmt):
    def __init__(self, condition: Expr, body: Stmt):
        self.condition = condition
        self.body = body

    def accept(self, visitor: "StmtVisitor[R]") -> R:
        return visitor.visit_while_stmt(self)


class Var(Stmt):
    def __init__(self, name: Token, initializer: Expr | None):
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: "StmtVisitor[R]") -> R:
        return visitor.visit_var_stmt(self)


class Block(Stmt):
    def __init__(self, statements: List[Stmt]):
        self.statements = statements

    def accept(self, visitor: "StmtVisitor[R]") -> R:
        return visitor.visit_block_stmt(self)


class Return(Stmt):
    def __init__(self, keyword: Token, value: Expr | None):
        self.keyword = keyword
        self.value = value

    def accept(self, visitor: "StmtVisitor[R]") -> R:
        return visitor.visit_return_stmt(self)


class Function(Stmt):
    def __init__(self, name: Token, params: List[Token], body: List[Stmt]):
        self.name = name
        self.params = params
        self.body = body

    def accept(self, visitor: "StmtVisitor[R]") -> R:
        return visitor.visit_function_stmt(self)


class StmtVisitor(Generic[R], ABC):
    @abstractmethod
    def visit_expression_stmt(self, stmt: Expression) -> R:
        pass

    @abstractmethod
    def visit_print_stmt(self, stmt: Print) -> R:
        pass

    @abstractmethod
    def visit_var_stmt(self, stmt: Var) -> R:
        pass

    @abstractmethod
    def visit_block_stmt(self, stmt: Block) -> R:
        pass

    @abstractmethod
    def visit_if_stmt(self, stmt: If) -> R:
        pass

    @abstractmethod
    def visit_while_stmt(self, stmt: While) -> R:
        pass

    @abstractmethod
    def visit_function_stmt(self, stmt: Function) -> R:
        pass

    @abstractmethod
    def visit_return_stmt(self, stmt: Return) -> R:
        pass
