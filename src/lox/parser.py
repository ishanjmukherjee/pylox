from typing import List, Optional

from lox.expr import Binary, Expr, Grouping, Literal, Unary
from lox.token import Token
from lox.token_type import TokenType


class ParseError(Exception):
    """Custom exception for parsing errors in the Lox language."""

    pass


class Parser:
    """
    A recursive descent parser for the Lox language.

    Takes a list of tokens and produces an AST. Operator precedence and
    associativity follows this grammar:

    expression -> equality
    equality   -> comparison ( ( "!=" | "==" ) comparison )*
    comparison -> term ( ( ">" | ">=" | "<" | "<=" ) term )*
    term       -> factor ( ( "-" | "+" ) factor )*
    factor     -> unary ( ( "/" | "*" ) unary )*
    unary      -> ( "!" | "-" ) unary | primary
    primary    -> NUMBER | STRING | "true" | "false" | "nil" | "(" expression ")"
    """

    def __init__(self, tokens: List[Token]):
        """
        Initialize the parser with a list of tokens to parse.

        Args:
            tokens: List of Token objects to be parsed
        """
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Optional[Expr]:
        """
        Parse the tokens into an AST.

        Returns:
            The root node of the AST if successful, None if there was an error
        """
        try:
            return self.expression()
        except ParseError:
            return None

    def expression(self) -> Expr:
        """Parse an expression (lowest precedence level)."""
        return self.equality()

    def equality(self) -> Expr:
        """
        Parse an equality expression (==, !=).

        equality -> comparison ( ( "!=" | "==" ) comparison )*
        """
        expr_node = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr_node = Binary(expr_node, operator, right)

        return expr_node

    def comparison(self) -> Expr:
        """
        Parse a comparison expression (>, >=, <, <=).

        comparison -> term ( ( ">" | ">=" | "<" | "<=" ) term )*
        """
        expr_node = self.term()

        while self.match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator = self.previous()
            right = self.term()
            expr_node = Binary(expr_node, operator, right)

        return expr_node

    def term(self) -> Expr:
        """
        Parse a term (+ or -).

        term -> factor ( ( "-" | "+" ) factor )*
        """
        expr_node = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            expr_node = Binary(expr_node, operator, right)

        return expr_node

    def factor(self) -> Expr:
        """
        Parse a factor (* or /).

        factor -> unary ( ( "/" | "*" ) unary )*
        """
        expr_node = self.unary()

        while self.match(TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.unary()
            expr_node = Binary(expr_node, operator, right)

        return expr_node

    def unary(self) -> Expr:
        """
        Parse a unary expression (! or -).

        unary -> ( "!" | "-" ) unary | primary
        """
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)

        return self.primary()

    def primary(self) -> Expr:
        """
        Parse a primary expression (literals, parentheses).

        primary -> NUMBER | STRING | "true" | "false" | "nil" | "(" expression ")"
        """
        if self.match(TokenType.FALSE):
            return Literal(False)
        if self.match(TokenType.TRUE):
            return Literal(True)
        if self.match(TokenType.NIL):
            return Literal(None)

        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)

        if self.match(TokenType.LEFT_PAREN):
            expr_node = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr_node)

        raise self.error(self.peek(), "Expect expression.")

    def match(self, *token_types: TokenType) -> bool:
        """
        Check if the current token matches any of the given types.
        If so, consume the token and return True.

        Args:
            token_types: Variable number of TokenType to match against

        Returns:
            True if a match was found and consumed, False otherwise
        """
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        """
        Consume the current token if it matches the expected type.

        Args:
            token_type: The expected TokenType
            message: Error message if the token doesn't match

        Returns:
            The consumed Token

        Raises:
            ParseError: If the current token doesn't match the expected type
        """
        if self.check(token_type):
            return self.advance()

        raise self.error(self.peek(), message)

    def check(self, token_type: TokenType) -> bool:
        """
        Check if the current token is of the given type without consuming it.

        Args:
            token_type: The TokenType to check against

        Returns:
            True if current token matches the type, False otherwise
        """
        if self.isAtEnd():
            return False
        return self.peek().type == token_type

    def advance(self) -> Token:
        """
        Consume the current token and return it.

        Returns:
            The consumed Token
        """
        if not self.isAtEnd():
            self.current += 1
        return self.previous()

    def isAtEnd(self) -> bool:
        """
        Check if we've reached the end of the token stream.

        Returns:
            True if at end of input, False otherwise
        """
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        """
        Return the current token without consuming it.

        Returns:
            The current Token
        """
        return self.tokens[self.current]

    def previous(self) -> Token:
        """
        Return the most recently consumed token.

        Returns:
            The previously consumed Token
        """
        return self.tokens[self.current - 1]

    def error(self, token: Token, message: str) -> ParseError:
        """
        Create a parse error at the given token.

        Args:
            token: The Token where the error occurred
            message: Description of the error

        Returns:
            A ParseError exception
        """
        if token.type == TokenType.EOF:
            # Importing Lox inside error reporter avoids circular dependency at
            # the cost of having to import Lox on *every* error. But this is a
            # small cost: errors shouldn't happen a lot in normal operation, and
            # Python caches imports after the first time anyway.
            from lox.lox import Lox

            Lox.report(token.line, " at end", message)
        else:
            from lox.lox import Lox

            Lox.report(token.line, f" at '{token.lexeme}'", message)
        return ParseError()
