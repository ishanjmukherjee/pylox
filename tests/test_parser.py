from typing import List

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule

from lox.expr import Binary, Grouping, Literal, Unary
from lox.parser import Parser
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
def valid_expressions(draw) -> List[Token]:
    """Generate token sequences that represent valid expressions."""

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
            parser = Parser([token, Token(TokenType.EOF, "", None, 1)])
            expr = parser.parse()
            assert isinstance(expr, Literal)
            assert expr.value == expected_value

    def test_grouping_expression(self):
        """Test parsing of grouped expressions."""
        tokens = [
            Token(TokenType.LEFT_PAREN, "(", None, 1),
            Token(TokenType.NUMBER, "123", 123.0, 1),
            Token(TokenType.RIGHT_PAREN, ")", None, 1),
            Token(TokenType.EOF, "", None, 1),
        ]
        parser = Parser(tokens)
        expr = parser.parse()
        assert isinstance(expr, Grouping)
        assert isinstance(expr.expression, Literal)
        assert expr.expression.value == 123.0

    def test_unary_expression(self):
        """Test parsing of unary expressions."""
        tokens = [
            Token(TokenType.MINUS, "-", None, 1),
            Token(TokenType.NUMBER, "123", 123.0, 1),
            Token(TokenType.EOF, "", None, 1),
        ]
        parser = Parser(tokens)
        expr = parser.parse()
        assert isinstance(expr, Unary)
        assert expr.operator.type == TokenType.MINUS
        assert isinstance(expr.right, Literal)
        assert expr.right.value == 123.0

    def test_binary_expression(self):
        """Test parsing of binary expressions."""
        tokens = [
            Token(TokenType.NUMBER, "1", 1.0, 1),
            Token(TokenType.PLUS, "+", None, 1),
            Token(TokenType.NUMBER, "2", 2.0, 1),
            Token(TokenType.EOF, "", None, 1),
        ]
        parser = Parser(tokens)
        expr = parser.parse()
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
            Token(TokenType.EOF, "", None, 1),
        ]
        parser = Parser(tokens)
        expr = parser.parse()
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
                    Token(TokenType.EOF, "", None, 1),
                ],
                lambda expr: (
                    isinstance(expr, Binary)
                    and expr.operator.type == TokenType.LESS
                    and isinstance(expr.left, Literal)
                    and expr.left.value == 1.0
                    and isinstance(expr.right, Literal)
                    and expr.right.value == 2.0
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
                    Token(TokenType.EOF, "", None, 1),
                ],
                lambda expr: (
                    isinstance(expr, Binary)
                    and expr.operator.type == TokenType.LESS
                    and isinstance(expr.left, Binary)
                    and expr.left.operator.type == TokenType.LESS
                    and isinstance(expr.right, Literal)
                    and expr.right.value == 3.0
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
                    Token(TokenType.EOF, "", None, 1),
                ],
                lambda expr: (
                    isinstance(expr, Binary)
                    and expr.operator.type == TokenType.LESS
                    and isinstance(expr.left, Literal)
                    and isinstance(expr.right, Binary)
                    and expr.right.operator.type == TokenType.PLUS
                    and isinstance(expr.right.left, Literal)
                    and isinstance(expr.right.right, Literal)
                ),
            ),
            # All comparison operators: 1 <= 2 >= 3 < 4 > 5
            (
                [
                    Token(TokenType.NUMBER, "1", 1.0, 1),
                    Token(TokenType.LESS_EQUAL, "<=", None, 1),
                    Token(TokenType.NUMBER, "2", 2.0, 1),
                    Token(TokenType.GREATER_EQUAL, ">=", None, 1),
                    Token(TokenType.NUMBER, "3", 3.0, 1),
                    Token(TokenType.LESS, "<", None, 1),
                    Token(TokenType.NUMBER, "4", 4.0, 1),
                    Token(TokenType.GREATER, ">", None, 1),
                    Token(TokenType.NUMBER, "5", 5.0, 1),
                    Token(TokenType.EOF, "", None, 1),
                ],
                lambda expr: (
                    isinstance(expr, Binary)
                    and expr.operator.type == TokenType.GREATER
                    and isinstance(expr.left, Binary)
                    and expr.left.operator.type == TokenType.LESS
                    and isinstance(expr.left.left, Binary)
                ),
            ),
            # Parenthesized comparison: (1 < 2) > 3
            (
                [
                    Token(TokenType.LEFT_PAREN, "(", None, 1),
                    Token(TokenType.NUMBER, "1", 1.0, 1),
                    Token(TokenType.LESS, "<", None, 1),
                    Token(TokenType.NUMBER, "2", 2.0, 1),
                    Token(TokenType.RIGHT_PAREN, ")", None, 1),
                    Token(TokenType.GREATER, ">", None, 1),
                    Token(TokenType.NUMBER, "3", 3.0, 1),
                    Token(TokenType.EOF, "", None, 1),
                ],
                lambda expr: (
                    isinstance(expr, Binary)
                    and expr.operator.type == TokenType.GREATER
                    and isinstance(expr.left, Grouping)
                    and isinstance(expr.left.expression, Binary)
                    and expr.left.expression.operator.type == TokenType.LESS
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
            Token(TokenType.EOF, "", None, 1),
        ]
        parser = Parser(tokens)
        result = parser.parse()
        # When we get a ParseError, the parser returns None, following the book
        assert result is None

    @given(valid_expressions())
    @settings(max_examples=100)
    def test_parser_with_valid_expressions(self, tokens):
        """Test parser with structurally valid expressions."""
        parser = Parser(tokens)
        result = parser.parse()
        assert result is not None  # should always parse successfully
        assert isinstance(result, (Binary, Grouping, Literal, Unary))


# The state machine "inverts" the parser in a sense. The parser takes arbitrary
# input and checks if it's valid. The state machine starts with known-valid
# pieces and composes them in ways that preserve validity.
@settings(max_examples=100, stateful_step_count=30)
class ParserStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.expressions = []  # Store complete, valid expressions

    @rule(value=literal_tokens())
    def add_literal_expression(self, value):
        """Add a new literal as a complete expression"""
        tokens = [value, Token(TokenType.EOF, "", None, 1)]
        parser = Parser(tokens)
        result = parser.parse()
        assert result is not None
        self.expressions.append(tokens[:-1])  # Store without EOF

    @rule(data=st.data())
    def combine_with_binary_op(self, data):
        """Combine two existing expressions with a binary operator"""
        # We need at least two expressions to combine
        if len(self.expressions) < 2:
            return

        # Randomly pick two expressions from our list of previously built valid
        # expressions.
        # self.expressions is a list of token lists, each representing a valid
        # expression.
        left = data.draw(st.sampled_from(self.expressions))
        right = data.draw(st.sampled_from(self.expressions))

        # Randomly pick a binary operator
        op = data.draw(
            st.sampled_from(
                [
                    Token(TokenType.PLUS, "+", None, 1),
                    Token(TokenType.MINUS, "-", None, 1),
                    Token(TokenType.STAR, "*", None, 1),
                ]
            )
        )

        # Combine into a new expression: left + op + right + EOF
        new_tokens = left + [op] + right + [Token(TokenType.EOF, "", None, 1)]

        # Verify the new expression is valid by parsing it
        parser = Parser(new_tokens)
        result = parser.parse()
        assert result is not None  # make sure it parsed successfully

        # Store the new valid expression (without EOF) for future combinations.
        # So, if self.expressions just started with two literals, Token(123) and
        # Token(456), and we drew a "+", [Token(123), Token("+"), Token(456)]
        # would be added as a valid expression. Now we have 3 valid expressions
        # in our "store" we can draw from to build even more complex
        # expressions.
        # This is a common technique for "deriving" valid expressions, most
        # memorably described in the rules for the MU-puzzle in "Godel, Escher,
        # Bach" by Douglas Hofstadter
        self.expressions.append(new_tokens[:-1])

    @rule(data=st.data())
    def wrap_in_parens(self, data):
        """Wrap an existing expression in parentheses"""
        # We need at least one expression to wrap in parens
        if not self.expressions:
            return

        expr = data.draw(st.sampled_from(self.expressions))
        new_tokens = (
            [Token(TokenType.LEFT_PAREN, "(", None, 1)]
            + expr
            + [Token(TokenType.RIGHT_PAREN, ")", None, 1)]
        )
        parser = Parser(new_tokens + [Token(TokenType.EOF, "", None, 1)])
        result = parser.parse()
        assert result is not None
        self.expressions.append(new_tokens)


# Convert state machine into a runnable test
TestParserStateMachine = ParserStateMachine.TestCase
