import sys
from pathlib import Path

from lox.scanner import Scanner


class Lox:
    had_error = False

    @classmethod
    def error(cls, line: int, message: str) -> None:
        """ "Report a basic syntax error with line number but no additional
        context.

        Args:
            line: Line number where the error occurred
            message: Description of the error"""
        cls.report(line, "", message)

    @classmethod
    def report(cls, line: int, where: str, message: str) -> None:
        """Print error to stderr and set error flag.

        All error reporting goes through this method to ensure consistent
        presentation across the interpreter. Uses stderr for unbuffered output,
        ensuring errors appear immediately even if the program crashes, and
        enabling terminal-specific formatting like red text.

        Args:
            line: Line number where the error occurred
            where: Additional context about error location (e.g. "in function
            declaration")
            message: Description of the error"""
        print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
        cls.had_error = True


def run_file(path: str) -> None:
    """Execute a Lox script from a file."""
    try:
        source = Path(path).read_text(encoding="utf-8")
        run(source)
    except UnicodeDecodeError as e:
        print(f"Error: Could not decode file {path}: {e}", file=sys.stderr)
        sys.exit(66)  # EX_NOINPUT
    # Exit if there was a syntax error
    if Lox.had_error:
        sys.exit(65)  # EX_DATAERR


def run_prompt() -> None:
    """Run an interactive prompt (REPL) for the Lox interpreter."""
    while True:
        try:
            line = input("> ")
            run(line)
            Lox.had_error = False
        except (EOFError, KeyboardInterrupt):
            break


def run(source: str) -> None:
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    # For now, just print the tokens
    for token in tokens:
        print(token)


def main() -> None:
    if len(sys.argv) > 2:
        print("Usage: pylox [script]")
        # Command line usage error.
        # Defined in https://man.freebsd.org/cgi/man.cgi?query=sysexits&apropos=0&sektion=0&manpath=FreeBSD+4.3-RELEASE&format=html.
        sys.exit(64)
    elif len(sys.argv) == 2:
        run_file(sys.argv[1])
    else:
        run_prompt()
