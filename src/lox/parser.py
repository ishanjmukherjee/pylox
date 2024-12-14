from typing import List, Optional

from lox.expr import (
    Assign,
    Binary,
    Call,
    Expr,
    Grouping,
    Literal,
    Logical,
    Unary,
    Variable,
)
from lox.stmt import Block, Expression, Function, If, Print, Return, Stmt, Var, While
from lox.token import Token
from lox.token_type import TokenType


class ParseError(Exception):
    """Custom exception"""

    pass


class Parser:
    """
    A recursive descent parser for the Lox language.

    Grammar:

    program     -> declaration* EOF ;
    declaration -> funDecl | varDecl | statement ;
    funDecl     -> "fun" function ;
    function    -> IDENTIFIER "(" parameters? ")" block ;
    parameters  -> IDENTIFIER ( "," IDENTIFIER )* ;
    varDecl     -> "var" IDENTIFIER ( "=" expression )? ";" ;
    statement   -> exprStmt | forStmt | ifStmt | printStmt | returnStmt |
                |  whileStmt | block ;
    forStmt     -> "for" "(" (varDecl | exprStmt | ";" )
                   expression? ";"
                   expression? ")" statement ;
    ifStmt      -> "if" "(" expression ")" statement ( "else" statement )? ;
    returnStmt  -> "return" expression? ";" ;
    block       -> "{" declaration* "}" ;
    exprStmt    -> expression ";" ;
    printStmt   -> "print" expression ";" ;
    whileStmt   -> "while" "(" expression ")" statement ;

    expression  -> assignment ;
    assignment  -> IDENTIFIER "=" assignment | logic_or ;
    logic_or    -> logic_and ( "or" logic_and )* ;
    logic_and   -> equality ( "and" equality)* ;
    equality    -> comparison ( ( "!=" | "==" ) comparison )* ;
    comparison  -> term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
    term        -> factor ( ( "-" | "+" ) factor )* ;
    factor      -> unary ( ( "/" | "*" ) unary )* ;
    unary       -> ( "!" | "-" ) unary | call ;
    call        -> primary ( "(" arguments? ")" )* ;
    arguments   -> expression ( "," expression )* ;
    primary     -> NUMBER | STRING | "true" | "false" | "nil"
                | "(" expression ")" | IDENTIFIER;
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> List[Stmt]:
        """
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
        # Example of error handling:
        # 2 + "two";  // type error: not caught at parse time
        # 2 + ;       // parse error: missing operand after +
        # print x;    // we still want this line to execute, so synchronize
        #                after the previous parse error
        try:
            if self.match(TokenType.FUN):
                return self.function("function")
            if self.match(TokenType.VAR):
                return self.var_declaration()

            # If not a function or a variable declaration, try a statement
            return self.statement()
        except ParseError:
            self.synchronize()
            return None

    def var_declaration(self) -> Stmt:
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")

        # (Optional) variable initialization
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Var(name, initializer)

    def while_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.")
        body = self.statement()

        return While(condition, body)

    def statement(self) -> Stmt:
        # Statements are either...
        # ... for...
        if self.match(TokenType.FOR):
            return self.for_statement()
        # ... if...
        if self.match(TokenType.IF):
            return self.if_statement()
        # ... print...
        if self.match(TokenType.PRINT):
            return self.print_statement()
        # ... return...
        if self.match(TokenType.RETURN):
            return self.return_statement()
        # ... while...
        if self.match(TokenType.WHILE):
            return self.while_statement()
        # ... block...
        if self.match(TokenType.LEFT_BRACE):
            return Block(self.block())
        # ... or expression
        return self.expression_statement()

    def function(self, kind: str) -> Function:
        name = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name.")

        self.consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        parameters = []

        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                if len(parameters) >= 255:
                    self.error(self.peek(), "Can't have more than 255 parameters.")

                parameters.append(
                    self.consume(TokenType.IDENTIFIER, "Expect parameter name.")
                )

                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self.consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self.block()
        return Function(name, parameters, body)

    def return_statement(self) -> Stmt:
        keyword = self.previous()
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return Return(keyword, value)

    def for_statement(self) -> Stmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        if self.match(TokenType.SEMICOLON):
            # Initializer has been omitted
            initializer = None
        elif self.match(TokenType.VAR):
            # Initializer is a variable
            initializer = self.var_declaration()
        else:
            # Initializer is an expression
            initializer = self.expression_statement()

        # If the next token is a semicolon, the condition has been omitted
        condition = self.expression() if not self.check(TokenType.SEMICOLON) else None
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        # If the next token is a right paren, the increment has been omitted
        increment = self.expression() if not self.check(TokenType.RIGHT_PAREN) else None
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after loop condition.")

        body = self.statement()

        # Desugaring
        if increment is not None:
            body = Block([body, Expression(increment)])
        if condition is None:
            condition = Literal(True)
        body = While(condition, body)
        if initializer is not None:
            body = Block([initializer, body])

        return body

    def if_statement(self) -> Stmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch = self.statement()
        else_branch = self.statement() if self.match(TokenType.ELSE) else None

        return If(condition, then_branch, else_branch)

    def print_statement(self) -> Stmt:
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Print(value)

    def block(self) -> List[Stmt]:
        statements: List[Stmt] = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.isAtEnd():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def expression_statement(self) -> Stmt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Expression(expr)

    def expression(self) -> Expr:
        """Lowest precedence level"""
        return self.assignment()

    def assignment(self) -> Expr:
        """="""
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
        """or"""
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
        """and"""
        expr = self.equality()

        while self.match(TokenType.AND):
            op = self.previous()
            right = self.equality()
            expr = Logical(expr, op, right)

        return expr

    def equality(self) -> Expr:
        """==, !="""
        expr = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)

        return expr

    def comparison(self) -> Expr:
        """>, >=, <, <="""
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
        """+, -"""
        expr = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            expr = Binary(expr, operator, right)

        return expr

    def factor(self) -> Expr:
        """*, /"""
        expr = self.unary()

        while self.match(TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.unary()
            expr = Binary(expr, operator, right)

        return expr

    def unary(self) -> Expr:
        """! or -"""
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)

        return self.call()

    def call(self) -> Expr:
        expr = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            else:
                break

        return expr

    def finish_call(self, callee: Expr) -> Expr:
        arguments = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    self.error(self.peek(), "Can't have more than 255 arguments.")
                arguments.append(self.expression())
                if not self.match(TokenType.COMMA):
                    break

        paren = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")

        return Call(callee, paren, arguments)

    def primary(self) -> Expr:
        """literals, parentheses"""
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
        """Consumes token if check succeeds"""
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()

        raise self.error(self.peek(), message)

    def check(self, token_type: TokenType) -> bool:
        """Doesn't consume token if check succeeds"""
        if self.isAtEnd():
            return False
        return self.peek().type == token_type

    def advance(self) -> Token:
        """Consume the current token and return it."""
        if not self.isAtEnd():
            self.current += 1
        return self.previous()

    def isAtEnd(self) -> bool:
        """
        Returns:
            True if at end of input, False otherwise
        """
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[self.current]

    def previous(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self.current - 1]

    def synchronize(self) -> None:
        """
        Advance while discarding tokens until reaching a likely statement
        boundary.
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
