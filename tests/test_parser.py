from typing import List

from hypothesis import given, settings
from hypothesis import strategies as st

from lox.expr import Binary, Grouping, Literal, Unary
from lox.parser import Parser
from lox.stmt import Expression
from lox.token import Token
from lox.token_type import TokenType


@st.composite
def simple_tokens(draw) -> Token:
    """Generate tokens for basic expressions."""
    token_types = [
        TokenType.MINUS,
        TokenType.PLUS,
        TokenType.SLASH,
        TokenType.STAR,
        TokenType.BANG,
        TokenType.EQUAL_EQUAL,
        TokenType.BANG_EQUAL,
        TokenType.GREATER,
        TokenType.GREATER_EQUAL,
        TokenType.LESS,
        TokenType.LESS_EQUAL,
        TokenType.LEFT_PAREN,
        TokenType.RIGHT_PAREN,
    ]

    token_type = draw(st.sampled_from(token_types))
    # Notice we create the dictionary and assign the lexeme in the same line
    lexeme = {
        TokenType.MINUS: "-",
        TokenType.PLUS: "+",
        TokenType.SLASH: "/",
        TokenType.STAR: "*",
        TokenType.BANG: "!",
        TokenType.EQUAL_EQUAL: "==",
        TokenType.BANG_EQUAL: "!=",
        TokenType.GREATER: ">",
        TokenType.GREATER_EQUAL: ">=",
        TokenType.LESS: "<",
        TokenType.LESS_EQUAL: "<=",
        TokenType.LEFT_PAREN: "(",
        TokenType.RIGHT_PAREN: ")",
    }[token_type]

    line = draw(st.integers(min_value=1, max_value=10000))
    return Token(token_type, lexeme, None, line)


