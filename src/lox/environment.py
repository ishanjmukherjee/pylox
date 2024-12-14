from typing import Any, Dict

from lox.token import Token


class Environment:
    def __init__(self, enclosing: "Environment | None" = None):
        self.values: Dict[str, Any] = {}
        self.enclosing = enclosing

    # define() always creates/updates a variable in the current scope, without
    # looking at outer scopes. assign() searches through the scope chain to find
    # an existing variable to update (and throws an error if it can't find one).
    # Some illustrative code to show how define() and assign() differ:
    # var answer = 42;    // Uses define() -- creates in current scope
    # {
    #   answer = 420;     // Uses assign() -- updates outer x
    #   var answer = 68;  // Uses define() -- creates NEW x in inner scope
    #   answer = 70;      // Uses assign() -- updates inner x
    # }
    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def get(self, name: Token) -> Any:
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        from lox.interpreter import RuntimeError

        raise RuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def assign(self, name: Token, value: Any) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        from lox.interpreter import RuntimeError

        raise RuntimeError(name, f"Undefined variable '{name.lexeme}'.")
