from typing import Any, Dict, List

from lox.token import Token
from lox.token_type import TokenType


class Scanner:
    keywords: Dict[str, TokenType] = {
        name.lower(): getattr(TokenType, name)
        for name in [
            "AND",
            "CLASS",
            "ELSE",
            "FALSE",
            "FOR",
            "FUN",
            "IF",
            "NIL",
            "OR",
            "PRINT",
            "RETURN",
            "SUPER",
            "THIS",
            "TRUE",
            "VAR",
            "WHILE",
        ]
    }

    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> List[Token]:
        while not self._is_at_end():
            # We are at the beginning of the next lexeme
            self.start = self.current
            self._scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def _scan_token(self) -> None:
        c = self._advance()
        match c:
            case "(":
                self._add_token(TokenType.LEFT_PAREN)
            case ")":
                self._add_token(TokenType.RIGHT_PAREN)
            case "{":
                self._add_token(TokenType.LEFT_BRACE)
            case "}":
                self._add_token(TokenType.RIGHT_BRACE)
            case ",":
                self._add_token(TokenType.COMMA)
            case ".":
                self._add_token(TokenType.DOT)
            case "-":
                self._add_token(TokenType.MINUS)
            case "+":
                self._add_token(TokenType.PLUS)
            case ";":
                self._add_token(TokenType.SEMICOLON)
            case "*":
                self._add_token(TokenType.STAR)
            case "!":
                token_type = (
                    TokenType.BANG_EQUAL if self._match("=") else TokenType.BANG
                )
                self._add_token(token_type)
            case "=":
                token_type = (
                    TokenType.EQUAL_EQUAL if self._match("=") else TokenType.EQUAL
                )
                self._add_token(token_type)
            case "<":
                token_type = (
                    TokenType.LESS_EQUAL if self._match("=") else TokenType.LESS
                )
                self._add_token(token_type)
            case ">":
                token_type = (
                    TokenType.GREATER_EQUAL if self._match("=") else TokenType.GREATER
                )
                self._add_token(token_type)
            case "/":
                if self._match("/"):
                    # A comment goes until the end of the line
                    while self._peek() != "\n" and not self._is_at_end():
                        self._advance()
                else:
                    self._add_token(TokenType.SLASH)
            case " " | "\r" | "\t":
                pass
            case "\n":
                self.line += 1
            case '"':
                self._string()
            case _:
                if c.isdigit():
                    self._number()
                elif c.isalpha() or c == "_":
                    self._identifier()
                else:
                    from lox.lox import Lox

                    Lox.error(self.line, "Unexpected character.")

    def _string(self) -> None:
        while self._peek() != '"' and not self._is_at_end():
            if self._peek() == "\n":
                self.line += 1
            self._advance()

        if self._is_at_end():
            from lox.lox import Lox

            Lox.error(self.line, "Unterminated string.")
            return

        # The closing "
        self._advance()

        # Trim the surrounding quotes
        value = self.source[self.start + 1 : self.current - 1]
        self._add_token(TokenType.STRING, value)

    def _number(self) -> None:
        while self._peek().isdigit():
            self._advance()

        # Look for a fractional part
        if self._peek() == "." and self._peek_next().isdigit():
            # Consume the '.'
            self._advance()

            while self._peek().isdigit():
                self._advance()

        value = float(self.source[self.start : self.current])
        self._add_token(TokenType.NUMBER, value)

    def _identifier(self) -> None:
        # Maximal munch
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        # Get the text of the identifier
        text = self.source[self.start : self.current]

        # Look up the token type, defaulting to IDENTIFIER if not a keyword
        token_type = self.keywords.get(text, TokenType.IDENTIFIER)
        self._add_token(token_type)

    def _peek(self) -> str:
        if self._is_at_end():
            # Use '' as the sentinel value instead of the Java '\0' in the
            # book, since Python strings aren't null terminated
            return ""
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return ""
        return self.source[self.current + 1]

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        self.current += 1
        return self.source[self.current - 1]

    def _match(self, expected: str) -> bool:
        if self._is_at_end():
            return False
        if self.source[self.current] != expected:
            return False

        self.current += 1
        return True

    def _add_token(self, type: TokenType, literal: Any = None) -> None:
        text = self.source[self.start : self.current]
        self.tokens.append(Token(type, text, literal, self.line))
