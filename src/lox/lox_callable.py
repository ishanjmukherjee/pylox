from abc import ABC, abstractmethod
from typing import Any, List

from lox.environment import Environment
from lox.stmt import Function


class LoxCallable(ABC):
    @abstractmethod
    # interpreter is of type Interpreter, but we don't import that class from
    # interpreter.py to avoid a circular dependency (or messy ways to get around
    # that circular dependency). Duck typing go brr.
    def call(self, interpreter, arguments: List[Any]) -> Any:
        pass

    @abstractmethod
    def arity(self) -> int:
        pass


class Return(Exception):
    def __init__(self, value: Any):
        super().__init__(None)
        self.value = value


class LoxFunction(LoxCallable):
    def __init__(self, declaration: Function, closure: Environment):
        self.declaration = declaration
        self.closure = closure

    def call(self, interpreter, arguments: List[Any]) -> Any:
        environment = Environment(self.closure)

        for i in range(len(self.declaration.params)):
            environment.define(self.declaration.params[i].lexeme, arguments[i])

        try:
            interpreter._execute_block(self.declaration.body, environment)
        except Return as return_value:
            return return_value.value

        return None

    def arity(self) -> int:
        return len(self.declaration.params)

    def __str__(self) -> str:
        # We want behavior like:
        # print add; // <fn add>
        return f"<fn {self.declaration.name.lexeme}>"