@st.composite
def literal_tokens(draw) -> Token:
    """Generate literal tokens."""
    # Generate a literal value
    literal_value = draw(
        st.one_of(
            st.none(),
            st.booleans(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(min_size=1, alphabet=st.characters(blacklist_categories=("Cs",))),
        )
    )

    # Determine token type based on literal value
    if literal_value is None:
        return Token(TokenType.NIL, "nil", None, 1)
    elif isinstance(literal_value, bool):
        token_type = TokenType.TRUE if literal_value else TokenType.FALSE
        lexeme = str(literal_value).lower()  # you can str() Python booleans!
        return Token(token_type, lexeme, literal_value, 1)
    elif isinstance(literal_value, float):
        return Token(TokenType.NUMBER, str(literal_value), literal_value, 1)
    else:  # string
        return Token(TokenType.STRING, f'"{literal_value}"', literal_value, 1)


@st.composite
def valid_expression_stmts(draw) -> List[Token]:
    """Generate token sequences that represent valid expression statements."""

    def generate_expr(depth=0) -> List[Token]:
        if depth > 5:  # Limit nesting depth
            # Base case: just generate a literal
            return [draw(literal_tokens())]

        expr_type = draw(st.sampled_from(["literal", "binary", "unary", "grouping"]))

        if expr_type == "literal":
            return [draw(literal_tokens())]
        elif expr_type == "binary":
            # Generate left expr, operator, right expr
            left = generate_expr(depth + 1)
            op = draw(
                st.sampled_from(
                    [
                        Token(TokenType.PLUS, "+", None, 1),
                        Token(TokenType.MINUS, "-", None, 1),
                        Token(TokenType.STAR, "*", None, 1),
                        Token(TokenType.SLASH, "/", None, 1),
                    ]
                )
            )
            right = generate_expr(depth + 1)
            # left and right are both lists: we use + to flatten and join them
            # with the operator in between
            return left + [op] + right
        elif expr_type == "unary":
            op = draw(
                st.sampled_from(
                    [
                        Token(TokenType.MINUS, "-", None, 1),
                        Token(TokenType.BANG, "!", None, 1),
                    ]
                )
            )
            expr = generate_expr(depth + 1)
            return [op] + expr
        else:  # grouping
            expr = generate_expr(depth + 1)
            return (
                [Token(TokenType.LEFT_PAREN, "(", None, 1)]
                + expr
                + [Token(TokenType.RIGHT_PAREN, ")", None, 1)]
            )

    tokens = generate_expr()
    tokens.append(Token(TokenType.SEMICOLON, ";", None, 1))
    tokens.append(Token(TokenType.EOF, "", None, 1))
    return tokens


class TestParser:
    def test_literal_expression(self):
        """Test parsing of literal values."""
        literals = [
            (Token(TokenType.NUMBER, "123", 123.0, 1), 123.0),
            (Token(TokenType.STRING, '"hello"', "hello", 1), "hello"),
            (Token(TokenType.TRUE, "true", True, 1), True),
            (Token(TokenType.FALSE, "false", False, 1), False),
            (Token(TokenType.NIL, "nil", None, 1), None),
        ]

        for token, expected_value in literals:
            parser = Parser(
                [
                    token,
                    Token(TokenType.SEMICOLON, ";", None, 1),
                    Token(TokenType.EOF, "", None, 1),
                ]
            )
            statements = parser.parse()
            assert isinstance(statements, list)
            assert len(statements) == 1
            assert isinstance(statements[0], Expression)
            assert isinstance(statements[0].expression, Literal)
            assert statements[0].expression.value == expected_value

    def test_grouping_expression(self):
        """Test parsing of grouped expressions."""
        tokens = [
            Token(TokenType.LEFT_PAREN, "(", None, 1),
            Token(TokenType.NUMBER, "123", 123.0, 1),
            Token(TokenType.RIGHT_PAREN, ")", None, 1),
            Token(TokenType.SEMICOLON, ";", None, 1),
            Token(TokenType.EOF, "", None, 1),
        ]
        parser = Parser(tokens)
        statements = parser.parse()
        assert isinstance(statements, list)
        assert len(statements) == 1
        assert isinstance(statements[0], Expression)
        assert isinstance(statements[0].expression, Grouping)
        assert isinstance(statements[0].expression.expression, Literal)
        assert statements[0].expression.expression.value == 123.0

    def test_unary_expression(self):
        """Test parsing of unary expressions."""
        tokens = [
            Token(TokenType.MINUS, "-", None, 1),
            Token(TokenType.NUMBER, "123", 123.0, 1),
            Token(TokenType.SEMICOLON, ";", None, 1),
            Token(TokenType.EOF, "", None, 1),
        ]
        parser = Parser(tokens)
        statements = parser.parse()
        assert isinstance(statements, list)
        assert len(statements) == 1
        assert isinstance(statements[0], Expression)
        assert isinstance(statements[0].expression, Unary)
        assert statements[0].expression.operator.type == TokenType.MINUS
        assert isinstance(statements[0].expression.right, Literal)
        assert statements[0].expression.right.value == 123.0

    def test_binary_expression(self):
        """Test parsing of binary expressions."""
        tokens = [
            Token(TokenType.NUMBER, "1", 1.0, 1),
            Token(TokenType.PLUS, "+", None, 1),
            Token(TokenType.NUMBER, "2", 2.0, 1),
            Token(TokenType.SEMICOLON, ";", None, 1),
            Token(TokenType.EOF, "", None, 1),
        ]
        parser = Parser(tokens)
        statements = parser.parse()
        assert isinstance(statements, list)
        assert len(statements) == 1
        assert isinstance(statements[0], Expression)
        expr = statements[0].expression
        assert isinstance(expr, Binary)
        assert expr.operator.type == TokenType.PLUS
        assert isinstance(expr.left, Literal)
        assert isinstance(expr.right, Literal)
        assert expr.left.value == 1.0
        assert expr.right.value == 2.0

    def test_operator_precedence(self):
        """Test that operator precedence is correctly handled."""
        # Test "1 + 2 * 3" is parsed as "(1 + (2 * 3))"
        tokens = [
            Token(TokenType.NUMBER, "1", 1.0, 1),
            Token(TokenType.PLUS, "+", None, 1),
            Token(TokenType.NUMBER, "2", 2.0, 1),
            Token(TokenType.STAR, "*", None, 1),
            Token(TokenType.NUMBER, "3", 3.0, 1),
            Token(TokenType.SEMICOLON, ";", None, 1),
            Token(TokenType.EOF, "", None, 1),
        ]
        parser = Parser(tokens)
        statements = parser.parse()
        assert isinstance(statements, list)
        assert len(statements) == 1
        assert isinstance(statements[0], Expression)
        expr = statements[0].expression
        assert isinstance(expr, Binary)
        assert expr.operator.type == TokenType.PLUS
        assert isinstance(expr.right, Binary)
        assert expr.right.operator.type == TokenType.STAR

    def test_comparison_expressions(self):
        """Test parsing of comparison expressions and their precedence."""
        # Test cases with expected AST structure:
        cases = [
            # Simple comparison: 1 < 2
            (
                [
                    Token(TokenType.NUMBER, "1", 1.0, 1),
                    Token(TokenType.LESS, "<", None, 1),
                    Token(TokenType.NUMBER, "2", 2.0, 1),
                    Token(TokenType.SEMICOLON, ";", None, 1),
                    Token(TokenType.EOF, "", None, 1),
                ],
                lambda stmts: (
                    isinstance(stmts, list)
                    and isinstance(stmts[0], Expression)
                    and isinstance(stmts[0].expression, Binary)
                    and stmts[0].expression.operator.type == TokenType.LESS
                    and isinstance(stmts[0].expression.left, Literal)
                    and stmts[0].expression.left.value == 1.0
                    and isinstance(stmts[0].expression.right, Literal)
                    and stmts[0].expression.right.value == 2.0
                ),
            ),
            # Chained comparison: 1 < 2 < 3 (should parse as (1 < 2) < 3)
            (
                [
                    Token(TokenType.NUMBER, "1", 1.0, 1),
                    Token(TokenType.LESS, "<", None, 1),
                    Token(TokenType.NUMBER, "2", 2.0, 1),
                    Token(TokenType.LESS, "<", None, 1),
                    Token(TokenType.NUMBER, "3", 3.0, 1),
                    Token(TokenType.SEMICOLON, ";", None, 1),
                    Token(TokenType.EOF, "", None, 1),
                ],
                lambda stmts: (
                    isinstance(stmts, list)
                    and isinstance(stmts[0], Expression)
                    and isinstance(stmts[0].expression, Binary)
                    and stmts[0].expression.operator.type == TokenType.LESS
                    and isinstance(stmts[0].expression.left, Binary)
                    and stmts[0].expression.left.operator.type == TokenType.LESS
                    and isinstance(stmts[0].expression.right, Literal)
                    and stmts[0].expression.right.value == 3.0
                ),
            ),
            # Mixed operators: 1 < 2 + 3
            (
                [
                    Token(TokenType.NUMBER, "1", 1.0, 1),
                    Token(TokenType.LESS, "<", None, 1),
                    Token(TokenType.NUMBER, "2", 2.0, 1),
                    Token(TokenType.PLUS, "+", None, 1),
                    Token(TokenType.NUMBER, "3", 3.0, 1),
                    Token(TokenType.SEMICOLON, ";", None, 1),
                    Token(TokenType.EOF, "", None, 1),
                ],
                lambda stmts: (
                    isinstance(stmts, list)
                    and isinstance(stmts[0], Expression)
                    and isinstance(stmts[0].expression, Binary)
                    and stmts[0].expression.operator.type == TokenType.LESS
                    and isinstance(stmts[0].expression.left, Literal)
                    and isinstance(stmts[0].expression.right, Binary)
                    and stmts[0].expression.right.operator.type == TokenType.PLUS
                    and isinstance(stmts[0].expression.right.left, Literal)
                    and isinstance(stmts[0].expression.right.right, Literal)
                ),
            ),
        ]

        for tokens, validator in cases:
            parser = Parser(tokens)
            expr = parser.parse()
            assert expr is not None, "Parser returned None"
            assert validator(expr), f"Invalid expression for tokens: {tokens}"

    def test_error_handling(self):
        """Test parser error handling."""
        # Test unmatched parentheses
        tokens = [
            Token(TokenType.LEFT_PAREN, "(", None, 1),
            Token(TokenType.NUMBER, "123", 123.0, 1),
            Token(TokenType.SEMICOLON, ";", None, 1),
            Token(TokenType.EOF, "", None, 1),
        ]
        parser = Parser(tokens)
        statements = parser.parse()
        assert isinstance(statements, list)
        # All ParseErrors means an empty list is returned
        assert len(statements) == 0

    @given(valid_expression_stmts())
    @settings(max_examples=100)
    def test_parser_with_valid_expression_stmts(self, tokens):
        """Test parser with structurally valid expressions."""
        parser = Parser(tokens)
        statements = parser.parse()
        assert isinstance(statements, list)
        assert len(statements) == 1  # should always parse successfully
        assert isinstance(statements[0], Expression)
        assert isinstance(statements[0].expression, (Binary, Grouping, Literal, Unary))
