from lox.parser import Parser
from lox.scanner import Scanner

if __name__ == "__main__":
    # main()
    source = "1 <= 2 >= 3 < 4 > 5"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    expression = parser.parse()
    print(f"Source: {source}")
    print(f"AST: {expression}")
