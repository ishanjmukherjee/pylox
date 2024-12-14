from typing import List, Optional

from lox.expr import Assign, Binary, Expr, Grouping, Literal, Logical, Unary, Variable
from lox.stmt import Block, Expression, If, Print, Stmt, Var
from lox.token import Token
from lox.token_type import TokenType


class ParseError(Exception):
    """Custom exception for parsing errors in the Lox language."""

    pass


class Parser:
    """
    A recursive descent parser for the Lox language.

    Grammar:

    program     -> declaration* EOF ;
    declaration -> varDecl | statement ;
    varDecl     -> "var" IDENTIFIER ( "=" expression )? ";" ;
    statement   -> exprStmt | ifStmt | printStmt | block ;
    ifStmt      -> "if" "(" expression ")" statement ( "else" statement )? ;
    block       -> "{" declaration* "}" ;
    exprStmt    -> expression ";" ;
    printStmt   -> "print" expression ";" ;

    expression  -> assignment ;
    assignment  -> IDENTIFIER "=" assignment | logic_or ;
    logic_or    -> logic_and ( "or" logic_and )* ;
    logic_and   -> equality ( "and" equality)* ;
    equality    -> comparison ( ( "!=" | "==" ) comparison )* ;
    comparison  -> term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
    term        -> factor ( ( "-" | "+" ) factor )* ;
    factor      -> unary ( ( "/" | "*" ) unary )* ;
    unary       -> ( "!" | "-" ) unary | primary ;
    primary     -> NUMBER | STRING | "true" | "false" | "nil"
                | "(" expression ")" | IDENTIFIER;
    """

    def __init__(self, tokens: List[Token]):
        """
        Initialize the parser with a list of tokens to parse.

        Args:
            tokens: List of Token objects to be parsed
        """
        self.tokens = tokens
        self.current = 0

    def parse(self) -> List[Stmt]:
        """
        Parse tokens into a list of statements.

        Returns:
            A list of parsed statements that form the program.
            Empty list if only parse errors were encountered.
        """
        # This is intended to be Parser's only public method
        statements: List[Stmt] = []
        while not self.isAtEnd():
            decl = self.declaration()
            if decl is not None:
                statements.append(decl)
        return statements

    def declaration(self) -> Optional[Stmt]:
        """Parse a declaration."""
        # Example of error handling:
        # 2 + "two";  // type error: not caught at parse time
        # 2 + ;       // parse error: missing operand after +
        # print x;    // we still want this line to execute, so synchronize
        #                after the previous parse error
        try:
            # First look for a variable declaration
            if self.match(TokenType.VAR):
                return self.var_declaration()

            # If not a variable declaration, try a statement
            return self.statement()
        except ParseError:
            self.synchronize()
            return None

    def var_declaration(self) -> Stmt:
        """Parse a variable declaration."""
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")

        # (Optional) variable initialization
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Var(name, initializer)

    def statement(self) -> Stmt:
        """Parse a statement."""
        # Statements are either...
        # ... if...
        if self.match(TokenType.IF):
            return self.if_statement()
        # ... print...
        if self.match(TokenType.PRINT):
            return self.print_statement()
        # ... block...
        if self.match(TokenType.LEFT_BRACE):
            return Block(self.block())
        # ... or expression
        return self.expression_statement()

    def if_statement(self) -> Stmt:
        """Parse an if statement."""
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch = self.statement()
        else_branch = self.statement() if self.match(TokenType.ELSE) else None

        return If(condition, then_branch, else_branch)

    def print_statement(self) -> Stmt:
        """Parse a print statement."""
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Print(value)

    def block(self) -> List[Stmt]:
        """Parse a block of statements."""
        statements: List[Stmt] = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.isAtEnd():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def expression_statement(self) -> Stmt:
        """Parse an expression statement."""
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Expression(expr)

    def expression(self) -> Expr:
        """Parse an expression (lowest precedence level)."""
        return self.assignment()

    def assignment(self) -> Expr:
        """Parse an assignment expression."""
        expr = self.logical_or()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expr, Variable):
                name = expr.name
                return Assign(name, value)

            self.error(equals, "Invalid assignment target.")

        return expr

    def logical_or(self) -> Expr:
        """Parse a logical or expression (or)."""
        # Do you notice this method's tasteful naming divergence from the book,
        # which has a bare "or", in order to avoid shadowing Python's built-in
        # or?
        expr = self.logical_and()

        while self.match(TokenType.OR):
            op = self.previous()
            right = self.logical_and()
            expr = Logical(expr, op, right)

        return expr

    def logical_and(self) -> Expr:
        """Parse a logical and expression (and)."""
        expr = self.equality()

        while self.match(TokenType.AND):
            op = self.previous()
            right = self.equality()
            expr = Logical(expr, op, right)

        return expr

    def equality(self) -> Expr:
        """
        Parse an equality expression (==, !=).

        equality -> comparison ( ( "!=" | "==" ) comparison )*
        """
        expr = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)

        return expr

    def comparison(self) -> Expr:
        """
        Parse a comparison expression (>, >=, <, <=).

        comparison -> term ( ( ">" | ">=" | "<" | "<=" ) term )*
        """
        expr = self.term()

        while self.match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator = self.previous()
            right = self.term()
            expr = Binary(expr, operator, right)

        return expr

    def term(self) -> Expr:
        """
        Parse a term (+ or -).

        term -> factor ( ( "-" | "+" ) factor )*
        """
        expr = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            expr = Binary(expr, operator, right)

        return expr

    def factor(self) -> Expr:
        """
        Parse a factor (* or /).

        factor -> unary ( ( "/" | "*" ) unary )*
        """
        expr = self.unary()

        while self.match(TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.unary()
            expr = Binary(expr, operator, right)

        return expr

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

        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous())

        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

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

    def synchronize(self) -> None:
        """
        Synchronize the parser state after encountering an error.
        Discard tokens until reaching a likely statement boundary.
        """
        self.advance()

        while not self.isAtEnd():
            if self.previous().type == TokenType.SEMICOLON:
                return

            # Don't try to catch expression or block statements
            if self.peek().type in {
                TokenType.CLASS,
                TokenType.FUN,
                TokenType.VAR,
                TokenType.FOR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.PRINT,
                TokenType.RETURN,
            }:
                return

            self.advance()

    def error(self, token: Token, message: str) -> ParseError:
        """
        Create a parse error at the given token.

        Args:
            token: The Token where the error occurred
            message: Description of the error

        Returns:
            A ParseError exception
        """
        # Importing Lox inside error reporter avoids circular dependency at
        # the cost of having to import Lox on *every* error. But this is a
        # small cost: errors shouldn't happen a lot in normal operation, and
        # Python caches imports after the first time anyway.
        from lox.lox import Lox

        if token.type == TokenType.EOF:
            Lox.report(token.line, " at end", message)
        else:
            Lox.report(token.line, f" at '{token.lexeme}'", message)
        return ParseError()
