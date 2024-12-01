from lox.ast_printer import AstPrinter
from lox.expr import Binary, Grouping, Literal
from lox.token import Token
from lox.token_type import TokenType

if __name__ == "__main__":
    # main()
    printer = AstPrinter()
    expr = Binary(
        Grouping(Literal(None)),
        Token(TokenType.MINUS, "-", None, 1),
        Grouping(Literal(None)),
    )
    print(f"Tree: {printer.print(expr)}\n")
