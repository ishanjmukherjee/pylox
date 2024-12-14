from typing import Any, List

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule

from lox.ast_printer import AstPrinter
from lox.expr import Binary, Expr, Grouping, Literal, Unary
from lox.token import Token
from lox.token_type import TokenType


# Custom strategies for generating test data
@st.composite
def tokens(draw) -> Token:
    """Generate valid tokens for our expressions."""
    token_types = [
        TokenType.MINUS,
        TokenType.PLUS,
        TokenType.SLASH,
        TokenType.STAR,
        TokenType.BANG,
        TokenType.EQUAL_EQUAL,
        TokenType.GREATER,
        TokenType.LESS,
    ]

    type_ = draw(st.sampled_from(token_types))
    lexeme = {
        TokenType.MINUS: "-",
        TokenType.PLUS: "+",
        TokenType.SLASH: "/",
        TokenType.STAR: "*",
        TokenType.BANG: "!",
        TokenType.EQUAL_EQUAL: "==",
        TokenType.GREATER: ">",
        TokenType.LESS: "<",
    }[type_]

    line = draw(st.integers(min_value=1, max_value=1000))
    return Token(type_, lexeme, None, line)


@st.composite
def literals(draw) -> Any:
    """Generate valid literal values."""
    return draw(
        st.one_of(
            st.none(),
            st.booleans(),
            st.floats(allow_nan=False, allow_infinity=False),
            # min_size=1 ensures no empty strings.
            # Blacklisting parens ensures the LPAREN == RPAREN in the structural
            # check below doesn't mess up.
            st.text(
                min_size=1,
                alphabet=st.characters(
                    blacklist_characters={"(", ")"}, blacklist_categories=("Cs",)
                ),
            ),
        )
    )


@st.composite
def expressions(draw, max_depth=3) -> "Expr":
    """Recursively generate valid expression trees."""
    if max_depth <= 1:
        # Base case: generate a literal
        return Literal(draw(literals()))

    # Recursive case: generate more complex expressions
    expr_type = draw(st.sampled_from(["binary", "grouping", "unary", "literal"]))

    if expr_type == "binary":
        left = draw(expressions(max_depth=max_depth - 1))
        right = draw(expressions(max_depth=max_depth - 1))
        operator = draw(tokens())
        return Binary(left, operator, right)
    elif expr_type == "grouping":
        expr = draw(expressions(max_depth=max_depth - 1))
        return Grouping(expr)
    elif expr_type == "unary":
        operator = draw(tokens())
        right = draw(expressions(max_depth=max_depth - 1))
        return Unary(operator, right)
    else:
        return Literal(draw(literals()))


class TestAstPrinter:
    @given(expressions())
    def test_printer_output_format(self, expr):
        """Test that printer output follows expected format."""
        printer = AstPrinter()
        result = printer.print(expr)

        # Basic structural checks
        assert isinstance(result, str)
        assert len(result) > 0

        # Check parentheses matching
        assert result.count("(") == result.count(")")

    @given(literals())
    def test_literal_printing(self, value):
        """Test that literals are printed correctly."""
        expr = Literal(value)
        printer = AstPrinter()
        result = printer.print(expr)

        if value is None:
            assert result == "nil"
        else:
            assert str(value) in result


class ExpressionStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.expressions: List[Expr] = []
        self.printer = AstPrinter()

    @rule(expr=expressions())
    def add_expression(self, expr):
        """Add a new expression and verify it can be printed."""
        try:
            # Verify we can print it
            self.printer.print(expr)
            self.expressions.append(expr)
        except Exception as e:
            pytest.fail(f"Failed to process expression: {str(e)}")

    @rule(data=st.data())
    def combine_expressions(self, data):
        """Combine existing expressions into larger ones."""
        if len(self.expressions) < 2:
            return

        expr1 = data.draw(st.sampled_from(self.expressions))
        expr2 = data.draw(st.sampled_from(self.expressions))
        operator = data.draw(tokens())

        new_expr = Binary(expr1, operator, expr2)
        # Verify we can print the combined expression
        self.printer.print(new_expr)
        self.expressions.append(new_expr)

    @rule(data=st.data())
    def wrap_in_grouping(self, data):
        """Wrap an existing expression in a grouping."""
        if not self.expressions:
            return

        expr = data.draw(st.sampled_from(self.expressions))
        new_expr = Grouping(expr)
        # Verify we can print the grouped expression
        self.printer.print(new_expr)
        self.expressions.append(new_expr)

    @rule(data=st.data())
    def apply_unary(self, data):
        """Apply a unary operator to an existing expression."""
        if not self.expressions:
            return

        expr = data.draw(st.sampled_from(self.expressions))
        operator = data.draw(tokens())
        new_expr = Unary(operator, expr)
        # Verify we can print the unary expression
        self.printer.print(new_expr)
        self.expressions.append(new_expr)


# Convert state machine into a runnable test
TestExpressions = ExpressionStateMachine.TestCase


def test_specific_cases():
    printer = AstPrinter()

    # Test deeply nested expressions
    expr = Binary(
        Binary(Literal(1), Token(TokenType.PLUS, "+", None, 1), Literal(2)),
        Token(TokenType.STAR, "*", None, 1),
        Binary(Literal(4), Token(TokenType.MINUS, "-", None, 1), Literal(3)),
    )
    result = printer.print(expr)
    assert result == "(* (+ 1 2) (- 4 3))"

    # Test unary with grouping
    expr = Unary(Token(TokenType.MINUS, "-", None, 1), Grouping(Literal(42)))
    result = printer.print(expr)
    assert result == "(- (group 42))"

    # Test nil literal
    expr = Literal(None)
    result = printer.print(expr)
    assert result == "nil"
