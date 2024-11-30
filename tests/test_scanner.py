from hypothesis import given
from hypothesis import strategies as st

from lox.scanner import Scanner
from lox.token_type import TokenType


class TestScanner:
    def test_empty_source(self) -> None:
        scanner = Scanner("")
        tokens = scanner.scan_tokens()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_single_character_tokens(self) -> None:
        source = "(){},.-+;*"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        expected_types = [
            TokenType.LEFT_PAREN,
            TokenType.RIGHT_PAREN,
            TokenType.LEFT_BRACE,
            TokenType.RIGHT_BRACE,
            TokenType.COMMA,
            TokenType.DOT,
            TokenType.MINUS,
            TokenType.PLUS,
            TokenType.SEMICOLON,
            TokenType.STAR,
            TokenType.EOF,
        ]

        assert len(tokens) == len(expected_types)
        for token, expected_type in zip(tokens, expected_types, strict=False):
            assert token.type == expected_type

    # Exclude surrogate code points
    @given(st.text(alphabet=st.characters(blacklist_categories=("Cs",))))
    def test_scanner_handles_arbitrary_input(self, source: str) -> None:
        """Property: Scanner should never crash on valid Unicode input."""
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        assert len(tokens) >= 1
        assert tokens[-1].type == TokenType.EOF

    def test_string_literal(self) -> None:
        source = '"Hello, World!"'
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        assert len(tokens) == 2  # String token + EOF
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].literal == "Hello, World!"

    def test_number_literal(self) -> None:
        source = "123.45"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        assert len(tokens) == 2  # Number token + EOF
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].literal == 123.45

    def test_identifiers_and_keywords(self) -> None:
        source = "var myVar = true;"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        expected_types = [
            TokenType.VAR,
            TokenType.IDENTIFIER,
            TokenType.EQUAL,
            TokenType.TRUE,
            TokenType.SEMICOLON,
            TokenType.EOF,
        ]

        assert len(tokens) == len(expected_types)
        for token, expected_type in zip(tokens, expected_types, strict=False):
            assert token.type == expected_type

    def test_comments(self) -> None:
        source = "// This is a comment\n123"
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        assert len(tokens) == 2  # Number token + EOF
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].literal == 123.0
